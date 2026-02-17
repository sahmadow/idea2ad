"""
Static Ad Renderer — Pillow-based image generation for all static ad types.

Takes an AdTypeDefinition + CreativeParameters and renders a composited image
by processing layers bottom-to-top. Supports multi-aspect-ratio export.

Layer types handled:
  background, text, product_image, scene_image, badge,
  review_card, comparison_layout, social_post_frame
"""

import asyncio
import io
import logging
import random
import re
from typing import Optional

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.schemas.ad_types import AdTypeDefinition, LayerDefinition
from app.schemas.creative_params import CreativeParameters
from app.services.image_compositor import (
    download_google_font,
    get_system_font_path,
    hex_to_rgba,
    parse_font_size,
)

logger = logging.getLogger(__name__)

# Canvas sizes per aspect ratio
ASPECT_RATIO_SIZES: dict[str, tuple[int, int]] = {
    "1:1": (1080, 1080),
    "9:16": (1080, 1920),
    "1.91:1": (1200, 628),
    "4:5": (1080, 1350),
}

# Font cache shared across renders
_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

# HTTP client for fetching images
_http_client: httpx.AsyncClient | None = None

# Image download cache (url -> bytes)
_image_cache: dict[str, bytes] = {}


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
    return _http_client


def _load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load font by name with caching. Falls back to Inter then default."""
    cache_key = (font_name.lower().strip(), size)
    if cache_key in _font_cache:
        return _font_cache[cache_key]

    # Clean font name (remove "Bold" suffix for lookup)
    base_name = font_name.replace(" Bold", "").replace(" bold", "").strip()

    for name in [base_name, "Inter", "Roboto"]:
        path = download_google_font(name) or get_system_font_path(name)
        if path:
            try:
                font = ImageFont.truetype(path, size)
                _font_cache[cache_key] = font
                return font
            except Exception:
                continue

    font = ImageFont.load_default()
    _font_cache[cache_key] = font
    return font


async def _fetch_image(url: str) -> bytes | None:
    """Fetch image from URL with caching."""
    if url in _image_cache:
        return _image_cache[url]
    try:
        client = _get_http_client()
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.content
        _image_cache[url] = data
        return data
    except Exception as e:
        logger.warning(f"Failed to fetch image {url}: {e}")
        return None


def _resolve_var(template: str, params: CreativeParameters) -> str:
    """Resolve {variable} placeholders from CreativeParameters."""
    def replacer(match: re.Match) -> str:
        path = match.group(1)
        # Array indexing: value_props[0]
        idx_match = re.match(r"(\w+)\[(\d+)\]", path)
        if idx_match:
            field = idx_match.group(1)
            idx = int(idx_match.group(2))
            val = getattr(params, field, [])
            if isinstance(val, list) and idx < len(val):
                return str(val[idx])
            return ""
        # Dotted path: brand_colors.primary
        parts = path.split(".")
        obj = params
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return ""
        return str(obj) if obj is not None else ""

    return re.sub(r"\{(\w+(?:\[\d+\])?(?:\.\w+)?)\}", replacer, template)


def _check_condition(condition: str | None, params: CreativeParameters) -> bool:
    """Check if a layer condition is met. Returns True if no condition."""
    if not condition:
        return True
    # Format: "field_exists" -> check that field is truthy
    if condition.endswith("_exists"):
        field = condition.replace("_exists", "")
        val = getattr(params, field, None)
        return bool(val)
    return True


def _darken_overlay(img: Image.Image, factor: float = 0.45) -> Image.Image:
    """Apply a semi-transparent dark overlay."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, int(255 * factor)))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def _add_shadow(img: Image.Image) -> Image.Image:
    """Add drop shadow beneath an RGBA image."""
    # Create shadow layer
    shadow = Image.new("RGBA", (img.width + 20, img.height + 20), (0, 0, 0, 0))
    # Paste a black silhouette offset
    silhouette = img.copy()
    silhouette_data = silhouette.load()
    for y in range(silhouette.height):
        for x in range(silhouette.width):
            r, g, b, a = silhouette_data[x, y]
            silhouette_data[x, y] = (0, 0, 0, min(a, 80))
    shadow.paste(silhouette, (10, 10))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))
    shadow.paste(img, (0, 0), img)
    return shadow


def _create_gradient(w: int, h: int, color1: str, color2: str) -> Image.Image:
    """Create a vertical gradient from color1 (top) to color2 (bottom)."""
    c1 = hex_to_rgba(color1)[:3]
    c2 = hex_to_rgba(color2)[:3]
    img = Image.new("RGB", (w, h))
    pixels = img.load()
    for y in range(h):
        ratio = y / max(h - 1, 1)
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        for x in range(w):
            pixels[x, y] = (r, g, b)
    return img


def _get_position_bbox(
    position: str,
    canvas_w: int,
    canvas_h: int,
    padding: int = 40,
) -> tuple[int, int, int, int]:
    """
    Map a named position to (x, y, max_w, max_h) bounding box.
    Used for text and images placement.
    """
    p = position.lower().replace("-", "_")
    half_w = canvas_w // 2
    third_h = canvas_h // 3

    pos_map = {
        "center": (padding, third_h, canvas_w - 2 * padding, third_h),
        "top_third": (padding, padding, canvas_w - 2 * padding, third_h - padding),
        "bottom_third": (padding, 2 * third_h, canvas_w - 2 * padding, third_h - padding),
        "bottom_center": (canvas_w // 4, canvas_h - third_h, half_w, third_h - padding),
        "center_bottom": (canvas_w // 4, canvas_h - third_h, half_w, third_h - padding),
        # Value prop positions (horizontal thirds)
        "middle_left": (padding, third_h + padding, canvas_w // 3 - padding, third_h - 2 * padding),
        "middle_center": (canvas_w // 3, third_h + padding, canvas_w // 3, third_h - 2 * padding),
        "middle_right": (2 * canvas_w // 3, third_h + padding, canvas_w // 3 - padding, third_h - 2 * padding),
        # Half-screen positions (for comparison layouts)
        "left_half": (0, 0, half_w, canvas_h),
        "right_half": (half_w, 0, half_w, canvas_h),
        "left_half_top": (padding, padding, half_w - 2 * padding, third_h),
        "left_half_center": (padding, third_h, half_w - 2 * padding, third_h),
        "left_half_middle": (padding, third_h, half_w - 2 * padding, third_h),
        "right_half_top": (half_w + padding, padding, half_w - 2 * padding, third_h),
        "right_half_center": (half_w + padding, third_h, half_w - 2 * padding, third_h),
        "right_half_middle": (half_w + padding, third_h, half_w - 2 * padding, third_h),
        "right_half_bottom": (half_w + padding, 2 * third_h, half_w - 2 * padding, third_h - padding),
        # Post body (for social post frames — centered with margin)
        "post_body": (padding + 20, third_h // 2 + 60, canvas_w - 2 * padding - 40, third_h * 2),
        "post_image": (padding, canvas_h // 2, canvas_w - 2 * padding, canvas_h // 2 - padding),
        # Full
        "full": (0, 0, canvas_w, canvas_h),
        # Badge corner
        "bottom_right": (canvas_w - 200, canvas_h - 100, 180, 60),
    }
    return pos_map.get(p, (padding, padding, canvas_w - 2 * padding, canvas_h - 2 * padding))


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current_line = ""

    for word in words:
        test = f"{current_line} {word}".strip()
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines or [text]


# =====================================================================
# Layer renderers
# =====================================================================


def _render_background(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    layer: LayerDefinition,
    params: CreativeParameters,
) -> None:
    """Render a solid color or gradient background."""
    color_str = _resolve_var(layer.source or "", params)
    fallback = layer.style.get("fallback", "#1A365D")

    if not color_str or not color_str.startswith("#"):
        color_str = fallback

    position = layer.position.lower().replace("-", "_")

    # Half-backgrounds for comparison layouts
    if "left_half" in position:
        x, y, w, h = _get_position_bbox(position, canvas.width, canvas.height)
        region = Image.new("RGBA", (w, h), hex_to_rgba(color_str))
        canvas.paste(region, (x, y))
        return
    if "right_half" in position:
        x, y, w, h = _get_position_bbox(position, canvas.width, canvas.height)
        region = Image.new("RGBA", (w, h), hex_to_rgba(color_str))
        canvas.paste(region, (x, y))
        return

    # Full background
    rgba = hex_to_rgba(color_str)
    canvas.paste(Image.new("RGBA", canvas.size, rgba), (0, 0))


def _render_text(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    layer: LayerDefinition,
    params: CreativeParameters,
) -> None:
    """Render a text layer with wrapping, color, and optional styling."""
    text = _resolve_var(layer.content or "", params)
    if not text:
        return

    style = layer.style
    font_name = _resolve_var(style.get("font", "Inter"), params)
    if font_name == "platform_native":
        font_name = "Inter"
    size_spec = style.get("size", layer.size or "medium")
    font_size = parse_font_size(size_spec)
    font = _load_font(font_name, font_size)

    color_str = _resolve_var(style.get("color", "#FFFFFF"), params)
    if not color_str.startswith("#"):
        color_str = "#FFFFFF"
    color = hex_to_rgba(color_str)

    x, y, max_w, max_h = _get_position_bbox(layer.position, canvas.width, canvas.height)
    lines = _wrap_text(text, font, max_w)

    # Optional uppercase
    if style.get("uppercase"):
        lines = [l.upper() for l in lines]

    # Draw each line
    line_spacing = int(font_size * 1.3)
    for i, line in enumerate(lines):
        line_y = y + i * line_spacing
        if line_y + font_size > canvas.height:
            break

        # Text shadow for readability over images
        if style.get("text_shadow"):
            draw.text((x + 2, line_y + 2), line, font=font, fill=(0, 0, 0, 160))

        # Strikethrough: draw text then line through middle
        draw.text((x, line_y), line, font=font, fill=color)

        if style.get("strikethrough"):
            bbox = font.getbbox(line)
            line_mid_y = line_y + font_size // 2
            draw.line(
                [(x, line_mid_y), (x + bbox[2] - bbox[0], line_mid_y)],
                fill=color,
                width=2,
            )


async def _render_product_image(
    canvas: Image.Image,
    layer: LayerDefinition,
    params: CreativeParameters,
) -> None:
    """Fetch product image, optionally remove bg + add shadow, paste onto canvas."""
    url = _resolve_var(layer.source or "", params)
    if not url or not url.startswith("http"):
        return

    img_bytes = await _fetch_image(url)
    if not img_bytes:
        return

    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    # Processing pipeline
    for proc in layer.processing:
        if proc == "remove_background":
            try:
                from app.services.background_remover import get_background_remover
                remover = get_background_remover()
                img_bytes_processed = await remover.remove_background(
                    _pil_to_bytes(img)
                )
                img = Image.open(io.BytesIO(img_bytes_processed)).convert("RGBA")
            except Exception as e:
                logger.warning(f"Background removal failed, using original: {e}")
        elif proc == "add_shadow":
            img = _add_shadow(img)

    # Fit into position bounding box
    x, y, max_w, max_h = _get_position_bbox(layer.position, canvas.width, canvas.height)
    img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

    # Center within bounding box
    paste_x = x + (max_w - img.width) // 2
    paste_y = y + (max_h - img.height) // 2
    canvas.paste(img, (paste_x, paste_y), img)


async def _render_scene_image(
    canvas: Image.Image,
    layer: LayerDefinition,
    params: CreativeParameters,
) -> None:
    """Render a scene image (full bleed or positioned) with optional darkening."""
    url = _resolve_var(layer.source or "", params)
    if not url or not url.startswith("http"):
        return

    img_bytes = await _fetch_image(url)
    if not img_bytes:
        return

    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    # Resize to fill canvas
    x, y, max_w, max_h = _get_position_bbox(layer.position, canvas.width, canvas.height)
    img = img.resize((max_w, max_h), Image.Resampling.LANCZOS)

    # Apply processing
    for proc in layer.processing:
        if proc == "slight_darken_overlay":
            img = _darken_overlay(img, 0.45)

    canvas.paste(img, (x, y), img)


def _render_badge(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    layer: LayerDefinition,
    params: CreativeParameters,
) -> None:
    """Render a pill-shaped badge (e.g., price tag)."""
    text = _resolve_var(layer.content or "", params)
    if not text:
        return

    style = layer.style
    bg_color_str = _resolve_var(style.get("background", "#FF6B35"), params)
    if not bg_color_str.startswith("#"):
        bg_color_str = "#FF6B35"
    bg_color = hex_to_rgba(bg_color_str)

    font = _load_font("Inter", 28)
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x, y, _, _ = _get_position_bbox(layer.position, canvas.width, canvas.height)
    pad_x, pad_y = 16, 8
    pill_rect = [x, y, x + text_w + 2 * pad_x, y + text_h + 2 * pad_y]

    try:
        draw.rounded_rectangle(pill_rect, radius=12, fill=bg_color)
    except AttributeError:
        draw.rectangle(pill_rect, fill=bg_color)

    draw.text((x + pad_x, y + pad_y), text, font=font, fill=(255, 255, 255, 255))


def _render_review_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    layer: LayerDefinition,
    params: CreativeParameters,
) -> None:
    """Render a review/testimonial card with rating stars."""
    style = layer.style
    variants = (layer.style_variant or "review_card").split("|")
    variant = random.choice(variants)

    # Card dimensions
    card_w = int(canvas.width * 0.85)
    card_h = int(canvas.height * 0.45)
    card_x = (canvas.width - card_w) // 2
    card_y = int(canvas.height * 0.08)

    # Card background based on variant
    card_bg = {
        "ios_message": (230, 230, 235, 255),  # light gray bubble
        "tweet_card": (255, 255, 255, 255),  # white card
        "review_card": (255, 255, 255, 255),  # white card
    }
    bg = card_bg.get(variant, (255, 255, 255, 255))

    try:
        draw.rounded_rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            radius=20,
            fill=bg,
        )
    except AttributeError:
        draw.rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            fill=bg,
        )

    # Author name
    author_names = ["Sarah K.", "Mike R.", "Jessica L.", "David M.", "Emma T."]
    author = random.choice(author_names)
    author_font = _load_font("Inter", 22)
    draw.text(
        (card_x + 24, card_y + 20),
        author,
        font=author_font,
        fill=(60, 60, 60, 255),
    )

    # Rating stars
    rating = style.get("rating", 5)
    stars = "\u2605" * rating + "\u2606" * (5 - rating)
    star_font = _load_font("Inter", 24)
    draw.text(
        (card_x + 24, card_y + 50),
        stars,
        font=star_font,
        fill=(255, 180, 0, 255),
    )

    # Testimonial text
    testimonial = ""
    if params.testimonials:
        testimonial = params.testimonials[0]
    elif params.social_proof:
        testimonial = f"Absolutely love this product. {params.social_proof}."
    else:
        testimonial = f"The {params.product_name} has completely changed my routine. Highly recommend!"

    body_font = _load_font("Inter", 26)
    lines = _wrap_text(testimonial, body_font, card_w - 48)
    for i, line in enumerate(lines[:5]):
        draw.text(
            (card_x + 24, card_y + 90 + i * 34),
            line,
            font=body_font,
            fill=(30, 30, 30, 255),
        )

    # Verified badge
    if style.get("verified", False):
        verified_font = _load_font("Inter", 18)
        draw.text(
            (card_x + 24, card_y + card_h - 36),
            "Verified Purchase",
            font=verified_font,
            fill=(100, 160, 100, 255),
        )


def _render_comparison_layout(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    layer: LayerDefinition,
    params: CreativeParameters,
) -> None:
    """Render the split comparison layout divider line."""
    layout = layer.style.get("layout", "split_vertical")

    if layout == "split_vertical":
        mid_x = canvas.width // 2
        # Draw a subtle divider line
        draw.line(
            [(mid_x, 0), (mid_x, canvas.height)],
            fill=(200, 200, 200, 255),
            width=2,
        )


def _render_social_post_frame(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    layer: LayerDefinition,
    params: CreativeParameters,
) -> None:
    """Render a social media post frame (platform chrome)."""
    variants = (layer.style_variant or "tweet").split("|")
    variant = random.choice(variants)

    # White card background
    margin = 30
    card_rect = [margin, margin, canvas.width - margin, canvas.height - margin]
    try:
        draw.rounded_rectangle(card_rect, radius=16, fill=(255, 255, 255, 255))
    except AttributeError:
        draw.rectangle(card_rect, fill=(255, 255, 255, 255))

    # Platform-specific chrome
    header_font = _load_font("Inter", 20)
    body_y_start = 80

    if variant == "reddit_post":
        # Reddit: gray bg, upvote arrows, subreddit name
        canvas.paste(Image.new("RGBA", canvas.size, (218, 224, 230, 255)), (0, 0))
        try:
            draw.rounded_rectangle(card_rect, radius=8, fill=(255, 255, 255, 255))
        except AttributeError:
            draw.rectangle(card_rect, fill=(255, 255, 255, 255))

        # Subreddit header
        sub_name = f"r/{params.product_category.lower().replace('/', '_').replace(' ', '')}"
        draw.text((margin + 16, margin + 12), sub_name, font=header_font, fill=(90, 90, 90, 255))
        # Username
        draw.text(
            (margin + 16, margin + 38),
            "u/real_user_2025 - 2h",
            font=_load_font("Inter", 16),
            fill=(140, 140, 140, 255),
        )
        # Upvote count
        vote_font = _load_font("Inter", 18)
        draw.text((margin + 16, canvas.height - 80), "847", font=vote_font, fill=(100, 100, 100, 255))

    elif variant == "tweet":
        # Tweet: profile pic circle, name, handle
        # Profile pic placeholder (circle)
        circle_x, circle_y = margin + 20, margin + 16
        draw.ellipse(
            [circle_x, circle_y, circle_x + 40, circle_y + 40],
            fill=(180, 200, 230, 255),
        )
        draw.text(
            (circle_x + 52, circle_y + 4),
            "Real Person",
            font=_load_font("Inter", 20),
            fill=(20, 20, 20, 255),
        )
        draw.text(
            (circle_x + 52, circle_y + 26),
            "@real_person",
            font=_load_font("Inter", 16),
            fill=(130, 130, 130, 255),
        )
        # Engagement stats
        stats_font = _load_font("Inter", 16)
        draw.text(
            (margin + 20, canvas.height - 70),
            "1.2K   328   42",
            font=stats_font,
            fill=(120, 120, 120, 255),
        )

    elif variant == "tiktok_comment":
        # TikTok comment style: dark bg
        canvas.paste(Image.new("RGBA", canvas.size, (22, 24, 35, 255)), (0, 0))
        # Profile and username
        draw.ellipse(
            [margin + 10, margin + 10, margin + 46, margin + 46],
            fill=(255, 90, 95, 255),
        )
        draw.text(
            (margin + 56, margin + 16),
            "user_name",
            font=_load_font("Inter", 18),
            fill=(230, 230, 230, 255),
        )

    elif variant == "instagram_story":
        # Instagram story: gradient top bar, story progress
        # Subtle gradient background
        bg = _create_gradient(canvas.width, canvas.height, "#833AB4", "#FD1D1D")
        canvas.paste(bg.convert("RGBA"), (0, 0))
        # Story content area (white card)
        inner_margin = 20
        inner_rect = [
            inner_margin, 80,
            canvas.width - inner_margin,
            canvas.height - inner_margin,
        ]
        try:
            draw.rounded_rectangle(inner_rect, radius=12, fill=(255, 255, 255, 250))
        except AttributeError:
            draw.rectangle(inner_rect, fill=(255, 255, 255, 250))

        # Story progress bar
        bar_y = 50
        draw.rounded_rectangle(
            [20, bar_y, canvas.width - 20, bar_y + 3],
            radius=2,
            fill=(255, 255, 255, 180),
        )


def _pil_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    """Convert PIL Image to bytes."""
    buf = io.BytesIO()
    if fmt == "PNG":
        img.convert("RGBA" if img.mode == "RGBA" else "RGB").save(buf, format=fmt, optimize=True)
    else:
        img.convert("RGB").save(buf, format=fmt, quality=95)
    buf.seek(0)
    return buf.getvalue()


# =====================================================================
# Main renderer
# =====================================================================


class StaticAdRenderer:
    """
    Renders a static ad image from an AdTypeDefinition + CreativeParameters.

    Processes layers bottom-to-top onto a Pillow canvas, then exports as PNG.
    """

    async def render_ad(
        self,
        ad_type: AdTypeDefinition,
        params: CreativeParameters,
        aspect_ratio: str = "1:1",
        hook_text: str | None = None,
    ) -> bytes:
        """
        Render a single static ad image.

        Args:
            ad_type: Ad type definition with layer stack
            params: Creative parameters with all data
            aspect_ratio: Target aspect ratio (1:1, 9:16, 1.91:1)
            hook_text: Optional pre-resolved hook text for organic/problem types

        Returns:
            PNG bytes of the rendered ad
        """
        w, h = ASPECT_RATIO_SIZES.get(aspect_ratio, (1080, 1080))
        canvas = Image.new("RGBA", (w, h), (26, 54, 93, 255))  # default dark blue
        draw = ImageDraw.Draw(canvas)

        # Inject hook text as a pseudo-param if provided
        if hook_text:
            # Temporarily set a field so {problem_hook} / {organic_hook} resolve
            object.__setattr__(params, "_hook_override", hook_text)
            # Patch resolve to handle hook vars
            original_scene = params.scene_problem
        try:
            for layer in ad_type.layers:
                # Check condition
                if not _check_condition(layer.condition, params):
                    continue

                await self._render_layer(canvas, draw, layer, params, hook_text)

        except Exception as e:
            logger.error(f"Render failed for {ad_type.id} @ {aspect_ratio}: {e}")
            # Return the canvas as-is (partial render)
        finally:
            # Clean up temp attribute
            if hasattr(params, "_hook_override"):
                try:
                    delattr(params, "_hook_override")
                except Exception:
                    pass

        return _pil_to_bytes(canvas)

    async def _render_layer(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        layer: LayerDefinition,
        params: CreativeParameters,
        hook_text: str | None = None,
    ) -> None:
        """Dispatch to the appropriate layer renderer."""
        lt = layer.type.lower()

        # For hook-based text layers, substitute hook text
        if hook_text and layer.content:
            content = layer.content
            if "{problem_hook}" in content or "{organic_hook}" in content:
                layer = layer.model_copy(
                    update={"content": content.replace("{problem_hook}", hook_text).replace("{organic_hook}", hook_text)}
                )

        if lt == "background":
            _render_background(canvas, draw, layer, params)
        elif lt == "text":
            _render_text(canvas, draw, layer, params)
        elif lt == "product_image":
            await _render_product_image(canvas, layer, params)
        elif lt == "scene_image":
            await _render_scene_image(canvas, layer, params)
        elif lt == "badge":
            _render_badge(canvas, draw, layer, params)
        elif lt == "review_card":
            _render_review_card(canvas, draw, layer, params)
        elif lt == "comparison_layout":
            _render_comparison_layout(canvas, draw, layer, params)
        elif lt == "social_post_frame":
            _render_social_post_frame(canvas, draw, layer, params)
        else:
            logger.warning(f"Unknown layer type: {lt}")

    async def render_all_ratios(
        self,
        ad_type: AdTypeDefinition,
        params: CreativeParameters,
        hook_text: str | None = None,
    ) -> dict[str, bytes]:
        """
        Render ad in all configured aspect ratios.

        Returns dict mapping ratio string to PNG bytes.
        """
        results = {}
        for ratio in ad_type.aspect_ratios:
            if ratio in ASPECT_RATIO_SIZES:
                img_bytes = await self.render_ad(ad_type, params, ratio, hook_text)
                results[ratio] = img_bytes
        return results


# Singleton
_renderer: Optional[StaticAdRenderer] = None


def get_static_renderer() -> StaticAdRenderer:
    """Get singleton StaticAdRenderer instance."""
    global _renderer
    if _renderer is None:
        _renderer = StaticAdRenderer()
    return _renderer
