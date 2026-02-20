"""Quick test: render a sample Reddit post and save to scripts/output/."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.v2.social_templates.reddit_post import (
    RedditPostParams,
    render_reddit_post,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    # Light mode
    light = RedditPostParams(
        username="startup_founder",
        body=(
            "Just launched our AI-powered ad creative tool and hit 1,000 users in "
            "the first week. We scrape your landing page, extract brand colors/fonts, "
            "and generate scroll-stopping ad creatives in seconds.\n\n"
            "No design skills needed. The whole process takes under 30 seconds.\n\n"
            "Would love feedback from the community!"
        ),
        subreddit="r/SaaS",
        upvotes=1247,
        comments=183,
        time_ago="4h",
    )
    img = await render_reddit_post(light)
    out = OUTPUT_DIR / "reddit_post_light.png"
    out.write_bytes(img)
    print(f"Light: {out} ({len(img) // 1024}KB)")

    # Dark mode
    dark = RedditPostParams(
        username="tech_enthusiast",
        body=(
            "I've been testing every AI ad generator on the market for the past month. "
            "Most of them produce generic templates that look nothing like your brand.\n\n"
            "Found one that actually scrapes your site and matches your exact design system. "
            "Game changer for small teams without a designer."
        ),
        subreddit="r/technology",
        upvotes=3892,
        comments=412,
        dark_mode=True,
        time_ago="8h",
    )
    img = await render_reddit_post(dark)
    out = OUTPUT_DIR / "reddit_post_dark.png"
    out.write_bytes(img)
    print(f"Dark: {out} ({len(img) // 1024}KB)")


if __name__ == "__main__":
    asyncio.run(main())
