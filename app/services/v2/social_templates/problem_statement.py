"""
Problem Statement Text Template — HTML-to-Image renderer via Playwright.

Generates a bold, text-only problem statement image (PNG).
No product image, no branding — intentionally raw and attention-grabbing.
Self-contained: system fonts, no external dependencies.
"""

import html
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProblemStatementParams:
    headline: str = "Your biggest problem"
    subtext: str | None = None
    bg_color: str = "#1A202C"
    bg_gradient: str | None = None
    text_color: str = "#FFFFFF"
    accent_color: str | None = None  # optional color for emphasis word
    font_style: str = "bold"  # bold, italic, uppercase
    alignment: str = "center"  # center, left


def _build_html(params: ProblemStatementParams) -> str:
    headline = html.escape(params.headline)
    bg_style = params.bg_gradient or params.bg_color
    text_color = params.text_color
    alignment = params.alignment

    font_weight = "800"
    font_style_css = "normal"
    text_transform = "none"
    if params.font_style == "italic":
        font_style_css = "italic"
    elif params.font_style == "uppercase":
        text_transform = "uppercase"
        font_weight = "900"

    subtext_html = ""
    if params.subtext:
        subtext = html.escape(params.subtext)
        subtext_html = f'<div class="subtext">{subtext}</div>'

    # Optional accent underline
    accent_html = ""
    if params.accent_color:
        accent_html = f"""<div class="accent-line" style="background:{params.accent_color};"></div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    width: 1080px;
    height: 1080px;
    background: {bg_style};
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    overflow: hidden;
}}

.container {{
    padding: 80px 100px;
    text-align: {alignment};
    max-width: 100%;
    width: 100%;
}}

.headline {{
    font-size: 64px;
    font-weight: {font_weight};
    font-style: {font_style_css};
    text-transform: {text_transform};
    line-height: 1.2;
    color: {text_color};
    letter-spacing: -1.5px;
    word-wrap: break-word;
}}

.accent-line {{
    width: 80px;
    height: 5px;
    border-radius: 3px;
    margin: 40px {"auto" if alignment == "center" else "0"};
}}

.subtext {{
    font-size: 26px;
    font-weight: 400;
    line-height: 1.5;
    color: {text_color};
    opacity: 0.65;
    margin-top: 32px;
    max-width: 800px;
    {"margin-left: auto; margin-right: auto;" if alignment == "center" else ""}
}}
</style>
</head>
<body>
    <div class="container">
        <div class="headline">{headline}</div>
        {accent_html}
        {subtext_html}
    </div>
</body>
</html>"""


async def render_problem_statement(params: ProblemStatementParams | None = None) -> bytes:
    from playwright.async_api import async_playwright

    if params is None:
        params = ProblemStatementParams()

    page_html = _build_html(params)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1080},
            device_scale_factor=2,
        )
        await page.set_content(page_html, wait_until="load")
        screenshot_bytes = await page.screenshot(
            type="png",
            clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
        )
        await browser.close()

    logger.info(f"Problem statement rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
