"""Meta Ads Campaign API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_db, get_campaign_generator
from app.database.models import (
    BusinessProfile,
    Campaign,
    CampaignAngle,
    CampaignCreative,
    CampaignStatus,
    HookType,
    AdFormat,
    PlatformPlacement,
    CreativeStatus,
)
from app.models.schemas import (
    CampaignCreateRequest,
    CampaignResponse,
    CampaignListResponse,
)
from app.services.campaign_generator import CampaignGeneratorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.post("/create", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignCreateRequest,
    db: AsyncSession = Depends(get_db),
    campaign_service: CampaignGeneratorService = Depends(get_campaign_generator),
):
    """Create a new Meta Ads campaign with 3 advertising angles."""
    # Get business profile
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == request.business_id)
    )
    business = result.scalar_one_or_none()

    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")

    # Build business data dict for AI
    business_data = {
        "name": business.name,
        "industry": business.industry,
        "description": business.description,
        "brand_voice": business.brand_voice,
        "brand_colors": business.brand_colors or [],
        "target_audience": business.target_audience,
        "unique_selling_points": business.unique_selling_points or [],
    }

    # Generate 3 advertising angles
    angles_data = await campaign_service.generate_angles(
        business=business_data,
        campaign_objective=request.campaign_objective,
        product_service=request.product_service,
        target_audience=request.target_audience,
    )

    # Create campaign in database
    campaign = Campaign(
        business_id=business.id,
        name=request.campaign_name,
        objective=request.campaign_objective,
        target_audience=request.target_audience,
        product_service=request.product_service,
        budget_range=request.budget_range,
        status=CampaignStatus.DRAFT,
    )
    db.add(campaign)
    await db.flush()

    # Create angles
    for i, angle_data in enumerate(angles_data[:3], start=1):
        hook_type_value = angle_data.get("hook_type", "pain_point")
        try:
            hook_type = HookType(hook_type_value)
        except ValueError:
            hook_type = HookType.PAIN_POINT

        angle = CampaignAngle(
            campaign_id=campaign.id,
            angle_number=i,
            hook_type=hook_type,
            title=angle_data.get("title", f"Angle {i}")[:255],
            description=angle_data.get("description"),
            target_emotion=angle_data.get("target_emotion"),
        )
        db.add(angle)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign.id)
        .options(
            selectinload(Campaign.angles).selectinload(CampaignAngle.creatives)
        )
    )
    campaign = result.scalar_one()

    logger.info(f"Created campaign '{campaign.name}' with 3 angles for business {business.name}")
    return campaign


@router.get("/list", response_model=CampaignListResponse)
async def list_campaigns(
    business_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
):
    """List all campaigns for a business."""
    result = await db.execute(
        select(Campaign)
        .where(Campaign.business_id == business_id)
        .options(
            selectinload(Campaign.angles).selectinload(CampaignAngle.creatives)
        )
        .order_by(Campaign.created_at.desc())
    )
    campaigns = result.scalars().all()

    return CampaignListResponse(
        campaigns=campaigns,
        total=len(campaigns),
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get campaign details with all angles and creatives."""
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id)
        .options(
            selectinload(Campaign.angles).selectinload(CampaignAngle.creatives)
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return campaign


@router.post("/{campaign_id}/generate-creatives", response_model=CampaignResponse)
async def generate_creatives(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    campaign_service: CampaignGeneratorService = Depends(get_campaign_generator),
):
    """Generate 5 creatives per angle for a campaign."""
    # Get campaign with angles
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id)
        .options(
            selectinload(Campaign.angles).selectinload(CampaignAngle.creatives)
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if not campaign.angles:
        raise HTTPException(status_code=400, detail="Campaign has no angles. Create campaign first.")

    # Get business profile
    biz_result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == campaign.business_id)
    )
    business = biz_result.scalar_one_or_none()

    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")

    business_data = {
        "name": business.name,
        "industry": business.industry,
        "description": business.description,
        "brand_voice": business.brand_voice,
        "brand_colors": business.brand_colors or [],
        "target_audience": business.target_audience,
        "unique_selling_points": business.unique_selling_points or [],
    }

    # Generate creatives for each angle
    for angle in campaign.angles:
        # Skip if creatives already exist
        if angle.creatives:
            continue

        angle_data = {
            "hook_type": angle.hook_type.value,
            "title": angle.title,
            "description": angle.description,
            "target_emotion": angle.target_emotion,
        }

        creatives_data = await campaign_service.generate_creatives(
            business=business_data,
            angle=angle_data,
            product_service=campaign.product_service or "",
            campaign_objective=campaign.objective,
            target_audience=campaign.target_audience,
        )

        for j, creative_data in enumerate(creatives_data[:5], start=1):
            # Validate ad_format
            ad_format_value = creative_data.get("ad_format", "single_image")
            try:
                ad_format = AdFormat(ad_format_value)
            except ValueError:
                ad_format = AdFormat.SINGLE_IMAGE

            # Validate placement
            placement_value = creative_data.get("platform_placement", "feed")
            try:
                placement = PlatformPlacement(placement_value)
            except ValueError:
                placement = PlatformPlacement.FEED

            # Generate image for the creative using Bria AI
            image_base64 = None
            try:
                image_base64 = await campaign_service.generate_creative_image(
                    image_concept=creative_data.get("image_concept", ""),
                    brand_colors=business_data.get("brand_colors"),
                    business_name=business_data.get("name"),
                    industry=business_data.get("industry"),
                    placement=placement_value,
                )
            except Exception as img_err:
                logger.warning(f"Image generation failed for creative {j}: {img_err}")

            creative = CampaignCreative(
                angle_id=angle.id,
                creative_number=j,
                headline=creative_data.get("headline", f"Headline {j}")[:255],
                primary_text=creative_data.get("primary_text", ""),
                description=creative_data.get("description"),
                call_to_action=creative_data.get("call_to_action", "LEARN_MORE"),
                image_concept=creative_data.get("image_concept"),
                image_base64=image_base64,
                ad_format=ad_format,
                platform_placement=placement,
                status=CreativeStatus.DRAFT,
            )
            db.add(creative)

    await db.commit()

    # Need to get a fresh view since angles already loaded without creatives.
    # Close and reopen the query to avoid stale relationship cache.
    campaign_id_val = campaign.id
    db.expunge_all()

    # Reload with all relationships from scratch
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id_val)
        .options(
            selectinload(Campaign.angles).selectinload(CampaignAngle.creatives)
        )
    )
    campaign = result.scalar_one()

    logger.info(f"Generated creatives for campaign '{campaign.name}'")
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a campaign and all its angles and creatives."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await db.delete(campaign)
    await db.commit()

    return {"detail": "Campaign deleted successfully", "id": campaign_id}
