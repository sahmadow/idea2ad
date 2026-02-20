"""
Social Template Bridges — map CreativeParameters + scraped_data to renderer params.

One bridge function per creative type. Each converts the generic pipeline data
into the specific dataclass that the corresponding social template renderer expects.
"""

import logging
import random

from app.schemas.creative_params import CreativeParameters

logger = logging.getLogger(__name__)


def bridge_branded_static(
    params: CreativeParameters,
    scraped_data: dict,
    copy: dict,
):
    """Map scraped design tokens → BrandedStaticParams."""
    from app.services.v2.social_templates.branded_static import BrandedStaticParams

    styling = scraped_data.get("styling", {})
    css_assets = scraped_data.get("css_assets", {})
    design_tokens = scraped_data.get("design_tokens", {})

    # Colors
    bgs = styling.get("backgrounds", [])
    accents = styling.get("accents", [])
    texts = styling.get("text", [])

    bg_color = bgs[0] if bgs else "#0f172a"
    accent = accents[0] if accents else "#3b82f6"
    text_color = "#ffffff"
    bg_lower = bg_color.lower()
    if bg_lower.startswith("#f") or bg_lower.startswith("#e") or bg_lower.startswith("#d") or bg_lower.startswith("#c") or bg_lower == "#ffffff":
        text_color = texts[0] if texts else "#1a202c"

    # Gradient or solid
    gradients = design_tokens.get("gradients", [])
    bg_gradient = gradients[0]["raw"] if gradients else None

    # Fonts
    fonts = styling.get("fonts", ["Inter"])
    font_family = fonts[0] if fonts else "Inter"

    # Font-face CSS
    font_faces = "\n".join(css_assets.get("font_faces", []))

    # Button styling
    btn = css_assets.get("button_styles", {})
    border_radius = design_tokens.get("border_radius", "12px") or "12px"

    # Headline: use raw scraped headers[0] (exact words from site)
    headers = scraped_data.get("headers", [])
    headline = headers[0] if headers else params.headline or params.product_name
    description = scraped_data.get("description", "") or params.product_description_short or ""
    brand_name = params.brand_name or ""

    return BrandedStaticParams(
        headline=headline,
        description=description,
        cta_text=params.cta_text or "Get Started",
        brand_name=brand_name,
        bg_color=bg_color,
        bg_gradient=bg_gradient,
        accent_color=accent,
        text_color=text_color,
        font_family=font_family,
        font_faces_css=font_faces,
        btn_bg=btn.get("backgroundColor"),
        btn_color=btn.get("color", "#ffffff"),
        btn_radius=btn.get("borderRadius", border_radius),
        btn_padding=btn.get("padding", "16px 48px"),
        btn_font_weight=btn.get("fontWeight", "600"),
        btn_font_size=btn.get("fontSize", "22px"),
    )


def bridge_reddit(params: CreativeParameters, copy: dict):
    """Map CreativeParameters + copy → RedditPostParams."""
    from app.services.v2.social_templates.reddit_post import RedditPostParams

    # Build post body from copy
    body = copy.get("primary_text", f"PSA: {params.product_name} actually lives up to the hype.")

    # Subreddit based on category
    category = params.product_category or "technology"
    subreddit_map = {
        "skincare": "r/SkincareAddiction",
        "fitness": "r/fitness",
        "saas": "r/SaaS",
        "software": "r/software",
        "health": "r/health",
        "food": "r/food",
        "finance": "r/personalfinance",
    }
    subreddit = subreddit_map.get(category.lower(), f"r/{category}")

    return RedditPostParams(
        username=f"honest_reviewer_{random.randint(10, 99)}",
        body=body,
        subreddit=subreddit,
        upvotes=random.randint(150, 800),
        comments=random.randint(20, 120),
        dark_mode=False,
        time_ago=f"{random.randint(2, 12)}h",
    )


def bridge_problem_statement(params: CreativeParameters, copy: dict):
    """Map CreativeParameters → ProblemStatementParams."""
    from app.services.v2.social_templates.problem_statement import ProblemStatementParams

    # Headline from pains or copy
    if params.customer_pains:
        headline = params.customer_pains[0]
        if not headline.endswith("?"):
            headline += "?"
    else:
        headline = copy.get("headline", "There's a better way")

    # Background from brand colors
    bg_color = "#1A202C"
    if params.brand_colors and params.brand_colors.primary:
        bc = params.brand_colors.primary
        if bc.lower() not in ("#ffffff", "#f7f7f7", "#fafafa", "#000000"):
            bg_color = bc

    return ProblemStatementParams(
        headline=headline,
        bg_color=bg_color,
        text_color="#FFFFFF",
        font_style="bold",
        alignment="center",
    )


def bridge_review_static(params: CreativeParameters, copy: dict):
    """Map CreativeParameters → ReviewStaticParams."""
    from app.services.v2.social_templates.review_static import ReviewStaticParams

    # Pick testimonial text
    if params.testimonials:
        review_text = params.testimonials[0]
    elif params.social_proof:
        review_text = f"Absolutely love this product. {params.social_proof}."
    else:
        review_text = f"The {params.product_name} has completely changed my routine. Highly recommend!"

    # Accent color (skip near-white)
    accent = "#FF6B35"
    if params.brand_colors:
        bc = params.brand_colors
        for c in [bc.secondary, bc.accent, bc.primary]:
            if c and c.startswith("#") and c.lower() not in ("#ffffff", "#f7f7f7", "#fafafa"):
                accent = c
                break

    reviewer_names = ["Sarah K.", "Mike R.", "Jessica L.", "David M.", "Emma T."]

    return ReviewStaticParams(
        reviewer_name=random.choice(reviewer_names),
        review_text=review_text,
        rating=5,
        product_name=params.product_name,
        variant="card",
        verified=True,
        accent_color=accent,
    )


def bridge_service_hero(params: CreativeParameters, copy: dict):
    """Map CreativeParameters → ServiceHeroParams."""
    from app.services.v2.social_templates.service_hero import ServiceHeroParams

    headline = params.headline or params.key_benefit or params.product_name
    scene_url = params.hero_image_url or ""

    return ServiceHeroParams(
        scene_image_url=scene_url,
        headline=headline,
        subtext=params.subheadline or params.product_description_short or None,
        cta_text=params.cta_text if params.cta_text != "Shop Now" else None,
        brand_name=params.brand_name or None,
        text_position="bottom",
        overlay_opacity=0.55,
    )
