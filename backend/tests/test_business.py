"""Tests for business profile API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_setup_business(client: AsyncClient, sample_business_data):
    """Test creating a new business profile."""
    response = await client.post("/api/business/setup", json=sample_business_data)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == sample_business_data["name"]
    assert data["industry"] == sample_business_data["industry"]
    assert data["brand_voice"] == sample_business_data["brand_voice"]
    assert data["brand_colors"] == sample_business_data["brand_colors"]
    assert data["id"] is not None
    assert data["created_at"] is not None


@pytest.mark.asyncio
async def test_setup_business_minimal(client: AsyncClient):
    """Test creating a business profile with minimal data."""
    minimal_data = {
        "name": "Simple Biz",
        "industry": "retail",
    }
    response = await client.post("/api/business/setup", json=minimal_data)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Simple Biz"
    assert data["brand_voice"] == "professional"  # Default
    assert data["languages"] == ["en"]  # Default


@pytest.mark.asyncio
async def test_setup_business_validation_error(client: AsyncClient):
    """Test business setup with invalid data."""
    invalid_data = {
        "name": "",  # Too short
        "industry": "tech",
    }
    response = await client.post("/api/business/setup", json=invalid_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_business(client: AsyncClient, sample_business_data):
    """Test retrieving a business profile by ID."""
    # Create first
    create_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = create_response.json()["id"]

    # Retrieve
    response = await client.get(f"/api/business/{business_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == business_id
    assert data["name"] == sample_business_data["name"]


@pytest.mark.asyncio
async def test_get_business_not_found(client: AsyncClient):
    """Test retrieving a non-existent business profile."""
    response = await client.get("/api/business/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_business(client: AsyncClient, sample_business_data):
    """Test updating a business profile."""
    # Create first
    create_response = await client.post("/api/business/setup", json=sample_business_data)
    business_id = create_response.json()["id"]

    # Update
    update_data = {
        "name": "TechFlow Solutions Pro",
        "brand_voice": "bold",
    }
    response = await client.put(
        f"/api/business/update?business_id={business_id}",
        json=update_data,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "TechFlow Solutions Pro"
    assert data["brand_voice"] == "bold"
    # Unchanged fields should remain
    assert data["industry"] == sample_business_data["industry"]


@pytest.mark.asyncio
async def test_update_business_not_found(client: AsyncClient):
    """Test updating a non-existent business profile."""
    response = await client.put(
        "/api/business/update?business_id=999",
        json={"name": "Updated"},
    )
    assert response.status_code == 404
