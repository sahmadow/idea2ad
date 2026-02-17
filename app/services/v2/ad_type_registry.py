"""
Ad Type Registry — all 11 ad types as structured, programmable specifications.

Strategy 1 (Product Aware): 6 types
Strategy 2 (Product Unaware): 5 types

Each definition tells the system what data it needs, how to compose the visual,
and how to generate copy — making creative generation fully deterministic.
"""

from app.schemas.ad_types import (
    AdTypeDefinition,
    LayerDefinition,
    CopyTemplate,
    VariantRule,
)


# =====================================================================
# STRATEGY 1: PRODUCT AWARE (Solution-Led)
# =====================================================================

PRODUCT_BENEFITS_STATIC = AdTypeDefinition(
    id="product_benefits_static",
    name="Product Benefits Static",
    strategy="product_aware",
    format="static",
    aspect_ratios=["1:1", "9:16", "1.91:1"],
    required_params=["product_name", "hero_image_url", "key_benefit", "value_props"],
    optional_params=["brand_colors", "brand_fonts", "social_proof", "price"],
    skip_condition=None,  # always generate — workhorse ad
    layers=[
        LayerDefinition(
            type="background",
            source="{brand_colors.primary}",
            style={"fallback": "#1A365D"},
        ),
        LayerDefinition(
            type="product_image",
            source="{hero_image_url}",
            position="center",
            size="large",
            processing=["remove_background", "add_shadow"],
        ),
        LayerDefinition(
            type="text",
            content="{key_benefit}",
            position="top_third",
            style={"size": "large", "font": "{brand_fonts[0]}"},
        ),
        LayerDefinition(
            type="text",
            content="✓ {value_props[0]}",
            position="middle_left",
            style={"size": "medium"},
        ),
        LayerDefinition(
            type="text",
            content="✓ {value_props[1]}",
            position="middle_center",
            style={"size": "medium"},
        ),
        LayerDefinition(
            type="text",
            content="✓ {value_props[2]}",
            position="middle_right",
            style={"size": "medium"},
        ),
        LayerDefinition(
            type="badge",
            content="{price}",
            position="bottom_right",
            condition="price_exists",
            style={"background": "{brand_colors.secondary}"},
        ),
    ],
    copy_templates=CopyTemplate(
        primary_text=(
            "{key_benefit} — here's why {product_name} is different:\n"
            "✓ {value_props[0]}\n"
            "✓ {value_props[1]}\n"
            "✓ {value_props[2]}\n"
            "{social_proof}"
        ),
        headline="{key_benefit}",
        description="{product_description_short}",
        cta_type="SHOP_NOW",
        fallbacks={"social_proof": "", "price": ""},
    ),
    variants=[
        VariantRule(vary="value_props"),
        VariantRule(vary="background", options=["solid_color", "gradient"]),
        VariantRule(vary="copy_angle", options=["benefit_first", "price_first"]),
    ],
)

PRODUCT_DEMO_VIDEO = AdTypeDefinition(
    id="product_demo_video",
    name="Product Demo",
    strategy="product_aware",
    format="video",
    aspect_ratios=["1:1", "9:16"],
    duration="8-15s",
    required_params=[
        "product_name", "hero_image_url", "product_images",
        "key_benefit", "key_differentiator",
    ],
    optional_params=["brand_colors", "brand_fonts", "value_props", "price"],
    skip_condition="len(product_images) < 3",
    frames=[
        {
            "frame": 1, "duration": "2s", "label": "hook",
            "text": "See {product_name} in action",
            "animation": "fade_in",
        },
        {
            "frame": 2, "duration": "3s", "label": "product_shot_1",
            "image_source": "{product_images[0]}",
            "text": "{key_differentiator}",
            "animation": "zoom_in",
        },
        {
            "frame": 3, "duration": "3s", "label": "product_shot_2",
            "image_source": "{product_images[1]}",
            "text": "{key_benefit}",
            "animation": "slide_left",
        },
        {
            "frame": 4, "duration": "2s", "label": "cta",
            "text": "{cta_text}",
            "animation": "pulse_cta",
        },
    ],
    copy_templates=CopyTemplate(
        primary_text=(
            "See why {product_name} is different.\n"
            "{key_differentiator} → {key_benefit}.\n"
            "{cta_text}"
        ),
        headline="{key_benefit}",
        cta_type="SHOP_NOW",
    ),
    variants=[
        VariantRule(vary="product_images"),
        VariantRule(vary="frame_order"),
    ],
)

REVIEW_STATIC = AdTypeDefinition(
    id="review_static",
    name="Review Static",
    strategy="product_aware",
    format="static",
    aspect_ratios=["1:1", "9:16"],
    required_params=["product_name", "hero_image_url", "social_proof"],
    optional_params=["testimonials", "brand_colors"],
    skip_condition="!social_proof AND len(testimonials) == 0",
    layers=[
        LayerDefinition(
            type="review_card",
            style_variant="ios_message|tweet_card|review_card",
            style={
                "author": "{generated_name}",
                "rating": 5,
                "verified": True,
            },
        ),
        LayerDefinition(
            type="product_image",
            source="{hero_image_url}",
            position="bottom_center",
            size="small",
            processing=["remove_background"],
        ),
    ],
    copy_templates=CopyTemplate(
        primary_text="This is why {social_proof} people switched to {product_name} 👇",
        headline="See why customers love it",
        cta_type="LEARN_MORE",
        fallbacks={"social_proof": "thousands of"},
    ),
    variants=[
        VariantRule(vary="style_variant", options=["ios_message", "tweet_card", "review_card"]),
        VariantRule(vary="testimonials"),
        VariantRule(vary="review_tone", options=["skeptic_converted", "enthusiastic", "specific_benefit"]),
    ],
)

US_VS_THEM_SOLUTION = AdTypeDefinition(
    id="us_vs_them_solution",
    name="Us Versus Them (Solution)",
    strategy="product_aware",
    format="static",
    aspect_ratios=["1:1", "9:16"],
    required_params=["product_name", "key_differentiator", "value_props", "hero_image_url"],
    optional_params=["brand_colors", "tone"],
    external_deps=["competitor_intelligence"],
    skip_condition=None,
    layers=[
        LayerDefinition(type="comparison_layout", style={"layout": "split_vertical"}),
        LayerDefinition(
            type="text", content="Others",
            position="left_half_top",
            style={"color": "#999999", "size": "medium"},
        ),
        LayerDefinition(
            type="text",
            content="{competitor_weakness}",
            position="left_half_middle",
            style={"color": "#999999", "strikethrough": True},
        ),
        LayerDefinition(
            type="text", content="{product_name}",
            position="right_half_top",
            style={"color": "{brand_colors.primary}", "bold": True},
        ),
        LayerDefinition(
            type="text", content="{key_differentiator}",
            position="right_half_middle",
            style={"color": "{brand_colors.primary}", "emphasis": True},
        ),
        LayerDefinition(
            type="product_image",
            source="{hero_image_url}",
            position="right_half_bottom",
            size="medium",
            processing=["remove_background"],
        ),
    ],
    copy_templates=CopyTemplate(
        primary_text=(
            "Most {product_category} brands do the same thing.\n"
            "{product_name} is different: {key_differentiator}.\n"
            "{social_proof}"
        ),
        headline="Not like the others",
        cta_type="LEARN_MORE",
        fallbacks={
            "social_proof": "",
            "competitor_weakness": "One-size-fits-all",
        },
    ),
    variants=[
        VariantRule(vary="comparison_points"),
        VariantRule(vary="competitor_data"),
    ],
)

ORGANIC_STATIC_SOLUTION = AdTypeDefinition(
    id="organic_static_solution",
    name="Organic Looking Static (Solution)",
    strategy="product_aware",
    format="static",
    aspect_ratios=["1:1", "9:16"],
    required_params=["product_name", "key_benefit", "hero_image_url"],
    optional_params=["social_proof", "price", "customer_desires"],
    skip_condition=None,
    layers=[
        LayerDefinition(
            type="social_post_frame",
            style_variant="instagram_story|reddit_post|tweet|tiktok_comment",
        ),
        LayerDefinition(
            type="text", content="{organic_hook}",
            position="post_body",
            style={"font": "platform_native", "size": "medium"},
        ),
        LayerDefinition(
            type="product_image",
            source="{hero_image_url}",
            position="post_image",
            size="medium",
            condition="style_variant != reddit_post",
        ),
    ],
    hook_templates={
        "instagram_story": [
            "Just found {product_name} and I'm obsessed 😭",
            "POV: you finally try {product_name}",
            "This is the {product_category} I've been telling everyone about",
        ],
        "reddit_post": [
            "PSA: {product_name} actually lives up to the hype",
            "Anyone else tried {product_name}? Here's my honest take after 2 weeks",
            "Finally found a {product_category} that actually works",
        ],
        "tweet": [
            "hot take: {product_name} is the only {product_category} worth buying",
            "been using {product_name} for a month and it's legit",
        ],
        "tiktok_comment": [
            "the {product_name} is actually life changing no cap",
            "I was today years old when I discovered {product_name}",
        ],
    },
    copy_templates=CopyTemplate(
        primary_text=(
            "{key_benefit}. {social_proof}.\n"
            "Try {product_name} →"
        ),
        headline="{product_name}",
        cta_type="SHOP_NOW",
        fallbacks={"social_proof": "People are catching on"},
    ),
    variants=[
        VariantRule(vary="style_variant", options=["instagram_story", "reddit_post", "tweet", "tiktok_comment"]),
        VariantRule(vary="organic_hook"),
    ],
)

FOUNDER_VIDEO_SOLUTION = AdTypeDefinition(
    id="founder_video_solution",
    name="Founder Video (Solution)",
    strategy="product_aware",
    format="video",
    aspect_ratios=["9:16", "1:1"],
    duration="15-60s",
    required_params=["product_name", "brand_name", "key_benefit", "key_differentiator"],
    optional_params=["value_props", "social_proof", "price"],
    skip_condition=None,  # always generate script
    frames=[
        {
            "frame": 1, "duration": "3s", "label": "hook",
            "text_overlay": "{key_differentiator}",
            "script": "What if I told you {key_benefit} was possible with just one {product_category}?",
        },
        {
            "frame": 2, "duration": "5s", "label": "intro_and_origin",
            "text_overlay": "{key_benefit}",
            "script": (
                "Hey, I'm [Name], founder of {brand_name}. "
                "I built {product_name} because {customer_pains[0]} — "
                "and nothing on the market solved it."
            ),
        },
        {
            "frame": 3, "duration": "5s", "label": "differentiator_and_proof",
            "text_overlay": "{social_proof}",
            "script": (
                "What makes {product_name} different is {key_differentiator}. "
                "{social_proof}."
            ),
        },
        {
            "frame": 4, "duration": "2s", "label": "cta",
            "text_overlay": "{cta_text}",
            "script": "Try it for yourself. Link in bio.",
        },
    ],
    copy_templates=CopyTemplate(
        primary_text=(
            "I built {product_name} because {customer_pains[0]}.\n"
            "Here's what makes it different → {key_differentiator}.\n"
            "{social_proof}"
        ),
        headline="From the founder of {brand_name}",
        cta_type="LEARN_MORE",
        fallbacks={"social_proof": "", "customer_pains[0]": "I saw a gap in the market"},
    ),
    variants=[
        VariantRule(vary="hook", options=["differentiator", "bold_claim", "question"]),
        VariantRule(vary="tone"),
        VariantRule(vary="script_length", options=["15s", "30s", "60s"]),
    ],
)


# =====================================================================
# STRATEGY 2: PRODUCT UNAWARE (Problem-Led)
# =====================================================================

PROBLEM_STATEMENT_TEXT = AdTypeDefinition(
    id="problem_statement_text",
    name="Problem Statement — Plain Text",
    strategy="product_unaware",
    format="static",
    aspect_ratios=["1:1", "9:16"],
    required_params=["customer_pains", "product_name"],
    optional_params=["brand_colors", "key_benefit", "product_description_short"],
    skip_condition=None,  # low data requirement — always generate
    layers=[
        LayerDefinition(
            type="background",
            source="{brand_colors.primary}",
            style={"fallback": "#1A202C"},
        ),
        LayerDefinition(
            type="text",
            content="{problem_hook}",
            position="center",
            size="xlarge",
            style={
                "font": "Inter Bold",
                "color": "#FFFFFF",
                "alignment": "center",
                "max_lines": 3,
            },
        ),
        # NO product image, NO branding — intentionally simple
    ],
    hook_templates={
        "default": [
            "{customer_pains[0]}?",
            "If you deal with {customer_pains[0]}, you're not alone.",
            "{customer_pains[0]} isn't normal.",
            "Stop accepting {customer_pains[0]} as just part of life.",
            "You don't have to live with {customer_pains[0]}.",
        ],
    },
    copy_templates=CopyTemplate(
        primary_text=(
            "{customer_pains[0]}?\n"
            "It's more common than you think.\n"
            "{product_name} was built to fix exactly this. →"
        ),
        headline="{key_benefit}",
        cta_type="LEARN_MORE",
        fallbacks={"key_benefit": "There's a better way"},
    ),
    variants=[
        VariantRule(vary="customer_pains"),
        VariantRule(vary="problem_hook"),
        VariantRule(vary="background"),
    ],
)

PROBLEM_STATEMENT_IMAGE = AdTypeDefinition(
    id="problem_statement_image",
    name="Problem Statement — Image",
    strategy="product_unaware",
    format="static",
    aspect_ratios=["1:1", "9:16"],
    required_params=["customer_pains", "scene_problem", "product_name"],
    optional_params=["brand_colors", "key_benefit"],
    skip_condition=None,
    layers=[
        LayerDefinition(
            type="scene_image",
            source="{scene_problem}",
            position="full",
            processing=["slight_darken_overlay"],
        ),
        LayerDefinition(
            type="text",
            content="{problem_hook}",
            position="top_third",
            style={
                "font": "Inter Bold",
                "size": "large",
                "color": "#FFFFFF",
                "text_shadow": True,
            },
        ),
        # NO product image
    ],
    hook_templates={
        "default": [
            "Tired of {customer_pains[0]}?",
            "This is what {customer_pains[0]} looks like.",
            "Sound familiar?",
            "Every. Single. Morning.",
        ],
    },
    copy_templates=CopyTemplate(
        primary_text=(
            "{customer_pains[0]} affects more people than you'd think.\n"
            "And most solutions don't actually work.\n"
            "{product_name} was designed to change that. →"
        ),
        headline="{key_benefit}",
        cta_type="LEARN_MORE",
        fallbacks={"key_benefit": "There's a fix for this"},
    ),
    variants=[
        VariantRule(vary="scene_problem"),
        VariantRule(vary="problem_hook"),
        VariantRule(vary="customer_pains"),
    ],
)

FOUNDER_VIDEO_PROBLEM = AdTypeDefinition(
    id="founder_video_problem",
    name="Founder Video (Problem)",
    strategy="product_unaware",
    format="video",
    aspect_ratios=["9:16", "1:1"],
    duration="15-60s",
    required_params=["product_name", "brand_name", "customer_pains", "key_benefit"],
    optional_params=["customer_desires", "key_differentiator", "objections"],
    skip_condition=None,
    frames=[
        {
            "frame": 1, "duration": "3s", "label": "hook",
            "text_overlay": "{customer_pains[0]}",
            "script": "I was so tired of {customer_pains[0]} that I did something about it.",
        },
        {
            "frame": 2, "duration": "8s", "label": "story",
            "script": (
                "For years, I dealt with {customer_pains[0]}. "
                "I tried everything — nothing worked. "
                "That's when I realized the whole approach was wrong."
            ),
        },
        {
            "frame": 3, "duration": "5s", "label": "reveal",
            "text_overlay": "{product_name}",
            "script": "So I built {product_name}. It {key_benefit}.",
        },
        {
            "frame": 4, "duration": "2s", "label": "cta",
            "text_overlay": "{cta_text}",
            "script": "If you deal with {customer_pains[0]} too, check it out.",
        },
    ],
    copy_templates=CopyTemplate(
        primary_text=(
            "I spent years dealing with {customer_pains[0]}.\n"
            "So I built something to fix it.\n"
            "Meet {product_name} →"
        ),
        headline="Why I built {product_name}",
        cta_type="LEARN_MORE",
    ),
    variants=[
        VariantRule(vary="customer_pains"),
        VariantRule(vary="tone", options=["vulnerable", "determined"]),
        VariantRule(vary="script_length", options=["15s", "30s", "60s"]),
    ],
)

ORGANIC_STATIC_PROBLEM = AdTypeDefinition(
    id="organic_static_problem",
    name="Organic Looking Static (Problem)",
    strategy="product_unaware",
    format="static",
    aspect_ratios=["1:1", "9:16"],
    required_params=["customer_pains"],
    optional_params=["product_name", "product_category", "key_benefit"],
    skip_condition=None,
    layers=[
        LayerDefinition(
            type="social_post_frame",
            style_variant="reddit_post|tweet|tiktok_comment|instagram_story",
        ),
        LayerDefinition(
            type="text",
            content="{organic_hook}",
            position="post_body",
            style={"font": "platform_native", "size": "medium"},
        ),
        # NO product image in the visual
    ],
    hook_templates={
        "reddit_post": [
            "Anyone else fed up with {customer_pains[0]}? I've tried everything.",
            "Rant: {customer_pains[0]} is ruining my daily routine",
            "Is it just me or is {customer_pains[0]} getting worse?",
        ],
        "tweet": [
            "Hot take: {customer_pains[0]} is way worse than people think",
            "{customer_pains[0]} and nobody talks about it",
            "normalize admitting that {customer_pains[0]} sucks",
        ],
        "tiktok_comment": [
            "when {customer_pains[0]} hits different at 3am 😭",
            "me pretending {customer_pains[0]} doesn't bother me:",
        ],
        "instagram_story": [
            "does anyone else deal with {customer_pains[0]} or just me?",
            "currently dealing with {customer_pains[0]} AMA",
        ],
    },
    copy_templates=CopyTemplate(
        primary_text=(
            "If you're dealing with {customer_pains[0]}, you're not alone.\n"
            "{product_name} →"
        ),
        headline="{key_benefit}",
        cta_type="LEARN_MORE",
        fallbacks={
            "key_benefit": "You don't have to live with this",
            "product_name": "There might be a solution",
        },
    ),
    variants=[
        VariantRule(vary="style_variant", options=["reddit_post", "tweet", "tiktok_comment", "instagram_story"]),
        VariantRule(vary="organic_hook"),
        VariantRule(vary="customer_pains"),
    ],
)

US_VS_THEM_PROBLEM = AdTypeDefinition(
    id="us_vs_them_problem",
    name="Us Versus Them (Before/After)",
    strategy="product_unaware",
    format="static",
    aspect_ratios=["1:1", "9:16"],
    required_params=["customer_pains", "customer_desires", "product_name"],
    optional_params=["hero_image_url", "brand_colors", "scene_problem", "scene_solution"],
    skip_condition=None,
    layers=[
        LayerDefinition(type="comparison_layout", style={"layout": "split_vertical"}),
        LayerDefinition(
            type="background", position="left_half",
            source="{scene_problem}",
            style={"fallback": "#E2E8F0"},
        ),
        LayerDefinition(
            type="text", content="Before",
            position="left_half_top",
            style={"color": "#718096", "size": "small", "uppercase": True},
        ),
        LayerDefinition(
            type="text", content="{customer_pains[0]}",
            position="left_half_center",
            style={"color": "#4A5568", "size": "medium"},
        ),
        LayerDefinition(
            type="background", position="right_half",
            source="{brand_colors.primary}",
            style={"fallback": "#276749"},
        ),
        LayerDefinition(
            type="text", content="After",
            position="right_half_top",
            style={"color": "#FFFFFF", "size": "small", "uppercase": True},
        ),
        LayerDefinition(
            type="text", content="{customer_desires[0]}",
            position="right_half_center",
            style={"color": "#FFFFFF", "size": "medium", "emphasis": True},
        ),
        LayerDefinition(
            type="product_image",
            source="{hero_image_url}",
            position="center_bottom",
            size="small",
            processing=["remove_background"],
            condition="hero_image_url_exists",
        ),
    ],
    copy_templates=CopyTemplate(
        primary_text=(
            "Before {product_name}: {customer_pains[0]}.\n"
            "After {product_name}: {customer_desires[0]}.\n"
            "Make the switch →"
        ),
        headline="Before vs After",
        cta_type="SHOP_NOW",
    ),
    variants=[
        VariantRule(vary="customer_pains"),
        VariantRule(vary="customer_desires"),
        VariantRule(vary="layout", options=["split_vertical", "split_horizontal"]),
    ],
)


# =====================================================================
# FULL REGISTRY
# =====================================================================

AD_TYPE_REGISTRY: dict[str, AdTypeDefinition] = {
    # Strategy 1: Product Aware
    "product_benefits_static": PRODUCT_BENEFITS_STATIC,
    "product_demo_video": PRODUCT_DEMO_VIDEO,
    "review_static": REVIEW_STATIC,
    "us_vs_them_solution": US_VS_THEM_SOLUTION,
    "organic_static_solution": ORGANIC_STATIC_SOLUTION,
    "founder_video_solution": FOUNDER_VIDEO_SOLUTION,
    # Strategy 2: Product Unaware
    "problem_statement_text": PROBLEM_STATEMENT_TEXT,
    "problem_statement_image": PROBLEM_STATEMENT_IMAGE,
    "founder_video_problem": FOUNDER_VIDEO_PROBLEM,
    "organic_static_problem": ORGANIC_STATIC_PROBLEM,
    "us_vs_them_problem": US_VS_THEM_PROBLEM,
}


def get_registry() -> dict[str, AdTypeDefinition]:
    """Return the full ad type registry."""
    return AD_TYPE_REGISTRY


def get_ad_type(ad_type_id: str) -> AdTypeDefinition | None:
    """Look up a single ad type by ID."""
    return AD_TYPE_REGISTRY.get(ad_type_id)


def get_product_aware_types() -> list[AdTypeDefinition]:
    """Return all Strategy 1 (product aware) ad types."""
    return [t for t in AD_TYPE_REGISTRY.values() if t.strategy == "product_aware"]


def get_product_unaware_types() -> list[AdTypeDefinition]:
    """Return all Strategy 2 (product unaware) ad types."""
    return [t for t in AD_TYPE_REGISTRY.values() if t.strategy == "product_unaware"]
