"""
Ad Type Registry — 6 approved static creative types for V2 pipeline.

Each type dispatches to a dedicated HTML+Playwright social template renderer.
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
            "PSA: {product_name} actually lives up to the hype. "
            "{key_benefit}. Worth trying if you deal with {customer_pains[0]}."
        ),
        headline="{product_name}",
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
        cta_type="LEARN_MORE",
        fallbacks={"headline": "{product_name}", "key_benefit": ""},
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
}


def get_registry() -> dict[str, AdTypeDefinition]:
    """Return the full ad type registry."""
    return AD_TYPE_REGISTRY


def get_ad_type(ad_type_id: str) -> AdTypeDefinition | None:
    """Look up a single ad type by ID."""
    return AD_TYPE_REGISTRY.get(ad_type_id)
