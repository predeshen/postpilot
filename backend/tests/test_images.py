"""Tests for image generation API endpoints (Bria AI on SageMaker)."""

import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient

from app.services.image_generator import (
    ImageGeneratorService,
    PLATFORM_DIMENSIONS,
    BRIA_MODELS,
    BRIA_ASPECT_RATIOS,
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

    def test_generate_image_ai_no_endpoint(self):
        """Test AI generation returns None when endpoint not configured."""
        # Without SAGEMAKER_ENDPOINT_NAME, should return None
        result = self.service.generate_image_ai(
            prompt="test prompt",
            platform="instagram_feed",
        )
        assert result is None

    def test_generate_image_falls_back_to_pillow(self):
        """Test that generate_image falls back to Pillow when AI fails."""
        import os

        path = self.service.generate_image(
            platform="instagram_feed",
            text="Test content for fallback",
            brand_colors=["#2563EB", "#FF6B6B"],
            business_name="TestBrand",
            output_filename="test_fallback.png",
            use_ai=True,  # Will fail (no endpoint) and fall back
        )
        assert os.path.exists(path)
        os.remove(path)

    def test_generate_image_no_ai(self):
        """Test that use_ai=False skips AI generation."""
        import os

        path = self.service.generate_image(
            platform="instagram_feed",
            text="Test without AI",
            brand_colors=["#2563EB"],
            output_filename="test_no_ai.png",
            use_ai=False,
        )
        assert os.path.exists(path)
        os.remove(path)

    def test_generate_image_from_prompt_no_endpoint(self):
        """Test on-demand generation returns failure without endpoint."""
        result = self.service.generate_image_from_prompt(
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
        assert "bria-ai-2-3-fast-commercial" in model_ids
        assert "bria-ai-2-3-commercial" in model_ids
        assert "bria-ai-2-2-hd-commercial" in model_ids

    def test_bria_aspect_ratios(self):
        """Test Bria aspect ratio mapping."""
        assert BRIA_ASPECT_RATIOS["instagram_feed"] == "1:1"
        assert BRIA_ASPECT_RATIOS["tiktok"] == "9:16"
        assert BRIA_ASPECT_RATIOS["instagram_story"] == "9:16"
        assert BRIA_ASPECT_RATIOS["facebook_feed"] == "16:9"
        assert BRIA_ASPECT_RATIOS["facebook_story"] == "9:16"

    def test_bria_models_dict(self):
        """Test Bria models dictionary."""
        assert BRIA_MODELS["bria-2.3-fast"] == "bria-ai-2-3-fast-commercial"
        assert BRIA_MODELS["bria-2.3"] == "bria-ai-2-3-commercial"
        assert BRIA_MODELS["bria-2.2-hd"] == "bria-ai-2-2-hd-commercial"

    def test_generate_image_ai_success(self):
        """Test successful AI image generation with mocked SageMaker."""
        import base64
        import json
        from io import BytesIO
        from unittest.mock import MagicMock, patch

        # Create a small test image in base64
        test_image_b64 = base64.b64encode(b"\x89PNG\r\n\x1a\nfake_image_data").decode()

        mock_client = MagicMock()
        response_payload = json.dumps({
            "result": "success",
            "artifacts": [{"seed": 42, "image_base64": test_image_b64, "embeddings_base64": []}]
        }).encode()
        mock_body = MagicMock()
        mock_body.read.return_value = response_payload
        mock_client.invoke_endpoint.return_value = {"Body": mock_body}

        service = ImageGeneratorService()
        service._sagemaker_client = mock_client

        with patch("app.services.image_generator.settings") as mock_settings:
            mock_settings.sagemaker_endpoint_name = "postpilot-bria"
            mock_settings.aws_region = "ca-central-1"

            result = service.generate_image_ai(
                prompt="A test prompt",
                platform="instagram_feed",
            )

        assert result == test_image_b64
        mock_client.invoke_endpoint.assert_called_once()

        # Verify the payload sent to SageMaker
        call_kwargs = mock_client.invoke_endpoint.call_args[1]
        assert call_kwargs["EndpointName"] == "postpilot-bria"
        assert call_kwargs["ContentType"] == "application/json"

        sent_payload = json.loads(call_kwargs["Body"])
        assert sent_payload["prompt"] == "A test prompt"
        assert sent_payload["eula_license_agreement"] is True
        assert sent_payload["aspect_ratio"] == "1:1"
        assert sent_payload["steps"] == 20

    def test_dimensions_to_platform(self):
        """Test dimension-to-platform mapping."""
        service = ImageGeneratorService()
        assert service._dimensions_to_platform(1080, 1080) == "instagram_feed"
        assert service._dimensions_to_platform(1080, 1920) == "tiktok"
        assert service._dimensions_to_platform(1200, 630) == "facebook_feed"


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
    # Without endpoint configured, success will be False (fallback)
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
    assert data["default_model"] == "bria-ai-2-3-fast-commercial"
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
