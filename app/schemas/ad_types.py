"""
Ad Type Registry — structured, programmable specification for every ad type.

Each ad type defines:
- What data it needs (required_params, optional_params)
- How to compose the visual (layers)
- How to generate copy (copy_templates)
- How to create variants (variant axes)
"""

from pydantic import BaseModel
from typing import Literal

# Strategy enum
Strategy = Literal["product_aware", "product_unaware"]
AdFormat = Literal["static", "video", "carousel"]


class LayerDefinition(BaseModel):
    """Single visual layer in an ad composition."""
    type: str  # background, text, product_image, scene_image, badge, icon,
               # review_card, comparison_layout, social_post_frame
    source: str | None = None  # parameter reference: "{hero_image_url}"
    content: str | None = None  # static or template text
    position: str = "center"  # top_third, center, bottom_third, left_half, etc.
    size: str = "medium"  # small, medium, large, xlarge, full
    processing: list[str] = []  # remove_background, add_shadow, grayscale, blur
    style: dict = {}  # font, color, weight, alignment overrides
    condition: str | None = None  # only render if condition met
    style_variant: str | None = None  # for layers with multiple looks


class CopyTemplate(BaseModel):
    """Parameterized ad copy with variable slots and fallbacks."""
    primary_text: str  # template with {variable} slots
    headline: str
    description: str | None = None
    cta_type: str = "SHOP_NOW"  # SHOP_NOW, LEARN_MORE, SIGN_UP, GET_OFFER
    fallbacks: dict = {}  # variable -> fallback value


class VariantRule(BaseModel):
    """Axis of variation for generating diverse creatives from one ad type."""
    vary: str  # which field to rotate: value_props, background, copy_angle, etc.
    options: list[str] = []  # explicit options (if not derived from params)


class AdTypeDefinition(BaseModel):
    """
    Complete programmable specification for a single ad type.

    The system uses this to:
    1. Check if enough data exists to generate it
    2. Compose the visual deterministically via layers
    3. Generate copy from templates with variable slots
    4. Produce variants across defined axes
    """
    id: str  # unique snake_case identifier
    name: str  # display name
    strategy: Strategy
    format: AdFormat
    aspect_ratios: list[str] = ["1:1", "9:16"]

    # Data requirements
    required_params: list[str] = []
    optional_params: list[str] = []
    external_deps: list[str] = []  # e.g. "competitor_intelligence"
    skip_condition: str | None = None  # e.g. "!social_proof"

    # Visual composition
    layers: list[LayerDefinition] = []

    # Copy
    copy_templates: CopyTemplate | None = None

    # Variant generation
    variants: list[VariantRule] = []

    # Video-specific
    duration: str | None = None  # "8-15s"
    frames: list[dict] = []  # frame definitions for video types

    # Hook templates (for organic/problem types)
    hook_templates: dict[str, list[str]] = {}
