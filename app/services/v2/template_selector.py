"""
Template Selector — two-pass algorithm that picks which ad types to generate.

Pass 1: Product Aware templates (skip based on data availability)
Pass 2: Product Unaware templates (always include at least one problem statement)

Each selected template is validated against CreativeParameters before inclusion.
"""

import logging
from app.schemas.creative_params import CreativeParameters
from app.schemas.ad_types import AdTypeDefinition
from app.services.v2.ad_type_registry import AD_TYPE_REGISTRY

logger = logging.getLogger(__name__)


def _has_param(params: CreativeParameters, param_name: str) -> bool:
    """Check if a parameter exists and is non-empty on CreativeParameters."""
    # Handle dotted paths like "brand_colors.primary"
    parts = param_name.split(".")
    obj = params
    for part in parts:
        if hasattr(obj, part):
            obj = getattr(obj, part)
        else:
            return False
    # Check non-empty
    if obj is None:
        return False
    if isinstance(obj, (list, dict, str)) and len(obj) == 0:
        return False
    return True


def _validate_ad_type(
    definition: AdTypeDefinition,
    params: CreativeParameters,
) -> bool:
    """
    Validate that all required params exist and skip conditions are not met.
    Returns True if the ad type can be generated.
    """
    # Check required params
    for param in definition.required_params:
        if not _has_param(params, param):
            logger.debug(f"Skipping {definition.id}: missing required param '{param}'")
            return False

    # Evaluate skip conditions
    if definition.skip_condition:
        cond = definition.skip_condition
        if cond == "!social_proof AND len(testimonials) == 0":
            if not params.has_social_proof():
                logger.debug(f"Skipping {definition.id}: no social proof")
                return False
        elif cond == "len(product_images) < 3":
            if not params.has_enough_product_images(3):
                logger.debug(f"Skipping {definition.id}: insufficient product images")
                return False

    return True


def select_templates(params: CreativeParameters) -> list[AdTypeDefinition]:
    """
    Two-pass template selection algorithm.

    Returns ordered list of AdTypeDefinitions that should be generated
    given the available CreativeParameters.
    """
    selected: list[AdTypeDefinition] = []

    # --- Pass 1: Product Aware ---

    # Always attempt product_benefits_static (workhorse)
    if params.has_enough_value_props(3):
        _try_add(selected, "product_benefits_static", params)

    # Review static only if social proof exists
    if params.has_social_proof():
        _try_add(selected, "review_static", params)
        _try_add(selected, "review_static_competition", params)

    # Us vs Them — always attempt (uses generic fallbacks if no competitor data)
    _try_add(selected, "us_vs_them_solution", params)

    # Always include organic solution
    _try_add(selected, "organic_static_solution", params)

    # Product demo only if enough product images
    if params.has_enough_product_images(3):
        _try_add(selected, "product_demo_video", params)

    # Founder video script always generated
    _try_add(selected, "founder_video_solution", params)

    # UGC avatar video (HeyGen) — OFF pending cost/quality eval
    # _try_add(selected, "ugc_avatar_video", params)

    # --- Pass 2: Product Unaware ---

    # Always include at least one problem statement
    _try_add(selected, "problem_statement_text", params)

    # Image problem statement if scene description available
    if params.has_scene_problem():
        _try_add(selected, "problem_statement_image", params)

    # Always include organic problem
    _try_add(selected, "organic_static_problem", params)

    # Before/after if we have both pains and desires
    if params.has_pains_and_desires():
        _try_add(selected, "us_vs_them_problem", params)

    # Founder video problem script always generated
    _try_add(selected, "founder_video_problem", params)

    logger.info(
        f"Selected {len(selected)} templates: "
        f"{[t.id for t in selected]}"
    )
    return selected


def _try_add(
    selected: list[AdTypeDefinition],
    ad_type_id: str,
    params: CreativeParameters,
) -> None:
    """Add ad type to selected list if it passes validation."""
    definition = AD_TYPE_REGISTRY.get(ad_type_id)
    if definition and _validate_ad_type(definition, params):
        selected.append(definition)
