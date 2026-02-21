"""
Ad Type Registry — 6 approved static + 2 video creative types for V2 pipeline.

Static types dispatch to HTML+Playwright social template renderers.
Video types dispatch to Remotion server-side rendering (MP4).
Layers are empty — rendering is handled by social_template_bridges + renderers.
"""

from app.schemas.ad_types import (
    AdTypeDefinition,
    CopyTemplate,
)


# =====================================================================
# 6 APPROVED STATIC TYPES
# =====================================================================

BRANDED_STATIC = AdTypeDefinition(
    id="branded_static",
    name="Branded Static",
    strategy="product_aware",
    format="static",
    aspect_ratios=["1:1"],
    required_params=["product_name"],
    optional_params=["brand_colors", "brand_fonts", "headline", "product_description_short"],
    skip_condition=None,  # always generate — uses scraped design tokens
    layers=[],  # rendered by social_templates/branded_static.py
    copy_templates=CopyTemplate(
        primary_text="{headline}\n\n{product_description_short}",
        headline="{headline}",
        description="{product_description_short}",
        cta_type="LEARN_MORE",
        fallbacks={"headline": "{product_name}", "product_description_short": ""},
    ),
)

ORGANIC_STATIC_REDDIT = AdTypeDefinition(
    id="organic_static_reddit",
    name="Organic Static (Reddit)",
    strategy="product_unaware",
    format="static",
    aspect_ratios=["1:1"],
    required_params=["product_name"],
    optional_params=["customer_pains", "key_benefit", "product_category"],
    skip_condition=None,  # always generate
    layers=[],  # rendered by social_templates/reddit_post.py
    copy_templates=CopyTemplate(
        primary_text=(
            "Genuinely surprised by {product_name}. "
            "{key_benefit}. If you deal with {customer_pains[0]}, check it out."
        ),
        headline="{product_name}",
        description="{key_benefit}",
        cta_type="LEARN_MORE",
        fallbacks={
            "key_benefit": "It actually works",
            "customer_pains[0]": "the usual problems",
        },
    ),
)

PROBLEM_STATEMENT_TEXT = AdTypeDefinition(
    id="problem_statement_text",
    name="Problem Statement — Plain Text",
    strategy="product_unaware",
    format="static",
    aspect_ratios=["1:1"],
    required_params=["product_name"],
    optional_params=["customer_pains", "brand_colors", "key_benefit"],
    skip_condition=None,  # always generate
    layers=[],  # rendered by social_templates/problem_statement.py
    copy_templates=CopyTemplate(
        primary_text=(
            "{customer_pains[0]}?\n"
            "It's more common than you think.\n"
            "{product_name} was built to fix exactly this. →"
        ),
        headline="{key_benefit}",
        description="{product_name} — built for this",
        cta_type="LEARN_MORE",
        fallbacks={
            "key_benefit": "There's a better way",
            "customer_pains[0]": "Your biggest problem",
        },
    ),
)

REVIEW_STATIC = AdTypeDefinition(
    id="review_static",
    name="Review Static",
    strategy="product_aware",
    format="static",
    aspect_ratios=["1:1"],
    required_params=["product_name"],
    optional_params=["social_proof", "testimonials", "brand_colors"],
    skip_condition="!social_proof AND len(testimonials) == 0",
    layers=[],  # rendered by social_templates/review_static.py
    copy_templates=CopyTemplate(
        primary_text="This is why {social_proof} people switched to {product_name} 👇",
        headline="See why customers love it",
        description="Real reviews from real customers",
        cta_type="LEARN_MORE",
        fallbacks={"social_proof": "thousands of"},
    ),
)

REVIEW_STATIC_COMPETITION = AdTypeDefinition(
    id="review_static_competition",
    name="Review Static (Competition)",
    strategy="product_aware",
    format="static",
    aspect_ratios=["1:1"],
    required_params=["product_name"],
    optional_params=["social_proof", "testimonials", "brand_colors", "product_category"],
    skip_condition="!social_proof AND len(testimonials) == 0",
    external_deps=["competitor_intelligence"],
    layers=[],  # rendered by social_templates/blog_review.py (already integrated)
    copy_templates=CopyTemplate(
        primary_text="Tired of {competitor_complaint}? {social_proof} people already switched to {product_name}",
        headline="Try {product_name} instead",
        description="See why people are switching",
        cta_type="LEARN_MORE",
        fallbacks={
            "social_proof": "thousands of",
            "competitor_complaint": "the same old problems",
        },
    ),
)

SERVICE_HERO = AdTypeDefinition(
    id="service_hero",
    name="Service Hero",
    strategy="product_aware",
    format="static",
    aspect_ratios=["1:1"],
    required_params=["product_name", "hero_image_url"],
    optional_params=["headline", "brand_name", "key_benefit"],
    skip_condition=None,  # gated by selector: only if hero_image_url exists
    layers=[],  # rendered by social_templates/service_hero.py
    copy_templates=CopyTemplate(
        primary_text="{key_benefit}\n\n{product_name} →",
        headline="{headline}",
        description="{product_description_short}",
        cta_type="LEARN_MORE",
        fallbacks={"headline": "{product_name}", "key_benefit": "", "product_description_short": ""},
    ),
)


# =====================================================================
# 2 VIDEO TYPES (Remotion-rendered)
# =====================================================================

BRANDED_STATIC_VIDEO = AdTypeDefinition(
    id="branded_static_video",
    name="Branded Video",
    strategy="product_aware",
    format="video",
    aspect_ratios=["1:1"],
    required_params=["product_name"],
    optional_params=["brand_colors", "brand_fonts", "headline", "product_description_short"],
    skip_condition=None,  # always generate — video version of branded_static
    layers=[],  # rendered by Remotion (BrandedStatic composition)
    copy_templates=CopyTemplate(
        primary_text="{headline}\n\n{product_description_short}",
        headline="{headline}",
        description="{product_description_short}",
        cta_type="LEARN_MORE",
        fallbacks={"headline": "{product_name}", "product_description_short": ""},
    ),
)

SERVICE_HERO_VIDEO = AdTypeDefinition(
    id="service_hero_video",
    name="Service Hero Video",
    strategy="product_aware",
    format="video",
    aspect_ratios=["1:1"],
    required_params=["product_name", "hero_image_url"],
    optional_params=["headline", "brand_name", "key_benefit"],
    skip_condition=None,  # gated by selector: only if hero_image_url exists
    layers=[],  # rendered by Remotion (ServiceHero composition)
    copy_templates=CopyTemplate(
        primary_text="{key_benefit}\n\n{product_name} →",
        headline="{headline}",
        description="{product_description_short}",
        cta_type="LEARN_MORE",
        fallbacks={"headline": "{product_name}", "key_benefit": "", "product_description_short": ""},
    ),
)


# =====================================================================
# FULL REGISTRY
# =====================================================================

AD_TYPE_REGISTRY: dict[str, AdTypeDefinition] = {
    "branded_static": BRANDED_STATIC,
    "organic_static_reddit": ORGANIC_STATIC_REDDIT,
    "problem_statement_text": PROBLEM_STATEMENT_TEXT,
    "review_static": REVIEW_STATIC,
    "review_static_competition": REVIEW_STATIC_COMPETITION,
    "service_hero": SERVICE_HERO,
    "branded_static_video": BRANDED_STATIC_VIDEO,
    "service_hero_video": SERVICE_HERO_VIDEO,
}


def get_registry() -> dict[str, AdTypeDefinition]:
    """Return the full ad type registry."""
    return AD_TYPE_REGISTRY


def get_ad_type(ad_type_id: str) -> AdTypeDefinition | None:
    """Look up a single ad type by ID."""
    return AD_TYPE_REGISTRY.get(ad_type_id)
