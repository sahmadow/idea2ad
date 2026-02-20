"""Render all social templates with peec.ai examples."""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.v2.social_templates.tweet import TweetParams, render_tweet
from app.services.v2.social_templates.tiktok_comment import TikTokCommentParams, render_tiktok_comment
from app.services.v2.social_templates.instagram_story import InstagramStoryParams, render_instagram_story
from app.services.v2.social_templates.problem_statement import ProblemStatementParams, render_problem_statement
from app.services.v2.social_templates.review_static import ReviewStaticParams, render_review_static
from app.services.v2.social_templates.reddit_post import RedditPostParams, render_reddit_post

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    t0 = time.time()

    renders = {
        # 1. Tweet
        "tweet_peec.png": render_tweet(TweetParams(
            display_name="Peec AI",
            handle="peec_ai",
            body=(
                "Your brand gets mentioned 4x more in ChatGPT than you think.\n\n"
                "But your competitors get mentioned 10x more.\n\n"
                "We built Peec to track exactly this — AI search visibility "
                "across ChatGPT, Perplexity, Claude, and Gemini.\n\n"
                "Stop guessing. Start measuring."
            ),
            verified=True,
            likes=847,
            retweets=213,
            replies=64,
            views=52300,
            time_ago="5h",
        )),

        # 2. TikTok Comment
        "tiktok_comment_peec.png": render_tiktok_comment(TikTokCommentParams(
            username="marketingmaya",
            body=(
                "just discovered peec.ai and I can finally see how often "
                "my brand shows up in AI search results. we were basically "
                "invisible on Perplexity and didn't even know 😭"
            ),
            likes=2841,
            time_ago="1d",
            replies=47,
            pinned=True,
        )),

        # 3. Instagram Story
        "ig_story_peec.png": render_instagram_story(InstagramStoryParams(
            username="peec.ai",
            body=(
                "POV: you finally check how your brand "
                "ranks in AI search results\n\n"
                "...and realize your competitors have "
                "been dominating ChatGPT mentions for months"
            ),
            bg_gradient="linear-gradient(135deg, #0F172A 0%, #1E40AF 50%, #7C3AED 100%)",
            verified=True,
            sticker_emoji=None,
            time_ago="3h",
        )),

        # 4. Problem Statement
        "problem_statement_peec.png": render_problem_statement(ProblemStatementParams(
            headline="Your brand is invisible in AI search results.",
            subtext=(
                "ChatGPT, Perplexity, and Claude are answering millions of queries "
                "about your industry every day. And they're recommending your competitors."
            ),
            bg_color="#0F172A",
            text_color="#FFFFFF",
            accent_color="#3B82F6",
        )),

        # 5. Review Static
        "review_static_peec.png": render_review_static(ReviewStaticParams(
            reviewer_name="James Chen",
            review_text=(
                "We had no idea how often our brand was being mentioned (or not mentioned) "
                "in AI search results. Peec showed us we were invisible on Perplexity "
                "while our main competitor was getting recommended in 73% of relevant queries.\n\n"
                "Within 2 months of optimizing based on Peec's insights, our AI visibility "
                "score went from 12 to 67. Essential tool for any marketing team."
            ),
            rating=5,
            product_name="Peec AI",
            reviewer_title="VP Marketing, SaaS Company",
            verified=True,
            accent_color="#3B82F6",
        )),

        # 6. Reddit Post (existing)
        "reddit_post_peec.png": render_reddit_post(RedditPostParams(
            username="growth_marketer",
            body=(
                "PSA: Your competitors are optimizing for AI search and you probably don't "
                "even know it.\n\n"
                "I just ran our brand through peec.ai and found out that ChatGPT recommends "
                "our top competitor in 8 out of 10 queries about our category. We show up in "
                "exactly zero.\n\n"
                "The tool tracks your brand's visibility across ChatGPT, Perplexity, Claude, "
                "and Gemini. Free tier lets you check basic metrics. Been using the paid plan "
                "for a month and it's become our most-checked dashboard after GA4."
            ),
            subreddit="r/marketing",
            upvotes=892,
            comments=127,
            time_ago="6h",
        )),
    }

    for filename, coro in renders.items():
        img = await coro
        out = OUTPUT_DIR / filename
        out.write_bytes(img)
        print(f"  {filename}: {len(img) // 1024}KB")

    elapsed = time.time() - t0
    print(f"\nAll 6 templates rendered in {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
