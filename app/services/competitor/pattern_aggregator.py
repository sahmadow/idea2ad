"""
Pattern Aggregator
Aggregates ad analysis data across competitors to identify winning patterns.
"""

import logging
from collections import Counter
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def aggregate_patterns(
    analyzed_ads: List[Dict[str, Any]],
    competitor_profiles: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Aggregate patterns across analyzed competitor ads.

    Args:
        analyzed_ads: List of analyzed ad dicts (from ad_analyzer)
        competitor_profiles: Optional list of competitor profile dicts

    Returns:
        Dict with aggregated pattern data
    """
    if not analyzed_ads:
        return {
            "total_ads": 0,
            "hook_distribution": {},
            "angle_distribution": {},
            "cta_distribution": {},
            "format_distribution": {},
            "top_hooks": [],
            "top_angles": [],
            "avg_strength": 0,
            "profitable_patterns": {},
        }

    total = len(analyzed_ads)

    # Count distributions
    hooks = Counter(ad.get("hook_type", "unknown") for ad in analyzed_ads)
    angles = Counter(ad.get("emotional_angle", "unknown") for ad in analyzed_ads)
    ctas = Counter(ad.get("cta_style", "unknown") for ad in analyzed_ads)
    formats = Counter(ad.get("format_type", "unknown") for ad in analyzed_ads)

    # Average strength score
    scores = [ad.get("strength_score", 0) for ad in analyzed_ads if ad.get("strength_score")]
    avg_strength = round(sum(scores) / len(scores), 1) if scores else 0

    # Analyze profitable ads specifically (30+ days active)
    profitable_ads = [ad for ad in analyzed_ads if ad.get("likely_profitable")]
    profitable_hooks = Counter(ad.get("hook_type", "unknown") for ad in profitable_ads)
    profitable_angles = Counter(ad.get("emotional_angle", "unknown") for ad in profitable_ads)

    # Top performing hook+angle combinations
    combo_counter = Counter()
    for ad in profitable_ads:
        combo = f"{ad.get('hook_type', 'unknown')}+{ad.get('emotional_angle', 'unknown')}"
        combo_counter[combo] += 1

    # Build distribution percentages
    def _to_pct(counter: Counter, total_count: int) -> Dict[str, float]:
        return {
            k: round(v / total_count * 100, 1)
            for k, v in counter.most_common()
        } if total_count > 0 else {}

    return {
        "total_ads": total,
        "profitable_ads": len(profitable_ads),
        "hook_distribution": _to_pct(hooks, total),
        "angle_distribution": _to_pct(angles, total),
        "cta_distribution": _to_pct(ctas, total),
        "format_distribution": _to_pct(formats, total),
        "top_hooks": [h for h, _ in hooks.most_common(3)],
        "top_angles": [a for a, _ in angles.most_common(3)],
        "avg_strength": avg_strength,
        "profitable_patterns": {
            "hooks": _to_pct(profitable_hooks, len(profitable_ads)),
            "angles": _to_pct(profitable_angles, len(profitable_ads)),
            "top_combos": [
                {"combo": c, "count": n}
                for c, n in combo_counter.most_common(5)
            ],
        },
        "competitor_count": len(competitor_profiles) if competitor_profiles else 0,
    }
