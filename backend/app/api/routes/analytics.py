"""Analytics API routes for content performance tracking."""

import logging
from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_theme_engine
from app.database.models import BusinessProfile, GeneratedPost, PostHistory, PostStatus
from app.models.schemas import PerformanceMetrics, ThemeScoreResponse
from app.services.theme_engine import ThemeEngineService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance(
    business_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
):
    """Get content performance analytics for a business."""
    # Get all posts for business
    result = await db.execute(
        select(GeneratedPost).where(GeneratedPost.business_id == business_id)
    )
    posts = result.scalars().all()

    if not posts:
        return PerformanceMetrics(
            total_posts=0,
            published_posts=0,
            average_engagement_rate=0.0,
            top_performing_platform=None,
            top_performing_pillar=None,
            posts_by_platform={},
            posts_by_status={},
        )

    # Calculate metrics
    total_posts = len(posts)
    published_posts = sum(1 for p in posts if p.status == PostStatus.PUBLISHED)

    # Posts by platform
    platform_counts = Counter(p.platform.value for p in posts)
    posts_by_platform = dict(platform_counts)

    # Posts by status
    status_counts = Counter(p.status.value for p in posts)
    posts_by_status = dict(status_counts)

    # Find top performing platform (by volume for now)
    top_platform = platform_counts.most_common(1)[0][0] if platform_counts else None

    # Find top performing pillar
    pillar_counts = Counter(
        p.pillar_type.value for p in posts if p.pillar_type is not None
    )
    top_pillar = pillar_counts.most_common(1)[0][0] if pillar_counts else None

    # Get engagement data from history
    history_result = await db.execute(select(PostHistory))
    history = history_result.scalars().all()

    avg_engagement = 0.0
    if history:
        engagement_rates = [h.engagement_rate for h in history if h.engagement_rate > 0]
        avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0

    return PerformanceMetrics(
        total_posts=total_posts,
        published_posts=published_posts,
        average_engagement_rate=round(avg_engagement, 2),
        top_performing_platform=top_platform,
        top_performing_pillar=top_pillar,
        posts_by_platform=posts_by_platform,
        posts_by_status=posts_by_status,
    )


@router.get("/theme-score", response_model=ThemeScoreResponse)
async def get_theme_score(
    business_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
    theme_service: ThemeEngineService = Depends(get_theme_engine),
):
    """Get theme consistency score for a business's content."""
    # Get business profile
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == business_id)
    )
    business = result.scalar_one_or_none()

    if not business:
        return ThemeScoreResponse(
            overall_score=0.0,
            brand_voice_consistency=0.0,
            visual_consistency=0.0,
            content_pillar_balance={},
            recommendations=["Set up a business profile first."],
        )

    business_data = {
        "name": business.name,
        "industry": business.industry,
        "brand_voice": business.brand_voice,
        "brand_colors": business.brand_colors or [],
        "target_audience": business.target_audience,
        "unique_selling_points": business.unique_selling_points or [],
    }

    # Get recent posts
    posts_result = await db.execute(
        select(GeneratedPost)
        .where(GeneratedPost.business_id == business_id)
        .order_by(GeneratedPost.created_at.desc())
        .limit(50)
    )
    posts = posts_result.scalars().all()

    post_data = [
        {
            "content": p.content,
            "pillar_type": p.pillar_type.value if p.pillar_type else "engagement",
            "platform": p.platform.value,
        }
        for p in posts
    ]

    # Calculate theme score
    score = theme_service.get_theme_score(business_data, post_data)

    return ThemeScoreResponse(
        overall_score=score["overall_score"],
        brand_voice_consistency=score["brand_voice_consistency"],
        visual_consistency=score["visual_consistency"],
        content_pillar_balance=score["content_pillar_balance"],
        recommendations=score["recommendations"],
    )
