"""
V2 API Router — dual-strategy creative generation pipeline.

POST /v2/analyze            → Extract CreativeParameters from URL
POST /v2/render             → Render static images for an AdPack
GET  /v2/ad-types           → List available ad types in the registry
GET  /v2/templates          → List all ad templates
GET  /v2/templates/{type}   → Get templates for a specific ad type
POST /v2/templates          → Create/update a template
PUT  /v2/templates/{id}     → Update a template by ID
POST /v2/templates/{id}/render → Render a template with given params
"""

import asyncio
import json
import logging
import os
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.schemas.creative_params import CreativeParameters
from app.schemas.ad_types import AdTypeDefinition
from app.schemas.ad_pack import (
    AdPack, GeneratedCreative, TargetingSpec,
    PrepareRequest, PreparedCampaign, GenerateRequest,
    CompetitorInsight,
)
from app.services.scraper import scrape_landing_page
from app.services.v2.parameter_extractor import (
    extract_creative_parameters,
    ExtractionError,
)
from app.services.v2.template_selector import select_templates
from app.services.v2.copy_generator import (
    generate_copy_from_template,
    generate_competition_copy,
    translate_copy,
    translate_params,
    _resolve_variable,
)
from app.services.v2.ad_type_registry import get_registry, get_ad_type
from app.services.v2.social_template_bridges import (
    bridge_branded_static,
    bridge_reddit,
    bridge_problem_statement,
    bridge_review_static,
    bridge_service_hero,
    bridge_product_centric,
    bridge_person_centric,
    bridge_branded_static_video,
    bridge_service_hero_video,
)
from app.services.v2.render_pipeline import (
    dispatch_render,
    render_static_creatives,
    render_competition_blog,
    upload_to_s3,
    upload_video_to_s3,
    build_targeting,
    add_manual_image_creative,
    build_manual_copy,
    competition_copy_store,
)
from app.services.v2.ugc_avatar_renderer import render_ugc_avatar, UGCAvatarResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2", tags=["v2"])

# In-memory stores for on-demand rendering
_pack_params: dict[str, CreativeParameters] = {}  # pack_id → params
_pack_scraped: dict[str, dict] = {}  # pack_id → scraped_data
_render_cache: dict[str, tuple[bytes, float]] = {}  # render_id → (PNG bytes, timestamp)
# competition_copy_store imported from render_pipeline

# Unified flow: session cache for prepare → generate handoff
# session_id → { params, scraped_data, competitor_data, image_url, ts }
SESSION_TTL = 1800  # 30 minutes
_prepared_sessions: dict[str, dict] = {}

# Persist paths (survive restarts)
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
LAST_PARAMS_PATH = DATA_DIR / "last_params.json"
PACKS_DIR = DATA_DIR / "packs"


def _persist_params(params: CreativeParameters) -> None:
    """Write CreativeParameters to disk for playground use."""
    try:
        LAST_PARAMS_PATH.parent.mkdir(parents=True, exist_ok=True)
        LAST_PARAMS_PATH.write_text(
            json.dumps(params.model_dump(mode="json"), indent=2)
        )
    except Exception as e:
        logger.warning(f"Failed to persist params: {e}")


def _persist_pack_data(pack_id: str, params: CreativeParameters, scraped_data: dict) -> None:
    """Persist pack params + scraped data to disk so render/pack survives restarts."""
    try:
        PACKS_DIR.mkdir(parents=True, exist_ok=True)
        pack_file = PACKS_DIR / f"{pack_id}.json"
        pack_file.write_text(json.dumps({
            "params": params.model_dump(mode="json"),
            "scraped": scraped_data,
        }))
    except Exception as e:
        logger.warning(f"Failed to persist pack data: {e}")


def _load_pack_data(pack_id: str) -> tuple[CreativeParameters | None, dict | None]:
    """Load pack params + scraped data from disk if not in memory."""
    try:
        pack_file = PACKS_DIR / f"{pack_id}.json"
        if not pack_file.exists():
            return None, None
        data = json.loads(pack_file.read_text())
        params = CreativeParameters(**data["params"])
        scraped = data.get("scraped", {})
        # Re-populate in-memory caches
        _pack_params[pack_id] = params
        _pack_scraped[pack_id] = scraped
        return params, scraped
    except Exception as e:
        logger.warning(f"Failed to load pack data for {pack_id}: {e}")
        return None, None


def _register_v2_pack_in_v1_store(pack: AdPack, source_url: str) -> None:
    """Register V2 AdPack in V1 adpack service so PATCH /adpack/{id} works."""
    try:
        from app.models import (
            AdPack as V1AdPack,
            AdCreative as V1AdCreative,
            SmartBroadTargeting,
            TargetingRationale,
            CampaignStructure,
        )
        from app.services.adpack import _ad_packs

        v1_creatives = []
        for c in pack.creatives:
            v1_creatives.append(V1AdCreative(
                id=c.id,
                strategy=c.strategy,
                primary_text=c.primary_text or "",
                headline=c.headline or "",
                description=c.description or "",
                image_url=c.asset_url,
                call_to_action=c.cta_type or "LEARN_MORE",
            ))

        t = pack.targeting
        geo_countries = t.geo_locations.get("countries", ["US"]) if t and t.geo_locations else ["US"]
        v1_targeting = SmartBroadTargeting(
            age_min=t.age_min if t else 18,
            age_max=t.age_max if t else 65,
            genders=["all"],
            geo_locations=geo_countries,
            rationale=TargetingRationale(
                age_range_reason=t.targeting_rationale or "" if t else "",
                geo_reason=f"Targeting {', '.join(geo_countries)}",
            ),
        )

        v1_pack = V1AdPack(
            id=pack.id,
            project_url=source_url,
            creatives=v1_creatives,
            targeting=v1_targeting,
            budget_daily=(pack.budget_daily_cents or 1500) / 100,
            duration_days=pack.duration_days or 3,
            campaign_structure=CampaignStructure(
                campaign_name=pack.campaign_name or "Campaign",
                adset_name=f"{pack.product_name or 'Campaign'} — Smart Broad",
                ad_count=len(v1_creatives),
            ),
            status=pack.status or "draft",
            brand_logo_url=pack.brand_logo_url,
        )

        _ad_packs[pack.id] = v1_pack
        logger.info(f"Registered V2 pack {pack.id} in V1 adpack store")
    except Exception as e:
        logger.warning(f"Failed to register V2 pack in V1 store: {e}")


# --- Request/Response models ---

class AnalyzeRequest(BaseModel):
    url: str
    competitor_url: str | None = None  # optional competitor URL for targeted competition copy
    generate_copy_variants: bool = False  # if True, also generate LLM copy variants
    render_images: bool = False  # if True, also render static images


class AnalyzeResponse(BaseModel):
    parameters: CreativeParameters
    selected_templates: list[dict]  # simplified template info
    ad_pack: AdPack


class TemplateInfo(BaseModel):
    id: str
    name: str
    strategy: str
    format: str
    aspect_ratios: list[str]


# --- Unified Flow: Prepare & Generate ---

DESCRIPTION_EXTRACTION_PROMPT = """You are a world-class performance marketer.

The user described their product/business in their own words:
"{description}"

Extract ALL parameters needed for ad creative generation. Return a JSON object with these fields:

{{
    "product_name": "string — short brand name",
    "business_type": "saas|ecommerce|service",
    "product_category": "string — simple lowercase category",
    "product_description_short": "string — max 15 words",
    "brand_name": "string — company/brand name",
    "key_benefit": "string — single most important benefit",
    "key_differentiator": "string — what makes it unique",
    "value_props": ["3-5 value propositions"],
    "customer_pains": ["3-5 pain points in customer's voice"],
    "customer_desires": ["3-5 desired outcomes"],
    "objections": ["common buying objections"],
    "tone": "premium|casual|clinical|playful|urgent",
    "cta_text": "string — best CTA for this product",
    "social_proof": "null",
    "testimonials": [],
    "urgency_hooks": [],
    "persona_primary": {{
        "label": "string — e.g. 'Health-conscious professional, 30-45'",
        "demographics": {{"age_min": 25, "age_max": 55, "gender_skew": "neutral|male|female"}},
        "psychographics": [],
        "scenes": ["visual scene 1", "scene 2"],
        "language_style": "string",
        "specific_pains": [],
        "specific_desires": []
    }},
    "scene_problem": "string — visual description of problem state",
    "scene_solution": "string — visual description of solved state",
    "scene_lifestyle": "string — aspirational lifestyle visual",
    "language": "{language_hint}",
    "target_countries": ["{country_hint}"],
    "product_summary": "string — 1-2 sentence summary of the product for user review",
    "target_audience": "string — who this product is for (e.g. 'Small business owners who need accounting automation')",
    "main_pain_point": "string — the core problem it solves or opportunity it creates",
    "messaging_unaware": "string — ad messaging angle for users who don't know they have this problem yet",
    "messaging_aware": "string — ad messaging angle for users who know the problem and are comparing solutions",
    "competitors": [
        {{"name": "string — competitor name", "weakness": "string — their main weakness from customer perspective"}}
    ]
}}

RULES:
- Infer intelligently from the description
- customer_pains in customer's voice
- product_summary should be a clear, concise explanation a user can review and edit
- competitors: Think about what someone would find if they searched "[product_name] alternatives" or "[product_name] vs". Identify the top 3 most commonly cited competitors or alternatives. For each, find their key weakness from typical negative customer feedback (something we can use as ad differentiation). You MUST try hard — most products have known alternatives. Only return empty array for truly novel categories.
- target_audience: describe the ideal customer profile concisely
- messaging_unaware: angle for people who don't realize they need this yet
- messaging_aware: angle for people actively comparing solutions
- Always return valid JSON
"""


def _cleanup_sessions():
    """Evict expired prepare sessions."""
    now = time.time()
    expired = [k for k, v in _prepared_sessions.items() if now - v.get("ts", 0) > SESSION_TTL]
    for k in expired:
        del _prepared_sessions[k]


async def _extract_params_from_description(description: str) -> tuple[CreativeParameters, str]:
    """Extract CreativeParameters from freeform text description via Gemini.
    Returns (params, product_summary)."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ExtractionError("GOOGLE_API_KEY not configured")

    from google import genai
    client = genai.Client(api_key=api_key)

    prompt = DESCRIPTION_EXTRACTION_PROMPT.format(
        description=description[:4000],
        language_hint="en",
        country_hint="US",
    )

    result = await client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    data = json.loads(result.text)
    if isinstance(data, list) and data:
        data = data[0]

    product_summary = data.pop("product_summary", description[:200])
    target_audience = data.pop("target_audience", "")
    main_pain_point = data.pop("main_pain_point", "")
    messaging_unaware = data.pop("messaging_unaware", "")
    messaging_aware = data.pop("messaging_aware", "")
    raw_competitors = data.pop("competitors", [])

    # Build CreativeParameters from LLM output
    from app.schemas.creative_params import BrandColors, PersonaDemographics, TargetPersona

    persona_primary = None
    if data.get("persona_primary"):
        p = data["persona_primary"]
        demo = p.get("demographics", {})
        persona_primary = TargetPersona(
            label=p.get("label", "General audience"),
            demographics=PersonaDemographics(
                age_min=demo.get("age_min", 18),
                age_max=demo.get("age_max", 65),
                gender_skew=demo.get("gender_skew", "neutral"),
            ),
            psychographics=p.get("psychographics", []),
            scenes=p.get("scenes", []),
            language_style=p.get("language_style", "Conversational"),
            specific_pains=p.get("specific_pains", []),
            specific_desires=p.get("specific_desires", []),
        )

    params = CreativeParameters(
        source_description=description,
        product_name=data.get("product_name", "Product"),
        business_type=data.get("business_type", "ecommerce") if data.get("business_type") in ("ecommerce", "saas", "service") else "ecommerce",
        product_category=data.get("product_category", "General"),
        product_description_short=data.get("product_description_short", ""),
        brand_name=data.get("brand_name", ""),
        key_benefit=data.get("key_benefit", ""),
        key_differentiator=data.get("key_differentiator", ""),
        value_props=data.get("value_props", []),
        customer_pains=data.get("customer_pains", []),
        customer_desires=data.get("customer_desires", []),
        objections=data.get("objections", []),
        tone=data.get("tone", "casual"),
        cta_text=data.get("cta_text", "Learn More"),
        social_proof=data.get("social_proof"),
        testimonials=data.get("testimonials", []),
        urgency_hooks=data.get("urgency_hooks", []),
        persona_primary=persona_primary,
        scene_problem=data.get("scene_problem"),
        scene_solution=data.get("scene_solution"),
        scene_lifestyle=data.get("scene_lifestyle"),
        language=data.get("language", "en"),
        target_countries=data.get("target_countries", ["US"]),
        headline=data.get("product_name", "Product"),
    )

    return params, product_summary, target_audience, main_pain_point, messaging_unaware, messaging_aware, raw_competitors


REVIEW_ANALYSIS_PROMPT = """You are a world-class performance marketer analyzing a product for ad creation.

Product: {product_name}
Category: {product_category}
Key Benefit: {key_benefit}
Key Differentiator: {key_differentiator}
Customer Pains: {customer_pains}
Description: {product_description}
Source URL: {source_url}

Based on this analysis, return a JSON object:

{{
    "product_summary": "string — 1-2 sentence description of the product",
    "target_audience": "string — who this product is for (concise ideal customer profile)",
    "main_pain_point": "string — the core problem it solves or opportunity it creates",
    "messaging_unaware": "string — ad messaging angle for users who don't know they have this problem",
    "messaging_aware": "string — ad messaging angle for users who know the problem and are comparing solutions",
    "competitors": [
        {{"name": "string — competitor name", "weakness": "string — their main weakness based on common negative customer feedback"}}
    ]
}}

RULES:
- competitors: Think about what someone would find if they searched "[product_name] alternatives" or "[product_name] vs". Identify the top 3 most commonly cited competitors or alternatives in this product category. For each competitor, identify their key weakness based on common negative customer feedback, reviews, and complaints (something we can use for ad differentiation). You MUST try hard to find competitors — most products have known alternatives. Only return empty array if this is a truly novel category with no alternatives.
- target_audience: describe the ideal customer concisely
- messaging_unaware: angle for people who don't realize they need this yet
- messaging_aware: angle for people actively comparing solutions
- Write in {language}
- Always return valid JSON
"""


async def _extract_review_analysis(params: CreativeParameters, source_url: str = "") -> dict:
    """Extract target audience, pain point, messaging, and competitors from params via Gemini."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {}

    from google import genai
    client = genai.Client(api_key=api_key)

    language_name = params.language or "en"
    prompt = REVIEW_ANALYSIS_PROMPT.format(
        product_name=params.product_name,
        product_category=params.product_category or "general",
        key_benefit=params.key_benefit or "",
        key_differentiator=params.key_differentiator or "",
        customer_pains=", ".join(params.customer_pains[:5]) if params.customer_pains else "unknown",
        product_description=params.product_description_short or "",
        source_url=source_url,
        language=language_name,
    )

    try:
        result = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(result.text)
        if isinstance(data, list) and data:
            data = data[0]
        return data
    except Exception as e:
        logger.warning(f"Review analysis extraction failed: {e}")
        return {}


@router.post("/prepare", response_model=PreparedCampaign)
async def prepare_campaign(body: PrepareRequest):
    """
    Step 1 of unified flow: analyze input (URL or description),
    extract parameters, return summary for user review.
    No creatives generated yet.
    """
    _cleanup_sessions()

    if not body.url and not body.description:
        raise HTTPException(status_code=400, detail="Provide url or description")

    session_id = str(uuid.uuid4())[:12]
    scraped_data = {}
    product_summary = ""
    target_audience = ""
    main_pain_point = ""
    messaging_unaware = ""
    messaging_aware = ""
    raw_competitors: list[dict] = []

    if body.url:
        # URL path: scrape + extract
        try:
            scraped_data = await scrape_landing_page(body.url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if not scraped_data.get("full_text"):
            raise HTTPException(status_code=400, detail="Failed to scrape URL")

        try:
            params, review_data = await extract_creative_parameters(scraped_data, source_url=body.url)
        except ExtractionError as e:
            raise HTTPException(status_code=422, detail=f"Extraction failed: {e}")

        # Review fields extracted in single Gemini call above
        product_summary = review_data.get("product_summary") or params.product_description_short or f"{params.product_name} — {params.key_benefit}"
        target_audience = review_data.get("target_audience", "")
        main_pain_point = review_data.get("main_pain_point", "")
        messaging_unaware = review_data.get("messaging_unaware", "")
        messaging_aware = review_data.get("messaging_aware", "")
        raw_competitors = review_data.get("competitors", [])

    else:
        # Description-only path: LLM extraction from freeform text
        try:
            params, product_summary, target_audience, main_pain_point, messaging_unaware, messaging_aware, raw_competitors = await _extract_params_from_description(body.description)
        except Exception as e:
            logger.error(f"Description extraction failed: {e}", exc_info=True)
            raise HTTPException(status_code=422, detail=f"Could not analyze description: {e}")

    # Translate params for non-English
    if params.language and params.language != "en":
        params = await translate_params(params)

    # Build competitors list (max 3)
    competitors = []
    for c in (raw_competitors or [])[:3]:
        if isinstance(c, dict) and c.get("name"):
            competitors.append(CompetitorInsight(
                name=c["name"],
                weakness=c.get("weakness", ""),
            ))

    # Cache session for generate step
    _prepared_sessions[session_id] = {
        "params": params,
        "scraped_data": scraped_data,
        "image_url": body.image_url,
        "ts": time.time(),
    }

    return PreparedCampaign(
        session_id=session_id,
        product_name=params.product_name,
        product_summary=product_summary,
        brand_logo_url=params.brand_logo_url,
        business_type=params.business_type,
        language=params.language or "en",
        target_countries=params.target_countries or ["US"],
        target_audience=target_audience,
        main_pain_point=main_pain_point,
        messaging_unaware=messaging_unaware,
        messaging_aware=messaging_aware,
        competitors=competitors,
    )


@router.post("/generate")
async def generate_from_prepared(body: GenerateRequest):
    """
    Step 2 of unified flow: generate creatives using cached params + user overrides.
    Returns full AdPack with rendered creatives.
    """
    from app.services.jobs import create_job, cleanup_old_jobs

    session = _prepared_sessions.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session expired or not found. Please re-analyze.")

    if time.time() - session.get("ts", 0) > SESSION_TTL:
        _prepared_sessions.pop(body.session_id, None)
        raise HTTPException(status_code=410, detail="Session expired. Please re-analyze.")

    # Start as background job (same pattern as analyze/async)
    cleanup_old_jobs()
    job_id = create_job(session["params"].source_url or "description")
    asyncio.create_task(_run_generate_job(job_id, body, session))

    # Clean up session after launching job
    _prepared_sessions.pop(body.session_id, None)

    return {"job_id": job_id, "status": "pending"}


async def _run_generate_job(job_id: str, body: GenerateRequest, session: dict):
    """Background task: run creative pipeline with prepared params + user overrides."""
    from app.services.jobs import update_job, JobStatus
    try:
        update_job(job_id, JobStatus.PROCESSING)

        params: CreativeParameters = session["params"]
        scraped_data: dict = session.get("scraped_data", {})
        image_url = session.get("image_url")

        # Apply user-selected language override (mandatory on frontend)
        original_language = params.language or "en"
        if body.language:
            params.language = body.language

        # Re-translate params if user changed the language (including to English)
        if params.language != original_language:
            params = await translate_params(params, force=True)

        # Build targeting from params (not user-editable at this stage)
        targeting = build_targeting(params)
        budget_cents = 1500
        duration = 3

        # Template selection
        selected = select_templates(params)
        if not selected:
            raise ValueError("No templates could be selected")

        # Apply user overrides from review page to params
        if body.product_summary:
            params.product_description_short = body.product_summary
        # Competitor info stored for potential use in competition copy
        competitor_data = None  # auto-detected competitors are informational only

        # Copy generation
        creatives: list[GeneratedCreative] = []
        needs_translation = params.language and params.language != "en"
        for template in selected:
            if template.id == "review_static_competition":
                base_copy = await generate_competition_copy(template, params, competitor_data)
            else:
                base_copy = generate_copy_from_template(template, params)
                if needs_translation:
                    base_copy = await translate_copy(base_copy, params)

            creative = GeneratedCreative(
                id=str(uuid.uuid4())[:12],
                ad_type_id=template.id,
                strategy=template.strategy,
                format=template.format,
                aspect_ratio="1:1",
                primary_text=base_copy["primary_text"],
                headline=base_copy["headline"],
                description=base_copy.get("description"),
                cta_type=base_copy["cta_type"],
                created_at=datetime.now(timezone.utc),
            )
            creatives.append(creative)

            if template.id == "review_static_competition":
                competition_copy_store[creative.id] = dict(base_copy)

        # Render statics
        creatives = await render_static_creatives(creatives, selected, params, scraped_data)

        # Add manual image creative if user uploaded
        if image_url:
            await add_manual_image_creative(creatives, image_url, None, params)

        # Assemble AdPack
        source = params.source_url or "description"
        pack = AdPack(
            id=str(uuid.uuid4())[:12],
            created_at=datetime.now(timezone.utc),
            source_url=params.source_url,
            product_name=params.product_name,
            brand_logo_url=params.brand_logo_url,
            language=params.language or "en",
            creatives=creatives,
            targeting=targeting,
            budget_daily_cents=budget_cents,
            duration_days=duration,
            campaign_name=f"{params.product_name} — {datetime.now().strftime('%b %Y')}",
            status="draft",
        )

        _pack_params[pack.id] = params
        _pack_scraped[pack.id] = scraped_data
        _persist_params(params)
        _register_v2_pack_in_v1_store(pack, source)

        result = {
            "parameters": params.model_dump(mode="json"),
            "ad_pack": pack.model_dump(mode="json"),
        }
        update_job(job_id, JobStatus.COMPLETE, result=result)
        logger.info(f"Generate job {job_id} completed: {len(creatives)} creatives")

    except Exception as e:
        logger.error(f"Generate job {job_id} failed: {e}", exc_info=True)
        update_job(job_id, JobStatus.FAILED, error=str(e))


# --- Endpoints ---

@router.get("/ad-types", response_model=list[TemplateInfo])
async def list_ad_types():
    """List all ad types in the registry."""
    registry = get_registry()
    return [
        TemplateInfo(
            id=t.id,
            name=t.name,
            strategy=t.strategy,
            format=t.format,
            aspect_ratios=t.aspect_ratios,
        )
        for t in registry.values()
    ]


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_v2(request: Request, body: AnalyzeRequest):
    """
    Full v2 analysis pipeline:
    1. Scrape URL
    2. Extract CreativeParameters (scraper + Gemini)
    3. Select templates (two-pass algorithm)
    4. Generate base copy for each selected template
    5. Return AdPack with creatives (images not yet generated)
    """
    # 1. Scrape (main URL + optional competitor in parallel)
    try:
        if body.competitor_url:
            scraped_data, competitor_data = await asyncio.gather(
                scrape_landing_page(body.url),
                scrape_landing_page(body.competitor_url),
            )
            logger.info(f"Scraped competitor: {body.competitor_url} ({len(competitor_data.get('full_text', ''))} chars)")
        else:
            scraped_data = await scrape_landing_page(body.url)
            competitor_data = None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not scraped_data.get("full_text"):
        raise HTTPException(status_code=400, detail="Failed to scrape URL or empty content")

    # 2. Extract parameters
    try:
        params, _ = await extract_creative_parameters(scraped_data, source_url=body.url)
    except ExtractionError as e:
        logger.error(f"Parameter extraction failed for {body.url}: {e}")
        raise HTTPException(status_code=422, detail=f"Parameter extraction failed: {e}")

    # 2b. Translate params for non-English
    if params.language and params.language != "en":
        params = await translate_params(params)

    # 3. Select templates
    selected = select_templates(params)
    if not selected:
        raise HTTPException(status_code=422, detail="No templates could be selected with available data")

    # 4. Generate copy and build creatives
    creatives: list[GeneratedCreative] = []
    needs_translation = params.language and params.language != "en"
    for template in selected:
        # Competition type uses LLM-generated copy (already language-aware)
        if template.id == "review_static_competition":
            base_copy = await generate_competition_copy(template, params, competitor_data)
        else:
            base_copy = generate_copy_from_template(template, params)
            if needs_translation:
                base_copy = await translate_copy(base_copy, params)

        creative = GeneratedCreative(
            id=str(uuid.uuid4())[:12],
            ad_type_id=template.id,
            strategy=template.strategy,
            format=template.format,
            aspect_ratio="1:1",
            primary_text=base_copy["primary_text"],
            headline=base_copy["headline"],
            description=base_copy.get("description"),
            cta_type=base_copy["cta_type"],
            created_at=datetime.now(timezone.utc),
        )
        creatives.append(creative)

        if template.id == "review_static_competition":
            competition_copy_store[creative.id] = dict(base_copy)

    # 5. Optional: render static images
    if body.render_images:
        creatives = await render_static_creatives(creatives, selected, params, scraped_data)

    # 6. Build targeting from persona
    targeting = build_targeting(params)

    # 7. Assemble AdPack
    pack = AdPack(
        id=str(uuid.uuid4())[:12],
        created_at=datetime.now(timezone.utc),
        source_url=body.url,
        product_name=params.product_name,
        brand_logo_url=params.brand_logo_url,
        language=params.language or "en",
        creatives=creatives,
        targeting=targeting,
        campaign_name=f"{params.product_name} — {datetime.now().strftime('%b %Y')}",
        status="draft",
    )

    _pack_params[pack.id] = params
    _pack_scraped[pack.id] = scraped_data
    _persist_params(params)
    _persist_pack_data(pack.id, params, scraped_data)
    _register_v2_pack_in_v1_store(pack, body.url)

    # Template info for response
    template_info = [
        {
            "id": t.id,
            "name": t.name,
            "strategy": t.strategy,
            "format": t.format,
        }
        for t in selected
    ]

    return AnalyzeResponse(
        parameters=params,
        selected_templates=template_info,
        ad_pack=pack,
    )


# --- Async V2 analysis (job-based, for frontend polling) ---

class AsyncAnalyzeRequest(BaseModel):
    url: str
    competitor_url: str | None = None  # optional competitor URL for targeted competition copy
    image_url: str | None = None  # optional user image for manual_image_upload creative
    edit_prompt: str | None = None  # optional Gemini edit prompt for the image


class AsyncJobResponse(BaseModel):
    job_id: str
    status: str
    url: str


@router.post("/analyze/async", response_model=AsyncJobResponse)
async def analyze_v2_async(body: AsyncAnalyzeRequest):
    """Start V2 analysis as background job. Poll /jobs/{job_id} for results."""
    from app.services.jobs import create_job, cleanup_old_jobs
    cleanup_old_jobs()
    job_id = create_job(body.url)
    asyncio.create_task(_run_v2_job(
        job_id, body.url,
        competitor_url=body.competitor_url,
        image_url=body.image_url,
        edit_prompt=body.edit_prompt,
    ))
    return AsyncJobResponse(job_id=job_id, status="pending", url=body.url)


async def _run_v2_job(
    job_id: str,
    url: str,
    competitor_url: str | None = None,
    image_url: str | None = None,
    edit_prompt: str | None = None,
):
    """Background task: run full V2 pipeline, store result in job store."""
    from app.services.jobs import update_job, JobStatus
    try:
        update_job(job_id, JobStatus.PROCESSING)

        # 1. Scrape (main URL + optional competitor in parallel)
        if competitor_url:
            scraped_data, competitor_data = await asyncio.gather(
                scrape_landing_page(url),
                scrape_landing_page(competitor_url),
            )
            logger.info(f"Scraped competitor: {competitor_url} ({len(competitor_data.get('full_text', ''))} chars)")
        else:
            scraped_data = await scrape_landing_page(url)
            competitor_data = None

        if not scraped_data.get("full_text"):
            raise ValueError("Failed to scrape URL or empty content")

        # 2. Extract parameters
        params, _ = await extract_creative_parameters(scraped_data, source_url=url)

        # 2b. Translate params for non-English
        if params.language and params.language != "en":
            params = await translate_params(params)

        # 3. Select templates
        selected = select_templates(params)
        if not selected:
            raise ValueError("No templates could be selected")

        # 4. Generate copy + build creatives (1:1 only per template)
        creatives: list[GeneratedCreative] = []
        needs_translation = params.language and params.language != "en"
        for template in selected:
            # Competition type uses LLM-generated copy (already language-aware)
            if template.id == "review_static_competition":
                base_copy = await generate_competition_copy(template, params, competitor_data)
            else:
                base_copy = generate_copy_from_template(template, params)
                if needs_translation:
                    base_copy = await translate_copy(base_copy, params)
            creative = GeneratedCreative(
                id=str(uuid.uuid4())[:12],
                ad_type_id=template.id,
                strategy=template.strategy,
                format=template.format,
                aspect_ratio="1:1",
                primary_text=base_copy["primary_text"],
                headline=base_copy["headline"],
                description=base_copy.get("description"),
                cta_type=base_copy["cta_type"],
                created_at=datetime.now(timezone.utc),
            )
            creatives.append(creative)

            # Store competition copy for blog rendering
            if template.id == "review_static_competition":
                competition_copy_store[creative.id] = dict(base_copy)

        # 5. Render static images (HTML+Playwright → S3)
        creatives = await render_static_creatives(creatives, selected, params, scraped_data)

        # 5a. UGC avatar video — OFF pending HeyGen cost/quality eval
        # await _render_ugc_avatar_creatives(creatives, selected, params)

        # 5b. Add manual_image_upload creative (#9) if user provided image
        if image_url:
            await add_manual_image_creative(creatives, image_url, edit_prompt, params)

        # 6. Build targeting
        targeting = build_targeting(params)

        # 7. Assemble AdPack
        pack = AdPack(
            id=str(uuid.uuid4())[:12],
            created_at=datetime.now(timezone.utc),
            source_url=url,
            product_name=params.product_name,
            brand_logo_url=params.brand_logo_url,
            language=params.language or "en",
            creatives=creatives,
            targeting=targeting,
            campaign_name=f"{params.product_name} — {datetime.now().strftime('%b %Y')}",
            status="draft",
        )

        _pack_params[pack.id] = params
        _pack_scraped[pack.id] = scraped_data
        _persist_params(params)
        _register_v2_pack_in_v1_store(pack, url)

        # 8. Store result in job — shape matches what frontend expects
        result = {
            "parameters": params.model_dump(mode="json"),
            "ad_pack": pack.model_dump(mode="json"),
        }
        update_job(job_id, JobStatus.COMPLETE, result=result)
        logger.info(f"V2 job {job_id} completed: {len(creatives)} creatives")

    except Exception as e:
        logger.error(f"V2 job {job_id} failed: {e}", exc_info=True)
        update_job(job_id, JobStatus.FAILED, error=str(e))


def _build_video_script(
    template: AdTypeDefinition, params: CreativeParameters
) -> str:
    """Concatenate frame scripts from an ad type definition, resolving variables."""
    parts = []
    for frame in template.frames:
        script_text = frame.get("script", "")
        if script_text:
            resolved = _resolve_variable(script_text, params)
            parts.append(resolved)
    return " ".join(parts)


RENDER_TTL_SECONDS = 3600  # 1 hour


def _cleanup_render_cache():
    """Evict expired render cache entries."""
    now = time.time()
    expired = [k for k, (_, ts) in _render_cache.items() if now - ts > RENDER_TTL_SECONDS]
    for k in expired:
        del _render_cache[k]


@router.get("/renders/{render_id}.png")
async def serve_render(render_id: str):
    """Serve a cached rendered image."""
    from fastapi.responses import Response
    entry = _render_cache.get(render_id)
    if not entry or (time.time() - entry[1]) > RENDER_TTL_SECONDS:
        raise HTTPException(status_code=404, detail="Render not found or expired")
    return Response(
        content=entry[0],
        media_type="image/png",
        headers={"Cache-Control": "max-age=3600"},
    )


class RenderPackRequest(BaseModel):
    pack_id: str
    force: bool = False  # bypass cache, re-render all


class RenderPackItem(BaseModel):
    ad_type_id: str
    aspect_ratio: str
    image_url: str
    generation_time_ms: int


class RenderPackResponse(BaseModel):
    renders: list[RenderPackItem]


@router.post("/render/pack", response_model=RenderPackResponse)
async def render_pack(body: RenderPackRequest):
    """Render static images for all creatives in a pack using stored params."""
    _cleanup_render_cache()

    params = _pack_params.get(body.pack_id)
    if not params:
        params, _ = _load_pack_data(body.pack_id)
    if not params:
        raise HTTPException(status_code=404, detail="Pack params not found — re-analyze the URL")

    selected = select_templates(params)
    static_templates = [t for t in selected if t.format == "static"]
    if not static_templates:
        raise HTTPException(status_code=422, detail="No static templates to render")

    renders: list[RenderPackItem] = []

    for template in static_templates:
        cache_key = f"{body.pack_id}_{template.id}_1x1"

        cached = _render_cache.get(cache_key)
        if not body.force and cached and (time.time() - cached[1]) <= RENDER_TTL_SECONDS:
            renders.append(RenderPackItem(
                ad_type_id=template.id,
                aspect_ratio="1:1",
                image_url=f"/v2/renders/{cache_key}.png",
                generation_time_ms=0,
            ))
            continue

        start = time.time()
        try:
            copy = generate_copy_from_template(template, params)
            if template.id == "review_static_competition":
                copy = await generate_competition_copy(template, params)

            scraped = _pack_scraped.get(body.pack_id, {})
            img_bytes = await dispatch_render(
                template.id, params, dict(copy), scraped, None
            )
            gen_ms = int((time.time() - start) * 1000)
            _render_cache[cache_key] = (img_bytes, time.time())
            renders.append(RenderPackItem(
                ad_type_id=template.id,
                aspect_ratio="1:1",
                image_url=f"/v2/renders/{cache_key}.png",
                generation_time_ms=gen_ms,
            ))
        except Exception as e:
            logger.error(f"Pack render failed {template.id}: {e}")
            continue

    return RenderPackResponse(renders=renders)


class RenderRequest(BaseModel):
    """Render static images for specified ad types."""
    parameters: CreativeParameters
    ad_type_ids: list[str] | None = None  # None = render all selected
    aspect_ratios: list[str] | None = None  # None = use ad type defaults
    upload_to_s3: bool = False


class RenderResult(BaseModel):
    creative_id: str
    ad_type_id: str
    aspect_ratio: str
    asset_url: str | None = None
    generation_time_ms: int = 0


@router.post("/render", response_model=list[RenderResult])
async def render_static(body: RenderRequest):
    """
    Render static images for given parameters and ad types.
    Returns list of rendered creatives with local/S3 URLs.
    """
    params = body.parameters
    selected = select_templates(params)

    if body.ad_type_ids:
        selected = [t for t in selected if t.id in body.ad_type_ids]

    static_types = [t for t in selected if t.format == "static"]
    if not static_types:
        raise HTTPException(status_code=422, detail="No renderable static types selected")

    results: list[RenderResult] = []

    for template in static_types:
        start = time.time()
        try:
            copy = generate_copy_from_template(template, params)
            if template.id == "review_static_competition":
                copy = await generate_competition_copy(template, params)

            img_bytes = await dispatch_render(
                template.id, params, dict(copy), {}, None
            )
            gen_ms = int((time.time() - start) * 1000)

            asset_url = None
            if body.upload_to_s3:
                asset_url = await upload_to_s3(img_bytes, template.id, "1:1")

            results.append(RenderResult(
                creative_id=str(uuid.uuid4())[:12],
                ad_type_id=template.id,
                aspect_ratio="1:1",
                asset_url=asset_url,
                generation_time_ms=gen_ms,
            ))
        except Exception as e:
            logger.error(f"Render failed {template.id}: {e}")
            continue

    return results


# --- Template CRUD endpoints ---

class TemplateResponse(BaseModel):
    id: str
    ad_type_id: str
    aspect_ratio: str
    name: str
    canvas_json: dict
    is_default: bool


class TemplateCreateRequest(BaseModel):
    ad_type_id: str
    aspect_ratio: str
    name: str
    canvas_json: dict
    is_default: bool = False


class TemplateUpdateRequest(BaseModel):
    name: str | None = None
    canvas_json: dict | None = None
    is_default: bool | None = None


class TemplateRenderRequest(BaseModel):
    parameters: CreativeParameters
    width: int | None = None
    height: int | None = None


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(ad_type_id: str | None = None):
    """List all templates, optionally filtered by ad_type_id."""
    from prisma import Prisma
    db = Prisma()
    await db.connect()
    try:
        where = {}
        if ad_type_id:
            where["ad_type_id"] = ad_type_id
        templates = await db.adtemplate.find_many(
            where=where,
            order={"created_at": "desc"},
        )
        return [
            TemplateResponse(
                id=t.id,
                ad_type_id=t.ad_type_id,
                aspect_ratio=t.aspect_ratio,
                name=t.name,
                canvas_json=t.canvas_json,
                is_default=t.is_default,
            )
            for t in templates
        ]
    finally:
        await db.disconnect()


@router.get("/templates/{ad_type_id}", response_model=list[TemplateResponse])
async def get_templates_for_type(ad_type_id: str):
    """Get all templates for a specific ad type."""
    from prisma import Prisma
    db = Prisma()
    await db.connect()
    try:
        templates = await db.adtemplate.find_many(
            where={"ad_type_id": ad_type_id},
            order={"aspect_ratio": "asc"},
        )
        if not templates:
            raise HTTPException(status_code=404, detail=f"No templates for ad type: {ad_type_id}")
        return [
            TemplateResponse(
                id=t.id,
                ad_type_id=t.ad_type_id,
                aspect_ratio=t.aspect_ratio,
                name=t.name,
                canvas_json=t.canvas_json,
                is_default=t.is_default,
            )
            for t in templates
        ]
    finally:
        await db.disconnect()


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(body: TemplateCreateRequest):
    """Create a new ad template."""
    from prisma import Prisma
    db = Prisma()
    await db.connect()
    try:
        template = await db.adtemplate.create(
            data={
                "ad_type_id": body.ad_type_id,
                "aspect_ratio": body.aspect_ratio,
                "name": body.name,
                "canvas_json": body.canvas_json,
                "is_default": body.is_default,
            }
        )
        return TemplateResponse(
            id=template.id,
            ad_type_id=template.ad_type_id,
            aspect_ratio=template.aspect_ratio,
            name=template.name,
            canvas_json=template.canvas_json,
            is_default=template.is_default,
        )
    finally:
        await db.disconnect()


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: str, body: TemplateUpdateRequest):
    """Update an existing template."""
    from prisma import Prisma
    db = Prisma()
    await db.connect()
    try:
        data = {}
        if body.name is not None:
            data["name"] = body.name
        if body.canvas_json is not None:
            data["canvas_json"] = body.canvas_json
        if body.is_default is not None:
            data["is_default"] = body.is_default

        if not data:
            raise HTTPException(status_code=400, detail="No fields to update")

        template = await db.adtemplate.update(
            where={"id": template_id},
            data=data,
        )
        return TemplateResponse(
            id=template.id,
            ad_type_id=template.ad_type_id,
            aspect_ratio=template.aspect_ratio,
            name=template.name,
            canvas_json=template.canvas_json,
            is_default=template.is_default,
        )
    except Exception as e:
        if "Record to update not found" in str(e):
            raise HTTPException(status_code=404, detail="Template not found")
        raise
    finally:
        await db.disconnect()


@router.post("/templates/{template_id}/render")
async def render_template(template_id: str, body: TemplateRenderRequest):
    """Render a specific template with given parameters. Returns PNG image."""
    from fastapi.responses import Response
    from prisma import Prisma

    db = Prisma()
    await db.connect()
    try:
        template = await db.adtemplate.find_unique(where={"id": template_id})
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        w = body.width or _ASPECT_RATIO_SIZES.get(template.aspect_ratio, (1080, 1080))[0]
        h = body.height or _ASPECT_RATIO_SIZES.get(template.aspect_ratio, (1080, 1080))[1]

        from app.services.v2.static_renderer import get_static_renderer
        renderer = get_static_renderer()
        img_bytes = await renderer.render_from_template(
            canvas_json=template.canvas_json,
            params=body.parameters,
            width=w,
            height=h,
        )
        return Response(content=img_bytes, media_type="image/png")
    finally:
        await db.disconnect()


_ASPECT_RATIO_SIZES: dict[str, tuple[int, int]] = {
    "1:1": (1080, 1080),
    "9:16": (1080, 1920),
    "1.91:1": (1200, 628),
    "4:5": (1080, 1350),
}


# --- Helper functions ---

async def _render_ugc_avatar_creatives(
    creatives: list[GeneratedCreative],
    templates: list[AdTypeDefinition],
    params: CreativeParameters,
) -> None:
    """Render UGC avatar videos via HeyGen for matching creatives."""
    from app.config import get_settings
    settings = get_settings()
    if not settings.heygen_api_key:
        logger.info("HeyGen not configured — skipping UGC avatar render")
        return

    template_map = {t.id: t for t in templates}

    for creative in creatives:
        if creative.ad_type_id != "ugc_avatar_video":
            continue

        template = template_map.get(creative.ad_type_id)
        if not template:
            continue

        script = _build_video_script(template, params)
        if not script.strip():
            logger.warning("Empty UGC avatar script — skipping render")
            continue

        logger.info(f"Rendering UGC avatar video ({len(script)} chars)")
        result = await render_ugc_avatar(script=script, upload_to_s3=True)

        if result.quota_exceeded:
            creative.description = "heygen_quota_exceeded"
            logger.warning("HeyGen quota exceeded — creative marked for UI prompt")
        elif result.success:
            creative.asset_url = result.asset_url
            creative.video_id = result.heygen_video_id
            creative.generation_time_ms = result.generation_time_ms
        else:
            logger.error(f"UGC avatar render failed: {result.error}")



# Render pipeline functions (dispatch_render, render_static_creatives,
# upload_to_s3, upload_video_to_s3, build_targeting, add_manual_image_creative,
# render_competition_blog) are imported from app.services.v2.render_pipeline
