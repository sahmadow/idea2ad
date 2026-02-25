"""
Branded Static Template — HTML-to-Image renderer via Playwright.

Uses scraped design tokens (colors, fonts, gradients, button styles) to generate
a pixel-perfect branded ad that mirrors the source site's visual identity.
Self-contained: inline CSS, Google Fonts import, no external dependencies.
"""

import html as html_mod
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BrandedStaticParams:
    headline: str = "Your headline here"
    description: str = ""
    cta_text: str = "Get Started"
    brand_name: str = ""
    # Design tokens from scraper
    bg_color: str = "#0f172a"
    bg_gradient: str | None = None  # raw CSS gradient
    accent_color: str = "#3b82f6"
    text_color: str = "#ffffff"
    font_family: str = "Inter"
    font_faces_css: str = ""  # @font-face rules from scraper
    # Button styling from scraper
    btn_bg: str | None = None
    btn_color: str = "#ffffff"
    btn_radius: str = "12px"
    btn_padding: str = "16px 48px"
    btn_font_weight: str = "600"
    btn_font_size: str = "22px"


def _build_html(params: BrandedStaticParams) -> str:
    headline = html_mod.escape(params.headline)
    description = html_mod.escape(params.description)
    cta = html_mod.escape(params.cta_text)
    brand = html_mod.escape(params.brand_name)
    font_family = params.font_family
    accent = params.accent_color
    bg_style = params.bg_gradient or params.bg_color
    btn_bg = params.btn_bg or accent
    text_color = params.text_color

    # Description color: slightly muted from text
    desc_color = "#94a3b8"

    # Brand section
    brand_html = ""
    if brand:
        brand_html = f'<div class="brand">{brand}</div>'

    # Description section
    desc_html = ""
    if description:
        desc_html = f'<p class="description">{description}</p>'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{params.font_faces_css}
@import url('https://fonts.googleapis.com/css2?family={font_family.replace(" ", "+")}:wght@400;600;700&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    width: 1080px;
    height: 1080px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: {bg_style};
    font-family: '{font_family}', system-ui, sans-serif;
    color: {text_color};
    overflow: hidden;
    position: relative;
}}

.accent-bar {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 6px;
    background: {accent};
}}

.brand {{
    position: absolute;
    top: 48px;
    left: 60px;
    font-size: 28px;
    font-weight: 700;
    color: {accent};
    letter-spacing: -0.5px;
}}

.content {{
    text-align: center;
    padding: 0 60px;
    max-width: 960px;
}}

.headline {{
    font-size: 54px;
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 28px;
    color: {text_color};
    letter-spacing: -1px;
}}

.description {{
    font-size: 22px;
    line-height: 1.5;
    color: {desc_color};
    margin-bottom: 48px;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
}}

.divider {{
    width: 80px;
    height: 4px;
    background: {accent};
    border-radius: 2px;
    margin: 0 auto 40px;
}}

.cta-btn {{
    display: inline-block;
    background: {btn_bg};
    color: {params.btn_color};
    padding: {params.btn_padding};
    border-radius: {params.btn_radius};
    font-family: '{font_family}', system-ui, sans-serif;
    font-size: {params.btn_font_size};
    font-weight: {params.btn_font_weight};
    text-decoration: none;
    letter-spacing: 0.3px;
}}
</style>
</head>
<body>
    <div class="accent-bar"></div>
    {brand_html}
    <div class="content">
        <h1 class="headline">{headline}</h1>
        <div class="divider"></div>
        {desc_html}
        <a class="cta-btn">{cta}</a>
    </div>
</body>
</html>"""


async def render_branded_static(params: BrandedStaticParams | None = None) -> bytes:
    """Render branded static ad to PNG bytes via Playwright."""
    from playwright.async_api import async_playwright

    if params is None:
        params = BrandedStaticParams()

    page_html = _build_html(params)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1080},
            device_scale_factor=2,
        )
        await page.set_content(page_html, wait_until="networkidle")
        # Wait for Google Fonts to load
        try:
            await page.wait_for_timeout(2000)
        except Exception:
            pass

        screenshot_bytes = await page.screenshot(
            type="png",
            clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
        )
        await browser.close()

    logger.info(f"Branded static rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
