"""FastAPI application entry point for PostPilot.

PostPilot is an AI-powered social media content generator built for
South African businesses. This backend is designed for on-demand operation -
it serves requests when the mobile app triggers it, and scales to zero when
idle. This keeps hosting costs minimal since you only pay for actual AI
generation calls.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.base import init_db, close_db
from app.api.routes import business, content, trends, analytics, schedule, campaigns, images
from app.models.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events - startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down application")
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "PostPilot API - AI-powered social media content generation for South African businesses. "
        "Generates brand-consistent content for TikTok, Instagram, and Facebook "
        "using AWS Bedrock (Claude). Designed for on-demand serverless deployment."
    ),
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(business.router)
app.include_router(content.router)
app.include_router(trends.router)
app.include_router(analytics.router)
app.include_router(schedule.router)
app.include_router(campaigns.router)
app.include_router(images.router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        service=settings.app_name,
    )


@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "description": (
            "PostPilot - On-demand AI content generation API for South African businesses. "
            "Content is generated when you request it - no 24/7 background workers needed. "
            "Perfect for serverless deployment (AWS Lambda) that scales to zero."
        ),
    }
