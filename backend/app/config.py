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

    # AWS Bedrock
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "eu-central-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    # Bria image model (different region)
    aws_image_region: str = "ca-central-1"
    bedrock_image_model_id: str = "bria.bria-ai-2-3-fast-commercial"

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
