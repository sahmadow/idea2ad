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

# ISO 639-1 → human-readable language name
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English", "az": "Azerbaijani", "de": "German", "fr": "French",
    "es": "Spanish", "it": "Italian", "pt": "Portuguese", "ru": "Russian",
    "tr": "Turkish", "ar": "Arabic", "zh": "Chinese", "ja": "Japanese",
    "ko": "Korean", "nl": "Dutch", "pl": "Polish", "sv": "Swedish",
    "da": "Danish", "fi": "Finnish", "no": "Norwegian", "uk": "Ukrainian",
    "cs": "Czech", "ro": "Romanian", "hu": "Hungarian", "el": "Greek",
    "he": "Hebrew", "th": "Thai", "vi": "Vietnamese", "id": "Indonesian",
    "ms": "Malay", "hi": "Hindi", "bn": "Bengali", "ka": "Georgian",
}


def _language_instruction(params: CreativeParameters) -> str:
    """Build language instruction for LLM prompts."""
    lang = params.language or "en"
    name = LANGUAGE_NAMES.get(lang, lang.upper())
    if lang == "en":
        return ""
    return (
        f"\nIMPORTANT: Write ALL ad copy in {name} ({lang}). "
        f"Do not translate brand names or product names.\n"
    )


class GeneratedCopy(dict):
    """Copy output for a single creative variant."""
    pass


def _clean_interpolated_text(text: str) -> str:
    """
    Post-process interpolated copy to fix punctuation artifacts.

    Fixes:
    - Trailing punctuation from array values ("neck pain." → "neck pain")
    - Duplicate punctuation after interpolation (".?" → "?", ".." → ".")
    - Lowercase first char when value appears mid-sentence
    """
    # Remove duplicate punctuation patterns
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\.\?", "?", text)
    text = re.sub(r"\.!", "!", text)
    text = re.sub(r"\?\.", "?", text)
    text = re.sub(r"!\.", "!", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _strip_trailing_punct(value: str) -> str:
    """Strip trailing sentence punctuation from interpolated values."""
    return value.rstrip(".!?;,")


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
                result = _strip_trailing_punct(str(value[index]))
                # Lowercase first char if mid-sentence (preceded by non-start text)
                start = match.start()
                if start > 0 and template[start - 1] == " " and result:
                    prev_char = template[start - 2] if start >= 2 else ""
                    if prev_char not in (".", "!", "?", ""):
                        result = result[0].lower() + result[1:]
                return result
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
        return _strip_trailing_punct(str(obj))

    return re.sub(r"\{(\w+(?:\[\d+\])?(?:\.\w+)?)\}", replacer, template)


def _resolve_cta_type(cta_type: str, params: CreativeParameters) -> str:
    """Remap CTA type based on business_type."""
    if cta_type == "SHOP_NOW":
        if params.business_type == "saas":
            return "SIGN_UP"
        if params.business_type == "service":
            return "LEARN_MORE"
    return cta_type


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
            cta_type=_resolve_cta_type("SHOP_NOW", params),
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

    # Fix interpolation artifacts (duplicate punct, trailing punct, etc.)
    primary_text = _clean_interpolated_text(primary_text)
    headline = _clean_interpolated_text(headline)
    if description:
        description = _clean_interpolated_text(description)

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
        cta_type=_resolve_cta_type(ct.cta_type, params),
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

    lang_inst = _language_instruction(params)
    prompt = f"""Generate {num_variants} tonal variants of this ad copy.
Keep the same structure and message, but vary the tone.
{lang_inst}
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


async def generate_competition_copy(
    ad_type: AdTypeDefinition,
    params: CreativeParameters,
    competitor_data: dict | None = None,
) -> GeneratedCopy:
    """
    Generate competition-led copy by researching competitor complaints via Gemini.

    If competitor_data is provided (scraped page), uses real competitor info for
    targeted copy. Otherwise falls back to generic competitor research.

    Returns GeneratedCopy with competition_testimonial for the review card visual.
    Falls back to template-fill if LLM fails.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No GOOGLE_API_KEY — falling back to template copy for competition")
        return _competition_fallback(ad_type, params)

    client = genai.Client(api_key=api_key)

    product_name = params.product_name or "this product"
    product_category = params.product_category or "this category"
    key_benefit = params.key_benefit or ""
    key_differentiator = params.key_differentiator or ""
    social_proof = params.social_proof or "thousands of"

    # Build competitor context section
    if competitor_data and competitor_data.get("full_text"):
        comp_text = competitor_data["full_text"][:3000]
        comp_title = competitor_data.get("title", "Unknown")
        comp_url = competitor_data.get("url", "")
        competitor_section = f"""
COMPETITOR PAGE (scraped from {comp_url}):
Title: {comp_title}
Content: {comp_text}

TASK: Compare the competitor's offering above against {product_name}. Identify specific weaknesses,
missing features, or pain points that {product_name} solves better. Use REAL gaps you can see in
their page — vague claims, missing features, limited scope, etc."""
        naming_rules = f"""- Reference the competitor generically (e.g., "other {product_category} tools", "my old tool")
- Do NOT mention the competitor by name — keep it generic
- The complaints should be REAL weaknesses you identified from the competitor's page"""
        logger.info(f"Using scraped competitor data: {comp_title} ({len(comp_text)} chars)")
    else:
        competitor_section = f"""
TASK: Research the competitive landscape for "{product_name}" in the "{product_category}" category.
Find common competitor frustrations and position {product_name} as the better alternative."""
        naming_rules = f"""- Do NOT name specific competitor brands
- Use generic references like "other {product_category} tools", "the old way", "traditional solutions" """

    lang_inst = _language_instruction(params)
    prompt = f"""You are an ad copywriter generating competition-focused ad copy.
{lang_inst}
PRODUCT INFO:
- Name: {product_name}
- Category: {product_category}
- Key Benefit: {key_benefit}
- Key Differentiator: {key_differentiator}
- Social Proof: {social_proof}
{competitor_section}

GENERATE:
1. competition_testimonial: A realistic 1-2 sentence review from someone who switched FROM a competitor TO {product_name}. Should mention a specific competitor pain point they escaped. Max 150 chars.
2. primary_text: Ad primary text (max {PRIMARY_TEXT_MAX} chars, optimal {PRIMARY_TEXT_OPTIMAL}). Lead with competitor frustration, pivot to {product_name} as solution. Include "switch to {product_name}" or "try {product_name} instead" messaging.
3. headline: Short punchy headline (max {HEADLINE_MAX} chars). "Try {product_name} instead" or "Switch to {product_name}" style.
4. competitor_complaint: The specific pain point competitors have (e.g., "overpriced subscriptions", "clunky interfaces"). Max 50 chars.

RULES:
{naming_rules}
- Keep tone confident but not aggressive
- Make the testimonial sound authentic and conversational

Return JSON object with fields: competition_testimonial, primary_text, headline, competitor_complaint"""

    for attempt in range(MAX_RETRIES + 1):
        try:
            result = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            data = json.loads(result.text)
            if isinstance(data, dict):
                competition_testimonial = str(data.get("competition_testimonial", ""))[:150]
                primary_text = str(data.get("primary_text", ""))[:PRIMARY_TEXT_MAX]
                headline = str(data.get("headline", f"Try {product_name} instead"))[:HEADLINE_MAX]
                competitor_complaint = str(data.get("competitor_complaint", ""))[:50]

                logger.info(f"Competition copy generated for {product_name}: complaint='{competitor_complaint}'")

                return GeneratedCopy(
                    primary_text=primary_text,
                    headline=headline,
                    description=competition_testimonial,
                    cta_type=_resolve_cta_type("LEARN_MORE", params),
                    competition_testimonial=competition_testimonial,
                    competitor_complaint=competitor_complaint,
                )

        except Exception as e:
            logger.warning(f"Competition copy generation attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAYS[attempt])

    # Fallback to template fill
    logger.warning("All competition copy attempts failed — using template fallback")
    return _competition_fallback(ad_type, params)


async def translate_params(params: CreativeParameters) -> CreativeParameters:
    """
    Translate user-facing text fields in CreativeParameters to the target language.
    Called ONCE after extraction for non-English pages. This ensures bridges and
    template variable resolution both produce target-language text.
    """
    lang = params.language or "en"
    if lang == "en":
        return params

    lang_name = LANGUAGE_NAMES.get(lang, lang.upper())

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No GOOGLE_API_KEY — skipping params translation")
        return params

    client = genai.Client(api_key=api_key)

    # Collect user-facing text to translate in one batch
    texts = {
        "key_benefit": params.key_benefit,
        "key_differentiator": params.key_differentiator,
        "product_description_short": params.product_description_short,
        "cta_text": params.cta_text,
        "social_proof": params.social_proof or "",
        "customer_pains": params.customer_pains,
        "customer_desires": params.customer_desires,
        "value_props": params.value_props,
        "objections": params.objections,
        "urgency_hooks": params.urgency_hooks,
    }

    prompt = f"""Translate these marketing texts to {lang_name} ({lang}).

{json.dumps(texts, ensure_ascii=False)}

RULES:
- Translate ALL text to {lang_name}
- Do NOT translate brand names or product names — keep them as-is
- If any text is already in {lang_name}, keep it unchanged
- Keep the same tone and emotional impact
- Return the SAME JSON structure with translated values

Return valid JSON."""

    try:
        result = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(result.text)
        if not isinstance(data, dict):
            return params

        # Apply translations back to a copy of params
        params_dict = params.model_dump()

        for key in ["key_benefit", "key_differentiator", "product_description_short", "cta_text", "social_proof"]:
            if data.get(key) and isinstance(data[key], str) and data[key].strip():
                params_dict[key] = data[key]

        for key in ["customer_pains", "customer_desires", "value_props", "objections", "urgency_hooks"]:
            if isinstance(data.get(key), list) and data[key]:
                params_dict[key] = [str(v) for v in data[key]]

        translated = CreativeParameters(**params_dict)
        logger.info(f"Translated {len(texts)} param fields to {lang_name}")
        return translated

    except Exception as e:
        logger.warning(f"Params translation to {lang_name} failed: {e}")
        return params


async def translate_copy(
    copy: GeneratedCopy,
    params: CreativeParameters,
) -> GeneratedCopy:
    """
    Translate template-filled copy to the target language via LLM.
    Only called when params.language != 'en'. Returns translated copy,
    or original if LLM fails.
    """
    lang = params.language or "en"
    if lang == "en":
        return copy

    lang_name = LANGUAGE_NAMES.get(lang, lang.upper())

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No GOOGLE_API_KEY — skipping copy translation")
        return copy

    client = genai.Client(api_key=api_key)

    prompt = f"""Translate this ad copy to {lang_name} ({lang}).

PRIMARY TEXT: {copy['primary_text']}
HEADLINE: {copy['headline']}
DESCRIPTION: {copy.get('description') or ''}

RULES:
- Translate ALL text to {lang_name}
- Do NOT translate brand names or product names — keep them as-is
- If parts of the text are already in {lang_name}, keep them unchanged
- Keep the same tone, urgency, and emotional impact
- Respect character limits: primary_text max {PRIMARY_TEXT_MAX}, headline max {HEADLINE_MAX}, description max {DESCRIPTION_MAX}
- Return valid JSON

Return JSON object with fields: primary_text, headline, description"""

    for attempt in range(MAX_RETRIES):
        try:
            result = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            data = json.loads(result.text)
            if isinstance(data, dict) and data.get("primary_text"):
                return GeneratedCopy(
                    primary_text=str(data["primary_text"])[:PRIMARY_TEXT_MAX],
                    headline=str(data.get("headline", copy["headline"]))[:HEADLINE_MAX],
                    description=str(data["description"])[:DESCRIPTION_MAX] if data.get("description") else copy.get("description"),
                    cta_type=copy["cta_type"],
                )
        except Exception as e:
            logger.warning(f"Copy translation attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])

    logger.warning(f"Copy translation to {lang_name} failed — using English")
    return copy


def _competition_fallback(
    ad_type: AdTypeDefinition,
    params: CreativeParameters,
) -> GeneratedCopy:
    """Template-based fallback for competition copy when LLM fails."""
    base = generate_copy_from_template(ad_type, params)
    # Add generic competition testimonial
    product_name = params.product_name or "this product"
    base["competition_testimonial"] = (
        f"Switched from our old solution and never looked back. {product_name} just works."
    )
    base["competitor_complaint"] = "the same old problems"
    return base
