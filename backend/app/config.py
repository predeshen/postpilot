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

    # AWS Bedrock (Claude for text generation)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "eu-central-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # Stability AI (image generation)
    stability_api_key: Optional[str] = None
    stability_model: str = "sd3.5-large-turbo"

    # Scheduler
    scheduler_enabled: bool = True
    scheduler_timezone: str = "Africa/Johannesburg"

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
