"""Pytest fixtures for testing the social media generator backend."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database.base import Base
from app.api.dependencies import get_db
from app.main import app

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with tables."""
    # Import models to ensure they are registered with Base
    from app.database import models  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with overridden dependencies."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_business_data():
    """Sample business profile data for testing."""
    return {
        "name": "TechFlow Solutions",
        "industry": "technology",
        "description": "AI-powered productivity tools for modern teams",
        "brand_voice": "professional",
        "brand_colors": ["#2980B9", "#2C3E50"],
        "target_audience": "Tech-savvy professionals aged 25-45",
        "unique_selling_points": ["AI-powered", "Team collaboration", "Cloud native"],
        "languages": ["en"],
        "website": "https://techflow.example.com",
    }


@pytest.fixture
def sample_content_request():
    """Sample content generation request data."""
    return {
        "business_id": 1,
        "platform": "instagram",
        "pillar_type": "educational",
        "language": "en",
        "num_variants": 2,
        "topic": "productivity tips",
        "include_hashtags": True,
        "include_image": False,
    }
