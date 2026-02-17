"""
Competitor Intelligence Router
Endpoints for competitor analysis, ad library lookups, and gap analysis.
"""

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings
from app.models import (
    CompetitorProfile,
    CompetitorIntelligence,
    GapRecommendation,
)
from app.services.competitor import (
    discover_competitor,
    resolve_facebook_page_id,
    fetch_competitor_ads,
    analyze_competitor_ads,
    aggregate_patterns,
    analyze_gaps,
    generate_recommendations,
)
from app.services.jobs import create_job, update_job, JobStatus

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/competitors", tags=["competitors"])


# =====================================
# Request / Response models
# =====================================

class CompetitorInput(BaseModel):
    name_or_url: str


class AnalyzeCompetitorsRequest(BaseModel):
    competitors: List[CompetitorInput]
    user_context: Optional[str] = None  # Description of user's product


class CompetitorIntelligenceResponse(BaseModel):
    job_id: str
    status: str


# =====================================
# Endpoints
# =====================================

@router.post("/analyze", response_model=CompetitorIntelligenceResponse)
@limiter.limit("5/minute")
async def analyze_competitors(request: Request, data: AnalyzeCompetitorsRequest):
    """
    Start async competitor intelligence analysis.
    Discovers competitors, fetches their ads, analyzes patterns, and finds gaps.

    Returns job_id - poll /jobs/{job_id} for results.
    """
    if not data.competitors:
        raise HTTPException(status_code=400, detail="At least one competitor is required")

    if len(data.competitors) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 competitors allowed")

    job_id = create_job("competitor_analysis")

    asyncio.create_task(
        _run_competitor_analysis(job_id, data.competitors, data.user_context)
    )

    return CompetitorIntelligenceResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
    )


@router.post("/discover")
@limiter.limit("10/minute")
async def discover_single_competitor(request: Request, data: CompetitorInput):
    """
    Discover a single competitor - resolve URL, scrape positioning data.
    Synchronous endpoint for quick lookups.
    """
    try:
        profile = await discover_competitor(data.name_or_url)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Competitor discovery failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to discover competitor")


@router.get("/ads/{page_id}")
@limiter.limit("5/minute")
async def get_competitor_ads(request: Request, page_id: str, limit: int = 25):
    """
    Fetch active ads for a specific Facebook Page ID from the Ad Library.
    """
    settings = get_settings()
    access_token = settings.meta_access_token

    result = await fetch_competitor_ads(
        page_id=page_id,
        access_token=access_token or None,
        limit=min(limit, 100),
    )

    if result.get("error"):
        raise HTTPException(status_code=502, detail=result["error"])

    return result


# =====================================
# Background task
# =====================================

async def _run_competitor_analysis(
    job_id: str,
    competitors: List[CompetitorInput],
    user_context: Optional[str] = None,
):
    """Background task that runs the full competitor intelligence pipeline."""
    try:
        update_job(job_id, JobStatus.PROCESSING)
        settings = get_settings()
        access_token = settings.meta_access_token or None

        # 1. Discover all competitors (parallel)
        discovery_tasks = [
            discover_competitor(c.name_or_url) for c in competitors
        ]
        profiles_raw = await asyncio.gather(*discovery_tasks, return_exceptions=True)

        profiles = []
        for i, result in enumerate(profiles_raw):
            if isinstance(result, Exception):
                logger.warning(f"Competitor discovery failed for {competitors[i].name_or_url}: {result}")
                profiles.append({
                    "name": competitors[i].name_or_url,
                    "url": None,
                    "error": str(result),
                })
            else:
                profiles.append(result)

        # 2. Resolve Facebook Page IDs (parallel)
        page_id_tasks = []
        for profile in profiles:
            url = profile.get("url")
            if url and access_token:
                page_id_tasks.append(resolve_facebook_page_id(url, access_token))
            else:
                page_id_tasks.append(_return_none())

        page_ids = await asyncio.gather(*page_id_tasks, return_exceptions=True)

        for i, page_id in enumerate(page_ids):
            if isinstance(page_id, Exception):
                page_id = None
            profiles[i]["facebook_page_id"] = page_id

        # 3. Fetch ads from Ad Library (parallel)
        all_ads = []
        ad_tasks = []
        for profile in profiles:
            page_id = profile.get("facebook_page_id")
            name = profile.get("name", "")
            if page_id:
                ad_tasks.append(
                    fetch_competitor_ads(
                        page_id=page_id,
                        access_token=access_token,
                        limit=50,
                    )
                )
            elif name:
                # Fallback: search by name
                ad_tasks.append(
                    fetch_competitor_ads(
                        search_terms=name,
                        access_token=access_token,
                        limit=25,
                    )
                )
            else:
                ad_tasks.append(_return_empty_ads())

        ad_results = await asyncio.gather(*ad_tasks, return_exceptions=True)

        for i, result in enumerate(ad_results):
            if isinstance(result, Exception):
                logger.warning(f"Ad fetch failed for {profiles[i].get('name', '')}: {result}")
                profiles[i]["ad_count"] = 0
            else:
                ads = result.get("ads", [])
                profiles[i]["ad_count"] = len(ads)
                all_ads.extend(ads)

        # 4. Analyze ads with LLM
        analyzed_ads = await analyze_competitor_ads(all_ads)

        # 5. Aggregate patterns
        aggregated = aggregate_patterns(analyzed_ads, profiles)

        # 6. Gap analysis
        gap_result = await analyze_gaps(
            aggregated_patterns=aggregated,
            competitor_profiles=profiles,
            user_context=user_context or "",
        )

        # 7. Generate recommendations
        recs_raw = generate_recommendations(gap_result, aggregated)
        recs = [
            GapRecommendation(**r).model_dump()
            for r in recs_raw
        ]

        # 8. Build competitor profiles for response
        competitor_profiles_out = []
        for p in profiles:
            competitor_profiles_out.append(
                CompetitorProfile(
                    name=p.get("name", "Unknown"),
                    url=p.get("url"),
                    positioning=p.get("positioning", ""),
                    claims=p.get("claims", []),
                    pricing=p.get("pricing"),
                    differentiators=p.get("differentiators", []),
                    facebook_page_id=p.get("facebook_page_id"),
                    ad_count=p.get("ad_count", 0),
                    error=p.get("error"),
                ).model_dump()
            )

        # 9. Build full intelligence report
        intelligence = CompetitorIntelligence(
            competitors=[CompetitorProfile(**cp) for cp in competitor_profiles_out],
            total_ads_analyzed=aggregated.get("total_ads", 0),
            profitable_ads_count=aggregated.get("profitable_ads", 0),
            hook_distribution=aggregated.get("hook_distribution", {}),
            angle_distribution=aggregated.get("angle_distribution", {}),
            cta_distribution=aggregated.get("cta_distribution", {}),
            format_distribution=aggregated.get("format_distribution", {}),
            top_hooks=aggregated.get("top_hooks", []),
            top_angles=aggregated.get("top_angles", []),
            avg_strength=aggregated.get("avg_strength", 0),
            gap_analysis=gap_result,
            recommendations=[GapRecommendation(**r) for r in recs],
            confidence_score=gap_result.get("confidence_score", 0),
            status="complete",
        )

        update_job(job_id, JobStatus.COMPLETE, result=intelligence.model_dump())
        logger.info(f"Competitor analysis job {job_id} completed: {len(all_ads)} ads analyzed")

    except Exception as e:
        logger.error(f"Competitor analysis job {job_id} failed: {e}", exc_info=True)
        update_job(job_id, JobStatus.FAILED, error=str(e))


async def _return_none():
    """Helper coroutine that returns None."""
    return None


async def _return_empty_ads():
    """Helper coroutine that returns empty ads result."""
    return {"ads": [], "total": 0}
