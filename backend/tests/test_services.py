"""Unit tests for backend services."""

import os
import pytest
from unittest.mock import patch, MagicMock

from app.services.ai_generator import AIGeneratorService, PLATFORM_GUIDELINES, PILLAR_PROMPTS
from app.services.theme_engine import ThemeEngineService, BRAND_VOICE_ARCHETYPES
from app.services.image_generator import ImageGeneratorService, PLATFORM_DIMENSIONS
from app.services.trending_hashtags import TrendingHashtagsService
from app.services.content_scheduler import ContentSchedulerService


# ============== AI Generator Tests ==============

class TestAIGenerator:
    """Tests for the AI content generator service."""

    def setup_method(self):
        self.service = AIGeneratorService()

    @pytest.mark.asyncio
    async def test_generate_content_mock(self):
        """Test mock content generation when Bedrock is unavailable."""
        business = {
            "name": "TestBrand",
            "industry": "technology",
            "brand_voice": "professional",
            "target_audience": "developers",
            "unique_selling_points": ["Fast", "Reliable"],
        }

        variants = await self.service.generate_content(
            business=business,
            platform="instagram",
            pillar_type="educational",
            num_variants=2,
        )

        assert len(variants) == 2
        assert all("content" in v for v in variants)
        assert all("hashtags" in v for v in variants)
        assert all(len(v["content"]) > 0 for v in variants)

    @pytest.mark.asyncio
    async def test_generate_content_all_pillars(self):
        """Test content generation for all pillar types."""
        business = {
            "name": "FoodBrand",
            "industry": "food",
            "brand_voice": "casual",
            "target_audience": "food lovers",
            "unique_selling_points": ["Organic", "Local"],
        }

        for pillar in ["educational", "promotional", "engagement", "behind_the_scenes", "testimonials"]:
            variants = await self.service.generate_content(
                business=business,
                platform="tiktok",
                pillar_type=pillar,
                num_variants=1,
            )
            assert len(variants) >= 1
            assert variants[0]["content"] != ""

    @pytest.mark.asyncio
    async def test_generate_content_respects_platform_length(self):
        """Test that generated content respects platform max length."""
        business = {
            "name": "Brand",
            "industry": "general",
            "brand_voice": "professional",
            "target_audience": "everyone",
            "unique_selling_points": [],
        }

        for platform in ["tiktok", "instagram", "facebook"]:
            variants = await self.service.generate_content(
                business=business,
                platform=platform,
                pillar_type="engagement",
                num_variants=1,
            )
            max_length = PLATFORM_GUIDELINES[platform]["max_length"]
            assert len(variants[0]["content"]) <= max_length

    @pytest.mark.asyncio
    async def test_generate_hashtags(self):
        """Test hashtag generation."""
        business = {
            "name": "TechCo",
            "industry": "technology",
        }

        hashtags = await self.service.generate_hashtags(
            business=business,
            platform="instagram",
            content="Great productivity tips for developers",
            count=5,
        )

        assert len(hashtags) == 5
        assert all(h.startswith("#") for h in hashtags)

    def test_brand_bible_prompt(self):
        """Test brand bible prompt generation."""
        business = {
            "name": "LuxBrand",
            "industry": "fashion",
            "brand_voice": "luxurious",
            "target_audience": "affluent millennials",
            "unique_selling_points": ["Handcrafted", "Sustainable"],
            "description": "Premium sustainable fashion",
        }

        prompt = self.service._build_brand_bible_prompt(business)
        assert "LuxBrand" in prompt
        assert "fashion" in prompt
        assert "luxurious" in prompt
        assert "Handcrafted" in prompt

    def test_platform_guidelines_complete(self):
        """Test that all platforms have complete guidelines."""
        for platform, guidelines in PLATFORM_GUIDELINES.items():
            assert "max_length" in guidelines
            assert "style" in guidelines
            assert "hashtag_count" in guidelines
            assert guidelines["max_length"] > 0

    def test_all_pillar_prompts_exist(self):
        """Test that all content pillar types have prompts."""
        expected_pillars = ["educational", "promotional", "engagement", "behind_the_scenes", "testimonials"]
        for pillar in expected_pillars:
            assert pillar in PILLAR_PROMPTS
            assert len(PILLAR_PROMPTS[pillar]) > 0


# ============== Theme Engine Tests ==============

class TestThemeEngine:
    """Tests for the theme consistency engine."""

    def setup_method(self):
        self.service = ThemeEngineService()

    def test_get_brand_voice_guidelines(self):
        """Test retrieving brand voice guidelines."""
        for voice in ["professional", "casual", "bold", "inspirational", "playful", "luxurious"]:
            guidelines = self.service.get_brand_voice_guidelines(voice)
            assert "traits" in guidelines
            assert "avoid" in guidelines
            assert "tone_words" in guidelines
            assert len(guidelines["traits"]) > 0

    def test_build_voice_prompt(self):
        """Test building brand voice prompt."""
        business = {
            "name": "TestBrand",
            "industry": "tech",
            "brand_voice": "bold",
            "target_audience": "startups",
            "unique_selling_points": ["Fast", "Scalable"],
        }

        prompt = self.service.build_voice_prompt(business)
        assert "BOLD" in prompt
        assert "tech" in prompt
        assert "startups" in prompt

    def test_score_content_consistency(self):
        """Test content consistency scoring."""
        business = {
            "brand_voice": "professional",
            "industry": "consulting",
        }

        # Content using professional tone words
        professional_content = "Discover proven solutions with our expertise. Results guaranteed."
        score = self.service.score_content_consistency(professional_content, business)

        assert 0.0 <= score["overall_score"] <= 1.0
        assert "tone_alignment" in score
        assert "guideline_compliance" in score
        assert score["voice_type"] == "professional"

    def test_pillar_distribution_balanced(self):
        """Test pillar distribution analysis with balanced content."""
        posts = [
            {"pillar_type": "educational"},
            {"pillar_type": "promotional"},
            {"pillar_type": "engagement"},
            {"pillar_type": "behind_the_scenes"},
            {"pillar_type": "testimonials"},
        ]

        result = self.service.get_pillar_distribution(posts)
        assert result["overall_balance_score"] > 0.5
        assert result["total_posts_analyzed"] == 5

    def test_pillar_distribution_unbalanced(self):
        """Test pillar distribution analysis with unbalanced content."""
        posts = [{"pillar_type": "promotional"}] * 10

        result = self.service.get_pillar_distribution(posts)
        assert len(result["recommendations"]) > 0
        assert result["overall_balance_score"] < 0.8

    def test_suggest_next_pillar(self):
        """Test next pillar suggestion."""
        # All promotional - should suggest something else
        posts = [{"pillar_type": "promotional"}] * 5
        suggestion = self.service.suggest_next_pillar(posts)
        assert suggestion != "promotional"

    def test_suggest_next_pillar_empty(self):
        """Test next pillar suggestion with no history."""
        suggestion = self.service.suggest_next_pillar([])
        assert suggestion == "educational"  # Default start

    def test_check_content_repetition(self):
        """Test content repetition detection."""
        recent = [
            "Check out our amazing new product today! Limited offer.",
            "Join our community and learn something new every day.",
        ]

        # Very similar content
        similar = "Check out our amazing new product today! Special offer."
        result = self.service.check_content_repetition(similar, recent)
        assert result["max_similarity"] > 0.5

        # Different content
        different = "Behind the scenes at our factory - watch how we craft each piece."
        result = self.service.check_content_repetition(different, recent)
        assert result["max_similarity"] < 0.5

    def test_get_theme_score_empty(self):
        """Test theme score with no posts."""
        business = {"name": "Brand", "brand_voice": "casual", "brand_colors": []}
        score = self.service.get_theme_score(business, [])
        assert score["overall_score"] == 0.0
        assert len(score["recommendations"]) > 0


# ============== Image Generator Tests ==============

class TestImageGenerator:
    """Tests for the image generator service."""

    def setup_method(self):
        self.service = ImageGeneratorService()

    @pytest.mark.asyncio
    async def test_generate_image_all_platforms(self):
        """Test image generation for all platform dimensions."""
        for platform_key, dims in PLATFORM_DIMENSIONS.items():
            path = await self.service.generate_image(
                platform=platform_key,
                text="Test content for image generation",
                brand_colors=["#2980B9", "#E74C3C"],
                style="bold_text",
                business_name="TestBrand",
                output_filename=f"test_{platform_key}.png",
            )
            assert os.path.exists(path)

            # Verify image dimensions
            from PIL import Image
            img = Image.open(path)
            assert img.size == (dims["width"], dims["height"])

            # Cleanup
            os.remove(path)

    @pytest.mark.asyncio
    async def test_generate_image_all_styles(self):
        """Test image generation with all template styles."""
        from app.services.image_generator import TEMPLATE_STYLES

        for style_name in TEMPLATE_STYLES:
            path = await self.service.generate_image(
                platform="instagram_feed",
                text="Style test content",
                brand_colors=["#1ABC9C"],
                style=style_name,
                output_filename=f"test_style_{style_name}.png",
            )
            assert os.path.exists(path)
            os.remove(path)

    @pytest.mark.asyncio
    async def test_generate_image_default_colors(self):
        """Test image generation with default colors (no brand colors)."""
        path = await self.service.generate_image(
            platform="facebook_feed",
            text="Default color test",
            output_filename="test_default_colors.png",
        )
        assert os.path.exists(path)
        os.remove(path)

    @pytest.mark.asyncio
    async def test_generate_all_platform_variants(self):
        """Test generating images for all platforms at once."""
        results = await self.service.generate_all_platform_variants(
            text="Multi-platform test",
            brand_colors=["#9B59B6", "#3498DB"],
            prefix="test_all",
        )

        assert len(results) == len(PLATFORM_DIMENSIONS)
        for platform_key, path in results.items():
            assert os.path.exists(path)
            os.remove(path)

    def test_get_available_styles(self):
        """Test getting available template styles."""
        styles = self.service.get_available_styles()
        assert len(styles) > 0
        assert all("id" in s for s in styles)
        assert all("config" in s for s in styles)

    def test_get_platform_dimensions(self):
        """Test getting platform dimension configurations."""
        dims = self.service.get_platform_dimensions()
        assert "tiktok" in dims
        assert "instagram_feed" in dims
        assert "instagram_story" in dims
        assert "facebook_feed" in dims
        assert "facebook_story" in dims

        # Verify expected dimensions
        assert dims["tiktok"]["width"] == 1080
        assert dims["tiktok"]["height"] == 1920
        assert dims["instagram_feed"]["width"] == 1080
        assert dims["instagram_feed"]["height"] == 1080
        assert dims["facebook_feed"]["width"] == 1200
        assert dims["facebook_feed"]["height"] == 630


# ============== Trending Hashtags Tests ==============

class TestTrendingHashtags:
    """Tests for the trending hashtags service."""

    def setup_method(self):
        self.service = TrendingHashtagsService()

    @pytest.mark.asyncio
    async def test_get_trending_hashtags(self):
        """Test fetching trending hashtags (falls back to curated data without API key)."""
        hashtags = await self.service.get_trending_hashtags(
            platform="instagram",
            industry="technology",
            limit=5,
        )
        assert len(hashtags) <= 5
        assert all("hashtag" in h for h in hashtags)
        assert all("score" in h for h in hashtags)

    @pytest.mark.asyncio
    async def test_get_trending_hashtags_caching(self):
        """Test that hashtags are cached properly."""
        # First call
        result1 = await self.service.get_trending_hashtags("tiktok", "food")
        # Second call should hit cache
        result2 = await self.service.get_trending_hashtags("tiktok", "food")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_get_trending_topics(self):
        """Test fetching trending topics (falls back without API key)."""
        topics = await self.service.get_trending_topics("fitness")
        assert len(topics) > 0
        assert all("title" in t for t in topics)
        assert all("description" in t for t in topics)
        assert all("relevance_score" in t for t in topics)
        assert all("content_angles" in t for t in topics)

    @pytest.mark.asyncio
    async def test_get_trending_topics_caching(self):
        """Test that topics are cached properly."""
        result1 = await self.service.get_trending_topics("technology")
        result2 = await self.service.get_trending_topics("technology")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_analyze_competitor_no_api_key(self):
        """Test competitor analysis returns unavailable without API key."""
        result = await self.service.analyze_competitor("testbrand", "instagram")
        assert result is not None
        assert result["status"] == "unavailable"
        assert result["competitor_handle"] == "testbrand"

    @pytest.mark.asyncio
    async def test_get_competitor_analysis(self):
        """Test competitor analysis."""
        competitors = await self.service.get_competitor_analysis("technology")
        assert len(competitors) > 0
        assert "name" in competitors[0]
        assert "top_hashtags" in competitors[0]
        assert "engagement_rate" in competitors[0]

    @pytest.mark.asyncio
    async def test_score_hashtag_relevance(self):
        """Test hashtag relevance scoring."""
        score = await self.service.score_hashtag_relevance(
            "#techtok", "technology", "tiktok"
        )
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_score_hashtag_relevance_unknown(self):
        """Test hashtag relevance scoring for unknown hashtag."""
        score = await self.service.score_hashtag_relevance(
            "#unknownhashtag", "technology", "tiktok"
        )
        assert score == 0.5

    def test_clear_cache(self):
        """Test cache clearing."""
        self.service._cache["test_key"] = {"data": [], "cached_at": None}
        self.service.clear_cache()
        assert len(self.service._cache) == 0

    def test_get_fallback_hashtags(self):
        """Test fallback hashtag data retrieval."""
        hashtags = self.service._get_fallback_hashtags("instagram", "fitness")
        assert len(hashtags) > 0
        assert all(h["hashtag"].startswith("#") for h in hashtags)
        # Should be sorted by score descending
        scores = [h["score"] for h in hashtags]
        assert scores == sorted(scores, reverse=True)

    def test_get_fallback_topics(self):
        """Test fallback topics data retrieval."""
        topics = self.service._get_fallback_topics("fitness")
        assert len(topics) == 5
        assert all("title" in t for t in topics)
        assert all(0.0 <= t["relevance_score"] <= 1.0 for t in topics)


# ============== Content Scheduler Tests ==============

class TestContentScheduler:
    """Tests for the content scheduler service."""

    def setup_method(self):
        self.service = ContentSchedulerService()

    def test_get_best_posting_times(self):
        """Test getting best posting times."""
        times = self.service.get_best_posting_times("instagram", 0)  # Monday
        assert len(times) > 0
        assert all(":" in t for t in times)

    def test_get_content_series_for_day(self):
        """Test getting content series suggestions."""
        # Monday should have Monday Motivation
        series = self.service.get_content_series_for_day(0)
        assert len(series) > 0
        assert any("Monday" in s["name"] for s in series)

    def test_get_upcoming_holidays(self):
        """Test getting upcoming holidays."""
        holidays = self.service.get_upcoming_holidays(365)
        assert len(holidays) > 0
        assert all("name" in h for h in holidays)
        assert all("days_until" in h for h in holidays)

    def test_generate_content_calendar(self):
        """Test content calendar generation."""
        calendar = self.service.generate_content_calendar(
            business_id=1,
            platforms=["instagram", "tiktok"],
            days=7,
        )
        assert len(calendar) > 0
        assert all("platform" in slot for slot in calendar)
        assert all("date" in slot for slot in calendar)
        assert all("pillar_type" in slot for slot in calendar)

    def test_should_generate_content(self):
        """Test content generation timing logic."""
        from datetime import datetime, timezone
        # With no last generation, should generate
        result = self.service.should_generate_content(
            last_generated_at=None,
            schedule_time=datetime.now(timezone.utc).strftime("%H:%M"),
        )
        # Result depends on timing window, just verify it returns a bool
        assert isinstance(result, bool)
