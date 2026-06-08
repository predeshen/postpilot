"""Image generation API routes using Stability AI."""

import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import get_image_generator
from app.models.schemas import ImageGenerateRequest, ImageGenerateResponse
from app.services.image_generator import ImageGeneratorService, PLATFORM_DIMENSIONS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image(
    request: ImageGenerateRequest,
    image_service: ImageGeneratorService = Depends(get_image_generator),
):
    """Generate an AI image from a text prompt using Stability AI.

    This endpoint allows on-demand image generation with custom prompts,
    dimensions, and optional model selection.

    Available models:
    - sd3.5-large-turbo (default) - Fast, high-quality generation
    - sd3.5-large - Highest quality, slightly slower
    - sd3.5-medium - Balanced quality and speed

    Note: Requires STABILITY_API_KEY to be configured.
    """
    result = await image_service.generate_image_from_prompt(
        prompt=request.prompt,
        width=request.width,
        height=request.height,
        model_id=request.model_id,
    )

    return ImageGenerateResponse(
        success=result["success"],
        image_base64=result["base64"],
        width=result["width"],
        height=result["height"],
        model_id=result["model_id"],
        prompt=result["prompt"],
        file_path=result["file_path"],
    )


@router.get("/models")
async def list_available_models(
    image_service: ImageGeneratorService = Depends(get_image_generator),
):
    """List available Stability AI image generation models."""
    return {
        "models": image_service.get_available_models(),
        "default_model": "sd3.5-large-turbo",
    }


@router.get("/platforms")
async def list_platform_dimensions(
    image_service: ImageGeneratorService = Depends(get_image_generator),
):
    """List platform-specific image dimensions."""
    return {
        "platforms": image_service.get_platform_dimensions(),
    }
