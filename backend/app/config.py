"""PostPilot application configuration using Pydantic Settings."""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "PostPilot"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./social_media.db"

    # AWS Configuration (single region for everything)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "ca-central-1"

    # Claude (Bedrock)
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # Bria Image Generation (SageMaker Marketplace)
    bedrock_image_model_id: str = "bria-ai-2-3-fast-commercial"
    sagemaker_endpoint_name: Optional[str] = None

    # Scheduler
    scheduler_enabled: bool = True
    scheduler_timezone: str = "UTC"

    # Content Generation
    default_language: str = "en"
    max_hashtags_per_post: int = 30
    content_cache_ttl: int = 3600

    # Image Generation
    default_font: str = "arial"
    image_quality: int = 95

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
