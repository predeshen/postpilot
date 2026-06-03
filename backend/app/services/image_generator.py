"""Image generation service using Bria AI models via AWS SageMaker.

Bria 2.3 Fast Commercial is a SageMaker Marketplace model that requires
a deployed SageMaker endpoint. It is NOT a direct Bedrock model.

Falls back to Pillow-based template generation when the SageMaker endpoint
is not configured or unavailable.
"""

import base64
import io
import json
import logging
import os
import random
import textwrap
from typing import Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from PIL import Image, ImageDraw, ImageFont

from app.config import settings

logger = logging.getLogger(__name__)

# Available Bria models on SageMaker Marketplace
BRIA_MODELS = {
    "bria-2.3-fast": "bria-ai-2-3-fast-commercial",
    "bria-2.3": "bria-ai-2-3-commercial",
    "bria-2.2-hd": "bria-ai-2-2-hd-commercial",
}

# Bria aspect ratios (SageMaker model uses aspect ratios, not pixel dimensions)
BRIA_ASPECT_RATIOS = {
    "tiktok": "9:16",
    "instagram_feed": "1:1",
    "instagram_story": "9:16",
    "facebook_feed": "16:9",
    "facebook_story": "9:16",
}

# Platform-specific image dimensions (used for Pillow fallback)
PLATFORM_DIMENSIONS = {
    "tiktok": {"width": 1080, "height": 1920, "label": "TikTok (9:16)"},
    "instagram_feed": {"width": 1080, "height": 1080, "label": "Instagram Feed (1:1)"},
    "instagram_story": {"width": 1080, "height": 1920, "label": "Instagram Story (9:16)"},
    "facebook_feed": {"width": 1200, "height": 630, "label": "Facebook Feed (16:9)"},
    "facebook_story": {"width": 1080, "height": 1920, "label": "Facebook Story (9:16)"},
}

# Template styles (for Pillow fallback)
TEMPLATE_STYLES = {
    "bold_text": {
        "text_position": "center",
        "text_size_ratio": 0.06,
        "padding_ratio": 0.1,
        "overlay_opacity": 180,
    },
    "minimal": {
        "text_position": "bottom",
        "text_size_ratio": 0.04,
        "padding_ratio": 0.05,
        "overlay_opacity": 200,
    },
    "gradient_overlay": {
        "text_position": "bottom",
        "text_size_ratio": 0.05,
        "padding_ratio": 0.08,
        "overlay_opacity": 160,
    },
    "split_layout": {
        "text_position": "top",
        "text_size_ratio": 0.045,
        "padding_ratio": 0.1,
        "overlay_opacity": 220,
    },
    "quote_style": {
        "text_position": "center",
        "text_size_ratio": 0.055,
        "padding_ratio": 0.12,
        "overlay_opacity": 190,
    },
}


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _get_contrast_color(bg_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Get contrasting text color (black or white) for readability."""
    luminance = (0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]) / 255
    return (255, 255, 255) if luminance < 0.5 else (0, 0, 0)


def _build_image_prompt(
    text: str,
    brand_colors: Optional[List[str]] = None,
    business_name: Optional[str] = None,
    industry: Optional[str] = None,
    style: str = "bold_text",
    platform: str = "instagram_feed",
) -> str:
    """Build a descriptive prompt for Bria AI image generation.

    Incorporates brand identity, colors, industry context, and platform
    to generate relevant social media visuals.
    """
    # Base prompt from the content
    prompt_parts = []

    # Add the core content/concept
    if text:
        # Trim long content to use as concept guidance
        concept = text[:200] if len(text) > 200 else text
        prompt_parts.append(f"A professional social media post visual about: {concept}")
    else:
        prompt_parts.append("A professional social media post visual")

    # Add industry context
    if industry:
        prompt_parts.append(f"for a {industry} business")

    # Add brand name context
    if business_name:
        prompt_parts.append(f"brand name: {business_name}")

    # Add color guidance
    if brand_colors and len(brand_colors) >= 1:
        color_names = ", ".join(brand_colors[:3])
        prompt_parts.append(f"using brand colors: {color_names}")

    # Add style guidance based on template style
    style_descriptions = {
        "bold_text": "bold and modern design with strong typography",
        "minimal": "clean minimal design with lots of whitespace",
        "gradient_overlay": "vibrant gradient background with modern aesthetic",
        "split_layout": "professional split-layout composition",
        "quote_style": "inspirational quote card design with elegant typography",
    }
    style_desc = style_descriptions.get(style, "professional modern design")
    prompt_parts.append(style_desc)

    # Add platform context
    platform_styles = {
        "tiktok": "trendy, eye-catching, vertical format, youth-oriented",
        "instagram_feed": "polished, aesthetic, square format, visually striking",
        "instagram_story": "dynamic, vertical, engaging, story-friendly",
        "facebook_feed": "professional, informative, wide format, shareable",
        "facebook_story": "casual, personal, vertical, story format",
    }
    platform_style = platform_styles.get(platform, "professional social media")
    prompt_parts.append(platform_style)

    # Quality modifiers
    prompt_parts.append("high quality, commercial photography style, clean composition, no text overlays")

    return ", ".join(prompt_parts)


class ImageGeneratorService:
    """Service for generating social media images using Bria AI on SageMaker.

    Primary: Uses Bria AI models via SageMaker endpoint for AI-generated images.
    Fallback: Uses Pillow-based template generation when endpoint is unavailable.
    """

    def __init__(self):
        """Initialize the image generator service."""
        self._output_dir = os.path.join(os.getcwd(), "generated_images")
        os.makedirs(self._output_dir, exist_ok=True)
        self._sagemaker_client = None

    @property
    def sagemaker_client(self):
        """Lazy initialization of boto3 SageMaker Runtime client."""
        if self._sagemaker_client is None:
            try:
                session_kwargs = {"region_name": settings.aws_region}
                if settings.aws_access_key_id and settings.aws_secret_access_key:
                    session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
                    session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

                session = boto3.Session(**session_kwargs)
                self._sagemaker_client = session.client("sagemaker-runtime")
            except (NoCredentialsError, Exception) as e:
                logger.warning(f"Failed to initialize SageMaker client: {e}")
                self._sagemaker_client = None
        return self._sagemaker_client

    def generate_image_ai(
        self,
        prompt: str,
        platform: str = "instagram_feed",
        negative_prompt: str = "text, watermark, blurry, low quality",
        steps: int = 20,
        seed: Optional[int] = None,
    ) -> Optional[str]:
        """Generate an image using Bria AI on SageMaker.

        Args:
            prompt: Text prompt describing the image to generate.
            platform: Platform key to determine aspect ratio.
            negative_prompt: Things to avoid in the generated image.
            steps: Number of inference steps (higher = better quality, slower).
            seed: Random seed for reproducibility. None for random.

        Returns:
            Base64-encoded image string, or None if generation fails.
        """
        if not settings.sagemaker_endpoint_name:
            logger.warning(
                "SageMaker endpoint not configured. "
                "Set SAGEMAKER_ENDPOINT_NAME to use Bria AI image generation."
            )
            return None

        if self.sagemaker_client is None:
            logger.warning("SageMaker client not available for image generation")
            return None

        # Determine aspect ratio from platform
        aspect_ratio = BRIA_ASPECT_RATIOS.get(platform, "1:1")

        # Use random seed if not specified
        if seed is None:
            seed = random.randint(1, 2**31 - 1)

        try:
            payload = json.dumps({
                "prompt": prompt,
                "steps": steps,
                "eula_license_agreement": True,
                "seed": seed,
                "aspect_ratio": aspect_ratio,
                "negative_prompt": negative_prompt,
            })

            response = self.sagemaker_client.invoke_endpoint(
                EndpointName=settings.sagemaker_endpoint_name,
                ContentType="application/json",
                Accept="application/json",
                Body=payload,
            )

            result = json.loads(response["Body"].read())

            # Bria SageMaker response format
            if result.get("result") == "success" and "artifacts" in result:
                if len(result["artifacts"]) > 0:
                    image_base64 = result["artifacts"][0]["image_base64"]
                    logger.info(
                        f"Successfully generated image via SageMaker "
                        f"(endpoint={settings.sagemaker_endpoint_name}, "
                        f"aspect_ratio={aspect_ratio})"
                    )
                    return image_base64

            logger.error(f"Unexpected Bria response format: {list(result.keys())}")
            return None

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"SageMaker API error ({error_code}): {error_msg}")
            return None
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None

    def generate_image(
        self,
        platform: str,
        text: str,
        brand_colors: List[str] = None,
        style: str = "bold_text",
        business_name: Optional[str] = None,
        industry: Optional[str] = None,
        logo_path: Optional[str] = None,
        output_filename: Optional[str] = None,
        use_ai: bool = True,
    ) -> str:
        """Generate a social media image.

        Attempts AI generation via Bria/SageMaker first, falls back to Pillow templates.

        Args:
            platform: Platform key (tiktok, instagram_feed, etc.)
            text: Text content / concept for the image
            brand_colors: List of hex color codes for the brand
            style: Template style name
            business_name: Business name for branding
            industry: Business industry for prompt context
            logo_path: Path to logo file for overlay (Pillow fallback only)
            output_filename: Custom output filename
            use_ai: Whether to attempt AI generation (default True)

        Returns:
            Path to the generated image file
        """
        # Get dimensions for the platform
        dimensions = PLATFORM_DIMENSIONS.get(platform, PLATFORM_DIMENSIONS["instagram_feed"])
        width = dimensions["width"]
        height = dimensions["height"]

        if output_filename is None:
            output_filename = f"{platform}_{style}_{os.getpid()}.png"

        output_path = os.path.join(self._output_dir, output_filename)

        # Attempt AI generation first
        if use_ai:
            prompt = _build_image_prompt(
                text=text,
                brand_colors=brand_colors,
                business_name=business_name,
                industry=industry,
                style=style,
                platform=platform,
            )

            image_base64 = self.generate_image_ai(
                prompt=prompt,
                platform=platform,
            )

            if image_base64:
                # Save the AI-generated image
                image_data = base64.b64decode(image_base64)
                with open(output_path, "wb") as f:
                    f.write(image_data)
                logger.info(f"Saved AI-generated image: {output_path} ({width}x{height})")
                return output_path
            else:
                logger.info("AI generation failed, falling back to Pillow template")

        # Fallback: Pillow-based template generation
        return self._generate_pillow_fallback(
            platform=platform,
            text=text,
            brand_colors=brand_colors,
            style=style,
            business_name=business_name,
            logo_path=logo_path,
            output_path=output_path,
            width=width,
            height=height,
        )

    def generate_image_from_prompt(
        self,
        prompt: str,
        width: int = 1080,
        height: int = 1080,
        model_id: Optional[str] = None,
        output_filename: Optional[str] = None,
    ) -> Dict:
        """Generate an image from a custom prompt (on-demand endpoint).

        Args:
            prompt: User-provided text prompt.
            width: Image width (used to determine aspect ratio).
            height: Image height (used to determine aspect ratio).
            model_id: Optional model override (unused, kept for API compat).
            output_filename: Optional filename for saving.

        Returns:
            Dict with base64 image data, file path, and metadata.
        """
        # Map width/height to the closest platform for aspect ratio
        platform = self._dimensions_to_platform(width, height)

        image_base64 = self.generate_image_ai(
            prompt=prompt,
            platform=platform,
        )

        result = {
            "success": image_base64 is not None,
            "base64": image_base64,
            "width": width,
            "height": height,
            "model_id": model_id or settings.bedrock_image_model_id,
            "prompt": prompt,
            "file_path": None,
        }

        # Also save to file if generation succeeded
        if image_base64:
            if output_filename is None:
                output_filename = f"custom_{width}x{height}_{os.getpid()}.png"
            output_path = os.path.join(self._output_dir, output_filename)
            image_data = base64.b64decode(image_base64)
            with open(output_path, "wb") as f:
                f.write(image_data)
            result["file_path"] = output_path

        return result

    def _dimensions_to_platform(self, width: int, height: int) -> str:
        """Map pixel dimensions to the closest platform key for aspect ratio."""
        ratio = width / height if height > 0 else 1.0
        if ratio > 1.5:
            return "facebook_feed"  # 16:9
        elif ratio < 0.7:
            return "tiktok"  # 9:16
        else:
            return "instagram_feed"  # 1:1

    def _generate_pillow_fallback(
        self,
        platform: str,
        text: str,
        brand_colors: Optional[List[str]],
        style: str,
        business_name: Optional[str],
        logo_path: Optional[str],
        output_path: str,
        width: int,
        height: int,
    ) -> str:
        """Generate image using Pillow templates (fallback when SageMaker unavailable)."""
        # Get style settings
        style_config = TEMPLATE_STYLES.get(style, TEMPLATE_STYLES["bold_text"])

        # Determine colors
        if brand_colors and len(brand_colors) >= 2:
            primary_color = _hex_to_rgb(brand_colors[0])
            secondary_color = _hex_to_rgb(brand_colors[1])
        elif brand_colors and len(brand_colors) == 1:
            primary_color = _hex_to_rgb(brand_colors[0])
            secondary_color = tuple(max(0, c - 40) for c in primary_color)
        else:
            primary_color = (41, 128, 185)  # Default blue
            secondary_color = (44, 62, 80)  # Default dark

        # Create base image with gradient background
        img = Image.new("RGB", (width, height), primary_color)
        draw = ImageDraw.Draw(img)

        # Draw gradient background
        self._draw_gradient(draw, width, height, primary_color, secondary_color)

        # Add semi-transparent overlay for text readability
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        padding = int(width * style_config["padding_ratio"])
        opacity = style_config["overlay_opacity"]

        if style_config["text_position"] == "center":
            overlay_y_start = height // 4
            overlay_y_end = 3 * height // 4
        elif style_config["text_position"] == "bottom":
            overlay_y_start = height // 2
            overlay_y_end = height
        else:  # top
            overlay_y_start = 0
            overlay_y_end = height // 2

        overlay_draw.rectangle(
            [(0, overlay_y_start), (width, overlay_y_end)],
            fill=(0, 0, 0, opacity),
        )

        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img)

        # Calculate font size
        font_size = int(width * style_config["text_size_ratio"])
        font = self._get_font(font_size)

        # Wrap text to fit
        max_chars = int((width - 2 * padding) / (font_size * 0.55))
        wrapped_text = textwrap.fill(text, width=max_chars)

        # Calculate text position
        text_color = _get_contrast_color((0, 0, 0))  # White on dark overlay

        # Get text bounding box
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        if style_config["text_position"] == "center":
            text_x = (width - text_width) // 2
            text_y = (height - text_height) // 2
        elif style_config["text_position"] == "bottom":
            text_x = (width - text_width) // 2
            text_y = height - text_height - padding * 3
        else:  # top
            text_x = (width - text_width) // 2
            text_y = padding * 3

        # Draw text
        draw.text((text_x, text_y), wrapped_text, fill=text_color, font=font)

        # Add business name watermark if provided
        if business_name:
            watermark_size = int(font_size * 0.5)
            watermark_font = self._get_font(watermark_size)
            watermark_bbox = draw.textbbox((0, 0), business_name, font=watermark_font)
            watermark_width = watermark_bbox[2] - watermark_bbox[0]
            watermark_x = width - watermark_width - padding
            watermark_y = height - watermark_size - padding
            draw.text(
                (watermark_x, watermark_y),
                business_name,
                fill=(255, 255, 255, 180),
                font=watermark_font,
            )

        # Add logo overlay if provided
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path).convert("RGBA")
                logo_size = int(width * 0.15)
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                logo_position = (padding, padding)
                img.paste(logo, logo_position, logo)
            except (IOError, OSError) as e:
                logger.warning(f"Failed to load logo: {e}")

        # Save the image
        img.save(output_path, "PNG", quality=settings.image_quality)
        logger.info(f"Generated Pillow fallback image: {output_path} ({width}x{height})")
        return output_path

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get a font at the specified size, falling back to default if needed."""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except (IOError, OSError):
                    continue

        try:
            return ImageFont.truetype("DejaVuSans-Bold", size)
        except (IOError, OSError):
            return ImageFont.load_default()

    def _draw_gradient(
        self,
        draw: ImageDraw.Draw,
        width: int,
        height: int,
        color_start: Tuple[int, int, int],
        color_end: Tuple[int, int, int],
        direction: str = "vertical",
    ) -> None:
        """Draw a gradient on the image."""
        if direction == "vertical":
            for y in range(height):
                ratio = y / height
                r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
                g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
                b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        else:
            for x in range(width):
                ratio = x / width
                r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
                g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
                b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
                draw.line([(x, 0), (x, height)], fill=(r, g, b))

    def generate_all_platform_variants(
        self,
        text: str,
        brand_colors: List[str] = None,
        style: str = "bold_text",
        business_name: Optional[str] = None,
        industry: Optional[str] = None,
        prefix: str = "post",
        use_ai: bool = True,
    ) -> Dict[str, str]:
        """Generate images for all platform dimensions.

        Args:
            text: Text content / concept for the image
            brand_colors: Brand color palette
            style: Template style
            business_name: Business name for branding
            industry: Business industry for context
            prefix: Filename prefix
            use_ai: Whether to attempt AI generation

        Returns:
            Dictionary mapping platform to file path
        """
        results = {}
        for platform_key in PLATFORM_DIMENSIONS:
            filename = f"{prefix}_{platform_key}.png"
            path = self.generate_image(
                platform=platform_key,
                text=text,
                brand_colors=brand_colors,
                style=style,
                business_name=business_name,
                industry=industry,
                output_filename=filename,
                use_ai=use_ai,
            )
            results[platform_key] = path

        return results

    def get_available_styles(self) -> List[Dict]:
        """Get list of available template styles."""
        return [
            {"id": style_id, "config": config}
            for style_id, config in TEMPLATE_STYLES.items()
        ]

    def get_platform_dimensions(self) -> Dict:
        """Get all platform dimension configurations."""
        return PLATFORM_DIMENSIONS

    def get_available_models(self) -> List[Dict]:
        """Get list of available Bria AI models (SageMaker Marketplace)."""
        return [
            {
                "id": model_id,
                "name": name,
                "description": desc,
            }
            for name, model_id, desc in [
                ("bria-2.3-fast", "bria-ai-2-3-fast-commercial", "Quick generation, real-time use (default)"),
                ("bria-2.3", "bria-ai-2-3-commercial", "Higher quality, slightly slower"),
                ("bria-2.2-hd", "bria-ai-2-2-hd-commercial", "Highest quality, best for final ad creatives"),
            ]
        ]


# Singleton instance
image_generator_service = ImageGeneratorService()
