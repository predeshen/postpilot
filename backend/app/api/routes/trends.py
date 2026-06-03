"""Trending hashtags and competitor analysis API routes."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_trending_service
from app.database.models import BusinessProfile
from app.models.schemas import (
    CompetitorAnalysisResponse,
    TrendingHashtagResponse,
    TrendsResponse,
)
from app.services.trending_hashtags import TrendingHashtagsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/hashtags", response_model=TrendsResponse)
async def get_trending_hashtags(
    platform: str = Query(default="instagram", pattern="^(tiktok|instagram|facebook)$"),
    industry: str = Query(default="general"),
    limit: int = Query(default=20, ge=1, le=50),
    trending_service: TrendingHashtagsService = Depends(get_trending_service),
):
    """Get trending hashtags for a platform and industry."""
    hashtags = await trending_service.get_trending_hashtags(
        platform=platform,
        industry=industry,
        limit=limit,
    )

    hashtag_responses = [
        TrendingHashtagResponse(
            hashtag=h["hashtag"],
            platform=platform,
            category=h.get("category"),
            relevance_score=h.get("score", 0.0) / 100.0,
            trend_score=h.get("score", 0.0),
            usage_count=int(h.get("score", 0) * 1000),
        )
        for h in hashtags
    ]

    return TrendsResponse(
        platform=platform,
        hashtags=hashtag_responses,
        updated_at=datetime.now(timezone.utc),
    )


@router.get("/competitors", response_model=list[CompetitorAnalysisResponse])
async def get_competitor_analysis(
    industry: str = Query(default="technology"),
    platform: Optional[str] = Query(default=None),
    trending_service: TrendingHashtagsService = Depends(get_trending_service),
):
    """Analyze competitor hashtag and content strategies."""
    competitors = await trending_service.get_competitor_analysis(
        industry=industry,
        platform=platform,
    )

    return [
        CompetitorAnalysisResponse(
            competitor_name=c["name"],
            top_hashtags=c["top_hashtags"],
            posting_frequency=c["posting_frequency"],
            engagement_rate=c["engagement_rate"],
            content_themes=c["content_themes"],
        )
        for c in competitors
    ]
