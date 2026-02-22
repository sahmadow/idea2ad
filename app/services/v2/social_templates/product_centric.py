"""
Product Centric Template — HTML-to-Image renderer via Playwright.

Pain point + headline + product image + CTA. Uses scraped product image.
Self-contained: inline CSS, system fonts, no external dependencies.
"""

import base64
import html as html_mod
import logging
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
class ProductCentricParams:
    headline: str = "Your headline here"
    pain_point: str | None = None
    subheadline: str | None = None
    cta_text: str = "Get Started"
    product_image_url: str | None = None
    product_image_bytes: bytes | None = None  # alternative: embed as base64
    logo_url: str | None = None
    bg_color: str = "#0f172a"
    bg_gradient: str | None = None
    accent_color: str = "#3b82f6"
    text_color: str = "#ffffff"
    font_family: str = "Inter"
    btn_bg: str | None = None
    btn_color: str = "#ffffff"
    btn_radius: str = "12px"


def _build_html(params: ProductCentricParams) -> str:
    headline = html_mod.escape(params.headline)
    cta = html_mod.escape(params.cta_text)
    accent = params.accent_color
    bg_style = params.bg_gradient or params.bg_color
    btn_bg = params.btn_bg or accent
    btn_color = params.btn_color or _text_on(btn_bg)
    text_color = params.text_color

    # Pain point
    pain_html = ""
    if params.pain_point:
        pain_html = f'<p class="pain-point">"{html_mod.escape(params.pain_point)}"</p>'

    # Subheadline
    sub_html = ""
    if params.subheadline:
        sub_html = f'<p class="subheadline">{html_mod.escape(params.subheadline)}</p>'

    # Logo
    logo_html = ""
    if params.logo_url:
        logo_html = f'<img class="logo" src="{html_mod.escape(params.logo_url)}" alt="Logo">'

    # Product image — prefer bytes (base64) over URL for reliability in Playwright
    product_html = ""
    if params.product_image_bytes:
        b64 = base64.b64encode(params.product_image_bytes).decode()
        product_html = f'''<div class="product-image-wrapper">
            <img class="product-image" src="data:image/png;base64,{b64}" alt="Product">
        </div>'''
    elif params.product_image_url:
        product_html = f'''<div class="product-image-wrapper">
            <img class="product-image" src="{html_mod.escape(params.product_image_url)}" alt="Product">
        </div>'''

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
    justify-content: center;
    background: {bg_style};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    color: {text_color};
    overflow: hidden;
    position: relative;
    padding: 50px 40px;
}}

.decoration-circle {{
    position: absolute;
    border-radius: 50%;
    background: {accent};
    opacity: 0.08;
}}

.decoration-circle.top-right {{
    width: 400px;
    height: 400px;
    top: -150px;
    right: -150px;
}}

.decoration-circle.bottom-left {{
    width: 250px;
    height: 250px;
    bottom: -80px;
    left: -80px;
}}

.logo {{
    position: absolute;
    top: 28px;
    left: 28px;
    max-width: 120px;
    max-height: 60px;
    object-fit: contain;
}}

.content {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    max-width: 95%;
    margin-bottom: 20px;
}}

.pain-point {{
    font-size: 24px;
    font-weight: 400;
    font-style: italic;
    color: {text_color};
    opacity: 0.75;
    margin-bottom: 20px;
    line-height: 1.3;
}}

.headline {{
    font-size: 64px;
    font-weight: 800;
    color: {text_color};
    margin-bottom: 16px;
    line-height: 1.1;
    letter-spacing: -1px;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}}

.subheadline {{
    font-size: 28px;
    font-weight: 500;
    color: {text_color};
    opacity: 0.85;
    line-height: 1.3;
}}

.product-image-wrapper {{
    display: flex;
    justify-content: center;
    align-items: center;
    flex: 1;
    padding: 20px;
}}

.product-image {{
    max-width: 85%;
    max-height: 320px;
    object-fit: contain;
    filter: drop-shadow(0 10px 30px rgba(0, 0, 0, 0.18));
}}

.cta-wrapper {{
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: auto;
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
    <div class="content">
        {pain_html}
        <h1 class="headline">{headline}</h1>
        {sub_html}
    </div>
    {product_html}
    <div class="cta-wrapper">
        <div class="cta-btn">{cta}</div>
    </div>
</body>
</html>"""


async def render_product_centric(params: ProductCentricParams | None = None) -> bytes:
    """Render product centric ad to PNG bytes via Playwright."""
    from playwright.async_api import async_playwright

    if params is None:
        params = ProductCentricParams()

    page_html = _build_html(params)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1080},
            device_scale_factor=2,
        )
        await page.set_content(page_html, wait_until="networkidle")
        # Wait for product image to load
        await page.wait_for_timeout(2000)
        screenshot_bytes = await page.screenshot(
            type="png",
            clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
        )
        await browser.close()

    logger.info(f"Product centric rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
