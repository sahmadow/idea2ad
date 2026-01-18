
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
    Generates creative assets (headlines, copy) using Google Gemini based on analysis.
    Raises CreativeGenerationError if generation fails after all retries.
    """
    # Validate input analysis first
    validate_analysis_input(analysis)

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise CreativeGenerationError("GOOGLE_API_KEY not configured. Cannot generate creatives.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
    Based on the following marketing analysis, generate 4 high-performing creative assets for a Meta Ads campaign.

    ANALYSIS:
    Summary: {analysis.summary}
    USP: {analysis.unique_selling_proposition}
    Pain Points: {analysis.pain_points}
    Keywords: {analysis.keywords}

    CRITICAL INSTRUCTIONS:
    1. USE THE KEYWORDS: Incorporate the provided 'Keywords' naturally into the Headlines and Primary Text.
    2. BE SPECIFIC: Use the specific terminology found in the 'Keywords' and 'Summary'.
    3. ADDRESS PAIN POINTS: The copy should directly address the user's pain points.

    REQUIRED ASSETS:
    1. 2x Headlines (Punchy, max 40 chars) - Must include a main keyword.
    2. 2x Primary Text (Persuasive, max 200 chars) - Focus on the 'Hook'.

    OUTPUT FORMAT (JSON ARRAY):
    [
        {{ "type": "headline", "content": "...", "rationale": "Why this works..." }},
        {{ "type": "copy_primary", "content": "...", "rationale": "..." }}
    ]
    """

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

            if isinstance(data, list):
                assets_data = data
            else:
                assets_data = data.get("assets", []) if "assets" in data else []

            if not assets_data:
                raise ValueError("Empty creatives response from LLM")

            assets = [CreativeAsset(**item) for item in assets_data]

            # Validate we have required asset types
            headlines = [a for a in assets if a.type == "headline"]
            primary_texts = [a for a in assets if a.type == "copy_primary"]

            if not headlines or not primary_texts:
                raise ValueError("Missing required headline or primary text assets")

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


async def generate_image_briefs(analysis: AnalysisResult) -> List[ImageBrief]:
    """
    Generates 3 distinct image briefs with explicit text overlay specifications.
    Raises CreativeGenerationError if generation fails after all retries.
    """
    # Validate input analysis first
    validate_analysis_input(analysis)

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

                image_brief = ImageBrief(
                    approach=brief_data.get("approach", ""),
                    visual_description=brief_data.get("visual_description", ""),
                    styling_notes=brief_data.get("styling_notes", ""),
                    text_overlays=text_overlays,
                    meta_best_practices=brief_data.get("meta_best_practices", []),
                    rationale=brief_data.get("rationale", ""),
                    product_image_prompt=brief_data.get("product_image_prompt")
                )
                image_briefs.append(image_brief)

            if len(image_briefs) < 2:
                raise ValueError("Insufficient image briefs generated (need at least 2)")

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
