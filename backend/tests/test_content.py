"""Tests for content generation and management API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_content(client: AsyncClient, sample_business_data):
    """Test AI content generation endpoint."""
    # Create business first
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    # Generate content
    content_request = {
        "business_id": business_id,
        "platform": "instagram",
        "pillar_type": "educational",
        "language": "en",
        "num_variants": 2,
        "include_hashtags": True,
        "include_image": False,
    }
    response = await client.post("/api/content/generate", json=content_request)
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert data[0]["platform"] == "instagram"
    assert data[0]["status"] == "draft"
    assert data[0]["content"] != ""
    assert len(data[0]["hashtags"]) > 0


@pytest.mark.asyncio
async def test_generate_content_all_platforms(client: AsyncClient, sample_business_data):
    """Test content generation for all supported platforms."""
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    for platform in ["tiktok", "instagram", "facebook"]:
        content_request = {
            "business_id": business_id,
            "platform": platform,
            "num_variants": 1,
            "include_hashtags": True,
            "include_image": False,
        }
        response = await client.post("/api/content/generate", json=content_request)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["platform"] == platform


@pytest.mark.asyncio
async def test_generate_content_business_not_found(client: AsyncClient):
    """Test content generation with invalid business ID."""
    content_request = {
        "business_id": 999,
        "platform": "instagram",
        "num_variants": 1,
        "include_hashtags": True,
        "include_image": False,
    }
    response = await client.post("/api/content/generate", json=content_request)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_content_calendar(client: AsyncClient, sample_business_data):
    """Test content calendar endpoint."""
    # Create business and content
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    # Generate some content
    content_request = {
        "business_id": business_id,
        "platform": "instagram",
        "num_variants": 2,
        "include_hashtags": True,
        "include_image": False,
    }
    await client.post("/api/content/generate", json=content_request)

    # Get calendar
    response = await client.get(f"/api/content/calendar?business_id={business_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert data["upcoming"] == 2  # All drafts
    assert data["published"] == 0


@pytest.mark.asyncio
async def test_approve_content(client: AsyncClient, sample_business_data):
    """Test content approval workflow."""
    # Create business and content
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    content_request = {
        "business_id": business_id,
        "platform": "instagram",
        "num_variants": 1,
        "include_hashtags": True,
        "include_image": False,
    }
    gen_response = await client.post("/api/content/generate", json=content_request)
    post_id = gen_response.json()[0]["id"]

    # Approve
    response = await client.post(f"/api/content/approve/{post_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_publish_content(client: AsyncClient, sample_business_data):
    """Test content publishing workflow."""
    # Create -> Generate -> Approve -> Publish
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    content_request = {
        "business_id": business_id,
        "platform": "facebook",
        "num_variants": 1,
        "include_hashtags": True,
        "include_image": False,
    }
    gen_response = await client.post("/api/content/generate", json=content_request)
    post_id = gen_response.json()[0]["id"]

    # Approve first
    await client.post(f"/api/content/approve/{post_id}")

    # Then publish
    response = await client.post(f"/api/content/publish/{post_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "published"


@pytest.mark.asyncio
async def test_publish_without_approval(client: AsyncClient, sample_business_data):
    """Test that publishing without approval fails."""
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    content_request = {
        "business_id": business_id,
        "platform": "tiktok",
        "num_variants": 1,
        "include_hashtags": True,
        "include_image": False,
    }
    gen_response = await client.post("/api/content/generate", json=content_request)
    post_id = gen_response.json()[0]["id"]

    # Try to publish directly (should fail)
    response = await client.post(f"/api/content/publish/{post_id}")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_regenerate_content(client: AsyncClient, sample_business_data):
    """Test content regeneration endpoint."""
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    content_request = {
        "business_id": business_id,
        "platform": "instagram",
        "pillar_type": "promotional",
        "num_variants": 1,
        "include_hashtags": True,
        "include_image": False,
    }
    gen_response = await client.post("/api/content/generate", json=content_request)
    post_id = gen_response.json()[0]["id"]
    original_content = gen_response.json()[0]["content"]

    # Regenerate
    response = await client.post(f"/api/content/regenerate/{post_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "draft"
