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

    # Headline: use raw scraped headers[0] (exact words from site — native language)
    headers = scraped_data.get("headers", [])
    headline = headers[0] if headers else params.headline or params.product_name
    # Description: scraped meta description (native language) or translated param
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
    body = copy.get("primary_text", f"Genuinely surprised by {params.product_name}. It actually lives up to the hype.")

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

    # For non-English: prefer translated copy headline (fully translated by translate_copy)
    # For English: use pain point from params (already English)
    if params.language and params.language != "en" and copy.get("headline"):
        headline = copy["headline"]
    elif params.customer_pains:
        headline = params.customer_pains[0].rstrip(".!;,")
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

    # Pick testimonial text (testimonials from scraping are already in native language)
    if params.testimonials:
        review_text = params.testimonials[0]
    elif params.social_proof:
        # social_proof is translated by translate_params for non-English
        review_text = params.social_proof
    elif params.key_benefit:
        # key_benefit is translated by translate_params for non-English
        review_text = params.key_benefit
    else:
        review_text = copy.get("primary_text", params.product_name)

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

    # params.headline is from scraping (native language)
    # params.key_benefit is translated by translate_params
    headline = params.headline or params.key_benefit or params.product_name
    # params.product_description_short is translated by translate_params
    subtext = params.subheadline or params.product_description_short or None
    scene_url = params.hero_image_url or ""

    return ServiceHeroParams(
        scene_image_url=scene_url,
        headline=headline,
        subtext=subtext,
        cta_text=params.cta_text if params.cta_text != "Shop Now" else None,
        brand_name=params.brand_name or None,
        text_position="bottom",
        overlay_opacity=0.55,
    )


def bridge_product_centric(
    params: CreativeParameters,
    scraped_data: dict,
    copy: dict,
):
    """Map CreativeParameters + scraped data → ProductCentricParams."""
    from app.services.v2.social_templates.product_centric import ProductCentricParams

    styling = scraped_data.get("styling", {})

    # Colors — same pattern as bridge_branded_static
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
    design_tokens = scraped_data.get("design_tokens", {})
    gradients = design_tokens.get("gradients", [])
    bg_gradient = gradients[0]["raw"] if gradients else None

    # Headline
    headline = copy.get("headline") or params.headline or params.key_benefit or params.product_name

    # Pain point
    pain_point = None
    if params.customer_pains:
        pain_point = params.customer_pains[0].rstrip(".!;,")

    # Product image — first available
    product_image_url = None
    if params.product_images:
        product_image_url = params.product_images[0]
    elif params.hero_image_url:
        product_image_url = params.hero_image_url

    # Button styling
    css_assets = scraped_data.get("css_assets", {})
    btn = css_assets.get("button_styles", {})

    return ProductCentricParams(
        headline=headline,
        pain_point=pain_point,
        subheadline=params.subheadline or params.product_description_short or None,
        cta_text=params.cta_text or "Get Started",
        product_image_url=product_image_url,
        logo_url=params.brand_logo_url,
        bg_color=bg_color,
        bg_gradient=bg_gradient,
        accent_color=accent,
        text_color=text_color,
        btn_bg=btn.get("backgroundColor"),
        btn_color=btn.get("color", "#ffffff"),
        btn_radius=btn.get("borderRadius", design_tokens.get("border_radius", "12px") or "12px"),
    )


def bridge_person_centric(params: CreativeParameters, copy: dict):
    """Map CreativeParameters + copy → PersonCentricParams."""
    from app.services.v2.social_templates.person_centric import PersonCentricParams

    headline = copy.get("headline") or params.headline or params.product_name
    subheadline = params.key_benefit or copy.get("description") or params.product_description_short or None

    # Colors from brand_colors
    bg_color = "#0f172a"
    accent = "#3b82f6"
    if params.brand_colors:
        bc = params.brand_colors
        if bc.primary and bc.primary.lower() not in ("#ffffff", "#f7f7f7", "#fafafa"):
            bg_color = bc.primary
        if bc.accent:
            accent = bc.accent
        elif bc.secondary:
            accent = bc.secondary

    return PersonCentricParams(
        headline=headline,
        subheadline=subheadline,
        cta_text=params.cta_text or "Get Started",
        person_image_bytes=None,  # set later in dispatch after generation
        logo_url=params.brand_logo_url,
        bg_color=bg_color,
        accent_color=accent,
    )


# =====================================================================
# VIDEO BRIDGES (Remotion props — plain dicts, not dataclasses)
# =====================================================================

def bridge_branded_static_video(
    params: CreativeParameters,
    scraped_data: dict,
    copy: dict,
) -> dict:
    """Map scraped design tokens → Remotion BrandedStatic props dict."""
    styling = scraped_data.get("styling", {})

    bgs = styling.get("backgrounds", [])
    accents = styling.get("accents", [])
    texts = styling.get("text", [])

    bg_color = bgs[0] if bgs else "#0f172a"
    accent = accents[0] if accents else "#3b82f6"
    text_color = "#ffffff"
    bg_lower = bg_color.lower()
    if bg_lower.startswith("#f") or bg_lower.startswith("#e") or bg_lower.startswith("#d") or bg_lower.startswith("#c") or bg_lower == "#ffffff":
        text_color = texts[0] if texts else "#1a202c"

    headers = scraped_data.get("headers", [])
    headline = headers[0] if headers else params.headline or params.product_name
    # Scraped description (native lang) or translated param
    description = scraped_data.get("description", "") or params.product_description_short or ""
    brand_name = params.brand_name or ""

    css_assets = scraped_data.get("css_assets", {})
    btn = css_assets.get("button_styles", {})

    return {
        "brandName": brand_name,
        "headline": headline,
        "description": description,
        "ctaText": params.cta_text or "Get Started",
        "bgColor": bg_color,
        "accentColor": accent,
        "textColor": text_color,
        "ctaBgColor": btn.get("backgroundColor"),
        "ctaTextColor": btn.get("color", "#ffffff"),
        "ctaBorderRadius": 12,
    }


def bridge_service_hero_video(
    params: CreativeParameters,
    copy: dict,
) -> dict:
    """Map CreativeParameters → Remotion ServiceHero props dict."""
    # params.headline is scraped (native lang), params.key_benefit is translated
    headline = params.headline or params.key_benefit or params.product_name
    scene_url = params.hero_image_url or ""

    return {
        "sceneImageUrl": scene_url,
        "headline": headline,
        "subtext": params.subheadline or params.product_description_short or None,
        "ctaText": params.cta_text,
        "brandName": params.brand_name or None,
        "accentColor": "#FFFFFF",
    }
