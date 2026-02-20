"""
HTML-to-Image ad creative generator for any landing page URL.
Scrapes design tokens, builds inline HTML/CSS, screenshots with Playwright at 2x DPR.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Add project root to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.scraper import scrape_landing_page

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_URL = "https://peec.ai"


def pick_colors(styling: dict) -> dict:
    """Extract best background, accent, and text colors from styling data."""
    bgs = styling.get("backgrounds", [])
    accents = styling.get("accents", [])
    texts = styling.get("text", [])

    bg = bgs[0] if bgs else "#0f172a"
    accent = accents[0] if accents else "#3b82f6"
    text_color = "#ffffff"
    # If bg is light, use dark text
    if bg.startswith("#f") or bg.startswith("#e") or bg == "#ffffff":
        text_color = texts[0] if texts else "#1a202c"

    return {"bg": bg, "accent": accent, "text": text_color}


async def html_to_image(data: dict) -> bytes:
    """Build inline HTML/CSS from extracted tokens, screenshot with Playwright."""
    from playwright.async_api import async_playwright

    styling = data.get("styling", {})
    css_assets = data.get("css_assets", {})
    design_tokens = data.get("design_tokens", {})
    colors = pick_colors(styling)
    fonts = styling.get("fonts", ["Inter"])
    font_family = fonts[0] if fonts else "Inter"
    headline = data["headers"][0] if data.get("headers") else data.get("title", "peec.ai")
    description = data.get("description", "AI-powered ad creative platform")
    cta = "Get Started Now"

    # Build font-face rules
    font_faces = "\n".join(css_assets.get("font_faces", []))

    # Gradient or solid bg
    gradients = design_tokens.get("gradients", [])
    bg_style = gradients[0]["raw"] if gradients else colors["bg"]

    border_radius = design_tokens.get("border_radius", "12px") or "12px"

    # Button styles from scrape
    btn = css_assets.get("button_styles", {})
    btn_bg = btn.get("backgroundColor", colors["accent"])
    btn_color = btn.get("color", "#ffffff")
    btn_radius = btn.get("borderRadius", border_radius)
    btn_padding = btn.get("padding", "16px 48px")
    btn_font_weight = btn.get("fontWeight", "600")
    btn_font_size = btn.get("fontSize", "22px")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{font_faces}
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
    color: #ffffff;
    overflow: hidden;
    position: relative;
}}

.accent-bar {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 6px;
    background: {colors["accent"]};
}}

.brand {{
    position: absolute;
    top: 48px;
    left: 60px;
    font-size: 28px;
    font-weight: 700;
    color: {colors["accent"]};
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
    color: {colors["text"]};
    letter-spacing: -1px;
}}

.description {{
    font-size: 22px;
    line-height: 1.5;
    color: #94a3b8;
    margin-bottom: 48px;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
}}

.divider {{
    width: 80px;
    height: 4px;
    background: {colors["accent"]};
    border-radius: 2px;
    margin: 0 auto 40px;
}}

.cta-btn {{
    display: inline-block;
    background: {btn_bg};
    color: {btn_color};
    padding: {btn_padding};
    border-radius: {btn_radius};
    font-family: '{font_family}', system-ui, sans-serif;
    font-size: {btn_font_size};
    font-weight: {btn_font_weight};
    text-decoration: none;
    letter-spacing: 0.3px;
}}
</style>
</head>
<body>
    <div class="accent-bar"></div>
    <div class="brand">peec.ai</div>
    <div class="content">
        <h1 class="headline">{headline}</h1>
        <div class="divider"></div>
        <p class="description">{description}</p>
        <a class="cta-btn">{cta}</a>
    </div>
</body>
</html>"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1080},
            device_scale_factor=2,
        )
        await page.set_content(html, wait_until="networkidle")
        # Wait for Google Fonts
        try:
            await page.wait_for_timeout(2000)
        except Exception:
            pass

        screenshot_bytes = await page.screenshot(
            type="png",
            clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
        )
        await browser.close()

    return screenshot_bytes


async def main():
    logger.info(f"Scraping {TARGET_URL}...")
    t0 = time.time()
    data = await scrape_landing_page(TARGET_URL)
    scrape_time = time.time() - t0
    logger.info(f"Scrape done in {scrape_time:.1f}s — {len(data.get('headers', []))} headers, {len(data.get('styling', {}).get('fonts', []))} fonts")

    t1 = time.time()
    img = await html_to_image(data)
    render_time = time.time() - t1

    out_path = OUTPUT_DIR / "approach_4_html_to_image.png"
    out_path.write_bytes(img)
    logger.info(f"Output: {out_path.name} ({len(img)//1024}KB, {render_time:.2f}s)")

    summary = {
        "target": TARGET_URL,
        "scrape_time_s": round(scrape_time, 2),
        "render_time_s": round(render_time, 2),
        "file_size_bytes": len(img),
        "scraped_data": {
            "title": data.get("title"),
            "headers": data.get("headers", [])[:3],
            "fonts": data.get("styling", {}).get("fonts", []),
            "colors": pick_colors(data.get("styling", {})),
        },
    }
    summary_path = OUTPUT_DIR / "comparison_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    logger.info("Done!")


if __name__ == "__main__":
    asyncio.run(main())
