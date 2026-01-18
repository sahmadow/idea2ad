"""
Image Compositor for applying text overlays with exact fonts and colors.
Uses Pillow for post-processing Imagen-generated images.
"""

import io
import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.request import urlretrieve

from PIL import Image, ImageDraw, ImageFont

from app.models import TextOverlay

logger = logging.getLogger(__name__)

# Google Fonts URL template
GOOGLE_FONTS_URL = "https://github.com/google/fonts/raw/main/ofl/{font_name}/{font_file}"

# Common Google Fonts with their file names
GOOGLE_FONTS_MAP = {
    "inter": "Inter-Bold.ttf",
    "roboto": "Roboto-Bold.ttf",
    "open sans": "OpenSans-Bold.ttf",
    "lato": "Lato-Bold.ttf",
    "montserrat": "Montserrat-Bold.ttf",
    "poppins": "Poppins-Bold.ttf",
    "raleway": "Raleway-Bold.ttf",
    "nunito": "Nunito-Bold.ttf",
    "playfair display": "PlayfairDisplay-Bold.ttf",
    "source sans pro": "SourceSansPro-Bold.ttf",
    "dm sans": "DMSans-Bold.ttf",
    "space grotesk": "SpaceGrotesk-Bold.ttf",
    "outfit": "Outfit-Bold.ttf",
    "plus jakarta sans": "PlusJakartaSans-Bold.ttf",
}

# Font cache directory
FONT_CACHE_DIR = Path(tempfile.gettempdir()) / "launchad_fonts"


def ensure_font_cache_dir():
    """Create font cache directory if it doesn't exist."""
    FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def download_google_font(font_name: str) -> Optional[str]:
    """
    Download a Google Font and cache it locally.

    Args:
        font_name: Font family name (e.g., "Inter", "Roboto")

    Returns:
        Path to downloaded font file, or None if download failed
    """
    font_key = font_name.lower().strip()
    if font_key not in GOOGLE_FONTS_MAP:
        return None

    ensure_font_cache_dir()
    font_file = GOOGLE_FONTS_MAP[font_key]
    cache_path = FONT_CACHE_DIR / font_file

    # Return cached font if exists
    if cache_path.exists():
        return str(cache_path)

    # Download font
    try:
        # Try direct GitHub URL
        font_folder = font_key.replace(" ", "").lower()
        url = f"https://github.com/google/fonts/raw/main/ofl/{font_folder}/{font_file}"
        urlretrieve(url, cache_path)
        logger.info(f"Downloaded font: {font_name} to {cache_path}")
        return str(cache_path)
    except Exception as e:
        logger.debug(f"Failed to download font {font_name}: {e}")
        return None


def get_system_font_path(font_name: str) -> Optional[str]:
    """
    Find a system font by name.

    Args:
        font_name: Font family name

    Returns:
        Path to font file, or None if not found
    """
    # Common system font directories
    font_dirs = []

    # macOS
    font_dirs.extend([
        Path.home() / "Library/Fonts",
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
    ])

    # Linux
    font_dirs.extend([
        Path.home() / ".fonts",
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
    ])

    # Windows
    font_dirs.append(Path("C:/Windows/Fonts"))

    font_key = font_name.lower().replace(" ", "")

    for font_dir in font_dirs:
        if not font_dir.exists():
            continue

        for font_file in font_dir.rglob("*.ttf"):
            if font_key in font_file.stem.lower():
                return str(font_file)

        for font_file in font_dir.rglob("*.otf"):
            if font_key in font_file.stem.lower():
                return str(font_file)

    return None


def hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    """Convert hex color to RGBA tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)


def parse_font_size(size_spec: str, base_size: int = 48) -> int:
    """
    Parse font size from specification.

    Args:
        size_spec: Size like "large", "medium", "small", or "48px"
        base_size: Base size for relative calculations

    Returns:
        Font size in pixels
    """
    size_spec = size_spec.lower().strip()

    # Named sizes
    size_map = {
        "small": 24,
        "medium": 36,
        "large": 48,
        "xlarge": 60,
        "xxlarge": 72,
    }

    if size_spec in size_map:
        return size_map[size_spec]

    # Pixel value (e.g., "48px", "48")
    try:
        return int(size_spec.replace("px", "").strip())
    except ValueError:
        return base_size


class ImageCompositor:
    """Composite text overlays onto generated images with exact fonts and colors."""

    def __init__(self, default_font_size: int = 48):
        self.default_font_size = default_font_size
        self._font_cache: dict = {}

    def _load_font(
        self,
        font_families: List[str],
        size: int
    ) -> ImageFont.FreeTypeFont:
        """
        Load font by family name, with fallbacks.

        Args:
            font_families: Preferred font families (in order)
            size: Font size in pixels

        Returns:
            Loaded PIL font
        """
        cache_key = (tuple(font_families), size)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        # Try each font family in order
        for family in font_families:
            family = family.strip().strip("'\"")

            # Try Google Fonts download
            font_path = download_google_font(family)
            if font_path:
                try:
                    font = ImageFont.truetype(font_path, size)
                    self._font_cache[cache_key] = font
                    return font
                except Exception:
                    pass

            # Try system font
            font_path = get_system_font_path(family)
            if font_path:
                try:
                    font = ImageFont.truetype(font_path, size)
                    self._font_cache[cache_key] = font
                    return font
                except Exception:
                    pass

        # Fallback to default sans-serif
        fallback_fonts = ["Inter", "Roboto", "Arial", "Helvetica"]
        for fallback in fallback_fonts:
            font_path = download_google_font(fallback)
            if font_path:
                try:
                    font = ImageFont.truetype(font_path, size)
                    self._font_cache[cache_key] = font
                    return font
                except Exception:
                    pass

            font_path = get_system_font_path(fallback)
            if font_path:
                try:
                    font = ImageFont.truetype(font_path, size)
                    self._font_cache[cache_key] = font
                    return font
                except Exception:
                    pass

        # Last resort: Pillow default
        logger.warning("Using default Pillow font - no TTF fonts found")
        return ImageFont.load_default()

    def _calculate_position(
        self,
        img_size: Tuple[int, int],
        position: str,
        text: str,
        font: ImageFont.FreeTypeFont
    ) -> Tuple[int, int]:
        """
        Calculate x,y coordinates for text position.

        Args:
            img_size: (width, height) of image
            position: Position name like "top-left", "center", "bottom-right"
            text: Text content to position
            font: Font being used

        Returns:
            (x, y) coordinates for text
        """
        width, height = img_size

        # Get text bounding box
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Padding from edges
        padding_x = int(width * 0.05)  # 5% padding
        padding_y = int(height * 0.05)

        # Normalize position string
        pos = position.lower().replace(" ", "-").replace("_", "-")

        # Calculate positions
        positions = {
            "top-left": (padding_x, padding_y),
            "top-center": ((width - text_width) // 2, padding_y),
            "top-right": (width - text_width - padding_x, padding_y),
            "center-left": (padding_x, (height - text_height) // 2),
            "center": ((width - text_width) // 2, (height - text_height) // 2),
            "center-right": (width - text_width - padding_x, (height - text_height) // 2),
            "bottom-left": (padding_x, height - text_height - padding_y * 2),
            "bottom-center": ((width - text_width) // 2, height - text_height - padding_y * 2),
            "bottom-right": (width - text_width - padding_x, height - text_height - padding_y * 2),
        }

        return positions.get(pos, positions["center"])

    def _draw_text_background(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        background_spec: str
    ):
        """
        Draw background behind text (pill shape or solid).

        Args:
            draw: PIL ImageDraw object
            x, y: Text position
            text: Text content
            font: Font being used
            background_spec: Background specification (e.g., "semi-transparent black", "solid #ff0000")
        """
        # Get text dimensions
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Padding for background
        pad_x = 20
        pad_y = 10

        # Parse background spec
        bg_spec = background_spec.lower()

        if "semi-transparent" in bg_spec:
            if "black" in bg_spec:
                bg_color = (0, 0, 0, 180)
            elif "white" in bg_spec:
                bg_color = (255, 255, 255, 180)
            else:
                bg_color = (0, 0, 0, 180)
        elif "solid" in bg_spec:
            # Extract hex color if present
            import re
            hex_match = re.search(r"#[a-fA-F0-9]{6}", bg_spec)
            if hex_match:
                bg_color = hex_to_rgba(hex_match.group(), 255)
            else:
                bg_color = (0, 0, 0, 255)
        elif bg_spec.startswith("#"):
            bg_color = hex_to_rgba(bg_spec, 230)
        else:
            # Default semi-transparent black
            bg_color = (0, 0, 0, 150)

        # Draw rounded rectangle (pill shape)
        rect_coords = [
            x - pad_x,
            y - pad_y,
            x + text_width + pad_x,
            y + text_height + pad_y
        ]

        # Draw with rounded corners if Pillow version supports it
        try:
            draw.rounded_rectangle(rect_coords, radius=15, fill=bg_color)
        except AttributeError:
            # Fallback for older Pillow versions
            draw.rectangle(rect_coords, fill=bg_color)

    async def composite_text_overlays(
        self,
        base_image: bytes,
        text_overlays: List[TextOverlay],
        font_families: List[str]
    ) -> bytes:
        """
        Add text overlays to base image with exact fonts and colors.

        Args:
            base_image: PNG bytes from Imagen
            text_overlays: List of TextOverlay specifications
            font_families: Preferred font families from styling guide

        Returns:
            PNG bytes with text composited
        """
        # Open base image
        img = Image.open(io.BytesIO(base_image)).convert("RGBA")

        # Create transparent overlay layer
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        # Apply each text overlay
        for overlay in text_overlays:
            try:
                # Parse font size
                font_size = parse_font_size(overlay.font_size, self.default_font_size)

                # Load font
                font = self._load_font(font_families, font_size)

                # Calculate position
                x, y = self._calculate_position(img.size, overlay.position, overlay.content, font)

                # Draw background if specified
                if overlay.background:
                    self._draw_text_background(draw, x, y, overlay.content, font, overlay.background)

                # Draw text
                text_color = hex_to_rgba(overlay.color)
                draw.text((x, y), overlay.content, font=font, fill=text_color)

                logger.debug(f"Added text overlay: '{overlay.content[:20]}...' at {overlay.position}")

            except Exception as e:
                logger.warning(f"Failed to apply text overlay: {e}")
                continue

        # Composite text layer onto base image
        result = Image.alpha_composite(img, txt_layer)

        # Convert to RGB for PNG output (removes alpha channel)
        result = result.convert("RGB")

        # Save to bytes
        output = io.BytesIO()
        result.save(output, format="PNG", optimize=True)
        output.seek(0)

        return output.getvalue()

    def composite_logo(
        self,
        base_image: bytes,
        logo_bytes: bytes,
        position: str = "top-left",
        max_size: int = 100
    ) -> bytes:
        """
        Composite logo onto image.

        Args:
            base_image: PNG bytes
            logo_bytes: Logo image bytes
            position: Position for logo
            max_size: Maximum logo dimension

        Returns:
            PNG bytes with logo composited
        """
        img = Image.open(io.BytesIO(base_image)).convert("RGBA")
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

        # Resize logo maintaining aspect ratio
        logo.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Calculate position
        padding = 20
        pos_map = {
            "top-left": (padding, padding),
            "top-right": (img.width - logo.width - padding, padding),
            "bottom-left": (padding, img.height - logo.height - padding),
            "bottom-right": (img.width - logo.width - padding, img.height - logo.height - padding),
        }

        pos = pos_map.get(position.lower().replace(" ", "-"), pos_map["top-left"])

        # Paste logo
        img.paste(logo, pos, logo)

        # Convert and save
        result = img.convert("RGB")
        output = io.BytesIO()
        result.save(output, format="PNG", optimize=True)
        output.seek(0)

        return output.getvalue()


# Singleton instance
_compositor: Optional[ImageCompositor] = None


def get_image_compositor() -> ImageCompositor:
    """Get singleton ImageCompositor instance."""
    global _compositor
    if _compositor is None:
        _compositor = ImageCompositor()
    return _compositor
