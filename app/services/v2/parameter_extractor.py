"""
Parameter Extractor — combines scraper output + Gemini LLM analysis
into a validated CreativeParameters object.

This is the entry point for the v2 pipeline. It:
1. Takes raw scraped_data from the existing scraper
2. Calls Gemini to infer pains, desires, personas, scenes, tone
3. Merges everything into a single CreativeParameters object
4. Applies fallback defaults for missing fields
"""

import os
import json
import asyncio
import logging
from urllib.parse import urlparse
from google import genai

from app.schemas.creative_params import (
    CreativeParameters,
    BrandColors,
    PersonaDemographics,
    TargetPersona,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]


class ExtractionError(Exception):
    """Raised when parameter extraction fails after all retries."""
    pass


# Gemini prompt for extracting structured creative parameters
EXTRACTION_PROMPT = """You are a world-class performance marketer and creative strategist.

Analyze this landing page content and extract ALL parameters needed for a dual-strategy
Meta ad campaign (both product-aware and product-unaware audiences).

LANDING PAGE CONTENT:
{scraped_text}

EXTRACTED COLORS:
- Backgrounds: {background_colors}
- Text: {text_colors}
- Accents (CTAs): {accent_colors}

EXTRACTED FONTS: {fonts}

OG IMAGE: {og_image}

HTML LANG ATTRIBUTE: {html_lang}
SOURCE URL: {source_url}

Return a JSON object with EXACTLY these fields:

{{
    "product_name": "string — short brand name as humans say it casually (e.g. 'Storytel' not 'Storytel Audiobook Subscription', 'Slack' not 'Slack Messaging Platform')",
    "business_type": "string — 'saas' for software/subscription products, 'ecommerce' for physical/digital goods, 'service' for agencies/consultancies",
    "product_category": "string — simple lowercase category as a normal person would say it (e.g. 'audiobooks', 'CRM software', 'mattresses', 'AI search analytics'). Never use slashes like 'Entertainment/Audiobooks'",
    "product_description_short": "string — max 15 words",
    "price": "string or null — e.g. '$79', '€65/mo'",
    "currency": "string or null — e.g. 'USD'",
    "brand_name": "string — company/brand name",
    "key_benefit": "string — single most important benefit to the customer",
    "key_differentiator": "string — what makes this product unique vs alternatives",
    "value_props": ["string — value prop 1", "prop 2", "prop 3", "prop 4", "prop 5"],
    "customer_pains": [
        "string — pain point phrased as customer would say it",
        "pain 2",
        "pain 3"
    ],
    "customer_desires": [
        "string — desired outcome 1",
        "outcome 2",
        "outcome 3"
    ],
    "objections": ["string — common buying objection 1", "objection 2"],
    "tone": "premium|casual|clinical|playful|urgent",
    "cta_text": "string — primary CTA from the page",
    "social_proof": "string or null — e.g. '12,847 5-star reviews'",
    "testimonials": ["string — real testimonial quote if found on page"],
    "urgency_hooks": ["string — any urgency/scarcity messages found"],
    "persona_primary": {{
        "label": "string — e.g. 'Health-conscious professional, 30-45'",
        "demographics": {{
            "age_min": 25,
            "age_max": 55,
            "gender_skew": "neutral|male|female"
        }},
        "psychographics": ["Values quality over price", "Researches before buying"],
        "scenes": ["visual scene 1 for this persona", "scene 2"],
        "language_style": "string — how to speak to them",
        "specific_pains": ["persona-specific pain 1"],
        "specific_desires": ["persona-specific desire 1"]
    }},
    "persona_secondary": {{
        "label": "string or null",
        "demographics": {{"age_min": 18, "age_max": 65, "gender_skew": "neutral"}},
        "psychographics": [],
        "scenes": [],
        "language_style": "",
        "specific_pains": [],
        "specific_desires": []
    }},
    "scene_problem": "string — visual description of the problem state (e.g. 'Person rubbing stiff neck at desk')",
    "scene_solution": "string — visual description of the solved state",
    "scene_lifestyle": "string — aspirational lifestyle visual",
    "language": "string — ISO 639-1 code of the page content language (e.g. 'en', 'az', 'de', 'fr', 'es'). Detect from actual text content, not just HTML attributes.",
    "target_countries": ["ISO 3166-1 alpha-2 country codes for the primary target market, inferred from language, currency, domain TLD, and content (e.g. ['AZ'] for .az domain with Azerbaijani content, ['US'] for English .com)"]
}}

RULES:
- customer_pains must be phrased in the customer's voice, not marketing speak
- value_props should be 3-5 concrete, specific benefits (not vague)
- key_benefit is THE single most compelling reason to buy
- key_differentiator is what NO competitor offers
- scene descriptions should be specific enough for AI image generation
- If data is missing from the page, infer intelligently from context
- For language: detect from actual page text content. Use html_lang as a hint if available, but verify against content
- For target_countries: infer from domain TLD (.az→AZ, .de→DE, .co.uk→GB), currency, language, and content context
- Always return valid JSON
"""


async def extract_creative_parameters(
    scraped_data: dict,
    source_url: str | None = None,
) -> CreativeParameters:
    """
    Main entry point: takes raw scraper output, returns CreativeParameters.

    Combines:
    - Direct extraction from scraped_data (colors, fonts, images, text)
    - LLM inference via Gemini (pains, desires, personas, scenes)
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ExtractionError("GOOGLE_API_KEY not configured")

    # --- Step 1: Extract direct fields from scraped data ---
    direct_params = _extract_direct_params(scraped_data, source_url)

    # --- Step 2: Call Gemini for inferred fields ---
    llm_params = await _extract_llm_params(scraped_data, api_key, source_url=source_url)

    # --- Step 3: Merge and build CreativeParameters ---
    params = _merge_params(direct_params, llm_params)

    logger.info(
        f"Extracted creative params: product='{params.product_name}', "
        f"pains={len(params.customer_pains)}, desires={len(params.customer_desires)}, "
        f"value_props={len(params.value_props)}"
    )
    return params


def _extract_direct_params(scraped_data: dict, source_url: str | None) -> dict:
    """Extract parameters directly available from scraper output (no LLM needed)."""
    styling = scraped_data.get("styling", {})
    logo_data = scraped_data.get("logo")

    # Determine brand colors from scraped styling
    bg_colors = styling.get("backgrounds", [])
    accent_colors = styling.get("accents", [])
    primary_color = bg_colors[0] if bg_colors else "#1A365D"
    secondary_color = accent_colors[0] if accent_colors else None

    # Brand name from domain if not extracted
    brand_name = ""
    if source_url:
        parsed = urlparse(source_url)
        # "cloudrest.com" -> "Cloudrest"
        domain_parts = parsed.netloc.replace("www.", "").split(".")
        if domain_parts:
            brand_name = domain_parts[0].capitalize()

    return {
        "source_url": source_url,
        "destination_url": source_url or "",
        "brand_name": brand_name,
        "brand_colors": BrandColors(
            primary=primary_color,
            secondary=secondary_color,
        ),
        "brand_fonts": styling.get("fonts", ["Inter"]) or ["Inter"],
        "brand_logo_url": logo_data.get("url") if logo_data else None,
        "hero_image_url": scraped_data.get("og_image") or None,
        "headline": (scraped_data.get("headers", [None]) or [None])[0] or scraped_data.get("title", ""),
        "subheadline": (scraped_data.get("headers", [None, None]) or [None, None])[1] if len(scraped_data.get("headers", [])) > 1 else None,
        "html_lang": scraped_data.get("language"),
    }


async def _extract_llm_params(scraped_data: dict, api_key: str, source_url: str | None = None) -> dict:
    """Call Gemini to infer marketing parameters from scraped content."""
    client = genai.Client(api_key=api_key)
    styling = scraped_data.get("styling", {})

    prompt = EXTRACTION_PROMPT.format(
        scraped_text=scraped_data.get("full_text", "")[:8000],
        background_colors=styling.get("backgrounds", []),
        text_colors=styling.get("text", []),
        accent_colors=styling.get("accents", []),
        fonts=styling.get("fonts", []),
        og_image=scraped_data.get("og_image", ""),
        html_lang=scraped_data.get("language") or "not set",
        source_url=source_url or "unknown",
    )

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            result = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            data = json.loads(result.text)

            # Handle list response
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict, got {type(data).__name__}")

            # Validate minimum quality
            if not data.get("product_name") or len(data.get("product_name", "")) < 2:
                raise ValueError("product_name is missing or too short")
            if not data.get("customer_pains") or len(data.get("customer_pains", [])) < 1:
                raise ValueError("customer_pains is missing or empty")

            return data

        except Exception as e:
            last_error = e
            logger.warning(f"LLM extraction attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])

    raise ExtractionError(f"LLM extraction failed after {MAX_RETRIES} attempts: {last_error}")


def _merge_params(direct: dict, llm: dict) -> CreativeParameters:
    """Merge direct-extracted and LLM-inferred params into CreativeParameters."""

    # Parse personas from LLM output
    persona_primary = None
    persona_secondary = None

    if llm.get("persona_primary"):
        try:
            p = llm["persona_primary"]
            demo = p.get("demographics", {})
            persona_primary = TargetPersona(
                label=p.get("label", "General audience"),
                demographics=PersonaDemographics(
                    age_min=demo.get("age_min", 18),
                    age_max=demo.get("age_max", 65),
                    gender_skew=demo.get("gender_skew", "neutral"),
                ),
                psychographics=p.get("psychographics", []),
                scenes=p.get("scenes", []),
                language_style=p.get("language_style", "Conversational"),
                specific_pains=p.get("specific_pains", []),
                specific_desires=p.get("specific_desires", []),
            )
        except Exception as e:
            logger.warning(f"Failed to parse primary persona: {e}")

    if llm.get("persona_secondary"):
        try:
            p = llm["persona_secondary"]
            if p.get("label"):
                demo = p.get("demographics", {})
                persona_secondary = TargetPersona(
                    label=p.get("label", ""),
                    demographics=PersonaDemographics(
                        age_min=demo.get("age_min", 18),
                        age_max=demo.get("age_max", 65),
                        gender_skew=demo.get("gender_skew", "neutral"),
                    ),
                    psychographics=p.get("psychographics", []),
                    scenes=p.get("scenes", []),
                    language_style=p.get("language_style", ""),
                    specific_pains=p.get("specific_pains", []),
                    specific_desires=p.get("specific_desires", []),
                )
        except Exception as e:
            logger.warning(f"Failed to parse secondary persona: {e}")

    # Build final CreativeParameters — direct params override LLM where both exist
    return CreativeParameters(
        # Source
        source_url=direct.get("source_url"),
        destination_url=direct.get("destination_url", ""),
        # Product core (LLM)
        product_name=llm.get("product_name", "Product"),
        business_type=llm.get("business_type", "ecommerce") if llm.get("business_type") in ("ecommerce", "saas", "service") else "ecommerce",
        product_category=llm.get("product_category", "General"),
        product_description_short=llm.get("product_description_short", ""),
        price=llm.get("price"),
        currency=llm.get("currency"),
        # Brand identity (direct)
        brand_name=llm.get("brand_name") or direct.get("brand_name", ""),
        brand_colors=direct.get("brand_colors", BrandColors()),
        brand_fonts=direct.get("brand_fonts", ["Inter"]),
        brand_logo_url=direct.get("brand_logo_url"),
        # Images (direct)
        hero_image_url=direct.get("hero_image_url"),
        # Headlines (direct with LLM fallback)
        headline=direct.get("headline") or llm.get("product_name", ""),
        subheadline=direct.get("subheadline"),
        # Messaging (LLM)
        key_benefit=llm.get("key_benefit", ""),
        key_differentiator=llm.get("key_differentiator", ""),
        value_props=llm.get("value_props", []),
        customer_pains=llm.get("customer_pains", []),
        customer_desires=llm.get("customer_desires", []),
        objections=llm.get("objections", []),
        # Social proof (LLM)
        social_proof=llm.get("social_proof"),
        testimonials=llm.get("testimonials", []),
        # CTA (LLM with fallback)
        cta_text=llm.get("cta_text", "Shop Now"),
        # Personas (LLM, parsed above)
        persona_primary=persona_primary,
        persona_secondary=persona_secondary,
        # Scenes (LLM)
        scene_problem=llm.get("scene_problem"),
        scene_solution=llm.get("scene_solution"),
        scene_lifestyle=llm.get("scene_lifestyle"),
        # Tone (LLM)
        tone=llm.get("tone", "casual"),
        urgency_hooks=llm.get("urgency_hooks", []),
        # Language & Geo (LLM with scraper hint)
        language=llm.get("language") or direct.get("html_lang") or "en",
        target_countries=llm.get("target_countries") if isinstance(llm.get("target_countries"), list) and llm.get("target_countries") else ["US"],
    )
