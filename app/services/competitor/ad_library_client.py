"""
Meta Ad Library API Client
Fetches active ads for competitors from the Meta Ad Library.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import httpx

logger = logging.getLogger(__name__)

AD_LIBRARY_URL = "https://graph.facebook.com/v18.0/ads_archive"

# Fields to request from the Ad Library API
AD_FIELDS = [
    "id",
    "ad_creative_bodies",
    "ad_creative_link_titles",
    "ad_creative_link_descriptions",
    "ad_creative_link_captions",
    "ad_snapshot_url",
    "page_id",
    "page_name",
    "publisher_platforms",
    "estimated_audience_size",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "impressions",
    "spend",
]


def _calculate_days_active(start_time: Optional[str], stop_time: Optional[str] = None) -> int:
    """
    Calculate how many days an ad has been running.
    Ads running 30+ days are likely profitable.
    """
    if not start_time:
        return 0
    try:
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end = (
            datetime.fromisoformat(stop_time.replace("Z", "+00:00"))
            if stop_time
            else datetime.now(timezone.utc)
        )
        return max(0, (end - start).days)
    except (ValueError, TypeError):
        return 0


def _parse_ad(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a raw Ad Library API response into a clean CompetitorAd dict."""
    bodies = raw.get("ad_creative_bodies", [])
    titles = raw.get("ad_creative_link_titles", [])
    descriptions = raw.get("ad_creative_link_descriptions", [])
    captions = raw.get("ad_creative_link_captions", [])

    days_active = _calculate_days_active(
        raw.get("ad_delivery_start_time"),
        raw.get("ad_delivery_stop_time"),
    )

    audience = raw.get("estimated_audience_size", {})
    audience_lower = audience.get("lower_bound", 0) if isinstance(audience, dict) else 0
    audience_upper = audience.get("upper_bound", 0) if isinstance(audience, dict) else 0

    return {
        "ad_id": raw.get("id", ""),
        "copy": bodies[0] if bodies else "",
        "headline": titles[0] if titles else "",
        "description": descriptions[0] if descriptions else "",
        "caption": captions[0] if captions else "",
        "snapshot_url": raw.get("ad_snapshot_url", ""),
        "page_id": raw.get("page_id", ""),
        "page_name": raw.get("page_name", ""),
        "platforms": raw.get("publisher_platforms", []),
        "audience_size_lower": audience_lower,
        "audience_size_upper": audience_upper,
        "start_time": raw.get("ad_delivery_start_time"),
        "stop_time": raw.get("ad_delivery_stop_time"),
        "days_active": days_active,
        "likely_profitable": days_active >= 30,
    }


async def fetch_competitor_ads(
    page_id: Optional[str] = None,
    search_terms: Optional[str] = None,
    access_token: Optional[str] = None,
    country: str = "US",
    limit: int = 50,
    ad_type: str = "ALL",
) -> Dict[str, Any]:
    """
    Fetch active ads from the Meta Ad Library API.

    Args:
        page_id: Facebook Page ID to fetch ads for
        search_terms: Search keywords (alternative to page_id)
        access_token: Meta API access token
        country: Country code for ad reach (default: US)
        limit: Max number of ads to fetch (handles pagination)
        ad_type: Type filter: ALL, POLITICAL_AND_ISSUE_ADS, etc.

    Returns:
        Dict with ads list and metadata
    """
    if not access_token:
        import os
        access_token = os.environ.get("META_ACCESS_TOKEN", "")

    if not access_token:
        return {
            "ads": [],
            "total": 0,
            "error": "No Meta access token available. Set META_ACCESS_TOKEN in .env",
        }

    if not page_id and not search_terms:
        return {
            "ads": [],
            "total": 0,
            "error": "Either page_id or search_terms is required",
        }

    params: Dict[str, Any] = {
        "access_token": access_token,
        "ad_reached_countries": f'["{country}"]',
        "ad_active_status": "ACTIVE",
        "ad_type": ad_type,
        "fields": ",".join(AD_FIELDS),
        "limit": min(limit, 100),  # API max per page is ~100
    }

    if page_id:
        params["search_page_ids"] = page_id
    elif search_terms:
        params["search_terms"] = search_terms

    all_ads: List[Dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            next_url = AD_LIBRARY_URL

            while next_url and len(all_ads) < limit:
                if next_url == AD_LIBRARY_URL:
                    resp = await client.get(next_url, params=params)
                else:
                    # Pagination URL already has params
                    resp = await client.get(next_url)

                data = resp.json()

                if "error" in data:
                    error_msg = data["error"].get("message", "Unknown error")
                    logger.error(f"Ad Library API error: {error_msg}")
                    return {
                        "ads": all_ads,
                        "total": len(all_ads),
                        "error": error_msg,
                    }

                raw_ads = data.get("data", [])
                for raw_ad in raw_ads:
                    parsed = _parse_ad(raw_ad)
                    all_ads.append(parsed)

                # Handle pagination
                paging = data.get("paging", {})
                next_url = paging.get("next") if len(all_ads) < limit else None

                if not raw_ads:
                    break  # No more results

        logger.info(f"Fetched {len(all_ads)} ads for page_id={page_id}, search={search_terms}")

        return {
            "ads": all_ads[:limit],
            "total": len(all_ads),
            "profitable_count": sum(1 for a in all_ads if a.get("likely_profitable")),
        }

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching ads: {e}")
        return {
            "ads": [],
            "total": 0,
            "error": f"HTTP error: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Error fetching competitor ads: {e}", exc_info=True)
        return {
            "ads": [],
            "total": 0,
            "error": str(e),
        }
