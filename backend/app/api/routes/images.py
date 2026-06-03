"""Image generation API routes using Bria AI on AWS SageMaker."""

import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import get_image_generator
from app.models.schemas import ImageGenerateRequest, ImageGenerateResponse
from app.services.image_generator import ImageGeneratorService, BRIA_MODELS, PLATFORM_DIMENSIONS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image(
    request: ImageGenerateRequest,
    image_service: ImageGeneratorService = Depends(get_image_generator),
):
    """Generate an AI image from a text prompt using Bria AI on SageMaker.

    This endpoint allows on-demand image generation with custom prompts,
    dimensions, and optional model selection.

    Available models (SageMaker Marketplace):
    - bria-ai-2-3-fast-commercial (default) - Quick generation
    - bria-ai-2-3-commercial - Higher quality
    - bria-ai-2-2-hd-commercial - Highest quality

    Note: Requires a deployed SageMaker endpoint (SAGEMAKER_ENDPOINT_NAME).
    """
    result = image_service.generate_image_from_prompt(
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
    """List available Bria AI image generation models (SageMaker Marketplace)."""
    return {
        "models": image_service.get_available_models(),
        "default_model": "bria-ai-2-3-fast-commercial",
    }


@router.get("/platforms")
async def list_platform_dimensions(
    image_service: ImageGeneratorService = Depends(get_image_generator),
):
    """List platform-specific image dimensions."""
    return {
        "platforms": image_service.get_platform_dimensions(),
    }
