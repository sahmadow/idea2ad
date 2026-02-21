"""
Review Static Template — HTML-to-Image renderer via Playwright.

Generates a pixel-perfect review/testimonial card image (PNG).
Supports multiple visual variants: app store, G2-style, minimal card.
Self-contained: inline SVG, system fonts, no external dependencies.
"""

import html
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def _perceived_brightness(hex_color: str) -> float:
    """Perceived brightness 0-255 using ITU-R BT.601 weights."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _text_on(bg_hex: str) -> str:
    """Return white or dark text color based on background brightness."""
    return "#FFFFFF" if _perceived_brightness(bg_hex) < 150 else "#1C1C1C"


@dataclass
class ReviewStaticParams:
    reviewer_name: str = "Sarah K."
    review_text: str = "Absolutely love this product. Changed my workflow completely."
    rating: int = 5  # 1-5
    product_name: str = "Product"
    variant: str = "card"  # card, app_store, minimal
    verified: bool = True
    reviewer_title: str | None = None  # e.g. "Marketing Director"
    avatar_url: str | None = None
    dark_mode: bool = False
    accent_color: str = "#FF6B35"


def _build_html(params: ReviewStaticParams) -> str:
    dark = params.dark_mode

    bg = "#0F0F0F" if dark else "#F0F2F5"
    card_bg = "#1C1C1E" if dark else "#FFFFFF"
    text_primary = "#FFFFFF" if dark else "#1C1C1C"
    text_secondary = "#A0A0A0" if dark else "#65676B"
    border_color = "#333" if dark else "#E4E6EB"
    star_color = "#FFB800"
    star_empty = "#333" if dark else "#D1D5DB"
    verified_color = "#22C55E"

    reviewer_name = html.escape(params.reviewer_name)
    review_text = html.escape(params.review_text)
    product_name = html.escape(params.product_name)
    accent = params.accent_color

    if params.avatar_url:
        avatar_html = f'<img src="{html.escape(params.avatar_url)}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" />'
    else:
        initials = "".join(w[0].upper() for w in params.reviewer_name.split()[:2])
        initials_color = _text_on(accent)
        avatar_html = f"""<div style="width:100%;height:100%;border-radius:50%;background:{accent};display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:700;color:{initials_color};">{html.escape(initials)}</div>"""

    # Stars
    star_full = f"""<svg viewBox="0 0 20 20" width="28" height="28" fill="{star_color}">
        <path d="M10 15.27L16.18 19l-1.64-7.03L20 7.24l-7.19-.61L10 0 7.19 6.63 0 7.24l5.46 4.73L3.82 19z"/>
    </svg>"""
    star_empty_svg = f"""<svg viewBox="0 0 20 20" width="28" height="28" fill="{star_empty}">
        <path d="M10 15.27L16.18 19l-1.64-7.03L20 7.24l-7.19-.61L10 0 7.19 6.63 0 7.24l5.46 4.73L3.82 19z"/>
    </svg>"""
    stars_html = star_full * params.rating + star_empty_svg * (5 - params.rating)

    reviewer_title_html = ""
    if params.reviewer_title:
        reviewer_title_html = f'<div class="reviewer-title">{html.escape(params.reviewer_title)}</div>'

    verified_html = ""
    if params.verified:
        verified_html = f"""<div class="verified">
            <svg viewBox="0 0 20 20" width="16" height="16" fill="{verified_color}">
                <path d="M10 0C4.477 0 0 4.477 0 10s4.477 10 10 10 10-4.477 10-10S15.523 0 10 0zm4.8 7.6l-5.6 5.6a.8.8 0 0 1-1.131 0l-2.87-2.87a.8.8 0 1 1 1.132-1.13L8.6 11.47l5.07-5.07a.8.8 0 1 1 1.13 1.13z"/>
            </svg>
            <span>Verified Purchase</span>
        </div>"""

    # Quote icon
    quote_svg = f"""<svg viewBox="0 0 24 24" width="48" height="48" fill="{accent}" opacity="0.2">
        <path d="M6 17h3l2-4V7H5v6h3zm8 0h3l2-4V7h-6v6h3z"/>
    </svg>"""

    S = 1.4

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    width: 1080px;
    height: 1080px;
    background: {bg};
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    overflow: hidden;
}}

.review-card {{
    width: 880px;
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: {int(16 * S)}px;
    padding: {int(40 * S)}px {int(36 * S)}px;
    position: relative;
}}

.quote-icon {{
    margin-bottom: {int(12 * S)}px;
}}

.stars {{
    display: flex;
    gap: 4px;
    margin-bottom: {int(16 * S)}px;
}}

.review-text {{
    font-size: {int(20 * S)}px;
    line-height: 1.55;
    color: {text_primary};
    margin-bottom: {int(28 * S)}px;
    word-wrap: break-word;
    white-space: pre-wrap;
    font-style: italic;
}}

.reviewer {{
    display: flex;
    align-items: center;
    gap: {int(12 * S)}px;
    padding-top: {int(20 * S)}px;
    border-top: 1px solid {border_color};
}}

.reviewer-avatar {{
    width: {int(48 * S)}px;
    height: {int(48 * S)}px;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
}}

.reviewer-info {{
    flex: 1;
}}

.reviewer-name {{
    font-size: {int(16 * S)}px;
    font-weight: 700;
    color: {text_primary};
    line-height: 1.3;
}}

.reviewer-title {{
    font-size: {int(13 * S)}px;
    color: {text_secondary};
    margin-top: 2px;
}}

.verified {{
    display: flex;
    align-items: center;
    gap: {int(6 * S)}px;
    font-size: {int(12 * S)}px;
    color: {verified_color};
    margin-top: {int(6 * S)}px;
}}

.product-label {{
    font-size: {int(13 * S)}px;
    color: {text_secondary};
    margin-bottom: {int(8 * S)}px;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
}}
</style>
</head>
<body>
    <div class="review-card">
        <div class="product-label">Review — {product_name}</div>
        <div class="quote-icon">{quote_svg}</div>
        <div class="stars">{stars_html}</div>
        <div class="review-text">"{review_text}"</div>
        <div class="reviewer">
            <div class="reviewer-avatar">{avatar_html}</div>
            <div class="reviewer-info">
                <div class="reviewer-name">{reviewer_name}</div>
                {reviewer_title_html}
                {verified_html}
            </div>
        </div>
    </div>
</body>
</html>"""


async def render_review_static(params: ReviewStaticParams | None = None) -> bytes:
    from playwright.async_api import async_playwright

    if params is None:
        params = ReviewStaticParams()

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

    logger.info(f"Review static rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
