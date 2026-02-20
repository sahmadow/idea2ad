"""
Tweet Template — HTML-to-Image renderer via Playwright.

Generates a pixel-perfect X/Twitter post image (PNG) from parameters.
Self-contained: inline SVG icons, system fonts, no external dependencies.
"""

import html
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TweetParams:
    display_name: str = "Tech User"
    handle: str = "techuser"
    body: str = "This is a sample tweet"
    verified: bool = False
    likes: int = 142
    retweets: int = 38
    replies: int = 12
    views: int = 14200
    avatar_url: str | None = None
    dark_mode: bool = False
    time_ago: str = "3h"


def _format_count(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _build_html(params: TweetParams) -> str:
    dark = params.dark_mode

    bg = "#000000" if dark else "#F7F9FA"
    card_bg = "#16181C" if dark else "#FFFFFF"
    border_color = "#2F3336" if dark else "#EFF3F4"
    text_primary = "#E7E9EA" if dark else "#0F1419"
    text_secondary = "#71767B" if dark else "#536471"
    icon_color = "#71767B" if dark else "#536471"
    link_color = "#1D9BF0"

    display_name = html.escape(params.display_name)
    handle = html.escape(params.handle)
    body = html.escape(params.body)
    time_ago = html.escape(params.time_ago)

    likes_str = _format_count(params.likes)
    retweets_str = _format_count(params.retweets)
    replies_str = _format_count(params.replies)
    views_str = _format_count(params.views)

    if params.avatar_url:
        avatar_html = f'<img src="{html.escape(params.avatar_url)}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" />'
    else:
        # Default avatar - gray circle with person silhouette
        avatar_html = f"""<svg viewBox="0 0 48 48" width="48" height="48" xmlns="http://www.w3.org/2000/svg">
            <circle cx="24" cy="24" r="24" fill="{link_color}"/>
            <circle cx="24" cy="18" r="8" fill="#FFFFFF"/>
            <ellipse cx="24" cy="38" rx="14" ry="12" fill="#FFFFFF"/>
        </svg>"""

    verified_svg = ""
    if params.verified:
        verified_svg = f"""<svg viewBox="0 0 22 22" width="20" height="20" style="margin-left:2px;flex-shrink:0;">
            <path d="M20.396 11c.396-.868.106-1.976-.896-2.395l-.16-.06c-.986-.378-1.556-1.326-1.326-2.375l.04-.16c.226-1.028-.442-2.014-1.47-2.24l-.16-.03c-1.036-.217-1.768-1.076-1.768-2.133v-.16c0-1.074-.896-1.97-1.97-1.97h-.16c-1.057 0-1.916-.732-2.133-1.768l-.03-.16C10.137.454 9.15-.214 8.123.012l-.16.04c-1.05.23-1.997-.34-2.375-1.326l-.06-.16C5.108-2.43 4-2.72 3.132-2.324l-.16.08c-.868.396-1.416 1.264-1.264 2.264l.02.16c.16 1.024-.426 1.97-1.424 2.33l-.16.06c-.998.36-1.502 1.426-1.126 2.434l.06.16c.372.996-.01 2.08-.926 2.618l-.14.08c-.916.544-1.194 1.7-.618 2.6l.08.14c.538.916.442 2.068-.268 2.862l-.1.12c-.72.792-.68 1.98.08 2.72l.12.1c.794.71.898 1.862.36 2.778l-.08.14c-.576.9-.298 2.056.618 2.6l.14.08c.916.538 1.298 1.622.926 2.618l-.06.16c-.376 1.008.128 2.074 1.126 2.434l.16.06c.998.36 1.584 1.306 1.424 2.33l-.02.16c-.152 1 .396 1.868 1.264 2.264l.16.08c.868.396 1.976.106 2.395-.896l.06-.16c.378-.986 1.326-1.556 2.375-1.326l.16.04c1.028.226 2.014-.442 2.24-1.47l.03-.16c.217-1.036 1.076-1.768 2.133-1.768h.16c1.074 0 1.97-.896 1.97-1.97v-.16c0-1.057.732-1.916 1.768-2.133l.16-.03c1.028-.226 1.696-1.212 1.47-2.24l-.04-.16c-.23-1.05.34-1.997 1.326-2.375l.16-.06c1.002-.42 1.292-1.528.896-2.396" fill="{link_color}"/>
            <path d="M9.585 14.929l-3.28-3.28a1 1 0 0 1 1.414-1.414l2.166 2.166 5.394-5.394a1 1 0 0 1 1.414 1.414l-6.108 6.108a1 1 0 0 1-1.414 0z" fill="#FFFFFF"/>
        </svg>"""

    # SVG icons
    reply_svg = f"""<svg viewBox="0 0 24 24" width="18" height="18" fill="{icon_color}">
        <path d="M1.751 10c0-4.42 3.584-8 8.005-8h4.366c4.49 0 8.129 3.64 8.129 8.13 0 2.25-.893 4.41-2.482 6l-4.67 4.67c-.39.39-1.024.39-1.414 0l-.354-.354a3.28 3.28 0 0 1-.96-2.316v-1.34H8.743C4.937 16.79 1.75 13.803 1.75 10z"/>
    </svg>"""

    retweet_svg = f"""<svg viewBox="0 0 24 24" width="18" height="18" fill="{icon_color}">
        <path d="M4.5 3.88l4.432 4.14-1.364 1.46L5.5 7.55V16c0 1.1.896 2 2 2H13v2H7.5c-2.209 0-4-1.791-4-4V7.55L1.432 9.48.068 8.02 4.5 3.88zM16.5 6H11V4h5.5c2.209 0 4 1.791 4 4v8.45l2.068-1.93 1.364 1.46-4.432 4.14-4.432-4.14 1.364-1.46 2.068 1.93V8c0-1.1-.896-2-2-2z"/>
    </svg>"""

    like_svg = f"""<svg viewBox="0 0 24 24" width="18" height="18" fill="{icon_color}">
        <path d="M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 5.44 7.304 5.5c-1.243.07-2.349.78-2.91 1.91-.552 1.12-.633 2.78.479 4.82 1.074 1.965 3.036 4.14 5.697 6.194.34.262.659.51.96.74.3-.23.619-.478.96-.74 2.66-2.055 4.622-4.23 5.696-6.195 1.112-2.04 1.031-3.7.479-4.82-.561-1.13-1.666-1.84-2.908-1.91z"/>
    </svg>"""

    views_svg = f"""<svg viewBox="0 0 24 24" width="18" height="18" fill="{icon_color}">
        <path d="M8.75 21V3h2v18h-2zM18.75 21V8.5h2V21h-2zM13.75 21v-9h2v9h-2zM3.75 21v-4h2v4h-2z"/>
    </svg>"""

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

.tweet-card {{
    width: 920px;
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: {int(16 * S)}px;
    padding: {int(16 * S)}px;
}}

.tweet-header {{
    display: flex;
    align-items: flex-start;
    gap: {int(10 * S)}px;
    margin-bottom: {int(8 * S)}px;
}}

.avatar {{
    width: {int(40 * S)}px;
    height: {int(40 * S)}px;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.avatar svg, .avatar img {{
    width: {int(40 * S)}px;
    height: {int(40 * S)}px;
}}

.name-col {{
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
    min-width: 0;
}}

.name-row {{
    display: flex;
    align-items: center;
    gap: 4px;
}}

.display-name {{
    font-weight: 700;
    font-size: {int(15 * S)}px;
    color: {text_primary};
    line-height: 1.2;
}}

.handle {{
    font-size: {int(14 * S)}px;
    color: {text_secondary};
    line-height: 1.2;
}}

.x-logo {{
    margin-left: auto;
    flex-shrink: 0;
}}

.tweet-body {{
    font-size: {int(17 * S)}px;
    line-height: 1.45;
    color: {text_primary};
    padding: {int(4 * S)}px 0 {int(12 * S)}px 0;
    word-wrap: break-word;
    white-space: pre-wrap;
}}

.tweet-time {{
    font-size: {int(14 * S)}px;
    color: {text_secondary};
    padding-bottom: {int(12 * S)}px;
    border-bottom: 1px solid {border_color};
    margin-bottom: {int(12 * S)}px;
}}

.tweet-actions {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 {int(8 * S)}px;
}}

.action {{
    display: flex;
    align-items: center;
    gap: {int(6 * S)}px;
    font-size: {int(13 * S)}px;
    color: {icon_color};
}}

.action svg {{
    width: {int(18 * S)}px;
    height: {int(18 * S)}px;
}}
</style>
</head>
<body>
    <div class="tweet-card">
        <div class="tweet-header">
            <div class="avatar">{avatar_html}</div>
            <div class="name-col">
                <div class="name-row">
                    <span class="display-name">{display_name}</span>
                    {verified_svg}
                </div>
                <span class="handle">@{handle}</span>
            </div>
            <div class="x-logo">
                <svg viewBox="0 0 24 24" width="{int(24 * S)}" height="{int(24 * S)}" fill="{text_primary}">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
            </div>
        </div>
        <div class="tweet-body">{body}</div>
        <div class="tweet-time">{time_ago}</div>
        <div class="tweet-actions">
            <div class="action">{reply_svg} <span>{_format_count(params.replies)}</span></div>
            <div class="action">{retweet_svg} <span>{retweets_str}</span></div>
            <div class="action">{like_svg} <span>{likes_str}</span></div>
            <div class="action">{views_svg} <span>{views_str}</span></div>
        </div>
    </div>
</body>
</html>"""


async def render_tweet(params: TweetParams | None = None) -> bytes:
    from playwright.async_api import async_playwright

    if params is None:
        params = TweetParams()

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

    logger.info(f"Tweet rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
