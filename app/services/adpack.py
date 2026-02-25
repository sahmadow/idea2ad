"""
AdPack Assembly Service (Phase 5)

Consolidates generated creatives into a unified AdPack structure,
derives Smart Broad targeting from persona analysis, and manages
the ad pack lifecycle.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional

from app.models import (
    AdCreative,
    AdPack,
    SmartBroadTargeting,
    TargetingRationale,
    CampaignStructure,
    CampaignDraft,
    AdPackUpdateRequest,
    CreativeAsset,
)

logger = logging.getLogger(__name__)

# In-memory store for ad packs (keyed by id)
_ad_packs: Dict[str, AdPack] = {}


def derive_smart_broad_targeting(
    buyer_persona: Dict[str, Any],
    keywords: List[str],
    geo_locations: Optional[List[str]] = None,
) -> SmartBroadTargeting:
    """
    Derive Smart Broad targeting parameters from buyer persona analysis.

    Smart Broad methodology:
    - Use age range from persona
    - Geographic targeting with exclusions
    - Minimal interest targeting (let Meta's algorithm optimize)
    """
    # Extract age range from persona
    age_range = buyer_persona.get("age_range", [18, 65])
    if isinstance(age_range, list) and len(age_range) >= 2:
        age_min = max(18, int(age_range[0]))
        age_max = min(65, int(age_range[1]))
    else:
        age_min, age_max = 18, 65

    # Extract gender
    gender_raw = buyer_persona.get("gender", "All")
    if isinstance(gender_raw, str):
        gender_lower = gender_raw.lower()
        if gender_lower in ("male", "men"):
            genders = ["male"]
        elif gender_lower in ("female", "women"):
            genders = ["female"]
        else:
            genders = ["all"]
    else:
        genders = ["all"]

    # Geographic targeting (use passed geo_locations, not hardcoded US)
    geo = geo_locations if geo_locations else ["US"]

    # Build rationale
    job_titles = buyer_persona.get("job_titles", [])
    education = buyer_persona.get("education", "")

    age_reason = f"Targeting {age_min}-{age_max} based on buyer persona analysis"
    if job_titles:
        age_reason += f" (typical for {', '.join(job_titles[:2])})"

    geo_reason = f"Targeting {', '.join(geo)} as primary market"

    exclusion_reason = None
    exclusions: List[str] = []
    if education and education.lower() not in ("all", "any", ""):
        exclusion_reason = (
            "No exclusions applied; Smart Broad lets Meta optimize delivery"
        )

    rationale = TargetingRationale(
        age_range_reason=age_reason,
        geo_reason=geo_reason,
        exclusion_reason=exclusion_reason
        or "Smart Broad: minimal exclusions for maximum algorithmic optimization",
        methodology="smart_broad",
    )

    return SmartBroadTargeting(
        age_min=age_min,
        age_max=age_max,
        genders=genders,
        geo_locations=geo,
        excluded_geo_locations=[],
        exclusions=exclusions,
        rationale=rationale,
    )


def _build_creatives_from_draft(draft: CampaignDraft) -> List[AdCreative]:
    """
    Build AdCreative list from CampaignDraft.

    Maps existing ads and creatives into the AdPack creative structure,
    assigning Product Aware / Product Unaware strategy labels.
    """
    creatives: List[AdCreative] = []

    # Get available headlines and primary texts
    headlines: List[CreativeAsset] = [
        c for c in draft.suggested_creatives if c.type == "headline"
    ]
    primary_texts: List[CreativeAsset] = [
        c for c in draft.suggested_creatives if c.type == "copy_primary"
    ]

    # First, add creatives from the generated ads (these have images)
    if draft.ads:
        for ad in draft.ads:
            strategy: str = (
                "product_aware" if ad.id % 2 == 1 else "product_unaware"
            )
            creative = AdCreative(
                id=str(uuid.uuid4())[:8],
                strategy=strategy,  # type: ignore[arg-type]
                primary_text=ad.primaryText,
                headline=ad.headline,
                description=ad.description,
                image_url=ad.imageUrl,
                image_brief=ad.imageBrief,
                call_to_action="LEARN_MORE",
            )
            creatives.append(creative)

    # Then, create additional creative variants from UNIQUE copy pairs only
    # Skip combos that duplicate existing creative text
    target_count = 10
    len(creatives)
    seen_copy: set[tuple[str, str]] = {
        (c.primary_text, c.headline) for c in creatives
    }

    if headlines and primary_texts:
        for i in range(len(headlines) * len(primary_texts)):
            h_idx = i % len(headlines)
            p_idx = i // len(headlines) % len(primary_texts)

            copy_key = (primary_texts[p_idx].content, headlines[h_idx].content)
            if copy_key in seen_copy:
                continue
            seen_copy.add(copy_key)

            strategy_label: str = (
                "product_aware" if len(creatives) % 2 == 0 else "product_unaware"
            )

            # Use image from existing ads if available
            image_url = None
            image_brief = None
            if draft.ads and len(draft.ads) > 0:
                source_ad = draft.ads[len(creatives) % len(draft.ads)]
                image_url = source_ad.imageUrl
                image_brief = source_ad.imageBrief

            creative = AdCreative(
                id=str(uuid.uuid4())[:8],
                strategy=strategy_label,  # type: ignore[arg-type]
                primary_text=primary_texts[p_idx].content,
                headline=headlines[h_idx].content,
                description=draft.analysis.summary[:90],
                image_url=image_url,
                image_brief=image_brief,
                call_to_action=draft.analysis.call_to_action or "LEARN_MORE",
            )
            creatives.append(creative)

            if len(creatives) >= target_count:
                break

    return creatives


def assemble_ad_pack(
    draft: CampaignDraft,
    job_id: Optional[str] = None,
) -> AdPack:
    """
    Assemble a complete AdPack from a CampaignDraft.

    This consolidates generated creatives, derives Smart Broad targeting
    from persona analysis, and sets default campaign parameters.
    """
    pack_id = str(uuid.uuid4())[:12]

    # Derive targeting from persona
    targeting = derive_smart_broad_targeting(
        buyer_persona=draft.analysis.buyer_persona,
        keywords=draft.analysis.keywords,
        geo_locations=draft.targeting.geo_locations if draft.targeting.geo_locations else None,
    )

    # Build creatives
    creatives = _build_creatives_from_draft(draft)

    # Generate campaign name from URL
    campaign_name = "Campaign"
    try:
        from urllib.parse import urlparse
        hostname = urlparse(draft.project_url).hostname or "campaign"
        campaign_name = hostname.replace("www.", "").split(".")[0].title()
    except Exception:
        pass

    campaign_structure = CampaignStructure(
        campaign_name=f"{campaign_name} - Ad Pack",
        objective="OUTCOME_SALES",
        adset_name=f"{campaign_name} - Smart Broad",
        ad_count=len(creatives),
    )

    ad_pack = AdPack(
        id=pack_id,
        project_url=draft.project_url,
        creatives=creatives,
        targeting=targeting,
        budget_daily=15.0,
        duration_days=3,
        campaign_structure=campaign_structure,
        status="draft",
        created_from=job_id,
    )

    # Store in memory
    _ad_packs[pack_id] = ad_pack
    logger.info(
        f"Assembled AdPack {pack_id}: {len(creatives)} creatives, "
        f"${ad_pack.budget_daily}/day for {ad_pack.duration_days} days"
    )

    return ad_pack


def get_ad_pack(pack_id: str) -> Optional[AdPack]:
    """Retrieve an AdPack by ID."""
    return _ad_packs.get(pack_id)


def update_ad_pack(pack_id: str, update: AdPackUpdateRequest) -> Optional[AdPack]:
    """
    Update an AdPack's fields (inline editing support).

    Supports updating:
    - Individual creative's copy (primary_text, headline, description)
    - Budget and duration
    """
    pack = _ad_packs.get(pack_id)
    if not pack:
        return None

    # Update budget/duration
    if update.budget_daily is not None:
        pack.budget_daily = max(1.0, update.budget_daily)
    if update.duration_days is not None:
        pack.duration_days = max(1, update.duration_days)

    # Update specific creative
    if update.creative_id:
        for creative in pack.creatives:
            if creative.id == update.creative_id:
                if update.primary_text is not None:
                    creative.primary_text = update.primary_text
                if update.headline is not None:
                    creative.headline = update.headline
                if update.description is not None:
                    creative.description = update.description
                break

    _ad_packs[pack_id] = pack
    return pack


def list_ad_packs() -> List[AdPack]:
    """List all ad packs."""
    return list(_ad_packs.values())


def delete_ad_pack(pack_id: str) -> bool:
    """Delete an ad pack."""
    if pack_id in _ad_packs:
        del _ad_packs[pack_id]
        return True
    return False
