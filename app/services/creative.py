
import os
import json
import google.generativeai as genai
from typing import List
from app.models import AnalysisResult, CreativeAsset, ImageBrief, TextOverlay

def load_prompt(prompt_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", prompt_name)
    try:
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"WARNING: Prompt file {prompt_name} not found. Using fallback.")
        return ""

async def generate_creatives(analysis: AnalysisResult) -> List[CreativeAsset]:
    """
    Generates creative assets (headlines, copy) using Google Gemini based on analysis.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return [
            CreativeAsset(type="headline", content="Unlock Your Potential Today", rationale="Direct benefit based on USP"),
            CreativeAsset(type="copy_primary", content="Stop struggling with X. Start doing Y with our solution.", rationale="Agitates pain point X"),
        ]

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
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

        result = await model.generate_content_async(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        content = result.text
        data = json.loads(content)
        
        if isinstance(data, list):
            assets_data = data
        else:
            assets_data = data.get("assets", []) if "assets" in data else []

        assets = [CreativeAsset(**item) for item in assets_data]
        return assets

    except Exception as e:
        print(f"Error generating creatives with Gemini: {e}")
        return []


async def generate_image_briefs(analysis: AnalysisResult) -> List[ImageBrief]:
    """
    Generates 3 distinct image briefs with explicit text overlay specifications.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        # Return mock image briefs
        return [
            ImageBrief(
                approach="product-focused",
                visual_description="Mock product image",
                styling_notes="Use brand colors",
                text_overlays=[
                    TextOverlay(content="Mock CTA", font_size="large", position="center", color="#000000")
                ],
                meta_best_practices=["Mobile-first design"],
                rationale="Mock rationale"
            )
        ]

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
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
        
        # Format prompt with analysis data
        sg = analysis.styling_guide
        prompt = prompt_template.format(
            summary=analysis.summary,
            unique_selling_proposition=analysis.unique_selling_proposition,
            pain_points=", ".join(analysis.pain_points),
            call_to_action=analysis.call_to_action,
            keywords=", ".join(analysis.keywords),
            buyer_persona=str(analysis.buyer_persona),
            primary_colors=", ".join(sg.primary_colors),
            secondary_colors=", ".join(sg.secondary_colors),
            font_families=", ".join(sg.font_families),
            design_style=sg.design_style,
            mood=sg.mood
        )

        result = await model.generate_content_async(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        content = result.text
        data = json.loads(content)
        
        # Parse image briefs
        if isinstance(data, list):
            briefs_data = data
        else:
            briefs_data = data.get("briefs", []) if "briefs" in data else []
        
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
                rationale=brief_data.get("rationale", "")
            )
            image_briefs.append(image_brief)
        
        return image_briefs

    except Exception as e:
        print(f"Error generating image briefs with Gemini: {e}")
        return []
