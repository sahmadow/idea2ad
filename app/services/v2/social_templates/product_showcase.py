"""
Product Showcase Template — Manual image upload with optional text overlay.

Takes an uploaded image as-is and optionally overlays a price tag or headline.
The 9th creative type: user provides the image, we just render it (+ optional text).
"""

import base64
import html
import logging
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

logger = logging.getLogger(__name__)


@dataclass
class ProductShowcaseParams:
    product_image_url: str = ""          # required: URL or file:// path
    overlay_text: str | None = None      # optional: price tag, headline, etc.
    overlay_position: str = "bottom-left" # bottom-left, bottom-right, top-left, top-right, center


def _resolve_image_url(url: str) -> str:
    """Convert file:// URLs to data URIs so set_content can display them."""
    if not url.startswith("file://"):
        return url
    path = Path(unquote(urlparse(url).path))
    if not path.is_file():
        logger.warning(f"Local image not found: {path}")
        return url
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def _build_html(params: ProductShowcaseParams) -> str:
    image_url = html.escape(_resolve_image_url(params.product_image_url))

    # Position mapping
    pos = params.overlay_position
    pos_css = {
        "bottom-left":  "bottom: 40px; left: 40px;",
        "bottom-right": "bottom: 40px; right: 40px;",
        "top-left":     "top: 40px; left: 40px;",
        "top-right":    "top: 40px; right: 40px;",
        "center":       "top: 50%; left: 50%; transform: translate(-50%, -50%);",
    }.get(pos, "bottom-left: 40px; left: 40px;")

    overlay_html = ""
    if params.overlay_text:
        overlay_html = f'<div class="overlay" style="{pos_css}">{html.escape(params.overlay_text)}</div>'

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
    position: relative;
}}

.image-fill {{
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
}}

.image-fill img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}}

.overlay {{
    position: absolute;
    background: rgba(0, 0, 0, 0.65);
    color: #FFFFFF;
    font-size: 42px;
    font-weight: 800;
    padding: 16px 32px;
    border-radius: 8px;
    letter-spacing: 0.5px;
    white-space: nowrap;
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
}}
</style>
</head>
<body>
    <div class="image-fill">
        <img src="{image_url}" alt="product">
    </div>
    {overlay_html}
</body>
</html>"""


async def render_product_showcase(params: ProductShowcaseParams | None = None) -> bytes:
    from playwright.async_api import async_playwright

    if params is None:
        params = ProductShowcaseParams()

    page_html = _build_html(params)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1080},
            device_scale_factor=2,
        )
        await page.set_content(page_html, wait_until="networkidle")
        await page.wait_for_timeout(1500)
        screenshot_bytes = await page.screenshot(
            type="png",
            clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
        )
        await browser.close()

    logger.info(f"Product showcase rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
