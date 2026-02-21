"""
AdPack and related models — the output of the creative assembly pipeline.

An AdPack is a complete set of ad creatives ready for preview and Meta API submission.
"""

from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class GeneratedCreative(BaseModel):
    """A single generated creative asset with copy and metadata."""
    id: str
    ad_type_id: str  # references AdTypeDefinition.id
    strategy: Literal["product_aware", "product_unaware"]
    format: Literal["static", "video", "carousel"]
    aspect_ratio: str  # "1:1", "9:16", "1.91:1"

    # Asset
    asset_url: str | None = None  # S3 URL
    asset_hash: str | None = None  # Meta image hash after upload
    video_id: str | None = None  # Meta video ID if video

    # Ad copy
    primary_text: str = ""
    headline: str = ""
    description: str | None = None
    cta_type: str = "SHOP_NOW"

    # Variant info
    variant_label: str | None = None  # e.g. "benefit-first, gradient bg"

    # Metadata
    created_at: datetime | None = None
    generation_time_ms: int = 0


class TargetingSpec(BaseModel):
    """Targeting configuration derived from persona analysis."""
    geo_locations: dict = {"countries": ["US"]}
    age_min: int = 18
    age_max: int = 65
    genders: list[int] | None = None  # [1]=male, [2]=female, None=all

    # Advantage+ broad targeting
    targeting_optimization: str = "expansion_all"

    # Exclusions derived from persona
    exclusions: dict | None = None

    # Human-readable rationale
    targeting_rationale: str = ""


class AdPack(BaseModel):
    """
    Complete ad pack ready for preview and Meta API launch.

    Contains creatives from both strategies, targeting, and campaign config.
    """
    id: str
    created_at: datetime | None = None

    # Source parameters
    source_url: str | None = None
    product_name: str = ""
    brand_logo_url: str | None = None
    language: str = "en"

    # Generated assets
    creatives: list[GeneratedCreative] = []

    # Campaign config
    targeting: TargetingSpec = TargetingSpec()
    budget_daily_cents: int = 1500  # $15/day default
    duration_days: int = 3

    # Campaign structure
    campaign_name: str = ""
    campaign_objective: str = "OUTCOME_TRAFFIC"

    # Status tracking
    status: Literal[
        "generating", "draft", "ready", "launched", "failed"
    ] = "generating"

    # Meta IDs (populated after launch)
    meta_campaign_id: str | None = None
    meta_adset_id: str | None = None
    meta_ad_ids: list[str] = []
