"""
Reddit Post Template — HTML-to-Image renderer via Playwright.

Generates a pixel-perfect Reddit post image (PNG) from parameters.
Self-contained: inline SVG icons, system fonts, no external dependencies.
"""

import html
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RedditPostParams:
    username: str = "reddit_user"
    body: str = "This is a sample post"
    subreddit: str = "r/technology"
    upvotes: int = 249
    comments: int = 57
    avatar_url: str | None = None
    dark_mode: bool = False
    show_awards: bool = True
    show_share: bool = True
    time_ago: str = "2h"


def _format_count(n: int) -> str:
    """Format number: 1234 -> 1.2k, 999 -> 999."""
    if n >= 100_000:
        return f"{n / 1_000:.0f}k"
    if n >= 10_000:
        return f"{n / 1_000:.1f}k"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def _build_html(params: RedditPostParams) -> str:
    """Build self-contained HTML matching Reddit's post UI."""
    dark = params.dark_mode

    # Color palette
    bg = "#030303" if dark else "#DAE0E6"
    card_bg = "#1A1A1B" if dark else "#FFFFFF"
    border_color = "#343536" if dark else "#EDEFF1"
    text_primary = "#D7DADC" if dark else "#1C1C1C"
    text_secondary = "#818384" if dark else "#787C7E"
    text_link = "#4FBCFF" if dark else "#0079D3"
    icon_color = "#818384" if dark else "#878A8C"
    vote_bar_bg = "#161617" if dark else "#F8F9FA"
    hover_bg = "#2D2D2E" if dark else "#F6F7F8"

    # Escaped content
    username = html.escape(params.username)
    body = html.escape(params.body)
    subreddit = html.escape(params.subreddit)
    time_ago = html.escape(params.time_ago)
    upvote_str = _format_count(params.upvotes)
    comment_str = _format_count(params.comments)

    # Default Snoo avatar (orange circle with white Snoo silhouette)
    if params.avatar_url:
        avatar_html = f'<img src="{html.escape(params.avatar_url)}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" />'
    else:
        avatar_html = f"""<svg viewBox="0 0 40 40" width="40" height="40" xmlns="http://www.w3.org/2000/svg">
            <circle cx="20" cy="20" r="20" fill="#FF4500"/>
            <ellipse cx="20" cy="23" rx="12" ry="10" fill="#FFFFFF"/>
            <circle cx="20" cy="14" r="6" fill="#FFFFFF"/>
            <circle cx="16" cy="22" r="2.5" fill="#FF4500"/>
            <circle cx="24" cy="22" r="2.5" fill="#FF4500"/>
            <ellipse cx="20" cy="27" rx="4" ry="1.5" fill="#FF4500" opacity="0.3"/>
            <line x1="14" y1="18" x2="18" y2="16" stroke="#FF4500" stroke-width="1.5" stroke-linecap="round"/>
            <line x1="22" y1="16" x2="26" y2="18" stroke="#FF4500" stroke-width="1.5" stroke-linecap="round"/>
        </svg>"""

    # SVG icons
    upvote_svg = f"""<svg viewBox="0 0 20 20" width="20" height="20" fill="{icon_color}">
        <path d="M12.877 19H7.123A1.125 1.125 0 0 1 6 17.877V11H2.126a1.114 1.114 0 0 1-1.007-.7 1.249 1.249 0 0 1 .171-1.343L9.166.368a1.128 1.128 0 0 1 1.668.004l7.872 8.581a1.25 1.25 0 0 1 .176 1.348 1.113 1.113 0 0 1-1.005.7H14v6.877A1.125 1.125 0 0 1 12.877 19"/>
    </svg>"""

    downvote_svg = f"""<svg viewBox="0 0 20 20" width="20" height="20" fill="{icon_color}">
        <path d="M7.123 1h5.754A1.125 1.125 0 0 1 14 2.123V9h3.874a1.114 1.114 0 0 1 1.007.7 1.249 1.249 0 0 1-.171 1.343l-7.876 8.589a1.128 1.128 0 0 1-1.668-.004L1.294 11.04a1.25 1.25 0 0 1-.176-1.348A1.113 1.113 0 0 1 2.123 9H6V2.123A1.125 1.125 0 0 1 7.123 1"/>
    </svg>"""

    comment_svg = f"""<svg viewBox="0 0 20 20" width="20" height="20" fill="{icon_color}">
        <path d="M7.725 19.872a.718.718 0 0 1-.607-.328.725.725 0 0 1-.118-.397V16H3.625A2.63 2.63 0 0 1 1 13.375v-9.75A2.629 2.629 0 0 1 3.625 1h12.75A2.63 2.63 0 0 1 19 3.625v9.75A2.63 2.63 0 0 1 16.375 16h-4.161l-4 3.681a.725.725 0 0 1-.489.191z"/>
    </svg>"""

    award_svg = f"""<svg viewBox="0 0 20 20" width="20" height="20" fill="{icon_color}">
        <path d="M10 0a5.44 5.44 0 0 0-5.44 5.44c0 2.537 1.752 4.665 4.107 5.248v3.222l-1.795 1.795a.734.734 0 0 0 .52 1.253h1.275v2.308a.734.734 0 0 0 1.468 0v-2.308h1.275a.734.734 0 0 0 .52-1.253l-1.795-1.795v-3.222c2.355-.583 4.107-2.711 4.107-5.248A5.44 5.44 0 0 0 10 0zm0 9.412a3.973 3.973 0 1 1 0-7.945 3.973 3.973 0 0 1 0 7.945z"/>
    </svg>"""

    share_svg = f"""<svg viewBox="0 0 20 20" width="20" height="20" fill="{icon_color}">
        <path d="M14.5 1C16.433 1 18 2.567 18 4.5S16.433 8 14.5 8c-1.1 0-2.075-.508-2.713-1.3L7.97 8.81A3.48 3.48 0 0 1 8 9.5c0 .233-.023.462-.067.683l3.756 2.13A3.49 3.49 0 0 1 14.5 11c1.933 0 3.5 1.567 3.5 3.5S16.433 18 14.5 18 11 16.433 11 14.5c0-.247.026-.488.074-.72L7.21 11.618A3.49 3.49 0 0 1 4.5 13C2.567 13 1 11.433 1 9.5S2.567 6 4.5 6c1.176 0 2.216.58 2.848 1.47l3.795-2.107A3.488 3.488 0 0 1 11 4.5C11 2.567 12.567 1 14.5 1z"/>
    </svg>"""

    # Optional sections
    awards_html = ""
    if params.show_awards:
        awards_html = f"""<div class="action-item">
            {award_svg}
            <span>Award</span>
        </div>"""

    share_html = ""
    if params.show_share:
        share_html = f"""<div class="action-item">
            {share_svg}
            <span>Share</span>
        </div>"""

    # Scale factor — Reddit's native sizes scaled up for 1080px ad canvas
    S = 1.5  # 1.5x scale for ad readability

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

.post-card {{
    width: 920px;
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: 6px;
    display: flex;
    flex-direction: row;
}}

/* Vote sidebar */
.vote-sidebar {{
    width: {int(56 * S)}px;
    min-width: {int(56 * S)}px;
    background: {vote_bar_bg};
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: {int(16 * S)}px;
    gap: {int(6 * S)}px;
    border-radius: 6px 0 0 6px;
}}

.vote-sidebar svg {{
    width: {int(20 * S)}px;
    height: {int(20 * S)}px;
    flex-shrink: 0;
}}

.vote-count {{
    font-size: {int(13 * S)}px;
    font-weight: 700;
    color: {text_primary};
    text-align: center;
    line-height: 1;
}}

/* Main content */
.post-main {{
    flex: 1;
    padding: {int(12 * S)}px {int(12 * S)}px 0 {int(12 * S)}px;
    min-width: 0;
}}

/* Post meta line */
.post-meta {{
    display: flex;
    align-items: center;
    gap: {int(8 * S)}px;
    margin-bottom: {int(14 * S)}px;
    line-height: 1;
}}

.avatar {{
    width: {int(28 * S)}px;
    height: {int(28 * S)}px;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.avatar svg {{
    width: {int(28 * S)}px;
    height: {int(28 * S)}px;
}}

.subreddit {{
    font-weight: 700;
    color: {text_primary};
    font-size: {int(13 * S)}px;
}}

.meta-sep {{
    color: {text_secondary};
    font-size: {int(8 * S)}px;
}}

.posted-by {{
    color: {text_secondary};
    font-size: {int(12 * S)}px;
}}

/* Post body */
.post-body {{
    font-size: {int(15 * S)}px;
    line-height: 1.55;
    color: {text_primary};
    padding: {int(4 * S)}px 0 {int(16 * S)}px 0;
    word-wrap: break-word;
    white-space: pre-wrap;
}}

/* Action bar */
.action-bar {{
    display: flex;
    align-items: center;
    gap: {int(4 * S)}px;
    padding: {int(6 * S)}px 0 {int(8 * S)}px 0;
    border-top: 1px solid {border_color};
    margin: 0;
}}

.action-item {{
    display: flex;
    align-items: center;
    gap: {int(6 * S)}px;
    padding: {int(8 * S)}px {int(10 * S)}px;
    border-radius: 3px;
    font-size: {int(12 * S)}px;
    font-weight: 700;
    color: {icon_color};
    line-height: 1;
}}

.action-item svg {{
    width: {int(18 * S)}px;
    height: {int(18 * S)}px;
    flex-shrink: 0;
}}

.action-item span {{
    white-space: nowrap;
}}
</style>
</head>
<body>
    <div class="post-card">
        <div class="vote-sidebar">
            {upvote_svg}
            <div class="vote-count">{upvote_str}</div>
            {downvote_svg}
        </div>
        <div class="post-main">
            <div class="post-meta">
                <div class="avatar">{avatar_html}</div>
                <span class="subreddit">{subreddit}</span>
                <span class="meta-sep">•</span>
                <span class="posted-by">Posted by u/{username} {time_ago} ago</span>
            </div>
            <div class="post-body">{body}</div>
            <div class="action-bar">
                <div class="action-item">
                    {comment_svg}
                    <span>{comment_str} Comments</span>
                </div>
                {awards_html}
                {share_html}
            </div>
        </div>
    </div>
</body>
</html>"""


async def render_reddit_post(params: RedditPostParams | None = None) -> bytes:
    """Render Reddit post to PNG bytes via Playwright."""
    from playwright.async_api import async_playwright

    if params is None:
        params = RedditPostParams()

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

    logger.info(f"Reddit post rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
