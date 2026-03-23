"""
AI Scene Text Overlay — AI-generated scene background + gradient text overlay via Playwright.

Two parts:
1. Scene image generation via Gemini 2.5 Flash Image (full-bleed abstract/conceptual scene)
2. HTML rendering via Playwright (gradient overlay + headline + subheadline + CTA)

Self-contained: inline CSS, base64 image embed, Google Fonts import.
"""

import base64
import html as html_mod
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AiSceneOverlayParams:
    headline: str = "Your headline here"
    subheadline: str | None = None
    cta_text: str = "Get Started"
    scene_image_bytes: bytes | None = None  # AI-generated scene PNG
    logo_url: str | None = None
    bg_color: str = "#1a1a2e"  # warm dark fallback
    accent_color: str = "#3b82f6"
    text_color: str = "#ffffff"
    font_family: str = "Inter"
    overlay_opacity: float = 0.65


async def generate_scene_image(params) -> bytes | None:
    """Generate an abstract/conceptual scene image using Gemini 2.5 Flash Image.

    Args:
        params: CreativeParameters with product_category, brand_colors, etc.

    Returns:
        PNG bytes or None on failure.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set — skipping scene image generation")
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        product_name = params.product_name or "the product"
        product_category = params.product_category or "product"

        # Scene context from available data
        scene_context = ""
        if params.scene_solution:
            scene_context = params.scene_solution
        elif params.scene_lifestyle:
            scene_context = params.scene_lifestyle
        elif params.key_benefit:
            scene_context = f"environment evoking {params.key_benefit}"

        # Inject brand colors into prompt
        color_hint = ""
        if params.brand_colors:
            colors = []
            if params.brand_colors.primary:
                colors.append(params.brand_colors.primary)
            if params.brand_colors.accent:
                colors.append(params.brand_colors.accent)
            if colors:
                color_hint = f"Use a color palette inspired by {', '.join(colors)}. "

        # Category-aware scene direction
        category_lower = product_category.lower()
        if category_lower in ("saas", "software", "technology", "ai"):
            scene_direction = (
                "Abstract technology scene with flowing data visualizations, "
                "soft gradients, and modern dashboard elements. "
                "Clean, futuristic, professional atmosphere."
            )
        elif category_lower in ("ecommerce", "retail", "fashion", "beauty"):
            scene_direction = (
                "Lifestyle product photography environment with warm lighting, "
                "elegant surfaces, and aspirational lifestyle setting."
            )
        elif category_lower in ("health", "fitness", "wellness"):
            scene_direction = (
                "Serene wellness scene with natural elements, soft light, "
                "and calming organic textures."
            )
        elif category_lower in ("finance", "fintech", "banking"):
            scene_direction = (
                "Professional financial scene with abstract charts, "
                "clean geometric patterns, and trustworthy blue tones."
            )
        else:
            scene_direction = (
                "Abstract conceptual scene with smooth gradients, "
                "soft bokeh, and professional atmosphere."
            )

        prompt = (
            f"{scene_direction} "
            f"{color_hint}"
            f"Scene context: {scene_context or f'environment related to {product_category}'}. "
            f"Full-bleed background image, 1080x1080 square format. "
            f"Slightly blurred/dreamy to work well behind text overlays. "
            f"IMPORTANT: Do not include any text, buttons, call-to-action elements, "
            f"logos, or text overlays in the image. Pure visual scene only."
        )

        logger.info(f"Generating scene image: {prompt[:120]}...")

        result = await client.aio.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in result.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                img_bytes = part.inline_data.data
                logger.info(f"Scene image generated: {len(img_bytes) // 1024}KB")
                return img_bytes

        logger.warning("Gemini returned no image for scene generation")
        return None

    except Exception as e:
        logger.error(f"Scene image generation failed: {e}", exc_info=True)
        return None


def _build_html(params: AiSceneOverlayParams) -> str:
    headline = html_mod.escape(params.headline)
    cta = html_mod.escape(params.cta_text)
    accent = params.accent_color
    text_color = params.text_color
    overlay_opacity = params.overlay_opacity
    font_family = params.font_family

    # Logo
    logo_html = ""
    if params.logo_url:
        logo_html = f'<img class="logo" src="{html_mod.escape(params.logo_url)}" alt="Logo">'

    # Scene image — embedded as base64 data URI or solid fallback
    bg_image_css = ""
    if params.scene_image_bytes:
        b64 = base64.b64encode(params.scene_image_bytes).decode()
        bg_image_css = f"background-image: url('data:image/png;base64,{b64}');"
    else:
        bg_image_css = f"background: {params.bg_color};"

    # Subheadline
    sub_html = ""
    if params.subheadline:
        sub_html = f'<p class="subheadline">{html_mod.escape(params.subheadline)}</p>'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family={font_family.replace(' ', '+')}:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    width: 1080px;
    height: 1080px;
    position: relative;
    overflow: hidden;
    font-family: '{font_family}', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}

.scene-bg {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    {bg_image_css}
    background-size: cover;
    background-position: center;
}}

.gradient-overlay {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(
        to bottom,
        rgba(0, 0, 0, 0.05) 0%,
        rgba(0, 0, 0, 0.15) 40%,
        rgba(0, 0, 0, {overlay_opacity}) 65%,
        rgba(0, 0, 0, {min(overlay_opacity + 0.2, 0.95)}) 100%
    );
}}

{logo_html and '''
.logo {{
    position: absolute;
    top: 32px;
    left: 32px;
    max-width: 120px;
    max-height: 56px;
    object-fit: contain;
    z-index: 10;
    filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
}}
''' or ''}

.text-zone {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 0 60px 60px 60px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    z-index: 5;
}}

.headline {{
    font-size: 62px;
    font-weight: 800;
    color: {text_color};
    line-height: 1.12;
    letter-spacing: -1.5px;
    text-shadow: 0 2px 16px rgba(0, 0, 0, 0.4);
    margin-bottom: 20px;
    max-width: 920px;
}}

.subheadline {{
    font-size: 26px;
    font-weight: 400;
    color: {text_color};
    opacity: 0.9;
    line-height: 1.35;
    margin-bottom: 32px;
    max-width: 800px;
    text-shadow: 0 1px 8px rgba(0, 0, 0, 0.3);
}}

.cta-btn {{
    display: inline-block;
    background: {accent};
    color: {text_color};
    padding: 20px 52px;
    border-radius: 12px;
    font-size: 24px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    text-decoration: none;
}}
</style>
</head>
<body>
    <div class="scene-bg"></div>
    <div class="gradient-overlay"></div>
    {logo_html}
    <div class="text-zone">
        <h1 class="headline">{headline}</h1>
        {sub_html}
        <div class="cta-btn">{cta}</div>
    </div>
</body>
</html>"""


async def render_ai_scene_overlay(params: AiSceneOverlayParams | None = None) -> bytes:
    """Render AI scene overlay ad to PNG bytes via Playwright."""
    from playwright.async_api import async_playwright

    if params is None:
        params = AiSceneOverlayParams()

    page_html = _build_html(params)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1080},
            device_scale_factor=2,
        )
        await page.set_content(page_html, wait_until="load")
        # Wait for base64 image + Google Fonts to render
        await page.wait_for_timeout(1500)
        screenshot_bytes = await page.screenshot(
            type="png",
            clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
        )
        await browser.close()

    logger.info(f"AI scene overlay rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
