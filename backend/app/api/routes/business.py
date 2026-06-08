"""Business profile API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.database.models import BusinessProfile
from app.models.schemas import (
    BusinessResponse,
    BusinessSetupRequest,
    BusinessUpdateRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/business", tags=["business"])


@router.post("/setup", response_model=BusinessResponse, status_code=201)
async def setup_business(
    request: BusinessSetupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new business profile with brand configuration."""
    business = BusinessProfile(
        name=request.name,
        industry=request.industry,
        description=request.description,
        brand_voice=request.brand_voice,
        brand_colors=request.brand_colors,
        target_audience=request.target_audience,
        unique_selling_points=request.unique_selling_points,
        languages=request.languages,
        website=request.website,
        logo_url=request.logo_url,
    )
    db.add(business)
    await db.commit()
    await db.refresh(business)
    logger.info(f"Created business profile: {business.name} (ID: {business.id})")
    return business


@router.put("/update", response_model=BusinessResponse)
async def update_business(
    request: BusinessUpdateRequest,
    business_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing business profile."""
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == business_id)
    )
    business = result.scalar_one_or_none()

    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(business, field, value)

    await db.commit()
    await db.refresh(business)
    logger.info(f"Updated business profile: {business.name} (ID: {business.id})")
    return business


@router.post("/logo", response_model=BusinessResponse)
async def upload_logo(
    business_id: int = 1,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a business logo (file upload option)."""
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == business_id)
    )
    business = result.scalar_one_or_none()

    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")

    # Validate file type
    if file.content_type not in ["image/png", "image/jpeg", "image/svg+xml"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Accepted: PNG, JPEG, SVG"
        )

    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 10MB."
        )

    # Save logo file
    import os
    logo_dir = os.path.join(os.getcwd(), "uploads", "logos")
    os.makedirs(logo_dir, exist_ok=True)

    file_extension = file.filename.split(".")[-1] if file.filename else "png"
    logo_filename = f"business_{business_id}_logo.{file_extension}"
    logo_path = os.path.join(logo_dir, logo_filename)

    with open(logo_path, "wb") as f:
        f.write(content)

    business.logo_path = logo_path
    await db.commit()
    await db.refresh(business)
    logger.info(f"Uploaded logo for business: {business.name}")
    return business


@router.post("/logo-url", response_model=BusinessResponse)
async def set_logo_url(
    business_id: int = 1,
    logo_url: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Set a business logo via URL (alternative to file upload).

    Provide a direct URL to your logo image (PNG, JPEG, SVG).
    The URL will be stored and used for branding in generated content.
    """
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == business_id)
    )
    business = result.scalar_one_or_none()

    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")

    if not logo_url:
        raise HTTPException(status_code=400, detail="logo_url is required")

    # Basic URL validation
    if not logo_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Must start with http:// or https://"
        )

    business.logo_url = logo_url
    await db.commit()
    await db.refresh(business)
    logger.info(f"Set logo URL for business: {business.name} -> {logo_url}")
    return business


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a business profile by ID."""
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == business_id)
    )
    business = result.scalar_one_or_none()

    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")

    return business
