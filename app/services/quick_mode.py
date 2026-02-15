"""Quick Mode ad generation - single Gemini call for copy + image."""

import os
import json
import asyncio
import base64
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]

TONE_OPTIONS = ["professional", "casual", "playful", "urgent", "friendly"]


class QuickModeError(Exception):
    """Raised when quick mode generation fails after all retries."""
    pass


async def generate_quick_copy(idea: str, tone: str) -> dict:
    """
    Generate ad copy from a business idea using a single Gemini call.

    Returns dict with keys: headline, primaryText, cta, visualPrompt,
    targetAudience, campaignName, description
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise QuickModeError("GOOGLE_API_KEY not configured")

    client = genai.Client(api_key=api_key)

    prompt = f"""You are an expert Facebook ad copywriter. Generate ad copy for this business idea.

BUSINESS IDEA: {idea}
TONE: {tone}

Return JSON with these exact keys:
{{
  "headline": "5-8 word attention-grabbing headline (max 40 chars)",
  "primaryText": "Compelling ad copy, 2-3 short paragraphs (max 300 chars). Include pain point, solution, and benefit.",
  "cta": "Call-to-action button text (e.g., Learn More, Get Started, Shop Now)",
  "description": "One-line value proposition (max 90 chars)",
  "visualPrompt": "Detailed image generation prompt: describe a photorealistic ad visual that would pair with this copy. Include composition, lighting, colors, mood. No text in the image.",
  "targetAudience": "Brief target audience description for Meta targeting (demographics, interests, behaviors)",
  "campaignName": "Short campaign name (max 30 chars)"
}}

IMPORTANT:
- Match the {tone} tone throughout
- Make the headline punchy and benefit-focused
- primaryText should follow: Hook -> Pain -> Solution -> CTA pattern
- visualPrompt should describe a visually striking, professional ad image
- No placeholder text, be specific to the business idea"""

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            result = await client.aio.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )

            data = json.loads(result.text)
            if isinstance(data, list) and len(data) > 0:
                data = data[0]

            if not isinstance(data, dict):
                raise ValueError(f"Expected dict, got {type(data).__name__}")

            # Validate required fields
            required = ["headline", "primaryText", "cta", "visualPrompt", "targetAudience", "campaignName"]
            missing = [k for k in required if not data.get(k)]
            if missing:
                raise ValueError(f"Missing fields: {missing}")

            # Ensure description exists
            if not data.get("description"):
                data["description"] = data["headline"]

            logger.info(f"Quick copy generated: {data['campaignName']}")
            return data

        except Exception as e:
            last_error = e
            logger.warning(f"Quick copy attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])

    raise QuickModeError(f"Quick copy generation failed after {MAX_RETRIES} attempts: {last_error}")


async def generate_quick_image(prompt: str, aspect_ratio: str = "1:1") -> bytes:
    """
    Generate an ad image using Gemini with image generation.

    Returns raw image bytes (PNG).
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise QuickModeError("GOOGLE_API_KEY not configured")

    client = genai.Client(api_key=api_key)

    enhanced_prompt = (
        f"Create a professional, high-quality advertisement image. "
        f"No text, no words, no letters, no watermarks. "
        f"Photorealistic, studio quality lighting. "
        f"{prompt}"
    )

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            result = await client.aio.models.generate_content(
                model='gemini-2.5-flash-image',
                contents=enhanced_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
            )

            # Extract image from response parts
            if result.candidates and result.candidates[0].content.parts:
                for part in result.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                        image_bytes = part.inline_data.data
                        if isinstance(image_bytes, str):
                            image_bytes = base64.b64decode(image_bytes)
                        logger.info(f"Quick image generated: {len(image_bytes)} bytes")
                        return image_bytes

            raise ValueError("No image data in Gemini response")

        except Exception as e:
            last_error = e
            logger.warning(f"Quick image attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])

    raise QuickModeError(f"Quick image generation failed after {MAX_RETRIES} attempts: {last_error}")
