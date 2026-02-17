"""
Copy Generator — two-pass copy generation for ad types.

Pass 1: Template fill — substitute {variables} from CreativeParameters
Pass 2: LLM variants — generate 2-3 tonal variants per ad type (optional)

Enforces copy constraints: primary_text 125 chars optimal / 500 hard max,
headline 40 chars, description 30 chars.
"""

import os
import re
import json
import asyncio
import logging
from google import genai

from app.schemas.creative_params import CreativeParameters
from app.schemas.ad_types import AdTypeDefinition, CopyTemplate

logger = logging.getLogger(__name__)

# Copy length constraints
PRIMARY_TEXT_OPTIMAL = 125
PRIMARY_TEXT_MAX = 500
HEADLINE_MAX = 40
DESCRIPTION_MAX = 30

MAX_RETRIES = 2
RETRY_DELAYS = [1, 2]


class GeneratedCopy(dict):
    """Copy output for a single creative variant."""
    pass


def _resolve_variable(template: str, params: CreativeParameters) -> str:
    """
    Replace {variable} placeholders with values from CreativeParameters.
    Supports: {field}, {field[0]}, {field.subfield}
    """
    def replacer(match: re.Match) -> str:
        path = match.group(1)
        fallback = ""

        # Handle array indexing: value_props[0]
        idx_match = re.match(r"(\w+)\[(\d+)\]", path)
        if idx_match:
            field_name = idx_match.group(1)
            index = int(idx_match.group(2))
            value = getattr(params, field_name, [])
            if isinstance(value, list) and index < len(value):
                return str(value[index])
            return fallback

        # Handle dotted paths: brand_colors.primary
        parts = path.split(".")
        obj = params
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return fallback
        if obj is None:
            return fallback
        return str(obj)

    return re.sub(r"\{(\w+(?:\[\d+\])?(?:\.\w+)?)\}", replacer, template)


def generate_copy_from_template(
    ad_type: AdTypeDefinition,
    params: CreativeParameters,
) -> GeneratedCopy:
    """
    Pass 1: Fill copy templates with parameter values.
    Returns a dict with primary_text, headline, description, cta_type.
    """
    ct = ad_type.copy_templates
    if not ct:
        return GeneratedCopy(
            primary_text="",
            headline="",
            description=None,
            cta_type="SHOP_NOW",
        )

    primary_text = _resolve_variable(ct.primary_text, params)
    headline = _resolve_variable(ct.headline, params)
    description = _resolve_variable(ct.description, params) if ct.description else None

    # Apply fallbacks for empty values
    for var, fallback in ct.fallbacks.items():
        placeholder = "{" + var + "}"
        if fallback is not None:
            if placeholder in primary_text:
                primary_text = primary_text.replace(placeholder, str(fallback))
            if placeholder in headline:
                headline = headline.replace(placeholder, str(fallback))

    # Clean up residual empty placeholders
    primary_text = re.sub(r"\{[^}]+\}", "", primary_text).strip()
    headline = re.sub(r"\{[^}]+\}", "", headline).strip()
    if description:
        description = re.sub(r"\{[^}]+\}", "", description).strip()

    # Enforce constraints
    if len(headline) > HEADLINE_MAX:
        headline = headline[:HEADLINE_MAX - 1] + "…"
    if description and len(description) > DESCRIPTION_MAX:
        description = description[:DESCRIPTION_MAX - 1] + "…"
    if len(primary_text) > PRIMARY_TEXT_MAX:
        primary_text = primary_text[:PRIMARY_TEXT_MAX - 3] + "..."

    return GeneratedCopy(
        primary_text=primary_text,
        headline=headline,
        description=description,
        cta_type=ct.cta_type,
    )


async def generate_copy_variants(
    ad_type: AdTypeDefinition,
    params: CreativeParameters,
    base_copy: GeneratedCopy,
    num_variants: int = 2,
) -> list[GeneratedCopy]:
    """
    Pass 2 (optional): Use LLM to generate tonal variants of the base copy.
    Returns list of variant copies (may include the original if LLM fails).
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No GOOGLE_API_KEY — skipping LLM copy variants")
        return [base_copy]

    client = genai.Client(api_key=api_key)

    prompt = f"""Generate {num_variants} tonal variants of this ad copy.
Keep the same structure and message, but vary the tone.

ORIGINAL:
Primary Text: {base_copy['primary_text']}
Headline: {base_copy['headline']}

PRODUCT: {params.product_name}
KEY BENEFIT: {params.key_benefit}
TONE: {params.tone}
AD TYPE: {ad_type.name} ({ad_type.strategy})

CONSTRAINTS:
- Primary text: max {PRIMARY_TEXT_MAX} chars (optimal: {PRIMARY_TEXT_OPTIMAL})
- Headline: max {HEADLINE_MAX} chars
- Keep the core message, vary delivery (casual vs urgent vs curiosity-driven)

Return JSON array of objects with primary_text and headline fields."""

    for attempt in range(MAX_RETRIES):
        try:
            result = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            data = json.loads(result.text)
            if isinstance(data, list):
                variants = []
                for item in data[:num_variants]:
                    variants.append(GeneratedCopy(
                        primary_text=str(item.get("primary_text", base_copy["primary_text"]))[:PRIMARY_TEXT_MAX],
                        headline=str(item.get("headline", base_copy["headline"]))[:HEADLINE_MAX],
                        description=base_copy.get("description"),
                        cta_type=base_copy["cta_type"],
                    ))
                return [base_copy] + variants

        except Exception as e:
            logger.warning(f"Copy variant generation attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])

    # Fallback: return original only
    return [base_copy]
