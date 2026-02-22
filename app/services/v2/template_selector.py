"""
Template Selector — picks which approved ad types to generate.

Selection logic:
- branded_static, organic_static_reddit, problem_statement_text: always
- review_static, review_static_competition: only if social proof exists
- service_hero: only if hero_image_url exists
- product_centric: only if product images or hero image exist
- person_centric: always (generates AI person image)
- branded_static_video: always (video counterpart of branded_static)
- service_hero_video: only if hero_image_url exists
"""

import logging
from app.schemas.creative_params import CreativeParameters
from app.schemas.ad_types import AdTypeDefinition
from app.services.v2.ad_type_registry import AD_TYPE_REGISTRY

logger = logging.getLogger(__name__)


def select_templates(params: CreativeParameters) -> list[AdTypeDefinition]:
    """Select approved ad types based on available data."""
    selected: list[AdTypeDefinition] = []

    # Always selected
    _try_add(selected, "branded_static", params)
    _try_add(selected, "organic_static_reddit", params)
    _try_add(selected, "problem_statement_text", params)

    # Conditional: social proof
    if params.has_social_proof():
        _try_add(selected, "review_static", params)
        _try_add(selected, "review_static_competition", params)

    # Conditional: hero image
    if params.hero_image_url:
        _try_add(selected, "service_hero", params)

    # Conditional: product images available
    if params.product_images or params.hero_image_url:
        _try_add(selected, "product_centric", params)

    # Person centric: always (generates AI person image)
    _try_add(selected, "person_centric", params)

    # Video types (Remotion-rendered)
    _try_add(selected, "branded_static_video", params)
    if params.hero_image_url:
        _try_add(selected, "service_hero_video", params)

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
    """Add ad type to selected list if it exists in registry."""
    definition = AD_TYPE_REGISTRY.get(ad_type_id)
    if definition:
        selected.append(definition)
