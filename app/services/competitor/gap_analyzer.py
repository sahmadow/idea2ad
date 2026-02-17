"""
Gap Analyzer
Identifies gaps in competitor ad strategies and generates actionable recommendations.
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

GAP_ANALYSIS_PROMPT = """You are an expert performance marketing strategist. Analyze the competitor ad landscape below and identify gaps and opportunities.

## Your Product/Service:
{user_context}

## Competitor Ad Patterns:
- Total ads analyzed: {total_ads}
- Hook distribution: {hook_distribution}
- Emotional angle distribution: {angle_distribution}
- CTA style distribution: {cta_distribution}
- Top performing hooks: {top_hooks}
- Top performing angles: {top_angles}
- Average ad strength: {avg_strength}/10
- Profitable ad patterns (30+ days active):
  - Hooks: {profitable_hooks}
  - Angles: {profitable_angles}
  - Top combos: {top_combos}

## Competitor Profiles:
{competitor_profiles}

Based on this data, provide:

1. **underused_hooks**: Hook types NOT heavily used by competitors (opportunity areas)
2. **underused_angles**: Emotional angles with low competition
3. **content_gaps**: Topics or approaches competitors are NOT covering
4. **differentiation_opportunities**: Ways to stand out from the crowd
5. **recommended_hooks**: Top 3 hook types to use (with rationale)
6. **recommended_angles**: Top 3 emotional angles to use (with rationale)
7. **recommended_combos**: Top 3 hook+angle combinations to test
8. **ad_copy_directions**: 3 specific ad copy directions to try (each with a sample opening line)
9. **confidence_score**: 1-10 how confident you are in these recommendations (based on data quality)

Return as a JSON object:
```json
{{
  "underused_hooks": ["hook_type1", "hook_type2"],
  "underused_angles": ["angle1", "angle2"],
  "content_gaps": ["gap1", "gap2", "gap3"],
  "differentiation_opportunities": ["opp1", "opp2", "opp3"],
  "recommended_hooks": [
    {{"hook": "...", "rationale": "..."}},
    {{"hook": "...", "rationale": "..."}},
    {{"hook": "...", "rationale": "..."}}
  ],
  "recommended_angles": [
    {{"angle": "...", "rationale": "..."}},
    {{"angle": "...", "rationale": "..."}},
    {{"angle": "...", "rationale": "..."}}
  ],
  "recommended_combos": [
    {{"hook": "...", "angle": "...", "rationale": "..."}},
    {{"hook": "...", "angle": "...", "rationale": "..."}},
    {{"hook": "...", "angle": "...", "rationale": "..."}}
  ],
  "ad_copy_directions": [
    {{"direction": "...", "sample_opening": "..."}},
    {{"direction": "...", "sample_opening": "..."}},
    {{"direction": "...", "sample_opening": "..."}}
  ],
  "confidence_score": 7
}}
```

Only return the JSON object. No other text."""


async def analyze_gaps(
    aggregated_patterns: Dict[str, Any],
    competitor_profiles: List[Dict[str, Any]] = None,
    user_context: str = "",
) -> Dict[str, Any]:
    """
    Analyze gaps in competitor ad strategies using LLM.

    Args:
        aggregated_patterns: Output from pattern_aggregator.aggregate_patterns()
        competitor_profiles: List of competitor profile dicts (from discovery)
        user_context: Description of the user's product/service

    Returns:
        Dict with gap analysis and recommendations
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY not configured for gap analysis")
        return _empty_gap_result("API key not configured")

    if aggregated_patterns.get("total_ads", 0) == 0:
        return _empty_gap_result("No competitor ads to analyze")

    # Build competitor profiles summary
    profiles_text = "No detailed competitor profiles available."
    if competitor_profiles:
        profiles_parts = []
        for p in competitor_profiles:
            name = p.get("name", "Unknown")
            positioning = p.get("positioning", "")
            claims = p.get("claims", [])
            claims_str = "; ".join(claims[:5]) if claims else "N/A"
            profiles_parts.append(f"- {name}: {positioning} | Claims: {claims_str}")
        profiles_text = "\n".join(profiles_parts)

    profitable = aggregated_patterns.get("profitable_patterns", {})
    prompt = GAP_ANALYSIS_PROMPT.format(
        user_context=user_context or "Not specified",
        total_ads=aggregated_patterns.get("total_ads", 0),
        hook_distribution=json.dumps(aggregated_patterns.get("hook_distribution", {})),
        angle_distribution=json.dumps(aggregated_patterns.get("angle_distribution", {})),
        cta_distribution=json.dumps(aggregated_patterns.get("cta_distribution", {})),
        top_hooks=", ".join(aggregated_patterns.get("top_hooks", [])),
        top_angles=", ".join(aggregated_patterns.get("top_angles", [])),
        avg_strength=aggregated_patterns.get("avg_strength", 0),
        profitable_hooks=json.dumps(profitable.get("hooks", {})),
        profitable_angles=json.dumps(profitable.get("angles", {})),
        top_combos=json.dumps(profitable.get("top_combos", [])),
        competitor_profiles=profiles_text,
    )

    client = genai.Client(api_key=api_key)

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            result = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )

            parsed = json.loads(result.text)
            if isinstance(parsed, dict):
                return parsed

            logger.warning(f"Unexpected gap analysis format: {type(parsed)}")

        except Exception as e:
            last_error = e
            logger.warning(f"Gap analysis attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])

    logger.error(f"Gap analysis failed after {MAX_RETRIES} attempts: {last_error}")
    return _empty_gap_result(str(last_error))


def generate_recommendations(
    gap_analysis: Dict[str, Any],
    aggregated_patterns: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate prioritized list of actionable recommendations from gap analysis.

    Args:
        gap_analysis: Output from analyze_gaps()
        aggregated_patterns: Output from aggregate_patterns()

    Returns:
        List of recommendation dicts sorted by priority
    """
    recommendations = []

    # Recommend hooks
    for item in gap_analysis.get("recommended_hooks", []):
        recommendations.append({
            "type": "hook",
            "action": f"Use '{item.get('hook', '')}' hook type",
            "rationale": item.get("rationale", ""),
            "priority": "high",
        })

    # Recommend angles
    for item in gap_analysis.get("recommended_angles", []):
        recommendations.append({
            "type": "angle",
            "action": f"Target '{item.get('angle', '')}' emotional angle",
            "rationale": item.get("rationale", ""),
            "priority": "high",
        })

    # Recommend combos
    for item in gap_analysis.get("recommended_combos", []):
        hook = item.get("hook", "")
        angle = item.get("angle", "")
        recommendations.append({
            "type": "combo",
            "action": f"Test '{hook}' + '{angle}' combination",
            "rationale": item.get("rationale", ""),
            "priority": "medium",
        })

    # Content gap opportunities
    for gap in gap_analysis.get("content_gaps", []):
        recommendations.append({
            "type": "content_gap",
            "action": f"Address content gap: {gap}",
            "rationale": "Not covered by competitors",
            "priority": "medium",
        })

    # Differentiation opportunities
    for opp in gap_analysis.get("differentiation_opportunities", []):
        recommendations.append({
            "type": "differentiation",
            "action": opp,
            "rationale": "Stand out from competitors",
            "priority": "high",
        })

    # Ad copy directions
    for direction in gap_analysis.get("ad_copy_directions", []):
        recommendations.append({
            "type": "copy_direction",
            "action": direction.get("direction", ""),
            "sample": direction.get("sample_opening", ""),
            "rationale": "Data-driven copy direction",
            "priority": "medium",
        })

    return recommendations


def _empty_gap_result(error: str = "") -> Dict[str, Any]:
    """Return empty gap analysis result."""
    return {
        "underused_hooks": [],
        "underused_angles": [],
        "content_gaps": [],
        "differentiation_opportunities": [],
        "recommended_hooks": [],
        "recommended_angles": [],
        "recommended_combos": [],
        "ad_copy_directions": [],
        "confidence_score": 0,
        "error": error,
    }
