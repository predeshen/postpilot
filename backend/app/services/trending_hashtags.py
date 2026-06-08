"""Trending hashtags service powered by Firecrawl web scraping and Claude analysis.

Uses Firecrawl to search the web for real trending hashtags and topics,
then feeds the scraped content to Claude (via AWS Bedrock) to extract
and rank relevant hashtags for the user's industry and platform.

Falls back to curated mock data if Firecrawl is unavailable.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Firecrawl API endpoints
FIRECRAWL_SEARCH_URL = "https://api.firecrawl.dev/v1/search"
FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v1/scrape"

# Fallback trending hashtags data by platform and industry
FALLBACK_TRENDING_DATA = {
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

# Fallback competitor data
FALLBACK_COMPETITOR_DATA = {
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
    """Service for fetching trending hashtags using Firecrawl and Claude.

    Flow:
    1. Firecrawl searches the web for trending hashtags/topics
    2. Scraped content is sent to Claude (Bedrock) for analysis
    3. Claude extracts and ranks relevant hashtags
    4. Results are cached for 1 hour to minimize API calls
    5. Falls back to curated data if Firecrawl/Bedrock unavailable
    """

    def __init__(self):
        """Initialize the trending hashtags service."""
        self._cache: Dict[str, Dict] = {}
        self._cache_ttl = timedelta(seconds=settings.content_cache_ttl)

    def _get_cache_key(self, prefix: str, *args: str) -> str:
        """Generate cache key from prefix and arguments."""
        return f"{prefix}:{':'.join(args)}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache:
            return False
        cached_at = self._cache[cache_key].get("cached_at")
        if cached_at is None:
            return False
        return datetime.now(timezone.utc) - cached_at < self._cache_ttl

    def _get_firecrawl_headers(self) -> Dict[str, str]:
        """Get Firecrawl API request headers."""
        return {
            "Authorization": f"Bearer {settings.firecrawl_api_key}",
            "Content-Type": "application/json",
        }

    async def _firecrawl_search(self, query: str, limit: int = 5) -> Optional[List[Dict]]:
        """Search the web using Firecrawl's search endpoint.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of search result dicts with markdown content, or None on failure
        """
        if not settings.firecrawl_api_key:
            logger.warning("Firecrawl API key not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    FIRECRAWL_SEARCH_URL,
                    headers=self._get_firecrawl_headers(),
                    json={
                        "query": query,
                        "limit": limit,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("data", [])
                else:
                    logger.warning(
                        f"Firecrawl search failed with status {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                    return None
        except httpx.TimeoutException:
            logger.warning("Firecrawl search timed out")
            return None
        except Exception as e:
            logger.error(f"Firecrawl search error: {e}")
            return None

    async def _firecrawl_scrape(self, url: str) -> Optional[str]:
        """Scrape a single URL using Firecrawl.

        Args:
            url: URL to scrape

        Returns:
            Markdown content of the page, or None on failure
        """
        if not settings.firecrawl_api_key:
            logger.warning("Firecrawl API key not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    FIRECRAWL_SCRAPE_URL,
                    headers=self._get_firecrawl_headers(),
                    json={
                        "url": url,
                        "formats": ["markdown"],
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("data", {}).get("markdown", "")
                else:
                    logger.warning(
                        f"Firecrawl scrape failed for {url}: "
                        f"status {response.status_code}"
                    )
                    return None
        except httpx.TimeoutException:
            logger.warning(f"Firecrawl scrape timed out for {url}")
            return None
        except Exception as e:
            logger.error(f"Firecrawl scrape error for {url}: {e}")
            return None

    async def _analyze_with_claude(self, prompt: str) -> Optional[str]:
        """Send analysis prompt to Claude via AWS Bedrock.

        Args:
            prompt: The analysis prompt

        Returns:
            Claude's response text, or None on failure
        """
        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            logger.warning("AWS credentials not configured for Claude analysis")
            return None

        try:
            import boto3

            session = boto3.Session(
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            bedrock_runtime = session.client("bedrock-runtime")

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
            })

            response = bedrock_runtime.invoke_model(
                modelId=settings.bedrock_model_id,
                body=body,
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())
            return response_body["content"][0]["text"]
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return None

    async def get_trending_hashtags(
        self,
        platform: str,
        industry: str = "general",
        limit: int = 20,
    ) -> List[Dict]:
        """Get trending hashtags for a platform and industry using Firecrawl.

        Searches the web for current trending hashtags, then uses Claude
        to analyze and rank them by relevance. Falls back to curated data
        if the APIs are unavailable.

        Args:
            platform: Target platform (tiktok, instagram, facebook)
            industry: Business industry category
            limit: Maximum number of hashtags to return

        Returns:
            List of hashtag dictionaries with scores
        """
        cache_key = self._get_cache_key("hashtags", platform, industry)

        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached hashtags for {cache_key}")
            return self._cache[cache_key]["data"][:limit]

        # Try Firecrawl-powered search
        hashtags = await self._fetch_hashtags_via_firecrawl(platform, industry)

        if not hashtags:
            # Fall back to curated data
            logger.info(f"Using fallback data for {platform}/{industry}")
            hashtags = self._get_fallback_hashtags(platform, industry)

        # Cache the results
        self._cache[cache_key] = {
            "data": hashtags,
            "cached_at": datetime.now(timezone.utc),
        }

        logger.info(f"Fetched {len(hashtags)} trending hashtags for {platform}/{industry}")
        return hashtags[:limit]

    async def _fetch_hashtags_via_firecrawl(
        self, platform: str, industry: str
    ) -> Optional[List[Dict]]:
        """Fetch trending hashtags using Firecrawl search + Claude analysis.

        Args:
            platform: Target social media platform
            industry: Business industry

        Returns:
            List of hashtag dicts or None if unavailable
        """
        if not settings.firecrawl_api_key:
            return None

        # Search for trending hashtags
        query = f"trending {industry} hashtags {platform} 2025 2026 South Africa"
        search_results = await self._firecrawl_search(query, limit=5)

        if not search_results:
            return None

        # Compile scraped content
        scraped_content = ""
        for result in search_results:
            if isinstance(result, dict):
                title = result.get("title", "")
                markdown = result.get("markdown", "")
                # Truncate each result to avoid token limits
                content_snippet = markdown[:2000] if markdown else ""
                scraped_content += f"\n--- {title} ---\n{content_snippet}\n"

        if not scraped_content.strip():
            return None

        # Use Claude to extract and rank hashtags
        prompt = f"""Analyze the following scraped web content about trending {industry} hashtags on {platform}.
Extract the most relevant and currently trending hashtags. Focus on hashtags that would work
well for South African businesses in the {industry} industry on {platform}.

Scraped content:
{scraped_content[:8000]}

Return ONLY a valid JSON array with exactly 20 hashtag objects. Each object must have:
- "hashtag": the hashtag including the # symbol
- "score": relevance/trending score from 0 to 100
- "category": the category (use "{industry}" or "general")

Sort by score descending. Example format:
[{{"hashtag": "#example", "score": 95.0, "category": "{industry}"}}]

Return ONLY the JSON array, no other text."""

        claude_response = await self._analyze_with_claude(prompt)

        if not claude_response:
            return None

        # Parse Claude's JSON response
        try:
            # Try to find JSON array in the response
            response_text = claude_response.strip()
            # Handle case where Claude wraps in markdown code block
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            hashtags = json.loads(response_text)
            if isinstance(hashtags, list) and len(hashtags) > 0:
                # Validate structure
                valid_hashtags = []
                for h in hashtags:
                    if isinstance(h, dict) and "hashtag" in h and "score" in h:
                        valid_hashtags.append({
                            "hashtag": h["hashtag"] if h["hashtag"].startswith("#") else f"#{h['hashtag']}",
                            "score": float(h.get("score", 50.0)),
                            "category": h.get("category", industry),
                        })
                if valid_hashtags:
                    valid_hashtags.sort(key=lambda x: x["score"], reverse=True)
                    return valid_hashtags
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning(f"Failed to parse Claude hashtag response: {e}")

        return None

    def _get_fallback_hashtags(self, platform: str, industry: str) -> List[Dict]:
        """Get fallback hashtag data when Firecrawl is unavailable.

        Args:
            platform: Target platform
            industry: Business industry

        Returns:
            List of curated hashtag dictionaries
        """
        platform_data = FALLBACK_TRENDING_DATA.get(platform, {})
        industry_hashtags = platform_data.get(industry.lower(), [])
        general_hashtags = platform_data.get("general", [])

        # Combine industry-specific and general trends
        combined = industry_hashtags + [
            h for h in general_hashtags if h not in industry_hashtags
        ]

        # Sort by score
        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined

    async def get_trending_topics(self, industry: str) -> List[Dict]:
        """Get trending topics in an industry using Firecrawl and Claude.

        Searches for current trends and content angles, then uses Claude
        to summarize them into actionable content ideas with relevance scores.

        Args:
            industry: Business industry category

        Returns:
            List of topic dicts with title, description, relevance_score, and content_angles
        """
        cache_key = self._get_cache_key("topics", industry)

        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached topics for {industry}")
            return self._cache[cache_key]["data"]

        # Try Firecrawl-powered topic discovery
        topics = await self._fetch_topics_via_firecrawl(industry)

        if not topics:
            # Fall back to generic topics
            topics = self._get_fallback_topics(industry)

        # Cache the results
        self._cache[cache_key] = {
            "data": topics,
            "cached_at": datetime.now(timezone.utc),
        }

        logger.info(f"Fetched {len(topics)} trending topics for {industry}")
        return topics

    async def _fetch_topics_via_firecrawl(self, industry: str) -> Optional[List[Dict]]:
        """Fetch trending topics using Firecrawl search + Claude analysis.

        Args:
            industry: Business industry

        Returns:
            List of topic dicts or None if unavailable
        """
        if not settings.firecrawl_api_key:
            return None

        # Search for trending topics and content ideas
        query = f"trending {industry} topics content ideas social media 2025 2026 South Africa"
        search_results = await self._firecrawl_search(query, limit=5)

        if not search_results:
            return None

        # Compile scraped content
        scraped_content = ""
        for result in search_results:
            if isinstance(result, dict):
                title = result.get("title", "")
                markdown = result.get("markdown", "")
                content_snippet = markdown[:2000] if markdown else ""
                scraped_content += f"\n--- {title} ---\n{content_snippet}\n"

        if not scraped_content.strip():
            return None

        # Use Claude to extract trending topics
        prompt = f"""Analyze the following scraped web content about trending topics in the {industry} industry.
Extract the most relevant trending topics that a South African business could create social media
content about right now.

Scraped content:
{scraped_content[:8000]}

Return ONLY a valid JSON array with exactly 10 topic objects. Each object must have:
- "title": short topic title (3-6 words)
- "description": one sentence description of the trend
- "relevance_score": score from 0.0 to 1.0 for how relevant this is right now
- "content_angles": array of 2-3 short content angle suggestions

Sort by relevance_score descending. Example:
[{{"title": "AI in Daily Life", "description": "People are sharing how AI tools help their daily routines.", "relevance_score": 0.92, "content_angles": ["Show your AI workflow", "Before/after with AI tools", "AI tips for beginners"]}}]

Return ONLY the JSON array, no other text."""

        claude_response = await self._analyze_with_claude(prompt)

        if not claude_response:
            return None

        # Parse Claude's JSON response
        try:
            response_text = claude_response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            topics = json.loads(response_text)
            if isinstance(topics, list) and len(topics) > 0:
                valid_topics = []
                for t in topics:
                    if isinstance(t, dict) and "title" in t:
                        valid_topics.append({
                            "title": t["title"],
                            "description": t.get("description", ""),
                            "relevance_score": float(t.get("relevance_score", 0.5)),
                            "content_angles": t.get("content_angles", []),
                        })
                if valid_topics:
                    valid_topics.sort(key=lambda x: x["relevance_score"], reverse=True)
                    return valid_topics
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning(f"Failed to parse Claude topics response: {e}")

        return None

    def _get_fallback_topics(self, industry: str) -> List[Dict]:
        """Get fallback trending topics when APIs are unavailable.

        Args:
            industry: Business industry

        Returns:
            List of generic topic suggestions
        """
        generic_topics = [
            {
                "title": f"{industry.title()} Industry Updates",
                "description": f"Latest developments and news in the {industry} space.",
                "relevance_score": 0.85,
                "content_angles": [
                    "Share your take on recent news",
                    "How this affects your audience",
                    "Predictions for the future",
                ],
            },
            {
                "title": "Behind the Scenes Content",
                "description": "Audiences love seeing the authentic side of businesses.",
                "relevance_score": 0.80,
                "content_angles": [
                    "Day in the life",
                    "How your product is made",
                    "Meet the team",
                ],
            },
            {
                "title": "User-Generated Content",
                "description": "Leveraging customer stories and testimonials for engagement.",
                "relevance_score": 0.78,
                "content_angles": [
                    "Customer spotlight",
                    "Before and after stories",
                    "Review compilation",
                ],
            },
            {
                "title": "Educational Tips and Tricks",
                "description": f"Quick tips related to {industry} that provide value to followers.",
                "relevance_score": 0.75,
                "content_angles": [
                    "Top 5 tips format",
                    "Common mistakes to avoid",
                    "Quick how-to tutorial",
                ],
            },
            {
                "title": "South African Local Trends",
                "description": "Content tied to local events, culture, and community.",
                "relevance_score": 0.72,
                "content_angles": [
                    "Local event tie-ins",
                    "SA-specific humor and culture",
                    "Support local movement",
                ],
            },
        ]
        return generic_topics

    async def analyze_competitor(
        self, competitor_handle: str, platform: str
    ) -> Optional[Dict]:
        """Analyze a competitor's social media strategy using Firecrawl.

        Scrapes the competitor's public social media presence and uses
        Claude to identify their hashtag strategy and content patterns.

        Args:
            competitor_handle: The competitor's social media handle (without @)
            platform: The platform to analyze

        Returns:
            Dict with competitor analysis or None if unavailable
        """
        cache_key = self._get_cache_key("competitor", competitor_handle, platform)

        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached competitor analysis for {competitor_handle}")
            return self._cache[cache_key]["data"]

        analysis = await self._fetch_competitor_via_firecrawl(competitor_handle, platform)

        if not analysis:
            # Return a basic structure indicating analysis was not possible
            analysis = {
                "competitor_handle": competitor_handle,
                "platform": platform,
                "status": "unavailable",
                "message": "Could not analyze competitor. Profile may be private or service unavailable.",
                "top_hashtags": [],
                "posting_frequency": "unknown",
                "engagement_rate": 0.0,
                "content_themes": [],
            }

        # Cache the results
        self._cache[cache_key] = {
            "data": analysis,
            "cached_at": datetime.now(timezone.utc),
        }

        return analysis

    async def _fetch_competitor_via_firecrawl(
        self, competitor_handle: str, platform: str
    ) -> Optional[Dict]:
        """Fetch competitor analysis using Firecrawl + Claude.

        Args:
            competitor_handle: Competitor's handle
            platform: Social media platform

        Returns:
            Dict with analysis or None
        """
        if not settings.firecrawl_api_key:
            return None

        # Build the URL to scrape based on platform
        platform_urls = {
            "instagram": f"https://www.instagram.com/{competitor_handle}/",
            "tiktok": f"https://www.tiktok.com/@{competitor_handle}",
            "facebook": f"https://www.facebook.com/{competitor_handle}",
        }

        url = platform_urls.get(platform)
        if not url:
            return None

        # Try scraping the profile page
        scraped_content = await self._firecrawl_scrape(url)

        # Also search for mentions of the competitor
        search_query = f"{competitor_handle} {platform} hashtags content strategy"
        search_results = await self._firecrawl_search(search_query, limit=3)

        combined_content = scraped_content or ""
        if search_results:
            for result in search_results:
                if isinstance(result, dict):
                    markdown = result.get("markdown", "")
                    combined_content += f"\n{markdown[:1500]}"

        if not combined_content.strip():
            return None

        # Use Claude to analyze the competitor
        prompt = f"""Analyze the following scraped content about the social media account @{competitor_handle} on {platform}.
Extract their content strategy patterns.

Content:
{combined_content[:6000]}

Return ONLY a valid JSON object with:
- "competitor_handle": "{competitor_handle}"
- "platform": "{platform}"
- "status": "analyzed"
- "top_hashtags": array of their most used hashtags (5-10)
- "posting_frequency": estimated posting frequency (e.g. "1-2x daily")
- "engagement_rate": estimated engagement rate as a number (e.g. 3.5)
- "content_themes": array of 3-5 content themes they focus on

Return ONLY the JSON object, no other text."""

        claude_response = await self._analyze_with_claude(prompt)

        if not claude_response:
            return None

        try:
            response_text = claude_response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            analysis = json.loads(response_text)
            if isinstance(analysis, dict) and "top_hashtags" in analysis:
                return analysis
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse competitor analysis response: {e}")

        return None

    async def get_competitor_analysis(
        self,
        industry: str,
        platform: Optional[str] = None,
    ) -> List[Dict]:
        """Analyze competitor hashtag strategies for an industry.

        Uses Firecrawl to search for competitor insights, falling back
        to curated data if unavailable.

        Args:
            industry: Business industry
            platform: Optional platform filter

        Returns:
            List of competitor analysis results
        """
        cache_key = self._get_cache_key("competitors", industry, platform or "all")

        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached competitor analysis for {industry}")
            return self._cache[cache_key]["data"]

        # Try Firecrawl-powered competitor research
        competitors = await self._fetch_industry_competitors_via_firecrawl(industry, platform)

        if not competitors:
            # Fall back to curated data
            competitors = FALLBACK_COMPETITOR_DATA.get(industry.lower(), [])
            if not competitors:
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

        # Cache the results
        self._cache[cache_key] = {
            "data": competitors,
            "cached_at": datetime.now(timezone.utc),
        }

        return competitors

    async def _fetch_industry_competitors_via_firecrawl(
        self, industry: str, platform: Optional[str]
    ) -> Optional[List[Dict]]:
        """Fetch industry competitor analysis using Firecrawl + Claude.

        Args:
            industry: Business industry
            platform: Optional platform filter

        Returns:
            List of competitor analysis dicts or None
        """
        if not settings.firecrawl_api_key:
            return None

        platform_str = platform or "social media"
        query = f"top {industry} brands {platform_str} South Africa hashtag strategy 2025"
        search_results = await self._firecrawl_search(query, limit=4)

        if not search_results:
            return None

        scraped_content = ""
        for result in search_results:
            if isinstance(result, dict):
                title = result.get("title", "")
                markdown = result.get("markdown", "")
                content_snippet = markdown[:2000] if markdown else ""
                scraped_content += f"\n--- {title} ---\n{content_snippet}\n"

        if not scraped_content.strip():
            return None

        prompt = f"""Analyze the following scraped content about {industry} brands on {platform_str}.
Identify 3-5 competitor brands and their social media strategies.

Content:
{scraped_content[:8000]}

Return ONLY a valid JSON array with competitor objects. Each must have:
- "name": brand/competitor name
- "top_hashtags": array of 5 hashtags they use
- "posting_frequency": estimated frequency (e.g. "2x daily")
- "engagement_rate": estimated rate as number (e.g. 3.5)
- "content_themes": array of 3 content themes

Return ONLY the JSON array, no other text."""

        claude_response = await self._analyze_with_claude(prompt)

        if not claude_response:
            return None

        try:
            response_text = claude_response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            competitors = json.loads(response_text)
            if isinstance(competitors, list) and len(competitors) > 0:
                return competitors
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse competitor analysis: {e}")

        return None

    async def score_hashtag_relevance(
        self,
        hashtag: str,
        business_industry: str,
        platform: str,
    ) -> float:
        """Score how relevant a hashtag is for a specific business.

        Args:
            hashtag: The hashtag to score
            business_industry: The business industry
            platform: Target platform

        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Check cached/fetched hashtags first
        cache_key = self._get_cache_key("hashtags", platform, business_industry)
        if self._is_cache_valid(cache_key):
            for h in self._cache[cache_key]["data"]:
                if h["hashtag"].lower() == hashtag.lower():
                    return h["score"] / 100.0

        # Check fallback data
        platform_data = FALLBACK_TRENDING_DATA.get(platform, {})
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
