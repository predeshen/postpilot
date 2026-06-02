"""Tests for image generation API endpoints (Bria AI on AWS Bedrock)."""

import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient

from app.services.image_generator import (
    ImageGeneratorService,
    PLATFORM_DIMENSIONS,
    BRIA_MODELS,
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

    def test_generate_image_ai_no_client(self):
        """Test AI generation returns None when client unavailable."""
        # Without AWS credentials, should return None
        result = self.service.generate_image_ai(
            prompt="test prompt",
            width=1080,
            height=1080,
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
            use_ai=True,  # Will fail (no credentials) and fall back
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

    def test_generate_image_from_prompt_no_credentials(self):
        """Test on-demand generation returns failure without credentials."""
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
        assert "bria.bria-2.3-fast-v1:0" in model_ids
        assert "bria.bria-2.3-v1:0" in model_ids
        assert "bria.bria-2.2-hd-v1:0" in model_ids

    def test_generate_image_ai_success(self):
        """Test successful AI image generation with mocked Bedrock."""
        import base64
        import json
        from io import BytesIO
        from unittest.mock import MagicMock

        # Create a small test image in base64
        test_image_b64 = base64.b64encode(b"\x89PNG\r\n\x1a\nfake_image_data").decode()

        mock_client = MagicMock()
        response_payload = json.dumps({
            "artifacts": [{"base64": test_image_b64}]
        }).encode()
        mock_body = BytesIO(response_payload)
        mock_client.invoke_model.return_value = {"body": mock_body}

        service = ImageGeneratorService()
        service._bedrock_client = mock_client

        result = service.generate_image_ai(
            prompt="A test prompt",
            width=1080,
            height=1080,
        )

        assert result == test_image_b64
        mock_client.invoke_model.assert_called_once()


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
    # Without credentials, success will be False (fallback)
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
    assert data["default_model"] == "bria.bria-2.3-fast-v1:0"
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
