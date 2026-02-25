"""
Instagram Story Template — HTML-to-Image renderer via Playwright.

Generates a pixel-perfect Instagram Story image (PNG) at 1080x1080.
Self-contained: inline SVG, system fonts, no external dependencies.
"""

import html
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InstagramStoryParams:
    username: str = "user_name"
    body: str = "This changed everything for me"
    avatar_url: str | None = None
    bg_gradient: str | None = None  # CSS gradient, e.g. "linear-gradient(...)"
    bg_color: str = "#833AB4"       # fallback solid color
    sticker_emoji: str | None = None  # optional emoji sticker
    time_ago: str = "2h"
    verified: bool = False
    show_reply_bar: bool = True


def _build_html(params: InstagramStoryParams) -> str:
    username = html.escape(params.username)
    body = html.escape(params.body)
    time_ago = html.escape(params.time_ago)

    bg_style = params.bg_gradient or params.bg_color

    if params.avatar_url:
        avatar_html = f'<img src="{html.escape(params.avatar_url)}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" />'
    else:
        avatar_html = """<svg viewBox="0 0 48 48" width="48" height="48" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="ig-grad" x1="0%" y1="100%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="#FEDA75"/>
                    <stop offset="25%" stop-color="#FA7E1E"/>
                    <stop offset="50%" stop-color="#D62976"/>
                    <stop offset="75%" stop-color="#962FBF"/>
                    <stop offset="100%" stop-color="#4F5BD5"/>
                </linearGradient>
            </defs>
            <circle cx="24" cy="24" r="23" fill="none" stroke="url(#ig-grad)" stroke-width="2.5"/>
            <circle cx="24" cy="24" r="20" fill="#333"/>
            <circle cx="24" cy="18" r="7" fill="#888"/>
            <ellipse cx="24" cy="36" rx="12" ry="10" fill="#888"/>
        </svg>"""

    verified_svg = ""
    if params.verified:
        verified_svg = """<svg viewBox="0 0 40 40" width="16" height="16" style="margin-left:4px;vertical-align:middle;">
            <circle cx="20" cy="20" r="20" fill="#3897F0"/>
            <path d="M17.5 28l-6-6 2.12-2.12L17.5 23.76l8.88-8.88L28.5 17z" fill="#FFFFFF"/>
        </svg>"""

    sticker_html = ""
    if params.sticker_emoji:
        sticker_html = f'<div class="sticker">{html.escape(params.sticker_emoji)}</div>'

    reply_html = ""
    if params.show_reply_bar:
        reply_html = """<div class="reply-bar">
            <div class="reply-input">Send message</div>
            <div class="reply-icons">
                <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="#FFFFFF" stroke-width="1.5">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
                <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="#FFFFFF" stroke-width="1.5">
                    <line x1="22" y1="2" x2="11" y2="13"/>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
            </div>
        </div>"""

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
    flex-direction: column;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    overflow: hidden;
    position: relative;
    color: #FFFFFF;
}}

/* Top progress bars */
.progress-bar {{
    display: flex;
    gap: 4px;
    padding: 12px 12px 0;
}}

.progress-seg {{
    flex: 1;
    height: 3px;
    background: rgba(255,255,255,0.35);
    border-radius: 2px;
}}

.progress-seg.active {{
    background: rgba(255,255,255,0.95);
}}

/* Story header */
.story-header {{
    display: flex;
    align-items: center;
    padding: 14px 16px;
    gap: 12px;
}}

.avatar {{
    width: 42px;
    height: 42px;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.avatar svg, .avatar img {{
    width: 42px;
    height: 42px;
}}

.username {{
    font-size: 16px;
    font-weight: 600;
    color: #FFFFFF;
}}

.time-ago {{
    font-size: 14px;
    color: rgba(255,255,255,0.6);
    margin-left: 4px;
}}

.header-actions {{
    margin-left: auto;
    display: flex;
    gap: 16px;
    align-items: center;
}}

/* Main content */
.story-content {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 60px;
    text-align: center;
    position: relative;
}}

.story-text {{
    font-size: 36px;
    font-weight: 700;
    line-height: 1.35;
    color: #FFFFFF;
    text-shadow: 0 2px 12px rgba(0,0,0,0.4);
    word-wrap: break-word;
    white-space: pre-wrap;
    max-width: 900px;
}}

.sticker {{
    position: absolute;
    bottom: 40px;
    right: 60px;
    font-size: 72px;
}}

/* Reply bar */
.reply-bar {{
    display: flex;
    align-items: center;
    padding: 16px 16px 24px;
    gap: 12px;
}}

.reply-input {{
    flex: 1;
    border: 1.5px solid rgba(255,255,255,0.4);
    border-radius: 24px;
    padding: 12px 20px;
    font-size: 16px;
    color: rgba(255,255,255,0.5);
    background: transparent;
}}

.reply-icons {{
    display: flex;
    gap: 12px;
    align-items: center;
}}
</style>
</head>
<body>
    <div class="progress-bar">
        <div class="progress-seg active"></div>
        <div class="progress-seg"></div>
        <div class="progress-seg"></div>
    </div>
    <div class="story-header">
        <div class="avatar">{avatar_html}</div>
        <span class="username">{username}{verified_svg}</span>
        <span class="time-ago">{time_ago}</span>
        <div class="header-actions">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="none">
                <circle cx="12" cy="5" r="2" fill="#FFFFFF"/>
                <circle cx="12" cy="12" r="2" fill="#FFFFFF"/>
                <circle cx="12" cy="19" r="2" fill="#FFFFFF"/>
            </svg>
            <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#FFFFFF" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
        </div>
    </div>
    <div class="story-content">
        <div class="story-text">{body}</div>
        {sticker_html}
    </div>
    {reply_html}
</body>
</html>"""


async def render_instagram_story(params: InstagramStoryParams | None = None) -> bytes:
    from playwright.async_api import async_playwright

    if params is None:
        params = InstagramStoryParams()

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

    logger.info(f"Instagram Story rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
