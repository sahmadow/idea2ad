"""
Static Ad Renderer — dual-mode rendering: Fabric.js templates (via Node.js renderer)
with Pillow fallback for ad types without templates.

Primary path: Load Fabric.js JSON template from DB → populate {{variables}} → send to
renderer microservice → return image bytes.

Fallback path: Original Pillow layer-based rendering (legacy).

Same StaticAdRenderer interface so v2.py router doesn't change.
"""

import asyncio
import base64
import io
import json
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


# =====================================================================
# Template-based rendering (primary path)
# =====================================================================


def _resolve_template_variables(
    canvas_json: dict,
    params: CreativeParameters,
    hook_text: str | None = None,
) -> dict:
    """
    Deep-walk a Fabric.js JSON dict, replacing {{variable}} placeholders
    in text fields with values from CreativeParameters.
    """
    json_str = json.dumps(canvas_json)

    def replacer(match: re.Match) -> str:
        path = match.group(1)

        # Hook overrides
        if hook_text and path in ("problem_hook", "organic_hook"):
            return hook_text

        # Array indexing: value_props[0]
        idx_match = re.match(r"(\w+)\[(\d+)\]", path)
        if idx_match:
            field = idx_match.group(1)
            idx = int(idx_match.group(2))
            val = getattr(params, field, [])
            if isinstance(val, list) and idx < len(val):
                # JSON-safe escape
                return str(val[idx]).replace('"', '\\"')
            return ""

        # Dotted path: brand_colors.primary
        parts = path.split(".")
        obj = params
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return ""
        result = str(obj) if obj is not None else ""
        return result.replace('"', '\\"')

    resolved = re.sub(r"\{\{(\w+(?:\[\d+\])?(?:\.\w+)?)\}\}", replacer, json_str)
    return json.loads(resolved)


async def _render_via_service(
    canvas_json: dict,
    width: int,
    height: int,
) -> bytes | None:
    """
    Render Fabric.js JSON via the Node.js renderer microservice.
    Returns PNG bytes or None if renderer is unavailable.
    """
    try:
        from app.services.v2.renderer_client import render_canvas
        return await render_canvas(canvas_json, width, height)
    except Exception as e:
        logger.warning(f"Renderer service unavailable, falling back to Pillow: {e}")
        return None


async def _load_template_from_db(
    ad_type_id: str,
    aspect_ratio: str,
) -> dict | None:
    """Load Fabric.js template JSON from AdTemplate table."""
    try:
        from prisma import Prisma
        db = Prisma()
        await db.connect()
        try:
            template = await db.adtemplate.find_first(
                where={
                    "ad_type_id": ad_type_id,
                    "aspect_ratio": aspect_ratio,
                },
                order={"is_default": "desc"},  # prefer default templates
            )
            if template:
                return template.canvas_json
        finally:
            await db.disconnect()
    except Exception as e:
        logger.debug(f"Template DB lookup failed for {ad_type_id}@{aspect_ratio}: {e}")
    return None


# =====================================================================
# Pillow fallback rendering (legacy)
# =====================================================================

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
        idx_match = re.match(r"(\w+)\[(\d+)\]", path)
        if idx_match:
            field = idx_match.group(1)
            idx = int(idx_match.group(2))
            val = getattr(params, field, [])
            if isinstance(val, list) and idx < len(val):
                return str(val[idx])
            return ""
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
    if not condition:
        return True
    if condition.endswith("_exists"):
        field = condition.replace("_exists", "")
        val = getattr(params, field, None)
        return bool(val)
    return True


def _darken_overlay(img: Image.Image, factor: float = 0.45) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, int(255 * factor)))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def _get_position_bbox(
    position: str, canvas_w: int, canvas_h: int, padding: int = 40,
) -> tuple[int, int, int, int]:
    p = position.lower().replace("-", "_")
    half_w = canvas_w // 2
    third_h = canvas_h // 3
    pos_map = {
        "center": (padding, third_h, canvas_w - 2 * padding, third_h),
        "top_third": (padding, padding, canvas_w - 2 * padding, third_h - padding),
        "bottom_third": (padding, 2 * third_h, canvas_w - 2 * padding, third_h - padding),
        "bottom_center": (canvas_w // 4, canvas_h - third_h, half_w, third_h - padding),
        "center_bottom": (canvas_w // 4, canvas_h - third_h, half_w, third_h - padding),
        "middle_left": (padding, third_h + padding, canvas_w // 3 - padding, third_h - 2 * padding),
        "middle_center": (canvas_w // 3, third_h + padding, canvas_w // 3, third_h - 2 * padding),
        "middle_right": (2 * canvas_w // 3, third_h + padding, canvas_w // 3 - padding, third_h - 2 * padding),
        "left_half": (0, 0, half_w, canvas_h),
        "right_half": (half_w, 0, half_w, canvas_h),
        "left_half_top": (padding, padding, half_w - 2 * padding, third_h),
        "left_half_center": (padding, third_h, half_w - 2 * padding, third_h),
        "left_half_middle": (padding, third_h, half_w - 2 * padding, third_h),
        "right_half_top": (half_w + padding, padding, half_w - 2 * padding, third_h),
        "right_half_center": (half_w + padding, third_h, half_w - 2 * padding, third_h),
        "right_half_middle": (half_w + padding, third_h, half_w - 2 * padding, third_h),
        "right_half_bottom": (half_w + padding, 2 * third_h, half_w - 2 * padding, third_h - padding),
        "post_body": (padding + 20, third_h // 2 + 60, canvas_w - 2 * padding - 40, third_h * 2),
        "post_image": (padding, canvas_h // 2, canvas_w - 2 * padding, canvas_h // 2 - padding),
        "full": (0, 0, canvas_w, canvas_h),
        "bottom_right": (canvas_w - 200, canvas_h - 100, 180, 60),
    }
    return pos_map.get(p, (padding, padding, canvas_w - 2 * padding, canvas_h - 2 * padding))


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
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


def _render_background(canvas: Image.Image, draw: ImageDraw.ImageDraw, layer: LayerDefinition, params: CreativeParameters) -> None:
    color_str = _resolve_var(layer.source or "", params)
    fallback = layer.style.get("fallback", "#1A365D")
    if not color_str or not color_str.startswith("#"):
        color_str = fallback
    position = layer.position.lower().replace("-", "_")
    if "left_half" in position or "right_half" in position:
        x, y, w, h = _get_position_bbox(position, canvas.width, canvas.height)
        region = Image.new("RGBA", (w, h), hex_to_rgba(color_str))
        canvas.paste(region, (x, y))
        return
    rgba = hex_to_rgba(color_str)
    canvas.paste(Image.new("RGBA", canvas.size, rgba), (0, 0))


def _render_text(canvas: Image.Image, draw: ImageDraw.ImageDraw, layer: LayerDefinition, params: CreativeParameters) -> None:
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
    if style.get("uppercase"):
        lines = [l.upper() for l in lines]
    line_spacing = int(font_size * 1.3)
    for i, line in enumerate(lines):
        line_y = y + i * line_spacing
        if line_y + font_size > canvas.height:
            break
        if style.get("text_shadow"):
            draw.text((x + 2, line_y + 2), line, font=font, fill=(0, 0, 0, 160))
        draw.text((x, line_y), line, font=font, fill=color)
        if style.get("strikethrough"):
            bbox = font.getbbox(line)
            line_mid_y = line_y + font_size // 2
            draw.line([(x, line_mid_y), (x + bbox[2] - bbox[0], line_mid_y)], fill=color, width=2)


async def _render_product_image(canvas: Image.Image, layer: LayerDefinition, params: CreativeParameters) -> None:
    url = _resolve_var(layer.source or "", params)
    if not url or not url.startswith("http"):
        return
    img_bytes = await _fetch_image(url)
    if not img_bytes:
        return
    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    for proc in layer.processing:
        if proc == "remove_background":
            try:
                from app.services.background_remover import get_background_remover
                remover = get_background_remover()
                img_bytes_processed = await remover.remove_background(_pil_to_bytes(img))
                img = Image.open(io.BytesIO(img_bytes_processed)).convert("RGBA")
            except Exception as e:
                logger.warning(f"Background removal failed: {e}")
        elif proc == "add_shadow":
            shadow = Image.new("RGBA", (img.width + 20, img.height + 20), (0, 0, 0, 0))
            silhouette = img.copy()
            sd = silhouette.load()
            for y2 in range(silhouette.height):
                for x2 in range(silhouette.width):
                    r, g, b, a = sd[x2, y2]
                    sd[x2, y2] = (0, 0, 0, min(a, 80))
            shadow.paste(silhouette, (10, 10))
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))
            shadow.paste(img, (0, 0), img)
            img = shadow
    x, y, max_w, max_h = _get_position_bbox(layer.position, canvas.width, canvas.height)
    img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    paste_x = x + (max_w - img.width) // 2
    paste_y = y + (max_h - img.height) // 2
    canvas.paste(img, (paste_x, paste_y), img)


async def _render_scene_image(canvas: Image.Image, layer: LayerDefinition, params: CreativeParameters) -> None:
    url = _resolve_var(layer.source or "", params)
    if not url or not url.startswith("http"):
        return
    img_bytes = await _fetch_image(url)
    if not img_bytes:
        return
    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    x, y, max_w, max_h = _get_position_bbox(layer.position, canvas.width, canvas.height)
    img = img.resize((max_w, max_h), Image.Resampling.LANCZOS)
    for proc in layer.processing:
        if proc == "slight_darken_overlay":
            img = _darken_overlay(img, 0.45)
    canvas.paste(img, (x, y), img)


def _render_badge(canvas: Image.Image, draw: ImageDraw.ImageDraw, layer: LayerDefinition, params: CreativeParameters) -> None:
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


def _render_review_card(canvas: Image.Image, draw: ImageDraw.ImageDraw, layer: LayerDefinition, params: CreativeParameters) -> None:
    style = layer.style
    variants = (layer.style_variant or "review_card").split("|")
    variant = random.choice(variants)
    card_w = int(canvas.width * 0.85)
    card_h = int(canvas.height * 0.45)
    card_x = (canvas.width - card_w) // 2
    card_y = int(canvas.height * 0.08)
    card_bg = {"ios_message": (230, 230, 235, 255), "tweet_card": (255, 255, 255, 255), "review_card": (255, 255, 255, 255)}
    bg = card_bg.get(variant, (255, 255, 255, 255))
    try:
        draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=20, fill=bg)
    except AttributeError:
        draw.rectangle([card_x, card_y, card_x + card_w, card_y + card_h], fill=bg)
    author_names = ["Sarah K.", "Mike R.", "Jessica L.", "David M.", "Emma T."]
    author = random.choice(author_names)
    author_font = _load_font("Inter", 22)
    draw.text((card_x + 24, card_y + 20), author, font=author_font, fill=(60, 60, 60, 255))
    rating = style.get("rating", 5)
    stars = "\u2605" * rating + "\u2606" * (5 - rating)
    star_font = _load_font("Inter", 24)
    draw.text((card_x + 24, card_y + 50), stars, font=star_font, fill=(255, 180, 0, 255))
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
        draw.text((card_x + 24, card_y + 90 + i * 34), line, font=body_font, fill=(30, 30, 30, 255))
    if style.get("verified", False):
        verified_font = _load_font("Inter", 18)
        draw.text((card_x + 24, card_y + card_h - 36), "Verified Purchase", font=verified_font, fill=(100, 160, 100, 255))


def _render_comparison_layout(canvas: Image.Image, draw: ImageDraw.ImageDraw, layer: LayerDefinition, params: CreativeParameters) -> None:
    layout = layer.style.get("layout", "split_vertical")
    if layout == "split_vertical":
        mid_x = canvas.width // 2
        draw.line([(mid_x, 0), (mid_x, canvas.height)], fill=(200, 200, 200, 255), width=2)


def _render_social_post_frame(canvas: Image.Image, draw: ImageDraw.ImageDraw, layer: LayerDefinition, params: CreativeParameters) -> None:
    variants = (layer.style_variant or "tweet").split("|")
    variant = random.choice(variants)
    margin = 30
    card_rect = [margin, margin, canvas.width - margin, canvas.height - margin]
    try:
        draw.rounded_rectangle(card_rect, radius=16, fill=(255, 255, 255, 255))
    except AttributeError:
        draw.rectangle(card_rect, fill=(255, 255, 255, 255))
    # Simplified social chrome — keeping functional but compact
    if variant == "tweet":
        draw.ellipse([margin + 20, margin + 16, margin + 60, margin + 56], fill=(180, 200, 230, 255))
        draw.text((margin + 72, margin + 20), "Real Person", font=_load_font("Inter", 20), fill=(20, 20, 20, 255))
        draw.text((margin + 72, margin + 42), "@real_person", font=_load_font("Inter", 16), fill=(130, 130, 130, 255))


def _pil_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    if fmt == "PNG":
        img.convert("RGBA" if img.mode == "RGBA" else "RGB").save(buf, format=fmt, optimize=True)
    else:
        img.convert("RGB").save(buf, format=fmt, quality=95)
    buf.seek(0)
    return buf.getvalue()


async def _pillow_render(
    ad_type: AdTypeDefinition,
    params: CreativeParameters,
    aspect_ratio: str,
    hook_text: str | None,
) -> bytes:
    """Legacy Pillow-based rendering (fallback when no template exists)."""
    w, h = ASPECT_RATIO_SIZES.get(aspect_ratio, (1080, 1080))
    canvas = Image.new("RGBA", (w, h), (26, 54, 93, 255))
    draw = ImageDraw.Draw(canvas)

    try:
        for layer in ad_type.layers:
            if not _check_condition(layer.condition, params):
                continue
            # Hook text substitution
            if hook_text and layer.content:
                content = layer.content
                if "{problem_hook}" in content or "{organic_hook}" in content:
                    layer = layer.model_copy(
                        update={"content": content.replace("{problem_hook}", hook_text).replace("{organic_hook}", hook_text)}
                    )

            lt = layer.type.lower()
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
    except Exception as e:
        logger.error(f"Pillow render failed for {ad_type.id}@{aspect_ratio}: {e}")

    return _pil_to_bytes(canvas)


# =====================================================================
# Main renderer (same interface as before)
# =====================================================================


class StaticAdRenderer:
    """
    Renders a static ad image from an AdTypeDefinition + CreativeParameters.

    Primary path: Fabric.js template → Node.js renderer microservice.
    Fallback: Pillow layer-based rendering.
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

        Tries template-based rendering first, falls back to Pillow.
        """
        w, h = ASPECT_RATIO_SIZES.get(aspect_ratio, (1080, 1080))

        # Try template-based rendering
        template_json = await _load_template_from_db(ad_type.id, aspect_ratio)
        if template_json:
            populated = _resolve_template_variables(template_json, params, hook_text)
            result = await _render_via_service(populated, w, h)
            if result:
                return result
            logger.info(f"Template render failed for {ad_type.id}@{aspect_ratio}, using Pillow")

        # Fallback to Pillow
        return await _pillow_render(ad_type, params, aspect_ratio, hook_text)

    async def render_from_template(
        self,
        canvas_json: dict,
        params: CreativeParameters,
        width: int = 1080,
        height: int = 1080,
        hook_text: str | None = None,
    ) -> bytes:
        """
        Render directly from provided Fabric.js JSON (for editor preview/save).
        """
        populated = _resolve_template_variables(canvas_json, params, hook_text)
        result = await _render_via_service(populated, width, height)
        if result:
            return result
        raise RuntimeError("Renderer service unavailable")

    async def render_all_ratios(
        self,
        ad_type: AdTypeDefinition,
        params: CreativeParameters,
        hook_text: str | None = None,
    ) -> dict[str, bytes]:
        """Render ad in all configured aspect ratios."""
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
