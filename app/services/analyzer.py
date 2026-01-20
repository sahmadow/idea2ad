
import os
import json
import asyncio
import logging
from google import genai
from app.models import AnalysisResult, StylingGuide

logger = logging.getLogger(__name__)

# Maximum retries for LLM calls
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds


class AnalysisError(Exception):
    """Raised when landing page analysis fails after all retries."""
    pass


def validate_analysis_result(data: dict) -> bool:
    """
    Validate that analysis result contains meaningful data.
    Returns True if valid, False if it looks like placeholder/failed data.
    """
    # Check required fields exist and have content
    summary = data.get("summary", "")
    usp = data.get("unique_selling_proposition", "")
    keywords = data.get("keywords", [])

    # Detect failure markers
    failure_markers = ["analysis failed", "n/a", "mock", "unknown", "error", "failed"]

    if not summary or len(summary) < 10:
        return False
    if not usp or len(usp) < 5:
        return False
    if not keywords or len(keywords) < 2:
        return False

    # Check for failure markers in content
    summary_lower = summary.lower()
    usp_lower = usp.lower()
    for marker in failure_markers:
        if marker in summary_lower or marker in usp_lower:
            return False

    return True

def load_prompt(prompt_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", prompt_name)
    try:
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Prompt file {prompt_name} not found. Using fallback.")
        return ""

async def analyze_landing_page_content(scraped_text: str, styling_data: dict) -> AnalysisResult:
    """
    Analyzes the scraped text using Google Gemini to extract marketing insights and styling guide.
    Returns an AnalysisResult object.
    Raises AnalysisError if analysis fails after all retries.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise AnalysisError("GOOGLE_API_KEY not configured. Cannot perform analysis.")

    client = genai.Client(api_key=api_key)

    # Load prompt template
    prompt_template = load_prompt("analyzer_prompt.md")

    # If prompt file not found, use inline fallback
    if not prompt_template:
        prompt_template = """
You are a world-class performance marketer. Analyze the following landing page content and extract key insights for a Facebook Ads campaign.

LANDING PAGE CONTENT:
{scraped_text}

EXTRACTED COLORS (categorized):
- Background colors: {background_colors}
- Text colors: {text_colors}
- Accent colors (CTAs/buttons): {accent_colors}
EXTRACTED FONTS: {fonts}

COLOR RULES: Background colors are typically primary brand colors. Text colors (black/white/gray) are usually NOT primary. Accent colors can be primary or secondary.

OUTPUT FORMAT (JSON ONLY):
{{
    "summary": "1 sentence description",
    "unique_selling_proposition": "Main hook/benefit",
    "pain_points": ["Pain 1", "Pain 2", "Pain 3"],
    "call_to_action": "Primary CTA",
    "buyer_persona": {{
        "age_range": [25, 45],
        "gender": "All/Male/Female",
        "education": "High School/College/etc",
        "job_titles": ["Job 1", "Job 2"]
    }},
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "styling_guide": {{
        "primary_colors": ["#HEX1", "#HEX2"],
        "secondary_colors": ["#HEX3", "#HEX4"],
        "font_families": ["Font 1", "Font 2"],
        "design_style": "Description of aesthetic",
        "mood": "Emotional tone"
    }}
}}
"""

    # Extract categorized colors (with backward compatibility)
    background_colors = styling_data.get("backgrounds", [])
    text_colors = styling_data.get("text", [])
    accent_colors = styling_data.get("accents", [])

    # Backward compatibility: if new structure not present, use legacy colors
    if not background_colors and not text_colors and not accent_colors:
        legacy_colors = styling_data.get("colors", [])
        # Can't categorize legacy colors, so pass them all as backgrounds
        background_colors = legacy_colors

    # Format prompt with actual data
    prompt = prompt_template.format(
        scraped_text=scraped_text[:8000],
        background_colors=background_colors,
        text_colors=text_colors,
        accent_colors=accent_colors,
        fonts=styling_data.get("fonts", [])
    )

    # Log content length for debugging
    logger.info(f"Analyzing content: {len(scraped_text)} chars, bg_colors: {len(background_colors)}, text_colors: {len(text_colors)}, accents: {len(accent_colors)}, fonts: {len(styling_data.get('fonts', []))}")

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

            # Handle case where Gemini returns a list instead of dict
            if isinstance(data, list) and len(data) > 0:
                data = data[0]

            if not isinstance(data, dict):
                raise ValueError(f"Expected dict from Gemini, got {type(data).__name__}")

            # Validate the analysis result
            if not validate_analysis_result(data):
                raise ValueError("Analysis returned invalid or incomplete data")

            # Parse styling guide
            styling_guide_data = data.get("styling_guide", {})
            styling_guide = StylingGuide(**styling_guide_data)

            # Create AnalysisResult with styling guide
            return AnalysisResult(
                summary=data.get("summary", ""),
                unique_selling_proposition=data.get("unique_selling_proposition", ""),
                pain_points=data.get("pain_points", []),
                call_to_action=data.get("call_to_action", ""),
                buyer_persona=data.get("buyer_persona", {}),
                keywords=data.get("keywords", []),
                styling_guide=styling_guide
            )

        except Exception as e:
            last_error = e
            logger.warning(f"Analysis attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")

            # Don't wait after the last attempt
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying analysis in {delay} seconds...")
                await asyncio.sleep(delay)

    # All retries exhausted
    logger.error(f"Analysis failed after {MAX_RETRIES} attempts. Last error: {last_error}")
    raise AnalysisError(f"Analysis failed after {MAX_RETRIES} attempts. Last error: {last_error}")

