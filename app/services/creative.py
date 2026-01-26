
import os
import json
import asyncio
import logging
from google import genai
from typing import List
from app.models import AnalysisResult, CreativeAsset, ImageBrief, TextOverlay

logger = logging.getLogger(__name__)

# Maximum retries for LLM calls
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds


class CreativeGenerationError(Exception):
    """Raised when creative generation fails after all retries."""
    pass


def validate_analysis_input(analysis: AnalysisResult) -> None:
    """
    Validate that the analysis input is valid for creative generation.
    Raises CreativeGenerationError if analysis contains failure markers.
    """
    failure_markers = ["analysis failed", "n/a", "mock", "unknown", "error"]

    summary_lower = analysis.summary.lower() if analysis.summary else ""
    usp_lower = analysis.unique_selling_proposition.lower() if analysis.unique_selling_proposition else ""

    for marker in failure_markers:
        if marker in summary_lower or marker in usp_lower:
            raise CreativeGenerationError(
                f"Cannot generate creatives from failed analysis. "
                f"Summary: '{analysis.summary}', USP: '{analysis.unique_selling_proposition}'"
            )

    if not analysis.summary or len(analysis.summary) < 10:
        raise CreativeGenerationError("Analysis summary is too short or empty")
    if not analysis.unique_selling_proposition or len(analysis.unique_selling_proposition) < 5:
        raise CreativeGenerationError("Analysis USP is too short or empty")
    if not analysis.keywords or len(analysis.keywords) < 2:
        raise CreativeGenerationError("Analysis has insufficient keywords")

def load_prompt(prompt_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    # Go up from app/services to project root, then into prompts/
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "prompts", prompt_name)
    try:
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Prompt file {prompt_name} not found. Using fallback.")
        return ""

async def generate_creatives(analysis: AnalysisResult) -> List[CreativeAsset]:
    """
    Generates creative assets with two styles:
    1. Long-form 10-section testimonial ad copy
    2. Short punchy direct-response ad copy
    Raises CreativeGenerationError if generation fails after all retries.
    """
    # Validate input analysis first
    validate_analysis_input(analysis)

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise CreativeGenerationError("GOOGLE_API_KEY not configured. Cannot generate creatives.")

    client = genai.Client(api_key=api_key)

    # Generate both long-form and short-form ad copy
    prompt = f"""You are an expert Facebook ad copywriter. Create TWO different ad copy styles for variety.

PRODUCT/SERVICE ANALYSIS:
Summary: {analysis.summary}
USP: {analysis.unique_selling_proposition}
Pain Points: {', '.join(analysis.pain_points)}
Keywords: {', '.join(analysis.keywords)}
CTA: {analysis.call_to_action}

=== AD 1: LONG-FORM (10-SECTION TESTIMONIAL) ===
Write using this EXACT structure:
1. Hook: First-person result statement with specific number. "I [achieved X] from [method] I [unexpected twist]."
2. Pattern interrupt: What WASN'T required. "No X. No Y. Just Z."
3. Pain mirror: "I was drowning." + 3 specific pressures your audience feels daily.
4. Dismiss old way: Why traditional solutions don't work for busy people.
5. Solution intro: Product name + one sentence on what it does.
6. Simple mechanism: "I [minimal input]. It [handles everything]."
7. Benefits stack: 5-6 checkmarks covering time, effort, status, automation, quality.
8. Depth contrast: Compare meaningful engagement vs. shallow alternative.
9. Competitive fear: "Your competitors are doing this. Your ideal clients are listening. Will they hear you or someone else?"
10. CTA: 👉 Action + benefit + now

=== AD 2: SHORT-FORM (DIRECT RESPONSE) ===
Write a punchy, concise ad (max 150 words):
- Strong hook with benefit
- 2-3 pain points addressed
- Clear value proposition
- Urgency + CTA

Return JSON:
{{
    "long_form": {{
        "ad_copy": "full 10-section ad copy",
        "headline": "5-8 word result headline",
        "secondary": "short follow-up line"
    }},
    "short_form": {{
        "ad_copy": "punchy short ad copy (max 150 words)",
        "headline": "punchy headline (max 40 chars)",
        "secondary": "benefit line"
    }}
}}"""

    last_error = None

    # Retry loop with exponential backoff
    for attempt in range(MAX_RETRIES):
        try:
            result = await client.aio.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )

            content = result.text
            data = json.loads(content)

            # Handle case where Gemini returns a list
            if isinstance(data, list) and len(data) > 0:
                data = data[0]

            if not isinstance(data, dict):
                raise ValueError(f"Expected dict from Gemini, got {type(data).__name__}")

            # Extract both ad styles
            long_form = data.get("long_form", {})
            short_form = data.get("short_form", {})

            long_copy = long_form.get("ad_copy", "")
            short_copy = short_form.get("ad_copy", "")
            long_headline = long_form.get("headline", "")
            short_headline = short_form.get("headline", "")

            if not long_copy or len(long_copy) < 100:
                raise ValueError("Long-form ad copy is too short or empty")
            if not short_copy or len(short_copy) < 50:
                raise ValueError("Short-form ad copy is too short or empty")

            # Build CreativeAssets - one of each style
            assets = [
                CreativeAsset(
                    type="headline",
                    content=long_headline or "Transform Your Results Today",
                    rationale="10-section testimonial headline"
                ),
                CreativeAsset(
                    type="headline",
                    content=short_headline or "Get Started Now",
                    rationale="Short-form direct response headline"
                ),
                CreativeAsset(
                    type="copy_primary",
                    content=long_copy,
                    rationale="10-section testimonial ad copy"
                ),
                CreativeAsset(
                    type="copy_primary",
                    content=short_copy,
                    rationale="Short-form direct response ad copy"
                )
            ]

            logger.info(f"Generated ads: long={len(long_copy)} chars, short={len(short_copy)} chars")
            return assets

        except Exception as e:
            last_error = e
            logger.warning(f"Creative generation attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")

            # Don't wait after the last attempt
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying creative generation in {delay} seconds...")
                await asyncio.sleep(delay)

    # All retries exhausted
    logger.error(f"Creative generation failed after {MAX_RETRIES} attempts. Last error: {last_error}")
    raise CreativeGenerationError(f"Creative generation failed after {MAX_RETRIES} attempts. Last error: {last_error}")


async def generate_image_briefs(
    analysis: AnalysisResult,
    business_type: str = "commerce",
    product_description: str = None,
    product_image_url: str = None
) -> List[ImageBrief]:
    """
    Generates image briefs based on business type:
    - commerce: Product-focused briefs (product, lifestyle, problem-solution)
    - saas: Person-centric + Brand-centric briefs

    Raises CreativeGenerationError if generation fails after all retries.
    """
    # Validate input analysis first
    validate_analysis_input(analysis)

    if business_type == "saas":
        return await generate_saas_briefs(analysis)
    else:
        return await generate_commerce_briefs(
            analysis,
            product_description=product_description,
            product_image_url=product_image_url
        )


async def generate_saas_briefs(analysis: AnalysisResult) -> List[ImageBrief]:
    """
    Generates 2 SaaS-specific image briefs:
    1. Person-centric: Imagen generates happy person, text above/below
    2. Brand-centric: Pure HTML template, no Imagen

    Raises CreativeGenerationError if generation fails after all retries.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise CreativeGenerationError("GOOGLE_API_KEY not configured. Cannot generate image briefs.")

    client = genai.Client(api_key=api_key)

    # Load SaaS-specific prompt template
    prompt_template = load_prompt("image_brief_saas_prompt.md")

    # If prompt file not found, use inline fallback
    if not prompt_template:
        prompt_template = """
Generate 2 distinct image briefs for a SaaS product Meta Ad campaign.

ANALYSIS:
Summary: {summary}
USP: {unique_selling_proposition}
Pain Points: {pain_points}
CTA: {call_to_action}
Keywords: {keywords}
Buyer Persona: {buyer_persona}

STYLING GUIDE:
Primary Colors: {primary_colors}
Secondary Colors: {secondary_colors}
Fonts: {font_families}
Design Style: {design_style}
Mood: {mood}

Create exactly 2 briefs:

BRIEF 1 - PERSON-CENTRIC:
- approach: "person-centric"
- creative_type: "person-centric"
- Headline text at top, subheadline + CTA at bottom
- Center space for a happy professional person image (will be AI-generated)
- Focus on emotional connection and transformation
- Visual description should describe the PERSON to generate (age, gender matching buyer persona, professional attire, happy/confident expression)

BRIEF 2 - BRAND-CENTRIC:
- approach: "brand-centric"
- creative_type: "brand-centric"
- Pure text/logo design (no AI image generation needed)
- Logo as focal point
- Main headline prominently displayed
- Brand gradient background
- CTA button

Return JSON array with exactly 2 briefs. Each brief must have:
- approach: string
- creative_type: string ("person-centric" or "brand-centric")
- visual_description: string (for person-centric, describe the person; for brand-centric, describe the layout)
- styling_notes: string
- text_overlays: array of objects with content, font_size, position, color, background
- meta_best_practices: array of strings
- rationale: string
- render_mode: "template"
- product_image_prompt: null for brand-centric, person description for person-centric

IMPORTANT: Keep text overlays SHORT. Headlines max 5-7 words. Subheadlines max 10 words.
"""

    # Format prompt with analysis data
    sg = analysis.styling_guide
    prompt = prompt_template.replace("{summary}", analysis.summary)
    prompt = prompt.replace("{unique_selling_proposition}", analysis.unique_selling_proposition)
    prompt = prompt.replace("{pain_points}", ", ".join(analysis.pain_points))
    prompt = prompt.replace("{call_to_action}", analysis.call_to_action)
    prompt = prompt.replace("{keywords}", ", ".join(analysis.keywords))
    prompt = prompt.replace("{buyer_persona}", str(analysis.buyer_persona))
    prompt = prompt.replace("{primary_colors}", ", ".join(sg.primary_colors))
    prompt = prompt.replace("{secondary_colors}", ", ".join(sg.secondary_colors))
    prompt = prompt.replace("{font_families}", ", ".join(sg.font_families))
    prompt = prompt.replace("{design_style}", sg.design_style)
    prompt = prompt.replace("{mood}", sg.mood)

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            result = await client.aio.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )

            content = result.text
            data = json.loads(content)
            logger.info(f"SaaS briefs LLM returned: {type(data)}")

            # Parse image briefs
            if isinstance(data, list):
                briefs_data = data
            else:
                briefs_data = data.get("briefs", []) if "briefs" in data else []

            if not briefs_data:
                raise ValueError("Empty image briefs response from LLM")

            image_briefs = []
            for brief_data in briefs_data:
                text_overlays = [
                    TextOverlay(**overlay)
                    for overlay in brief_data.get("text_overlays", [])
                ]

                image_brief = ImageBrief(
                    approach=brief_data.get("approach", ""),
                    visual_description=brief_data.get("visual_description", ""),
                    styling_notes=brief_data.get("styling_notes", ""),
                    text_overlays=text_overlays,
                    meta_best_practices=brief_data.get("meta_best_practices", []),
                    rationale=brief_data.get("rationale", ""),
                    product_image_prompt=brief_data.get("product_image_prompt"),
                    render_mode=brief_data.get("render_mode", "template"),
                    creative_type=brief_data.get("creative_type", brief_data.get("approach", ""))
                )
                image_briefs.append(image_brief)

            if len(image_briefs) < 2:
                raise ValueError("Insufficient SaaS image briefs generated (need at least 2)")

            logger.info(f"Generated {len(image_briefs)} SaaS briefs: {[b.creative_type for b in image_briefs]}")
            return image_briefs

        except Exception as e:
            last_error = e
            logger.warning(f"SaaS brief generation attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying SaaS brief generation in {delay} seconds...")
                await asyncio.sleep(delay)

    logger.error(f"SaaS brief generation failed after {MAX_RETRIES} attempts. Last error: {last_error}")
    raise CreativeGenerationError(f"SaaS brief generation failed after {MAX_RETRIES} attempts. Last error: {last_error}")


async def generate_commerce_briefs(
    analysis: AnalysisResult,
    product_description: str = None,
    product_image_url: str = None
) -> List[ImageBrief]:
    """
    Generates 3 commerce-specific image briefs:
    - product-focused, lifestyle, problem-solution

    If user provided product_description, uses it for product_image_prompt.
    If user provided product_image_url, sets it directly on brief.

    Raises CreativeGenerationError if generation fails after all retries.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise CreativeGenerationError("GOOGLE_API_KEY not configured. Cannot generate image briefs.")

    client = genai.Client(api_key=api_key)

    # Load prompt template
    prompt_template = load_prompt("image_brief_prompt.md")

    # If prompt file not found, use inline fallback
    if not prompt_template:
        prompt_template = """
Generate 3 distinct image briefs for Meta Ads with different approaches: product-focused, lifestyle, and problem-solution.

ANALYSIS:
Summary: {summary}
USP: {unique_selling_proposition}
Pain Points: {pain_points}
CTA: {call_to_action}
Keywords: {keywords}

STYLING GUIDE:
Primary Colors: {primary_colors}
Secondary Colors: {secondary_colors}
Fonts: {font_families}
Design Style: {design_style}
Mood: {mood}

Return JSON array with 3 image briefs, each containing: approach, visual_description, styling_notes, text_overlays (array of objects with content, font_size, position, color, background), meta_best_practices (array), and rationale.
"""

    # Format prompt with analysis data using replace to avoid conflicts with JSON braces
    sg = analysis.styling_guide
    prompt = prompt_template.replace("{summary}", analysis.summary)
    prompt = prompt.replace("{unique_selling_proposition}", analysis.unique_selling_proposition)
    prompt = prompt.replace("{pain_points}", ", ".join(analysis.pain_points))
    prompt = prompt.replace("{call_to_action}", analysis.call_to_action)
    prompt = prompt.replace("{keywords}", ", ".join(analysis.keywords))
    prompt = prompt.replace("{buyer_persona}", str(analysis.buyer_persona))
    prompt = prompt.replace("{primary_colors}", ", ".join(sg.primary_colors))
    prompt = prompt.replace("{secondary_colors}", ", ".join(sg.secondary_colors))
    prompt = prompt.replace("{font_families}", ", ".join(sg.font_families))
    prompt = prompt.replace("{design_style}", sg.design_style)
    prompt = prompt.replace("{mood}", sg.mood)

    last_error = None

    # Retry loop with exponential backoff
    for attempt in range(MAX_RETRIES):
        try:
            result = await client.aio.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )

            content = result.text
            data = json.loads(content)
            logger.info(f"LLM returned briefs with keys: {[list(b.keys()) for b in (data if isinstance(data, list) else data.get('briefs', []))]}")

            # Parse image briefs
            if isinstance(data, list):
                briefs_data = data
            else:
                briefs_data = data.get("briefs", []) if "briefs" in data else []

            if not briefs_data:
                raise ValueError("Empty image briefs response from LLM")

            image_briefs = []
            for brief_data in briefs_data:
                # Parse text overlays
                text_overlays = [
                    TextOverlay(**overlay)
                    for overlay in brief_data.get("text_overlays", [])
                ]

                # Use user-provided product description if available
                product_prompt = brief_data.get("product_image_prompt")
                if product_description:
                    product_prompt = product_description

                image_brief = ImageBrief(
                    approach=brief_data.get("approach", ""),
                    visual_description=brief_data.get("visual_description", ""),
                    styling_notes=brief_data.get("styling_notes", ""),
                    text_overlays=text_overlays,
                    meta_best_practices=brief_data.get("meta_best_practices", []),
                    rationale=brief_data.get("rationale", ""),
                    product_image_prompt=product_prompt,
                    creative_type="product"  # Commerce briefs are product-focused
                )

                # Set user-provided product image URL directly
                if product_image_url:
                    image_brief.product_image_url = product_image_url

                image_briefs.append(image_brief)

            if len(image_briefs) < 2:
                raise ValueError("Insufficient image briefs generated (need at least 2)")

            logger.info(f"Generated {len(image_briefs)} commerce briefs")
            return image_briefs

        except Exception as e:
            last_error = e
            logger.warning(f"Image brief generation attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")

            # Don't wait after the last attempt
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying image brief generation in {delay} seconds...")
                await asyncio.sleep(delay)

    # All retries exhausted
    logger.error(f"Image brief generation failed after {MAX_RETRIES} attempts. Last error: {last_error}")
    raise CreativeGenerationError(f"Image brief generation failed after {MAX_RETRIES} attempts. Last error: {last_error}")
