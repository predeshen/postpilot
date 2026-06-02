"""Image template engine using Pillow for platform-specific social media images."""

import io
import logging
import os
import textwrap
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from app.config import settings

logger = logging.getLogger(__name__)

# Platform-specific image dimensions
PLATFORM_DIMENSIONS = {
    "tiktok": {"width": 1080, "height": 1920, "label": "TikTok (9:16)"},
    "instagram_feed": {"width": 1080, "height": 1080, "label": "Instagram Feed (1:1)"},
    "instagram_story": {"width": 1080, "height": 1920, "label": "Instagram Story (9:16)"},
    "facebook_feed": {"width": 1200, "height": 630, "label": "Facebook Feed"},
    "facebook_story": {"width": 1080, "height": 1920, "label": "Facebook Story (9:16)"},
}

# Template styles
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


class ImageGeneratorService:
    """Service for generating platform-specific social media images."""

    def __init__(self):
        """Initialize the image generator service."""
        self._output_dir = os.path.join(os.getcwd(), "generated_images")
        os.makedirs(self._output_dir, exist_ok=True)

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get a font at the specified size, falling back to default if needed."""
        # Try common system font paths
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

        # Fall back to default font
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

    def generate_image(
        self,
        platform: str,
        text: str,
        brand_colors: List[str] = None,
        style: str = "bold_text",
        business_name: Optional[str] = None,
        logo_path: Optional[str] = None,
        output_filename: Optional[str] = None,
    ) -> str:
        """
        Generate a social media image with text overlay.

        Args:
            platform: Platform key (tiktok, instagram_feed, instagram_story, etc.)
            text: Text to overlay on the image
            brand_colors: List of hex color codes for the brand
            style: Template style name
            business_name: Business name for branding
            logo_path: Path to logo file for overlay
            output_filename: Custom output filename

        Returns:
            Path to the generated image file
        """
        # Get dimensions
        dimensions = PLATFORM_DIMENSIONS.get(platform, PLATFORM_DIMENSIONS["instagram_feed"])
        width = dimensions["width"]
        height = dimensions["height"]

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
        if output_filename is None:
            output_filename = f"{platform}_{style}_{os.getpid()}.png"

        output_path = os.path.join(self._output_dir, output_filename)
        img.save(output_path, "PNG", quality=settings.image_quality)

        logger.info(f"Generated image: {output_path} ({width}x{height})")
        return output_path

    def generate_all_platform_variants(
        self,
        text: str,
        brand_colors: List[str] = None,
        style: str = "bold_text",
        business_name: Optional[str] = None,
        prefix: str = "post",
    ) -> Dict[str, str]:
        """
        Generate images for all platform dimensions.

        Args:
            text: Text to overlay
            brand_colors: Brand color palette
            style: Template style
            business_name: Business name for branding
            prefix: Filename prefix

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
                output_filename=filename,
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


# Singleton instance
image_generator_service = ImageGeneratorService()
