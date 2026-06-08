"""Tests for image generation API endpoints (Stability AI)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from app.services.image_generator import (
    ImageGeneratorService,
    PLATFORM_DIMENSIONS,
    PLATFORM_ASPECT_RATIOS,
    _build_image_prompt,
)


# ============== Unit Tests for Image Generator Service ==============

class TestImageGeneratorServiceUnit:
    """Unit tests for the image generator service."""

    def setup_method(self):
        self.service = ImageGeneratorService()

    def test_build_image_prompt_basic(self):
        """Test building a basic image prompt."""
        prompt = _build_image_prompt(text="fitness post about running")
        assert "fitness post about running" in prompt
        assert "professional" in prompt.lower() or "social media" in prompt.lower()

    def test_build_image_prompt_with_brand_colors(self):
        """Test prompt includes brand colors."""
        prompt = _build_image_prompt(
            text="test content",
            brand_colors=["#FF6B6B", "#2563EB"],
        )
        assert "#FF6B6B" in prompt
        assert "#2563EB" in prompt

    def test_build_image_prompt_with_industry(self):
        """Test prompt includes industry context."""
        prompt = _build_image_prompt(
            text="test",
            industry="fitness",
        )
        assert "fitness" in prompt

    def test_build_image_prompt_with_business_name(self):
        """Test prompt includes business name."""
        prompt = _build_image_prompt(
            text="test",
            business_name="FitCo",
        )
        assert "FitCo" in prompt

    def test_build_image_prompt_platform_context(self):
        """Test prompt changes based on platform."""
        prompt_tiktok = _build_image_prompt(text="test", platform="tiktok")
        prompt_fb = _build_image_prompt(text="test", platform="facebook_feed")

        assert "tiktok" in prompt_tiktok.lower() or "trendy" in prompt_tiktok.lower()
        assert "facebook" in prompt_fb.lower() or "professional" in prompt_fb.lower()

    @pytest.mark.asyncio
    async def test_generate_image_ai_no_api_key(self):
        """Test AI generation returns None when API key not configured."""
        with patch("app.services.image_generator.settings") as mock_settings:
            mock_settings.stability_api_key = None
            result = await self.service.generate_image_ai(
                prompt="test prompt",
                aspect_ratio="1:1",
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_image_falls_back_to_pillow(self):
        """Test that generate_image falls back to Pillow when AI fails."""
        import os

        path = await self.service.generate_image(
            platform="instagram_feed",
            text="Test content for fallback",
            brand_colors=["#2563EB", "#FF6B6B"],
            business_name="TestBrand",
            output_filename="test_fallback.png",
            use_ai=True,  # Will fail (no API key) and fall back
        )
        assert os.path.exists(path)
        os.remove(path)

    @pytest.mark.asyncio
    async def test_generate_image_no_ai(self):
        """Test that use_ai=False skips AI generation."""
        import os

        path = await self.service.generate_image(
            platform="instagram_feed",
            text="Test without AI",
            brand_colors=["#2563EB"],
            output_filename="test_no_ai.png",
            use_ai=False,
        )
        assert os.path.exists(path)
        os.remove(path)

    @pytest.mark.asyncio
    async def test_generate_image_from_prompt_no_api_key(self):
        """Test on-demand generation returns failure without API key."""
        result = await self.service.generate_image_from_prompt(
            prompt="A beautiful sunset",
            width=1080,
            height=1080,
        )
        assert result["success"] is False
        assert result["base64"] is None
        assert result["width"] == 1080
        assert result["height"] == 1080
        assert result["prompt"] == "A beautiful sunset"

    def test_get_available_models(self):
        """Test listing available models."""
        models = self.service.get_available_models()
        assert len(models) == 3
        model_ids = [m["id"] for m in models]
        assert "sd3.5-large-turbo" in model_ids
        assert "sd3.5-large" in model_ids
        assert "sd3.5-medium" in model_ids

    def test_platform_aspect_ratios(self):
        """Test platform aspect ratio mapping."""
        assert PLATFORM_ASPECT_RATIOS["instagram_feed"] == "1:1"
        assert PLATFORM_ASPECT_RATIOS["tiktok"] == "9:16"
        assert PLATFORM_ASPECT_RATIOS["instagram_story"] == "9:16"
        assert PLATFORM_ASPECT_RATIOS["facebook_feed"] == "16:9"
        assert PLATFORM_ASPECT_RATIOS["facebook_story"] == "9:16"

    @pytest.mark.asyncio
    async def test_generate_image_ai_success(self):
        """Test successful AI image generation with mocked httpx."""
        import httpx

        fake_image_bytes = b"\x89PNG\r\n\x1a\nfake_image_data"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_image_bytes

        with patch("app.services.image_generator.settings") as mock_settings:
            mock_settings.stability_api_key = "sk-test-key"
            mock_settings.stability_model = "sd3.5-large-turbo"

            with patch("app.services.image_generator.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client

                result = await self.service.generate_image_ai(
                    prompt="A test prompt",
                    aspect_ratio="1:1",
                )

        assert result == fake_image_bytes
        mock_client.post.assert_called_once()

        # Verify the request was made correctly
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        assert call_args[1]["headers"]["Authorization"] == "Bearer sk-test-key"
        assert call_args[1]["data"]["prompt"] == "A test prompt"
        assert call_args[1]["data"]["model"] == "sd3.5-large-turbo"
        assert call_args[1]["data"]["aspect_ratio"] == "1:1"

    def test_dimensions_to_platform(self):
        """Test dimension-to-platform mapping."""
        service = ImageGeneratorService()
        assert service._dimensions_to_platform(1080, 1080) == "instagram_feed"
        assert service._dimensions_to_platform(1080, 1920) == "tiktok"
        assert service._dimensions_to_platform(1200, 630) == "facebook_feed"

    def test_dimensions_to_aspect_ratio(self):
        """Test dimension-to-aspect-ratio mapping."""
        service = ImageGeneratorService()
        assert service._dimensions_to_aspect_ratio(1080, 1080) == "1:1"
        assert service._dimensions_to_aspect_ratio(1080, 1920) == "9:16"
        assert service._dimensions_to_aspect_ratio(1200, 630) == "16:9"


# ============== API Endpoint Tests ==============

@pytest.mark.asyncio
async def test_generate_image_endpoint(client: AsyncClient):
    """Test the /api/images/generate endpoint."""
    request_data = {
        "prompt": "A professional social media post for a tech company",
        "width": 1080,
        "height": 1080,
    }
    response = await client.post("/api/images/generate", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert "success" in data
    assert data["width"] == 1080
    assert data["height"] == 1080
    assert data["prompt"] == request_data["prompt"]
    # Without API key configured, success will be False
    assert data["success"] is False


@pytest.mark.asyncio
async def test_generate_image_endpoint_validation(client: AsyncClient):
    """Test validation on the image generation endpoint."""
    # Empty prompt
    response = await client.post("/api/images/generate", json={
        "prompt": "",
        "width": 1080,
        "height": 1080,
    })
    assert response.status_code == 422

    # Width too small
    response = await client.post("/api/images/generate", json={
        "prompt": "test",
        "width": 100,
        "height": 1080,
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_models_endpoint(client: AsyncClient):
    """Test the /api/images/models endpoint."""
    response = await client.get("/api/images/models")
    assert response.status_code == 200

    data = response.json()
    assert "models" in data
    assert "default_model" in data
    assert data["default_model"] == "sd3.5-large-turbo"
    assert len(data["models"]) == 3


@pytest.mark.asyncio
async def test_list_platforms_endpoint(client: AsyncClient):
    """Test the /api/images/platforms endpoint."""
    response = await client.get("/api/images/platforms")
    assert response.status_code == 200

    data = response.json()
    assert "platforms" in data
    assert "tiktok" in data["platforms"]
    assert "instagram_feed" in data["platforms"]
    assert data["platforms"]["instagram_feed"]["width"] == 1080
    assert data["platforms"]["instagram_feed"]["height"] == 1080


@pytest.mark.asyncio
async def test_generate_post_image_endpoint(client: AsyncClient, sample_business_data):
    """Test the /api/content/{post_id}/generate-image endpoint."""
    # Create business
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    # Generate a post first
    content_request = {
        "business_id": business_id,
        "platform": "instagram",
        "pillar_type": "educational",
        "language": "en",
        "num_variants": 1,
        "include_image": False,
    }
    content_response = await client.post("/api/content/generate", json=content_request)
    assert content_response.status_code == 200
    post_id = content_response.json()[0]["id"]

    # Generate image for the post
    response = await client.post(f"/api/content/{post_id}/generate-image")
    assert response.status_code == 200

    data = response.json()
    assert data["post_id"] == post_id
    assert data["platform"] in ["instagram_feed", "instagram"]
    assert "success" in data


@pytest.mark.asyncio
async def test_generate_post_image_not_found(client: AsyncClient):
    """Test generating image for non-existent post."""
    response = await client.post("/api/content/9999/generate-image")
    assert response.status_code == 404
