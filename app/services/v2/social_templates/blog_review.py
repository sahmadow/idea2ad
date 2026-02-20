"""
Blog Review Template — HTML-to-Image renderer via Playwright.

Generates a pixel-perfect blog post / article card image (PNG).
Looks like a real blog review snippet — author avatar, title, body, read time.
Self-contained: inline SVG, system fonts, no external dependencies.
"""

import html
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BlogReviewParams:
    author_name: str = "Sarah Chen"
    author_title: str | None = None  # e.g. "Marketing Lead"
    blog_title: str = "Why I finally switched"
    body: str = "This is a sample blog review."
    read_time: str = "3 min read"
    date: str = "Feb 2026"
    publication: str | None = None  # e.g. "Medium", "Substack"
    avatar_url: str | None = None
    accent_color: str = "#3B82F6"
    dark_mode: bool = False
    show_claps: bool = True
    claps: int = 284
    show_bookmark: bool = True


def _build_html(params: BlogReviewParams) -> str:
    dark = params.dark_mode

    bg = "#121212" if dark else "#F5F5F5"
    card_bg = "#1C1C1E" if dark else "#FFFFFF"
    text_primary = "#FFFFFF" if dark else "#1A1A1A"
    text_secondary = "#999" if dark else "#6B6B6B"
    text_body = "#E0E0E0" if dark else "#333333"
    border_color = "#333" if dark else "#E8E8E8"
    accent = params.accent_color
    author_name = html.escape(params.author_name)
    blog_title = html.escape(params.blog_title)
    body = html.escape(params.body)
    read_time = html.escape(params.read_time)
    date = html.escape(params.date)

    # Avatar — initials fallback
    if params.avatar_url:
        avatar_html = f'<img src="{html.escape(params.avatar_url)}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" />'
    else:
        initials = "".join(w[0].upper() for w in params.author_name.split()[:2])
        avatar_html = f"""<div style="width:100%;height:100%;border-radius:50%;background:{accent};display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;color:#FFFFFF;letter-spacing:1px;">{html.escape(initials)}</div>"""

    # Publication badge
    pub_html = ""
    if params.publication:
        pub_html = f"""<div class="publication-badge">
            <span class="pub-icon">&#9679;</span>
            <span>Published in <strong>{html.escape(params.publication)}</strong></span>
        </div>"""

    # Clap / like bar
    clap_svg = f"""<svg viewBox="0 0 24 24" width="22" height="22" fill="{text_secondary}">
        <path d="M11.37 2.07a1.5 1.5 0 0 1 1.26 0l.09.05 5.3 3.2a1.5 1.5 0 0 1 .72 1.03l.02.1.94 6.13a1.5 1.5 0 0 1-.3 1.2l-.07.08-4.37 4.37a1.5 1.5 0 0 1-.97.43h-.13l-6.13-.94a1.5 1.5 0 0 1-1.1-.7l-.05-.1-3.2-5.3a1.5 1.5 0 0 1-.04-1.3l.05-.1 3.5-5.5a1.5 1.5 0 0 1 .98-.65l.1-.01 3.4-.28z"/>
    </svg>"""

    bookmark_svg = f"""<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="{text_secondary}" stroke-width="1.5">
        <path d="M17 3H7a2 2 0 0 0-2 2v16l7-3 7 3V5a2 2 0 0 0-2-2z"/>
    </svg>"""

    actions_html = ""
    parts = []
    if params.show_claps:
        parts.append(f"""<div class="action-item">
            {clap_svg}
            <span>{params.claps}</span>
        </div>""")
    if params.show_bookmark:
        parts.append(f"""<div class="action-item action-right">
            {bookmark_svg}
        </div>""")
    if parts:
        actions_html = f'<div class="action-bar">{"".join(parts)}</div>'

    # Author title
    author_title_html = ""
    if params.author_title:
        author_title_html = f' · <span class="author-role">{html.escape(params.author_title)}</span>'

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
    font-family: Georgia, 'Times New Roman', 'Noto Serif', serif;
    overflow: hidden;
}}

.blog-card {{
    width: 900px;
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: {int(12 * S)}px;
    overflow: hidden;
}}

.accent-bar {{
    height: 5px;
    background: {accent};
}}

.card-inner {{
    padding: {int(36 * S)}px {int(32 * S)}px {int(28 * S)}px;
}}

/* Author row */
.author-row {{
    display: flex;
    align-items: center;
    gap: {int(12 * S)}px;
    margin-bottom: {int(20 * S)}px;
}}

.author-avatar {{
    width: {int(44 * S)}px;
    height: {int(44 * S)}px;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
}}

.author-meta {{
    flex: 1;
}}

.author-name {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: {int(15 * S)}px;
    font-weight: 600;
    color: {text_primary};
    line-height: 1.3;
}}

.author-role {{
    color: {text_secondary};
    font-weight: 400;
}}

.author-date {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: {int(12 * S)}px;
    color: {text_secondary};
    margin-top: 3px;
}}

/* Publication badge */
.publication-badge {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: {int(12 * S)}px;
    color: {text_secondary};
    margin-bottom: {int(16 * S)}px;
}}

.pub-icon {{
    color: {accent};
    font-size: 8px;
}}

/* Title */
.blog-title {{
    font-size: {int(26 * S)}px;
    font-weight: 700;
    color: {text_primary};
    line-height: 1.3;
    margin-bottom: {int(18 * S)}px;
    letter-spacing: -0.3px;
}}

/* Body */
.blog-body {{
    font-size: {int(16 * S)}px;
    line-height: 1.7;
    color: {text_body};
    margin-bottom: {int(24 * S)}px;
    word-wrap: break-word;
    white-space: pre-wrap;
}}

/* Actions */
.action-bar {{
    display: flex;
    align-items: center;
    gap: {int(8 * S)}px;
    padding-top: {int(16 * S)}px;
    border-top: 1px solid {border_color};
}}

.action-item {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    display: flex;
    align-items: center;
    gap: {int(6 * S)}px;
    font-size: {int(13 * S)}px;
    color: {text_secondary};
}}

.action-right {{
    margin-left: auto;
}}
</style>
</head>
<body>
    <div class="blog-card">
        <div class="accent-bar"></div>
        <div class="card-inner">
            <div class="author-row">
                <div class="author-avatar">{avatar_html}</div>
                <div class="author-meta">
                    <div class="author-name">{author_name}{author_title_html}</div>
                    <div class="author-date">{date} · {read_time}</div>
                </div>
            </div>
            {pub_html}
            <div class="blog-title">{blog_title}</div>
            <div class="blog-body">{body}</div>
            {actions_html}
        </div>
    </div>
</body>
</html>"""


async def render_blog_review(params: BlogReviewParams | None = None) -> bytes:
    """Render blog review card to PNG bytes via Playwright."""
    from playwright.async_api import async_playwright

    if params is None:
        params = BlogReviewParams()

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

    logger.info(f"Blog review rendered: {len(screenshot_bytes) // 1024}KB")
    return screenshot_bytes
