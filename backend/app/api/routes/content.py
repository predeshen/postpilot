"""Content generation and management API routes."""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_ai_generator, get_theme_engine, get_image_generator
from app.database.models import BusinessProfile, GeneratedPost, PostStatus, Platform, ContentPillarType
from app.models.schemas import (
    ContentApproveResponse,
    ContentCalendarResponse,
    ContentGenerateRequest,
    GeneratedPostResponse,
    ImageGenerateRequest,
    ImageGenerateResponse,
    PostImageGenerateResponse,
)
from app.services.ai_generator import AIGeneratorService
from app.services.image_generator import ImageGeneratorService
from app.services.theme_engine import ThemeEngineService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/content", tags=["content"])


@router.post("/generate", response_model=list[GeneratedPostResponse])
async def generate_content(
    request: ContentGenerateRequest,
    db: AsyncSession = Depends(get_db),
    ai_service: AIGeneratorService = Depends(get_ai_generator),
    theme_service: ThemeEngineService = Depends(get_theme_engine),
    image_service: ImageGeneratorService = Depends(get_image_generator),
):
    """Generate AI-powered social media content for a business."""
    # Get business profile
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == request.business_id)
    )
    business = result.scalar_one_or_none()

    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")

    # Build business data dict
    business_data = {
        "name": business.name,
        "industry": business.industry,
        "description": business.description,
        "brand_voice": business.brand_voice,
        "brand_colors": business.brand_colors or [],
        "target_audience": business.target_audience,
        "unique_selling_points": business.unique_selling_points or [],
    }

    # Determine pillar type
    pillar_type = request.pillar_type or "engagement"

    # Generate content variants
    variants = await ai_service.generate_content(
        business=business_data,
        platform=request.platform,
        pillar_type=pillar_type,
        topic=request.topic,
        language=request.language,
        num_variants=request.num_variants,
    )

    # Create posts in database
    created_posts = []
    variant_group = str(uuid.uuid4())[:8]

    for variant in variants:
        # Score theme consistency
        theme_score_data = theme_service.score_content_consistency(
            variant.get("content", ""), business_data
        )

        # Generate image if requested
        image_path = None
        if request.include_image:
            try:
                platform_key = request.platform
                if request.platform == "instagram":
                    platform_key = "instagram_feed"
                elif request.platform == "facebook":
                    platform_key = "facebook_feed"

                image_path = await image_service.generate_image(
                    platform=platform_key,
                    text=variant.get("content", "")[:100],
                    brand_colors=business.brand_colors,
                    business_name=business.name,
                )
            except Exception as e:
                logger.warning(f"Image generation failed: {e}")

        post = GeneratedPost(
            business_id=business.id,
            platform=Platform(request.platform),
            content=variant.get("content", ""),
            hashtags=variant.get("hashtags", []),
            image_path=image_path,
            status=PostStatus.DRAFT,
            pillar_type=ContentPillarType(pillar_type) if pillar_type in [e.value for e in ContentPillarType] else None,
            engagement_hook=variant.get("engagement_hook"),
            variant_group=variant_group,
            language=request.language,
            theme_score=theme_score_data.get("overall_score"),
        )
        db.add(post)
        created_posts.append(post)

    await db.commit()

    # Refresh to get IDs
    for post in created_posts:
        await db.refresh(post)

    logger.info(f"Generated {len(created_posts)} content variants for business {business.name}")
    return created_posts


@router.get("/calendar", response_model=ContentCalendarResponse)
async def get_content_calendar(
    business_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
):
    """Get content calendar with all posts for a business."""
    result = await db.execute(
        select(GeneratedPost)
        .where(GeneratedPost.business_id == business_id)
        .order_by(GeneratedPost.created_at.desc())
        .limit(50)
    )
    posts = result.scalars().all()

    # Count statistics
    total = len(posts)
    upcoming = sum(1 for p in posts if p.status in [PostStatus.DRAFT, PostStatus.APPROVED])
    published = sum(1 for p in posts if p.status == PostStatus.PUBLISHED)

    return ContentCalendarResponse(
        posts=posts,
        total=total,
        upcoming=upcoming,
        published=published,
    )


@router.post("/approve/{post_id}", response_model=ContentApproveResponse)
async def approve_content(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Approve a generated post for publishing."""
    result = await db.execute(
        select(GeneratedPost).where(GeneratedPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.status != PostStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Post cannot be approved from '{post.status.value}' status"
        )

    post.status = PostStatus.APPROVED
    await db.commit()

    return ContentApproveResponse(
        id=post.id,
        status="approved",
        message="Post approved and ready for publishing",
    )


@router.post("/publish/{post_id}", response_model=ContentApproveResponse)
async def publish_content(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Publish an approved post."""
    result = await db.execute(
        select(GeneratedPost).where(GeneratedPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.status != PostStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"Post must be approved before publishing (current: '{post.status.value}')"
        )

    post.status = PostStatus.PUBLISHED
    post.published_at = datetime.now(timezone.utc)
    await db.commit()

    return ContentApproveResponse(
        id=post.id,
        status="published",
        message="Post published successfully",
    )


@router.post("/regenerate/{post_id}", response_model=GeneratedPostResponse)
async def regenerate_content(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    ai_service: AIGeneratorService = Depends(get_ai_generator),
    theme_service: ThemeEngineService = Depends(get_theme_engine),
):
    """Regenerate content for a specific post."""
    result = await db.execute(
        select(GeneratedPost).where(GeneratedPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Get business profile
    biz_result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == post.business_id)
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

    # Regenerate
    pillar = post.pillar_type.value if post.pillar_type else "engagement"
    variants = await ai_service.generate_content(
        business=business_data,
        platform=post.platform.value,
        pillar_type=pillar,
        num_variants=1,
    )

    if variants:
        variant = variants[0]
        post.content = variant.get("content", post.content)
        post.hashtags = variant.get("hashtags", post.hashtags)
        post.engagement_hook = variant.get("engagement_hook")
        post.status = PostStatus.DRAFT

        # Re-score theme consistency
        score_data = theme_service.score_content_consistency(post.content, business_data)
        post.theme_score = score_data.get("overall_score")

        await db.commit()
        await db.refresh(post)

    return post


@router.post("/{post_id}/generate-image", response_model=PostImageGenerateResponse)
async def generate_post_image(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    image_service: ImageGeneratorService = Depends(get_image_generator),
):
    """Generate an AI image for a specific post using Stability AI.

    Uses the post content and associated business brand identity to generate
    a relevant image for the post's target platform.
    """
    result = await db.execute(
        select(GeneratedPost).where(GeneratedPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Get business profile for brand context
    biz_result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == post.business_id)
    )
    business = biz_result.scalar_one_or_none()

    # Determine platform key
    platform_key = post.platform.value
    if platform_key == "instagram":
        platform_key = "instagram_feed"
    elif platform_key == "facebook":
        platform_key = "facebook_feed"

    # Generate image with brand context
    brand_colors = business.brand_colors if business else None
    business_name = business.name if business else None
    industry = business.industry if business else None

    image_path = await image_service.generate_image(
        platform=platform_key,
        text=post.content[:200],
        brand_colors=brand_colors,
        business_name=business_name,
        industry=industry,
        output_filename=f"post_{post_id}_{platform_key}.png",
    )

    # Update post with image path
    post.image_path = image_path
    await db.commit()

    # Read the image file and return as base64
    import base64
    image_base64 = None
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

    return PostImageGenerateResponse(
        post_id=post.id,
        image_path=image_path,
        image_base64=image_base64,
        platform=platform_key,
        success=image_path is not None,
    )
