"""
Service Hero Template — HTML-to-Image renderer via Playwright.

Full-bleed scene photo with headline overlay + gradient scrim.
Designed for service businesses (lawyers, consultants, agencies, etc.)
where showing people/scenes is key.
"""

import html
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ServiceHeroParams:
    scene_image_url: str = ""           # required: URL of the scene photo
    headline: str = "We fight for you."
    subtext: str | None = None
    cta_text: str | None = None         # e.g. "Free Consultation"
    brand_name: str | None = None
    text_position: str = "bottom"       # bottom, center, top
    overlay_opacity: float = 0.55       # 0-1, how dark the gradient scrim
    accent_color: str = "#FFFFFF"
    headline_color: str = "#FFFFFF"
    subtext_color: str = "rgba(255,255,255,0.85)"


def _build_html(params: ServiceHeroParams) -> str:
    headline = html.escape(params.headline)
    scene_url = html.escape(params.scene_image_url)
    opacity = max(0, min(1, params.overlay_opacity))

    # Gradient scrim direction based on text position
    if params.text_position == "top":
        gradient = f"linear-gradient(to bottom, rgba(0,0,0,{opacity}) 0%, rgba(0,0,0,{opacity * 0.6}) 50%, transparent 100%)"
        align = "flex-start"
        pad_top = "100px"
        pad_bottom = "0"
    elif params.text_position == "center":
        gradient = f"linear-gradient(to bottom, rgba(0,0,0,{opacity * 0.3}) 0%, rgba(0,0,0,{opacity}) 35%, rgba(0,0,0,{opacity}) 65%, rgba(0,0,0,{opacity * 0.3}) 100%)"
        align = "center"
        pad_top = "0"
        pad_bottom = "0"
    else:  # bottom
        gradient = f"linear-gradient(to top, rgba(0,0,0,{opacity}) 0%, rgba(0,0,0,{opacity * 0.7}) 45%, rgba(0,0,0,{opacity * 0.2}) 70%, transparent 100%)"
        align = "flex-end"
        pad_top = "0"
        pad_bottom = "80px"

    subtext_html = ""
    if params.subtext:
        subtext_html = f'<div class="subtext">{html.escape(params.subtext)}</div>'

    cta_html = ""
    if params.cta_text:
        cta_html = f'<div class="cta">{html.escape(params.cta_text)}</div>'

    brand_html = ""
    if params.brand_name:
        brand_html = f'<div class="brand">{html.escape(params.brand_name)}</div>'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    width: 1080px;
    height: 1080px;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: #000;
}}

.scene {{
    width: 1080px;
    height: 1080px;
    background-image: url('{scene_url}');
    background-size: cover;
    background-position: center;
    position: relative;
}}

.overlay {{
    position: absolute;
    inset: 0;
    background: {gradient};
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: {align};
    padding: {pad_top} 72px {pad_bottom} 72px;
}}

.brand {{
    position: absolute;
    top: 40px;
    left: 72px;
    font-size: 22px;
    font-weight: 700;
    color: {params.accent_color};
    letter-spacing: 1px;
    text-transform: uppercase;
    text-shadow: 0 2px 8px rgba(0,0,0,0.5);
}}

.text-block {{
    max-width: 900px;
}}

.headline {{
    font-size: 62px;
    font-weight: 800;
    line-height: 1.15;
    color: {params.headline_color};
    letter-spacing: -1px;
    text-shadow: 0 2px 16px rgba(0,0,0,0.6);
    margin-bottom: 20px;
}}

.subtext {{
    font-size: 24px;
    font-weight: 400;
    line-height: 1.5;
    color: {params.subtext_color};
    text-shadow: 0 1px 8px rgba(0,0,0,0.5);
    margin-bottom: 32px;
    max-width: 750px;
}}

.cta {{
    display: inline-block;
    padding: 16px 40px;
    background: {params.accent_color};
    color: #000000;
    font-size: 20px;
    font-weight: 700;
    border-radius: 6px;
    letter-spacing: 0.5px;
    text-shadow: none;
}}
</style>
</head>
<body>
    <div class="scene">
        <div class="overlay">
            {brand_html}
            <div class="text-block">
                <div class="headline">{headline}</div>
                {subtext_html}
                {cta_html}
            </div>
        </div>
    </div>
</body>
</html>"""


async def render_service_hero(params: ServiceHeroParams | None = None) -> bytes:
    from playwright.async_api import async_playwright

    if params is None:
        params = ServiceHeroParams()

    page_html = _build_html(params)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1080},
            device_scale_factor=2,
        )
        await page.set_content(page_html, wait_until="networkidle")
        # Extra wait for image loading
        await page.wait_for_timeout(1500)
        screenshot_bytes = await page.screenshot(
            type="png",
            clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
        )
        await browser.close()

    logger.info(f"Service hero rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
