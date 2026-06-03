"""Trending hashtags service for fetching and caching platform trends."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Simulated trending hashtags data by platform and industry
TRENDING_DATA = {
    "tiktok": {
        "general": [
            {"hashtag": "#fyp", "score": 99.0, "category": "general"},
            {"hashtag": "#viral", "score": 95.0, "category": "general"},
            {"hashtag": "#trending", "score": 90.0, "category": "general"},
            {"hashtag": "#foryou", "score": 88.0, "category": "general"},
            {"hashtag": "#tiktokbusiness", "score": 75.0, "category": "business"},
        ],
        "technology": [
            {"hashtag": "#techtok", "score": 92.0, "category": "technology"},
            {"hashtag": "#techreview", "score": 85.0, "category": "technology"},
            {"hashtag": "#gadgets", "score": 80.0, "category": "technology"},
            {"hashtag": "#ai", "score": 95.0, "category": "technology"},
            {"hashtag": "#coding", "score": 78.0, "category": "technology"},
        ],
        "food": [
            {"hashtag": "#foodtok", "score": 94.0, "category": "food"},
            {"hashtag": "#recipe", "score": 88.0, "category": "food"},
            {"hashtag": "#foodie", "score": 90.0, "category": "food"},
            {"hashtag": "#cooking", "score": 85.0, "category": "food"},
            {"hashtag": "#homemade", "score": 80.0, "category": "food"},
        ],
        "fitness": [
            {"hashtag": "#fitnessmotivation", "score": 91.0, "category": "fitness"},
            {"hashtag": "#workout", "score": 89.0, "category": "fitness"},
            {"hashtag": "#gymtok", "score": 87.0, "category": "fitness"},
            {"hashtag": "#healthylifestyle", "score": 83.0, "category": "fitness"},
            {"hashtag": "#transformation", "score": 80.0, "category": "fitness"},
        ],
    },
    "instagram": {
        "general": [
            {"hashtag": "#instagood", "score": 97.0, "category": "general"},
            {"hashtag": "#photooftheday", "score": 93.0, "category": "general"},
            {"hashtag": "#instadaily", "score": 88.0, "category": "general"},
            {"hashtag": "#reels", "score": 92.0, "category": "general"},
            {"hashtag": "#explorepage", "score": 85.0, "category": "general"},
        ],
        "technology": [
            {"hashtag": "#techstagram", "score": 82.0, "category": "technology"},
            {"hashtag": "#startuplife", "score": 80.0, "category": "technology"},
            {"hashtag": "#innovation", "score": 78.0, "category": "technology"},
            {"hashtag": "#artificialintelligence", "score": 85.0, "category": "technology"},
            {"hashtag": "#futuretech", "score": 75.0, "category": "technology"},
        ],
        "food": [
            {"hashtag": "#foodporn", "score": 95.0, "category": "food"},
            {"hashtag": "#instafood", "score": 93.0, "category": "food"},
            {"hashtag": "#foodphotography", "score": 88.0, "category": "food"},
            {"hashtag": "#yummy", "score": 85.0, "category": "food"},
            {"hashtag": "#homecooking", "score": 80.0, "category": "food"},
        ],
        "fitness": [
            {"hashtag": "#fitfam", "score": 90.0, "category": "fitness"},
            {"hashtag": "#gymlife", "score": 88.0, "category": "fitness"},
            {"hashtag": "#fitnessjourney", "score": 86.0, "category": "fitness"},
            {"hashtag": "#wellness", "score": 84.0, "category": "fitness"},
            {"hashtag": "#healthyliving", "score": 82.0, "category": "fitness"},
        ],
    },
    "facebook": {
        "general": [
            {"hashtag": "#supportsmallbusiness", "score": 88.0, "category": "general"},
            {"hashtag": "#community", "score": 85.0, "category": "general"},
            {"hashtag": "#facebookreels", "score": 80.0, "category": "general"},
            {"hashtag": "#share", "score": 75.0, "category": "general"},
            {"hashtag": "#smallbusiness", "score": 82.0, "category": "general"},
        ],
        "technology": [
            {"hashtag": "#techlife", "score": 78.0, "category": "technology"},
            {"hashtag": "#digitalworld", "score": 75.0, "category": "technology"},
            {"hashtag": "#techinnovation", "score": 72.0, "category": "technology"},
            {"hashtag": "#software", "score": 70.0, "category": "technology"},
            {"hashtag": "#startup", "score": 76.0, "category": "technology"},
        ],
        "food": [
            {"hashtag": "#foodlovers", "score": 82.0, "category": "food"},
            {"hashtag": "#recipeoftheday", "score": 78.0, "category": "food"},
            {"hashtag": "#delicious", "score": 80.0, "category": "food"},
            {"hashtag": "#comfortfood", "score": 75.0, "category": "food"},
            {"hashtag": "#mealprep", "score": 73.0, "category": "food"},
        ],
        "fitness": [
            {"hashtag": "#fitnessgoals", "score": 80.0, "category": "fitness"},
            {"hashtag": "#motivation", "score": 78.0, "category": "fitness"},
            {"hashtag": "#healthylife", "score": 76.0, "category": "fitness"},
            {"hashtag": "#exercise", "score": 74.0, "category": "fitness"},
            {"hashtag": "#strongertogether", "score": 72.0, "category": "fitness"},
        ],
    },
}

# Simulated competitor data
COMPETITOR_DATA = {
    "technology": [
        {
            "name": "TechBrand Competitor",
            "top_hashtags": ["#innovation", "#techlife", "#startup", "#ai", "#futuretech"],
            "posting_frequency": "2x daily",
            "engagement_rate": 3.5,
            "content_themes": ["product demos", "industry news", "team culture"],
        }
    ],
    "food": [
        {
            "name": "FoodBrand Competitor",
            "top_hashtags": ["#foodie", "#homecooking", "#recipe", "#delicious", "#yummy"],
            "posting_frequency": "3x daily",
            "engagement_rate": 4.2,
            "content_themes": ["recipes", "food photography", "restaurant reviews"],
        }
    ],
    "fitness": [
        {
            "name": "FitBrand Competitor",
            "top_hashtags": ["#fitfam", "#gymlife", "#workout", "#gains", "#fitnessmotivation"],
            "posting_frequency": "1x daily",
            "engagement_rate": 5.1,
            "content_themes": ["workout tutorials", "transformations", "nutrition tips"],
        }
    ],
}


class TrendingHashtagsService:
    """Service for fetching and managing trending hashtags."""

    def __init__(self):
        """Initialize the trending hashtags service."""
        self._cache: Dict[str, Dict] = {}
        self._cache_ttl = timedelta(seconds=settings.content_cache_ttl)

    def _get_cache_key(self, platform: str, industry: str) -> str:
        """Generate cache key for platform + industry combination."""
        return f"{platform}:{industry}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache:
            return False
        cached_at = self._cache[cache_key].get("cached_at")
        if cached_at is None:
            return False
        return datetime.now(timezone.utc) - cached_at < self._cache_ttl

    async def get_trending_hashtags(
        self,
        platform: str,
        industry: str = "general",
        limit: int = 20,
    ) -> List[Dict]:
        """
        Get trending hashtags for a platform and industry.

        Args:
            platform: Target platform (tiktok, instagram, facebook)
            industry: Business industry category
            limit: Maximum number of hashtags to return

        Returns:
            List of hashtag dictionaries with scores
        """
        cache_key = self._get_cache_key(platform, industry)

        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached hashtags for {cache_key}")
            return self._cache[cache_key]["data"][:limit]

        # Fetch trending data (simulated - in production would call platform APIs)
        platform_data = TRENDING_DATA.get(platform, {})
        industry_hashtags = platform_data.get(industry.lower(), [])
        general_hashtags = platform_data.get("general", [])

        # Combine industry-specific and general trends
        combined = industry_hashtags + [
            h for h in general_hashtags if h not in industry_hashtags
        ]

        # Sort by score
        combined.sort(key=lambda x: x["score"], reverse=True)

        # Cache the results
        self._cache[cache_key] = {
            "data": combined,
            "cached_at": datetime.now(timezone.utc),
        }

        logger.info(f"Fetched {len(combined)} trending hashtags for {platform}/{industry}")
        return combined[:limit]

    async def get_competitor_analysis(
        self,
        industry: str,
        platform: Optional[str] = None,
    ) -> List[Dict]:
        """
        Analyze competitor hashtag strategies.

        Args:
            industry: Business industry
            platform: Optional platform filter

        Returns:
            List of competitor analysis results
        """
        competitors = COMPETITOR_DATA.get(industry.lower(), [])

        if not competitors:
            # Return generic competitor data
            competitors = [
                {
                    "name": f"{industry.title()} Industry Leader",
                    "top_hashtags": [
                        f"#{industry.lower()}",
                        "#business",
                        "#growth",
                        "#success",
                        "#entrepreneur",
                    ],
                    "posting_frequency": "1-2x daily",
                    "engagement_rate": 3.0,
                    "content_themes": ["educational", "promotional", "community"],
                }
            ]

        return competitors

    async def score_hashtag_relevance(
        self,
        hashtag: str,
        business_industry: str,
        platform: str,
    ) -> float:
        """
        Score how relevant a hashtag is for a specific business.

        Args:
            hashtag: The hashtag to score
            business_industry: The business industry
            platform: Target platform

        Returns:
            Relevance score between 0.0 and 1.0
        """
        platform_data = TRENDING_DATA.get(platform, {})
        industry_hashtags = platform_data.get(business_industry.lower(), [])

        for h in industry_hashtags:
            if h["hashtag"].lower() == hashtag.lower():
                return h["score"] / 100.0

        # Default moderate relevance for unknown hashtags
        return 0.5

    def clear_cache(self) -> None:
        """Clear the hashtag cache."""
        self._cache.clear()
        logger.info("Hashtag cache cleared")


# Singleton instance
trending_hashtags_service = TrendingHashtagsService()
