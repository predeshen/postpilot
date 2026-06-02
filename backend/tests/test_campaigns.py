"""Tests for Meta Ads Campaign API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_campaign(client: AsyncClient, sample_business_data):
    """Test creating a new campaign with 3 angles."""
    # Create business first
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    assert biz_response.status_code == 201
    business_id = biz_response.json()["id"]

    # Create campaign
    campaign_request = {
        "business_id": business_id,
        "campaign_name": "Summer Promo 2024",
        "campaign_objective": "conversions",
        "target_audience": "Tech professionals aged 25-45 in South Africa",
        "product_service": "AI productivity tools for teams",
        "budget_range": "R5000-R15000/month",
    }
    response = await client.post("/api/campaigns/create", json=campaign_request)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Summer Promo 2024"
    assert data["objective"] == "conversions"
    assert data["status"] == "draft"
    assert len(data["angles"]) == 3
    assert data["angles"][0]["angle_number"] == 1
    assert data["angles"][1]["angle_number"] == 2
    assert data["angles"][2]["angle_number"] == 3


@pytest.mark.asyncio
async def test_create_campaign_business_not_found(client: AsyncClient):
    """Test creating a campaign with invalid business ID."""
    campaign_request = {
        "business_id": 999,
        "campaign_name": "Test Campaign",
        "campaign_objective": "awareness",
        "product_service": "Test product",
    }
    response = await client.post("/api/campaigns/create", json=campaign_request)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_campaign_invalid_objective(client: AsyncClient, sample_business_data):
    """Test creating a campaign with invalid objective."""
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    campaign_request = {
        "business_id": business_id,
        "campaign_name": "Test Campaign",
        "campaign_objective": "invalid_objective",
        "product_service": "Test product",
    }
    response = await client.post("/api/campaigns/create", json=campaign_request)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_campaign(client: AsyncClient, sample_business_data):
    """Test getting campaign details."""
    # Create business and campaign
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    campaign_request = {
        "business_id": business_id,
        "campaign_name": "Get Test Campaign",
        "campaign_objective": "traffic",
        "product_service": "Website builder for SMEs",
    }
    create_response = await client.post("/api/campaigns/create", json=campaign_request)
    campaign_id = create_response.json()["id"]

    # Get campaign
    response = await client.get(f"/api/campaigns/{campaign_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == campaign_id
    assert data["name"] == "Get Test Campaign"
    assert len(data["angles"]) == 3


@pytest.mark.asyncio
async def test_get_campaign_not_found(client: AsyncClient):
    """Test getting a non-existent campaign."""
    response = await client.get("/api/campaigns/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_creatives(client: AsyncClient, sample_business_data):
    """Test generating creatives for campaign angles."""
    # Create business and campaign
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    campaign_request = {
        "business_id": business_id,
        "campaign_name": "Creatives Test",
        "campaign_objective": "conversions",
        "product_service": "Online fitness coaching",
        "target_audience": "Women aged 25-40 in Johannesburg",
    }
    create_response = await client.post("/api/campaigns/create", json=campaign_request)
    campaign_id = create_response.json()["id"]

    # Generate creatives
    response = await client.post(f"/api/campaigns/{campaign_id}/generate-creatives")
    assert response.status_code == 200

    data = response.json()
    assert len(data["angles"]) == 3

    # Each angle should have 5 creatives
    for angle in data["angles"]:
        assert len(angle["creatives"]) == 5
        for creative in angle["creatives"]:
            assert creative["headline"] != ""
            assert creative["primary_text"] != ""
            assert creative["call_to_action"] != ""
            assert creative["ad_format"] in ["single_image", "carousel", "video", "collection"]
            assert creative["platform_placement"] in ["feed", "stories", "reels", "audience_network"]
            assert creative["status"] == "draft"


@pytest.mark.asyncio
async def test_generate_creatives_campaign_not_found(client: AsyncClient):
    """Test generating creatives for non-existent campaign."""
    response = await client.post("/api/campaigns/999/generate-creatives")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_campaigns(client: AsyncClient, sample_business_data):
    """Test listing campaigns for a business."""
    # Create business
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    # Create multiple campaigns
    for i in range(3):
        campaign_request = {
            "business_id": business_id,
            "campaign_name": f"Campaign {i + 1}",
            "campaign_objective": "conversions",
            "product_service": f"Product {i + 1}",
        }
        await client.post("/api/campaigns/create", json=campaign_request)

    # List campaigns
    response = await client.get(f"/api/campaigns/list?business_id={business_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 3
    assert len(data["campaigns"]) == 3


@pytest.mark.asyncio
async def test_list_campaigns_empty(client: AsyncClient, sample_business_data):
    """Test listing campaigns when none exist."""
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    response = await client.get(f"/api/campaigns/list?business_id={business_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 0
    assert data["campaigns"] == []


@pytest.mark.asyncio
async def test_delete_campaign(client: AsyncClient, sample_business_data):
    """Test deleting a campaign."""
    # Create business and campaign
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    campaign_request = {
        "business_id": business_id,
        "campaign_name": "Delete Test",
        "campaign_objective": "awareness",
        "product_service": "Coaching service",
    }
    create_response = await client.post("/api/campaigns/create", json=campaign_request)
    campaign_id = create_response.json()["id"]

    # Delete campaign
    response = await client.delete(f"/api/campaigns/{campaign_id}")
    assert response.status_code == 200
    assert response.json()["id"] == campaign_id

    # Verify it's gone
    get_response = await client.get(f"/api/campaigns/{campaign_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_campaign_not_found(client: AsyncClient):
    """Test deleting a non-existent campaign."""
    response = await client.delete("/api/campaigns/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_campaign_angles_have_correct_hook_types(client: AsyncClient, sample_business_data):
    """Test that generated angles have valid hook types."""
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    campaign_request = {
        "business_id": business_id,
        "campaign_name": "Hook Types Test",
        "campaign_objective": "leads",
        "product_service": "Business consulting",
    }
    response = await client.post("/api/campaigns/create", json=campaign_request)
    assert response.status_code == 200

    data = response.json()
    valid_hook_types = ["pain_point", "aspirational", "social_proof", "curiosity", "urgency", "contrarian"]
    for angle in data["angles"]:
        assert angle["hook_type"] in valid_hook_types
        assert angle["title"] != ""


@pytest.mark.asyncio
async def test_campaign_full_workflow(client: AsyncClient, sample_business_data):
    """Test the full campaign workflow: create -> generate creatives -> view."""
    # Setup
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    # Step 1: Create campaign
    campaign_request = {
        "business_id": business_id,
        "campaign_name": "Full Workflow Test",
        "campaign_objective": "engagement",
        "product_service": "Social media management tool",
        "target_audience": "Small business owners in Cape Town",
        "budget_range": "R3000-R8000/month",
    }
    create_response = await client.post("/api/campaigns/create", json=campaign_request)
    assert create_response.status_code == 200
    campaign_id = create_response.json()["id"]

    # Step 2: Generate creatives
    creatives_response = await client.post(f"/api/campaigns/{campaign_id}/generate-creatives")
    assert creatives_response.status_code == 200

    # Step 3: Get full campaign
    get_response = await client.get(f"/api/campaigns/{campaign_id}")
    assert get_response.status_code == 200

    data = get_response.json()
    assert data["name"] == "Full Workflow Test"
    assert data["budget_range"] == "R3000-R8000/month"
    assert len(data["angles"]) == 3

    total_creatives = sum(len(angle["creatives"]) for angle in data["angles"])
    assert total_creatives == 15  # 3 angles x 5 creatives


@pytest.mark.asyncio
async def test_generate_creatives_idempotent(client: AsyncClient, sample_business_data):
    """Test that generating creatives twice does not duplicate them."""
    biz_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = biz_response.json()["id"]

    campaign_request = {
        "business_id": business_id,
        "campaign_name": "Idempotent Test",
        "campaign_objective": "traffic",
        "product_service": "E-commerce store",
    }
    create_response = await client.post("/api/campaigns/create", json=campaign_request)
    campaign_id = create_response.json()["id"]

    # Generate creatives twice
    await client.post(f"/api/campaigns/{campaign_id}/generate-creatives")
    response = await client.post(f"/api/campaigns/{campaign_id}/generate-creatives")
    assert response.status_code == 200

    data = response.json()
    # Should still only have 5 creatives per angle (not 10)
    for angle in data["angles"]:
        assert len(angle["creatives"]) == 5
