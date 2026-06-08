"""Trending hashtags, topics, and competitor analysis API routes.

Uses Firecrawl for real-time web scraping and Claude for analysis.
Falls back to curated data when services are unavailable.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_trending_service
from app.models.schemas import (
    CompetitorAnalysisResponse,
    TrendingHashtagResponse,
    TrendingTopicResponse,
    TrendingTopicsResponse,
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
    """Get trending hashtags for a platform and industry.

    Uses Firecrawl to search the web for current trending hashtags,
    then Claude analyzes and ranks them. Results are cached for 1 hour.
    Falls back to curated data if Firecrawl is unavailable.
    """
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


@router.get("/topics", response_model=TrendingTopicsResponse)
async def get_trending_topics(
    industry: str = Query(default="general"),
    trending_service: TrendingHashtagsService = Depends(get_trending_service),
):
    """Get trending topics and content ideas for an industry.

    Uses Firecrawl to discover what is trending in the industry right now,
    then Claude summarizes into actionable content angles. Results cached for 1 hour.
    Falls back to generic topic suggestions if Firecrawl is unavailable.
    """
    topics = await trending_service.get_trending_topics(industry=industry)

    topic_responses = [
        TrendingTopicResponse(
            title=t["title"],
            description=t["description"],
            relevance_score=t["relevance_score"],
            content_angles=t["content_angles"],
        )
        for t in topics
    ]

    return TrendingTopicsResponse(
        industry=industry,
        topics=topic_responses,
        updated_at=datetime.now(timezone.utc),
    )


@router.get("/competitors", response_model=list[CompetitorAnalysisResponse])
async def get_competitor_analysis(
    industry: str = Query(default="technology"),
    platform: Optional[str] = Query(default=None),
    trending_service: TrendingHashtagsService = Depends(get_trending_service),
):
    """Analyze competitor hashtag and content strategies for an industry.

    Uses Firecrawl to research top brands in the industry and their
    social media strategies. Falls back to curated data if unavailable.
    """
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


@router.get("/competitors/analyze")
async def analyze_specific_competitor(
    handle: str = Query(..., description="Competitor's social media handle (without @)"),
    platform: str = Query(default="instagram", pattern="^(tiktok|instagram|facebook)$"),
    trending_service: TrendingHashtagsService = Depends(get_trending_service),
):
    """Analyze a specific competitor's social media strategy.

    Uses Firecrawl to scrape the competitor's public profile and
    Claude to identify their hashtag strategy and content patterns.
    """
    result = await trending_service.analyze_competitor(
        competitor_handle=handle,
        platform=platform,
    )

    return result
