"""
Person Centric Template — AI person image generation + HTML-to-Image via Playwright.

Two parts:
1. Person image generation via Gemini 2.5 Flash Image (same model as image_editor.py)
2. HTML rendering via Playwright (headline + person image + CTA)

Self-contained: inline CSS, base64 image embed, system fonts.
"""

import base64
import html as html_mod
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def _perceived_brightness(hex_color: str) -> float:
    """Perceived brightness 0-255 using ITU-R BT.601 weights."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except (ValueError, IndexError):
        return 128
    return 0.299 * r + 0.587 * g + 0.114 * b


def _text_on(bg_hex: str) -> str:
    """Return white or dark text color based on background brightness."""
    return "#FFFFFF" if _perceived_brightness(bg_hex) < 150 else "#1C1C1C"


@dataclass
class PersonCentricParams:
    headline: str = "Your headline here"
    subheadline: str | None = None
    cta_text: str = "Get Started"
    person_image_bytes: bytes | None = None  # AI-generated person PNG
    logo_url: str | None = None
    bg_color: str = "#0f172a"
    bg_gradient: str | None = None
    accent_color: str = "#3b82f6"
    text_color: str = "#ffffff"
    font_family: str = "Inter"
    btn_bg: str | None = None
    btn_color: str = "#ffffff"
    btn_radius: str = "12px"


async def generate_person_image(params) -> bytes | None:
    """Generate a person image using Gemini 2.5 Flash Image.

    Args:
        params: CreativeParameters with persona_primary, product_name, etc.

    Returns:
        PNG bytes or None on failure.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set — skipping person image generation")
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Build persona description
        persona_desc = ""
        if params.persona_primary:
            persona_desc = params.persona_primary.label or ""

        product_name = params.product_name or "the product"
        product_category = params.product_category or "product"

        # Build scene context from available data
        scene_context = ""
        if params.scene_solution:
            scene_context = params.scene_solution
        elif product_category:
            scene_context = f"using {product_name} in a natural setting"

        # Build prompt — person actively using the product
        prompt = (
            f"Professional lifestyle photograph of a {persona_desc} "
            f"actively using {product_name} ({product_category}). "
            f"{scene_context}. "
            f"Clean composition, commercial photography, studio lighting, "
            f"4K quality. Single person, no text overlays."
        )

        logger.info(f"Generating person image: {prompt[:120]}...")

        result = await client.aio.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract image from response
        for part in result.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                img_bytes = part.inline_data.data
                logger.info(f"Person image generated: {len(img_bytes) // 1024}KB")
                return img_bytes

        logger.warning("Gemini returned no image for person generation")
        return None

    except Exception as e:
        logger.error(f"Person image generation failed: {e}", exc_info=True)
        return None


def _build_html(params: PersonCentricParams) -> str:
    headline = html_mod.escape(params.headline)
    cta = html_mod.escape(params.cta_text)
    accent = params.accent_color
    bg_style = params.bg_gradient or params.bg_color
    btn_bg = params.btn_bg or accent
    btn_color = params.btn_color or _text_on(btn_bg)
    text_color = params.text_color

    # Logo
    logo_html = ""
    if params.logo_url:
        logo_html = f'<img class="logo" src="{html_mod.escape(params.logo_url)}" alt="Logo">'

    # Person image — embedded as base64 data URI
    person_html = ""
    if params.person_image_bytes:
        b64 = base64.b64encode(params.person_image_bytes).decode()
        person_html = f'<img class="person-image" src="data:image/png;base64,{b64}" alt="Person">'
    else:
        # Placeholder circle when no person image
        person_html = '<div class="person-placeholder"></div>'

    # Subheadline
    sub_html = ""
    if params.subheadline:
        sub_html = f'<p class="subheadline">{html_mod.escape(params.subheadline)}</p>'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    width: 1080px;
    height: 1080px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    background: {bg_style};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    color: {text_color};
    overflow: hidden;
    position: relative;
    padding: 30px 40px;
}}

.decoration-circle {{
    position: absolute;
    border-radius: 50%;
    background: {accent};
    opacity: 0.06;
}}

.decoration-circle.top-right {{
    width: 350px;
    height: 350px;
    top: -120px;
    right: -120px;
}}

.decoration-circle.bottom-left {{
    width: 200px;
    height: 200px;
    bottom: -60px;
    left: -60px;
}}

.logo {{
    position: absolute;
    top: 28px;
    left: 28px;
    max-width: 100px;
    max-height: 50px;
    object-fit: contain;
}}

.top-zone {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    max-width: 90%;
    z-index: 2;
}}

.headline {{
    font-size: 58px;
    font-weight: 800;
    color: {text_color};
    line-height: 1.1;
    letter-spacing: -1px;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}}

.person-zone {{
    flex: 2;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 10px 0;
    min-height: 480px;
}}

.person-image {{
    max-width: 95%;
    max-height: 600px;
    width: auto;
    height: auto;
    object-fit: contain;
    filter: drop-shadow(0 20px 50px rgba(0, 0, 0, 0.3));
    border-radius: 24px;
}}

.person-placeholder {{
    width: 400px;
    height: 400px;
    border-radius: 50%;
    background: {accent};
    opacity: 0.15;
}}

.bottom-zone {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    max-width: 90%;
    z-index: 2;
}}

.subheadline {{
    font-size: 26px;
    font-weight: 500;
    color: {text_color};
    opacity: 0.85;
    margin-bottom: 24px;
    line-height: 1.3;
}}

.cta-btn {{
    display: inline-block;
    background: {btn_bg};
    color: {btn_color};
    padding: 22px 56px;
    border-radius: {params.btn_radius};
    font-size: 26px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 4px 12px rgba(0, 0, 0, 0.2);
    text-decoration: none;
}}
</style>
</head>
<body>
    <div class="decoration-circle top-right"></div>
    <div class="decoration-circle bottom-left"></div>
    {logo_html}
    <div class="top-zone">
        <h1 class="headline">{headline}</h1>
    </div>
    <div class="person-zone">
        {person_html}
    </div>
    <div class="bottom-zone">
        {sub_html}
        <div class="cta-btn">{cta}</div>
    </div>
</body>
</html>"""


async def render_person_centric(params: PersonCentricParams | None = None) -> bytes:
    """Render person centric ad to PNG bytes via Playwright."""
    from playwright.async_api import async_playwright

    if params is None:
        params = PersonCentricParams()

    page_html = _build_html(params)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1080},
            device_scale_factor=2,
        )
        await page.set_content(page_html, wait_until="load")
        # Wait for base64 image to render
        await page.wait_for_timeout(1000)
        screenshot_bytes = await page.screenshot(
            type="png",
            clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
        )
        await browser.close()

    logger.info(f"Person centric rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
