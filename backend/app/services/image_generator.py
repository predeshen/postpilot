"""Image generation service using Stability AI (Stable Diffusion 3.5 Large Turbo).

Uses the Stability AI REST API for high-quality AI image generation.
Falls back to Pillow-based template generation when the API key is not set.
"""

import base64
import io
import logging
import os
import textwrap
from typing import Dict, List, Optional, Tuple

import httpx
from PIL import Image, ImageDraw, ImageFont

from app.config import settings

logger = logging.getLogger(__name__)

# Platform aspect ratios for Stability AI
PLATFORM_ASPECT_RATIOS = {
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
    """Build a descriptive prompt for Stability AI image generation.

    Incorporates brand identity, colors, industry context, and platform
    to generate relevant social media visuals.
    """
    prompt_parts = []

    # Add the core content/concept
    if text:
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
    """Service for generating social media images using Stability AI.

    Primary: Uses Stability AI SD3.5 Large Turbo for AI-generated images.
    Fallback: Uses Pillow-based template generation when API key is not set.
    """

    def __init__(self):
        """Initialize the image generator service."""
        self._output_dir = os.path.join(os.getcwd(), "generated_images")
        os.makedirs(self._output_dir, exist_ok=True)

    async def generate_image_ai(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        negative_prompt: str = "text, watermark, blurry, low quality",
    ) -> Optional[bytes]:
        """Generate image using Stability AI SD3.5 Large Turbo.

        Args:
            prompt: Text prompt describing the image to generate.
            aspect_ratio: Aspect ratio string (1:1, 9:16, 16:9, etc.).
            negative_prompt: Things to avoid in the generated image.

        Returns:
            Raw image bytes, or None if generation fails.
        """
        if not settings.stability_api_key:
            logger.warning(
                "Stability AI API key not configured. "
                "Set STABILITY_API_KEY to use AI image generation."
            )
            return None

        url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        headers = {
            "Authorization": f"Bearer {settings.stability_api_key}",
            "Accept": "image/*",
        }

        data = {
            "prompt": prompt,
            "model": settings.stability_model,
            "aspect_ratio": aspect_ratio,
            "negative_prompt": negative_prompt,
            "output_format": "png",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, data=data)

                if response.status_code == 200:
                    logger.info(
                        f"Successfully generated image via Stability AI "
                        f"(model={settings.stability_model}, "
                        f"aspect_ratio={aspect_ratio}, "
                        f"size={len(response.content)} bytes)"
                    )
                    return response.content
                else:
                    logger.error(
                        f"Stability AI error: {response.status_code} - {response.text[:500]}"
                    )
                    return None
        except httpx.TimeoutException:
            logger.error("Stability AI request timed out")
            return None
        except Exception as e:
            logger.error(f"Stability AI request failed: {e}")
            return None

    async def generate_image(
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

        Attempts AI generation via Stability AI first, falls back to Pillow templates.

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

            aspect_ratio = PLATFORM_ASPECT_RATIOS.get(platform, "1:1")
            image_bytes = await self.generate_image_ai(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )

            if image_bytes:
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                logger.info(f"Saved AI-generated image: {output_path}")
                return output_path
            else:
                logger.info("AI generation unavailable, falling back to Pillow template")

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

    async def generate_image_from_prompt(
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
        # Map width/height to aspect ratio
        aspect_ratio = self._dimensions_to_aspect_ratio(width, height)

        image_bytes = await self.generate_image_ai(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
        )

        image_base64 = None
        if image_bytes:
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        result = {
            "success": image_bytes is not None,
            "base64": image_base64,
            "width": width,
            "height": height,
            "model_id": model_id or settings.stability_model,
            "prompt": prompt,
            "file_path": None,
        }

        # Also save to file if generation succeeded
        if image_bytes:
            if output_filename is None:
                output_filename = f"custom_{width}x{height}_{os.getpid()}.png"
            output_path = os.path.join(self._output_dir, output_filename)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            result["file_path"] = output_path

        return result

    def _dimensions_to_aspect_ratio(self, width: int, height: int) -> str:
        """Map pixel dimensions to the closest aspect ratio string."""
        ratio = width / height if height > 0 else 1.0
        if ratio > 1.5:
            return "16:9"
        elif ratio < 0.7:
            return "9:16"
        else:
            return "1:1"

    def _dimensions_to_platform(self, width: int, height: int) -> str:
        """Map pixel dimensions to the closest platform key."""
        ratio = width / height if height > 0 else 1.0
        if ratio > 1.5:
            return "facebook_feed"
        elif ratio < 0.7:
            return "tiktok"
        else:
            return "instagram_feed"

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
        """Generate image using Pillow templates (fallback when Stability AI unavailable)."""
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

    async def generate_all_platform_variants(
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
            path = await self.generate_image(
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
        """Get list of available Stability AI models."""
        return [
            {
                "id": "sd3.5-large-turbo",
                "name": "Stable Diffusion 3.5 Large Turbo",
                "description": "Fast, high-quality generation (default)",
            },
            {
                "id": "sd3.5-large",
                "name": "Stable Diffusion 3.5 Large",
                "description": "Highest quality, slightly slower",
            },
            {
                "id": "sd3.5-medium",
                "name": "Stable Diffusion 3.5 Medium",
                "description": "Balanced quality and speed",
            },
        ]


# Singleton instance
image_generator_service = ImageGeneratorService()
