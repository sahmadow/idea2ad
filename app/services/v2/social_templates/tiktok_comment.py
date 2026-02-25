"""
TikTok Comment Template — HTML-to-Image renderer via Playwright.

Generates a pixel-perfect TikTok comment section image (PNG).
Self-contained: inline SVG icons, system fonts, no external dependencies.
"""

import html
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TikTokCommentParams:
    username: str = "user1234"
    body: str = "This is a sample comment"
    likes: int = 1243
    avatar_url: str | None = None
    time_ago: str = "2d"
    replies: int = 23
    is_creator: bool = False
    pinned: bool = False


def _format_count(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _build_html(params: TikTokCommentParams) -> str:
    # TikTok comments are always dark
    bg = "#121212"
    card_bg = "#1E1E1E"
    text_primary = "#FFFFFF"
    text_secondary = "rgba(255,255,255,0.5)"
    like_color = "rgba(255,255,255,0.5)"
    creator_badge_bg = "rgba(254,44,85,0.15)"
    creator_badge_color = "#FE2C55"
    pinned_color = "rgba(255,255,255,0.4)"

    username = html.escape(params.username)
    body = html.escape(params.body)
    time_ago = html.escape(params.time_ago)
    likes_str = _format_count(params.likes)
    replies_str = _format_count(params.replies)

    if params.avatar_url:
        avatar_html = f'<img src="{html.escape(params.avatar_url)}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" />'
    else:
        avatar_html = """<svg viewBox="0 0 48 48" width="48" height="48" xmlns="http://www.w3.org/2000/svg">
            <circle cx="24" cy="24" r="24" fill="#333"/>
            <circle cx="24" cy="18" r="8" fill="#666"/>
            <ellipse cx="24" cy="38" rx="14" ry="12" fill="#666"/>
        </svg>"""

    heart_svg = f"""<svg viewBox="0 0 24 24" width="18" height="18" fill="{like_color}">
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
    </svg>"""

    creator_html = ""
    if params.is_creator:
        creator_html = '<span class="creator-badge">Creator</span>'

    pinned_html = ""
    if params.pinned:
        pinned_html = f"""<div class="pinned">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="{pinned_color}">
                <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/>
            </svg>
            <span>Pinned</span>
        </div>"""

    S = 1.5

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

.comment-section {{
    width: 920px;
    background: {card_bg};
    border-radius: {int(16 * S)}px;
    padding: {int(20 * S)}px {int(16 * S)}px;
}}

.section-header {{
    font-size: {int(16 * S)}px;
    font-weight: 700;
    color: {text_primary};
    margin-bottom: {int(20 * S)}px;
    padding-bottom: {int(12 * S)}px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
}}

.section-header .sort {{
    font-size: {int(13 * S)}px;
    font-weight: 400;
    color: {text_secondary};
}}

.comment {{
    display: flex;
    gap: {int(12 * S)}px;
    align-items: flex-start;
}}

.avatar {{
    width: {int(40 * S)}px;
    height: {int(40 * S)}px;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
}}

.avatar svg, .avatar img {{
    width: {int(40 * S)}px;
    height: {int(40 * S)}px;
}}

.comment-content {{
    flex: 1;
    min-width: 0;
}}

.comment-username {{
    font-size: {int(14 * S)}px;
    color: {text_secondary};
    margin-bottom: {int(4 * S)}px;
    display: flex;
    align-items: center;
    gap: {int(6 * S)}px;
}}

.creator-badge {{
    font-size: {int(11 * S)}px;
    background: {creator_badge_bg};
    color: {creator_badge_color};
    padding: 2px {int(6 * S)}px;
    border-radius: {int(3 * S)}px;
    font-weight: 500;
}}

.comment-body {{
    font-size: {int(16 * S)}px;
    line-height: 1.45;
    color: {text_primary};
    margin-bottom: {int(8 * S)}px;
    word-wrap: break-word;
    white-space: pre-wrap;
}}

.comment-meta {{
    display: flex;
    align-items: center;
    gap: {int(16 * S)}px;
    font-size: {int(13 * S)}px;
    color: {text_secondary};
}}

.like-section {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: {int(4 * S)}px;
    margin-left: auto;
    flex-shrink: 0;
    padding-top: {int(8 * S)}px;
}}

.like-section svg {{
    width: {int(22 * S)}px;
    height: {int(22 * S)}px;
}}

.like-count {{
    font-size: {int(12 * S)}px;
    color: {text_secondary};
}}

.pinned {{
    display: flex;
    align-items: center;
    gap: {int(4 * S)}px;
    font-size: {int(12 * S)}px;
    color: {pinned_color};
    margin-bottom: {int(8 * S)}px;
}}

.reply-link {{
    color: {text_secondary};
    font-weight: 500;
}}
</style>
</head>
<body>
    <div class="comment-section">
        <div class="section-header">
            <span>Comments</span>
            <span class="sort">Top comments</span>
        </div>
        {pinned_html}
        <div class="comment">
            <div class="avatar">{avatar_html}</div>
            <div class="comment-content">
                <div class="comment-username">
                    <span>{username}</span>
                    {creator_html}
                    <span>· {time_ago}</span>
                </div>
                <div class="comment-body">{body}</div>
                <div class="comment-meta">
                    <span class="reply-link">Reply</span>
                    <span>View {replies_str} replies</span>
                </div>
            </div>
            <div class="like-section">
                {heart_svg}
                <span class="like-count">{likes_str}</span>
            </div>
        </div>
    </div>
</body>
</html>"""


async def render_tiktok_comment(params: TikTokCommentParams | None = None) -> bytes:
    from playwright.async_api import async_playwright

    if params is None:
        params = TikTokCommentParams()

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

    logger.info(f"TikTok comment rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
