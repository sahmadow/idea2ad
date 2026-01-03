
import os
import json
from google import genai
from app.models import AnalysisResult, StylingGuide

def load_prompt(prompt_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", prompt_name)
    try:
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"WARNING: Prompt file {prompt_name} not found. Using fallback.")
        return ""

async def analyze_landing_page_content(scraped_text: str, styling_data: dict) -> AnalysisResult:
    """
    Analyzes the scraped text using Google Gemini to extract marketing insights and styling guide.
    Returns an AnalysisResult object.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_API_KEY not found. Returning mock analysis.")
        return AnalysisResult(
            summary="Mock Analysis (No GOOGLE_API_KEY)",
            unique_selling_proposition="Mock USP",
            pain_points=["Mock Pain 1"],
            call_to_action="Mock CTA",
            buyer_persona={"note": "Add GOOGLE_API_KEY for real persona"},
            keywords=["mock", "data"],
            styling_guide=StylingGuide(
                primary_colors=["#000000"],
                secondary_colors=["#FFFFFF"],
                font_families=["Arial"],
                design_style="Mock Style",
                mood="Mock Mood"
            )
        )

    try:
        client = genai.Client(api_key=api_key)

        # Load prompt template
        prompt_template = load_prompt("analyzer_prompt.md")

        # If prompt file not found, use inline fallback
        if not prompt_template:
            prompt_template = """
You are a world-class performance marketer. Analyze the following landing page content and extract key insights for a Facebook Ads campaign.

LANDING PAGE CONTENT:
{scraped_text}

EXTRACTED COLORS: {colors}
EXTRACTED FONTS: {fonts}

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

        # Format prompt with actual data
        prompt = prompt_template.format(
            scraped_text=scraped_text[:8000],
            colors=styling_data.get("colors", []),
            fonts=styling_data.get("fonts", [])
        )

        result = await client.aio.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )

        content = result.text
        data = json.loads(content)
        
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
        print(f"Error in analysis with Gemini: {e}")
        # Fallback for dev/error cases
        return AnalysisResult(
            summary="Analysis failed",
            unique_selling_proposition="N/A",
            pain_points=[],
            call_to_action="N/A",
            buyer_persona={},
            keywords=[],
            styling_guide=StylingGuide(
                primary_colors=["#000000"],
                secondary_colors=["#FFFFFF"],
                font_families=["Arial"],
                design_style="Unknown",
                mood="Unknown"
            )
        )

