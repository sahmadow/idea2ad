"""Render review_static_competition creative using blog + Reddit templates + Gemini copy.

Usage:
    python scripts/test_competition_creative.py                          # generic competition
    python scripts/test_competition_creative.py journeylauncher.com      # targeted competitor
"""

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.v2.social_templates.reddit_post import RedditPostParams, render_reddit_post
from app.services.v2.social_templates.blog_review import BlogReviewParams, render_blog_review
from app.services.v2.copy_generator import generate_competition_copy
from app.services.v2.ad_type_registry import get_ad_type
from app.schemas.creative_params import CreativeParameters

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    t0 = time.time()

    # Optional competitor URL from CLI arg
    competitor_url = sys.argv[1] if len(sys.argv) > 1 else None
    if competitor_url and not competitor_url.startswith("http"):
        competitor_url = f"https://{competitor_url}"

    # Load params from last analysis
    params_path = Path(__file__).resolve().parent.parent / "data" / "last_params.json"
    if params_path.exists():
        print(f"Loading params from {params_path}")
        params = CreativeParameters(**json.loads(params_path.read_text()))
    else:
        print("Using hardcoded peec.ai params")
        params = CreativeParameters(
            product_name="Peec AI",
            product_description_short="AI search analytics for marketing teams",
            product_category="AI search analytics",
            key_benefit="Understand and improve your brand's performance in AI search",
            key_differentiator="Tracks visibility across ChatGPT, Perplexity, Claude, and Gemini",
            social_proof="1500+ marketing teams",
            value_props=["Track AI search visibility", "Monitor brand mentions across LLMs", "Competitor benchmarking"],
            customer_pains=["No visibility into AI search performance", "Competitors dominating AI recommendations"],
            hero_image_url="https://peec.ai/og-image.png",
        )

    # Scrape competitor if provided
    competitor_data = None
    if competitor_url:
        from app.services.scraper import scrape_landing_page
        print(f"Scraping competitor: {competitor_url}")
        competitor_data = await scrape_landing_page(competitor_url)
        print(f"  Scraped: {competitor_data.get('title', '?')} ({len(competitor_data.get('full_text', ''))} chars)")

    # Generate competition copy
    ad_type = get_ad_type("review_static_competition")
    mode = "targeted" if competitor_data else "generic"
    print(f"\nGenerating {mode} competition copy for {params.product_name}...")
    comp_copy = await generate_competition_copy(ad_type, params, competitor_data)

    testimonial = comp_copy.get("competition_testimonial", "")
    complaint = comp_copy.get("competitor_complaint", "")
    headline = comp_copy.get("headline", "")

    print(f"  complaint: {complaint}")
    print(f"  testimonial: {testimonial}")
    print(f"  headline: {headline}")

    product_name = params.product_name or "this product"
    category = params.product_category or "tools"

    # Build body text
    body = (
        f"I've been using various {category} for years and honestly "
        f"most of them are terrible. {complaint}.\n\n"
        f"{testimonial}\n\n"
        f"If you're still dealing with {complaint.lower()}, "
        f"just try {product_name}. It's not even close."
    )

    # Render blog review
    blog_params = BlogReviewParams(
        author_name="Sarah Chen",
        author_title="Marketing Lead",
        blog_title=f"Why I switched to {product_name} (and never looked back)",
        body=body,
        read_time="3 min read",
        date="Feb 2026",
        accent_color="#3B82F6",
        claps=284,
    )

    suffix = f"_vs_{competitor_url.split('//')[1].split('/')[0].split('.')[0]}" if competitor_url else ""

    print(f"\nRendering blog review...")
    img = await render_blog_review(blog_params)
    out = OUTPUT_DIR / f"review_static_competition_blog{suffix}.png"
    out.write_bytes(img)
    print(f"  Saved: {out} ({len(img) // 1024}KB)")

    # Render Reddit post
    reddit_params = RedditPostParams(
        username="former_skeptic",
        body=body,
        subreddit=f"r/{category.replace(' ', '').lower()[:20]}",
        upvotes=743,
        comments=89,
        time_ago="4h",
    )

    print(f"Rendering Reddit post...")
    img = await render_reddit_post(reddit_params)
    out = OUTPUT_DIR / f"review_static_competition_reddit{suffix}.png"
    out.write_bytes(img)
    print(f"  Saved: {out} ({len(img) // 1024}KB)")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
