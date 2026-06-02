"""Dependency injection for API routes."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import get_session
from app.services.ai_generator import ai_generator_service
from app.services.campaign_generator import campaign_generator_service
from app.services.content_scheduler import content_scheduler_service
from app.services.image_generator import image_generator_service
from app.services.theme_engine import theme_engine_service
from app.services.trending_hashtags import trending_hashtags_service


async def get_db() -> AsyncSession:
    """Get database session dependency."""
    async for session in get_session():
        yield session


def get_ai_generator():
    """Get AI generator service instance."""
    return ai_generator_service


def get_campaign_generator():
    """Get campaign generator service instance."""
    return campaign_generator_service


def get_trending_service():
    """Get trending hashtags service instance."""
    return trending_hashtags_service


def get_scheduler_service():
    """Get content scheduler service instance."""
    return content_scheduler_service


def get_image_generator():
    """Get image generator service instance."""
    return image_generator_service


def get_theme_engine():
    """Get theme engine service instance."""
    return theme_engine_service
