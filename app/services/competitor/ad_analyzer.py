"""
Competitor Ad Analyzer
Uses LLM to analyze individual competitor ads for hook types, emotional angles, and CTA styles.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List

from google import genai

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]

ANALYSIS_PROMPT = """You are an expert performance marketer analyzing competitor Facebook/Instagram ads.

For each ad below, identify:
1. **hook_type**: How the ad grabs attention. One of: question, statistic, bold_claim, social_proof, urgency, curiosity, pain_point, benefit_lead, story, contrast
2. **emotional_angle**: The primary emotion targeted. One of: fear, aspiration, frustration, excitement, trust, curiosity, belonging, relief, pride, fomo
3. **cta_style**: The call-to-action approach. One of: direct, soft_ask, urgency, value_proposition, social_proof, free_trial, learn_more, scarcity
4. **format_type**: The ad format. One of: single_image, carousel, video, slideshow, collection, text_only
5. **key_message**: A 1-sentence summary of the ad's core message
6. **strength_score**: Rate 1-10 how strong/compelling this ad is

Ads to analyze:
{ads_json}

Return a JSON array with one object per ad:
```json
[
  {{
    "ad_id": "...",
    "hook_type": "...",
    "emotional_angle": "...",
    "cta_style": "...",
    "format_type": "...",
    "key_message": "...",
    "strength_score": 7
  }}
]
```

Only return the JSON array. No other text."""


async def analyze_competitor_ads(
    ads: List[Dict[str, Any]],
    batch_size: int = 10,
) -> List[Dict[str, Any]]:
    """
    Analyze competitor ads using LLM to extract hook types, angles, and patterns.

    Args:
        ads: List of competitor ad dicts (from ad_library_client)
        batch_size: Number of ads to analyze per LLM call

    Returns:
        List of analyzed ad dicts with hook_type, emotional_angle, etc.
    """
    if not ads:
        return []

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY not configured for ad analysis")
        return ads  # Return unanalyzed ads

    client = genai.Client(api_key=api_key)
    analyzed = []

    # Process in batches
    for i in range(0, len(ads), batch_size):
        batch = ads[i:i + batch_size]
        batch_result = await _analyze_batch(client, batch)
        analyzed.extend(batch_result)

    return analyzed


async def _analyze_batch(
    client: genai.Client,
    ads: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Analyze a batch of ads with the LLM."""
    # Build simplified ad data for prompt
    ads_for_prompt = []
    for ad in ads:
        ads_for_prompt.append({
            "ad_id": ad.get("ad_id", ""),
            "copy": ad.get("copy", "")[:500],
            "headline": ad.get("headline", ""),
            "description": ad.get("description", ""),
            "days_active": ad.get("days_active", 0),
        })

    prompt = ANALYSIS_PROMPT.format(ads_json=json.dumps(ads_for_prompt, indent=2))

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            result = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )

            content = result.text
            parsed = json.loads(content)

            if isinstance(parsed, list):
                # Merge LLM analysis back into original ad data
                analysis_map = {a["ad_id"]: a for a in parsed if isinstance(a, dict)}

                merged = []
                for ad in ads:
                    ad_id = ad.get("ad_id", "")
                    analysis = analysis_map.get(ad_id, {})
                    merged_ad = {**ad, **analysis}
                    merged.append(merged_ad)

                return merged

            logger.warning(f"Unexpected response format: {type(parsed)}")

        except Exception as e:
            last_error = e
            logger.warning(f"Ad analysis attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])

    logger.error(f"Ad analysis failed after {MAX_RETRIES} attempts: {last_error}")
    return ads  # Return unanalyzed ads as fallback
