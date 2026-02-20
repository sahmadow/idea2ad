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
from app.schemas.ad_pack import AdPack, GeneratedCreative, TargetingSpec
from app.services.scraper import scrape_landing_page
from app.services.v2.parameter_extractor import (
    extract_creative_parameters,
    ExtractionError,
)
from app.services.v2.template_selector import select_templates
from app.services.v2.copy_generator import (
    generate_copy_from_template,
    generate_competition_copy,
    _resolve_variable,
)
from app.services.v2.ad_type_registry import get_registry, get_ad_type
from app.services.v2.static_renderer import get_static_renderer
from app.services.v2.ugc_avatar_renderer import render_ugc_avatar, UGCAvatarResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2", tags=["v2"])

# In-memory stores for on-demand rendering
_pack_params: dict[str, CreativeParameters] = {}  # pack_id → params
_render_cache: dict[str, tuple[bytes, float]] = {}  # render_id → (PNG bytes, timestamp)
_competition_copy_store: dict[str, dict] = {}  # creative_id → competition copy dict

# Persist path for last params (survives restarts)
LAST_PARAMS_PATH = Path(__file__).resolve().parents[2] / "data" / "last_params.json"


def _persist_params(params: CreativeParameters) -> None:
    """Write CreativeParameters to disk for playground use."""
    try:
        LAST_PARAMS_PATH.parent.mkdir(parents=True, exist_ok=True)
        LAST_PARAMS_PATH.write_text(
            json.dumps(params.model_dump(mode="json"), indent=2)
        )
    except Exception as e:
        logger.warning(f"Failed to persist params: {e}")


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
        params = await extract_creative_parameters(scraped_data, source_url=body.url)
    except ExtractionError as e:
        logger.error(f"Parameter extraction failed for {body.url}: {e}")
        raise HTTPException(status_code=422, detail=f"Parameter extraction failed: {e}")

    # 3. Select templates
    selected = select_templates(params)
    if not selected:
        raise HTTPException(status_code=422, detail="No templates could be selected with available data")

    # 4. Generate copy and build creatives
    creatives: list[GeneratedCreative] = []
    for template in selected:
        # Competition type uses LLM-generated copy
        if template.id == "review_static_competition":
            base_copy = await generate_competition_copy(template, params, competitor_data)
        else:
            base_copy = generate_copy_from_template(template, params)

        # Resolve hook text for organic/problem types
        hook_text = _resolve_hook(template, params)

        # Generate one creative per template (1:1 default; other ratios on demand via render)
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
            _competition_copy_store[creative.id] = dict(base_copy)

    # 5. Optional: render static images
    if body.render_images:
        creatives = await _render_static_creatives(creatives, selected, params)

    # 6. Build targeting from persona
    targeting = _build_targeting(params)

    # 7. Assemble AdPack
    pack = AdPack(
        id=str(uuid.uuid4())[:12],
        created_at=datetime.now(timezone.utc),
        source_url=body.url,
        product_name=params.product_name,
        creatives=creatives,
        targeting=targeting,
        campaign_name=f"{params.product_name} — {datetime.now().strftime('%b %Y')}",
        status="draft",
    )

    _pack_params[pack.id] = params
    _persist_params(params)

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
        params = await extract_creative_parameters(scraped_data, source_url=url)

        # 3. Select templates
        selected = select_templates(params)
        if not selected:
            raise ValueError("No templates could be selected")

        # 4. Generate copy + build creatives (1:1 only per template)
        creatives: list[GeneratedCreative] = []
        for template in selected:
            # Competition type uses LLM-generated copy (with optional competitor data)
            if template.id == "review_static_competition":
                base_copy = await generate_competition_copy(template, params, competitor_data)
            else:
                base_copy = generate_copy_from_template(template, params)
            hook_text = _resolve_hook(template, params)
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
                _competition_copy_store[creative.id] = dict(base_copy)

        # 5. Render UGC avatar video (if selected and HeyGen configured)
        await _render_ugc_avatar_creatives(creatives, selected, params)

        # 5b. Add manual_image_upload creative (#9) if user provided image
        if image_url:
            await _add_manual_image_creative(creatives, image_url, edit_prompt, params)

        # 6. Build targeting
        targeting = _build_targeting(params)

        # 7. Assemble AdPack
        pack = AdPack(
            id=str(uuid.uuid4())[:12],
            created_at=datetime.now(timezone.utc),
            source_url=url,
            product_name=params.product_name,
            creatives=creatives,
            targeting=targeting,
            campaign_name=f"{params.product_name} — {datetime.now().strftime('%b %Y')}",
            status="draft",
        )

        _pack_params[pack.id] = params
        _persist_params(params)

        # 8. Store result in job — shape matches what frontend expects
        result = {
            "parameters": params.model_dump(mode="json"),
            "ad_pack": pack.model_dump(mode="json"),
        }
        update_job(job_id, JobStatus.COMPLETE, result=result)
        logger.info(f"V2 job {job_id} completed: {len(creatives)} creatives")

    except Exception as e:
        logger.error(f"V2 job {job_id} failed: {e}", exc_info=True)
        from app.services.jobs import update_job, JobStatus
        update_job(job_id, JobStatus.FAILED, error=str(e))


async def _add_manual_image_creative(
    creatives: list[GeneratedCreative],
    image_url: str,
    edit_prompt: str | None,
    params: CreativeParameters,
) -> None:
    """Add manual_image_upload creative (#9) with optional Gemini edit."""
    try:
        import httpx
        from app.services.s3 import get_s3_service
        from app.routers.quick import _validate_image_url

        # Download image (with SSRF validation)
        _validate_image_url(image_url)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            image_bytes = resp.content

        # Optionally edit with Gemini
        if edit_prompt:
            from app.services.v2.image_editor import edit_image
            logger.info(f"Editing user image with prompt: {edit_prompt[:80]}")
            image_bytes = await edit_image(image_bytes, edit_prompt)

        # Render product showcase
        from app.services.v2.social_templates.product_showcase import (
            render_product_showcase, ProductShowcaseParams,
        )

        s3 = get_s3_service()

        # Upload (possibly edited) image for showcase rendering
        temp_id = f"v2_manual_{uuid.uuid4().hex[:8]}"
        temp_result = s3.upload_image(image_bytes, temp_id)
        showcase_url = temp_result["url"] if temp_result.get("success") else image_url

        showcase_bytes = await render_product_showcase(
            ProductShowcaseParams(product_image_url=showcase_url)
        )

        # Upload final render
        render_id = f"v2_manual_showcase_{uuid.uuid4().hex[:8]}"
        render_result = s3.upload_image(showcase_bytes, render_id)
        asset_url = render_result["url"] if render_result.get("success") else None

        # Add two creatives: product_aware and product_unaware
        for strategy in ["product_aware", "product_unaware"]:
            copy = _build_manual_copy(params, strategy)

            creatives.append(GeneratedCreative(
                id=uuid.uuid4().hex[:12],
                ad_type_id="manual_image_upload",
                strategy=strategy,
                format="static",
                aspect_ratio="1:1",
                asset_url=asset_url,
                primary_text=copy["primary_text"],
                headline=copy["headline"],
                description=copy.get("description"),
                cta_type=copy.get("cta_type", "LEARN_MORE"),
                created_at=datetime.now(timezone.utc),
            ))

        logger.info("Added manual_image_upload creatives (aware + unaware)")

    except Exception as e:
        logger.error(f"Failed to add manual image creative: {e}", exc_info=True)


def _build_manual_copy(params: CreativeParameters, strategy: str) -> dict:
    """Build simple copy for manual_image_upload creative."""
    if strategy == "product_aware":
        primary = f"Discover {params.product_name}"
        if params.key_benefit:
            primary += f" — {params.key_benefit}"
        headline = params.headline or params.product_name
    else:
        # Product unaware — lead with pain/desire
        if params.customer_pains:
            primary = f"Tired of {params.customer_pains[0].lower().rstrip('.')}? {params.product_name} can help."
        elif params.key_benefit:
            primary = f"What if you could {params.key_benefit.lower().rstrip('.')}?"
        else:
            primary = f"There's a better way. Meet {params.product_name}."
        headline = params.subheadline or params.product_name

    return {
        "primary_text": primary[:500],
        "headline": (headline or params.product_name)[:40],
        "description": (params.product_description_short or "")[:30] or None,
        "cta_type": "SIGN_UP" if params.business_type == "saas" else "LEARN_MORE",
    }


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
        raise HTTPException(status_code=404, detail="Pack params not found — re-analyze the URL")

    selected = select_templates(params)
    static_templates = [t for t in selected if t.format == "static"]
    if not static_templates:
        raise HTTPException(status_code=422, detail="No static templates to render")

    renderer = get_static_renderer()
    renders: list[RenderPackItem] = []

    for template in static_templates:
        hook_text = _resolve_hook(template, params)
        cache_key = f"{body.pack_id}_{template.id}_1x1"

        # Use cached render if available (unless force re-render)
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
            # Competition type → Playwright blog template
            if template.id == "review_static_competition":
                comp_copy = await generate_competition_copy(template, params)
                img_bytes = await _render_competition_blog(params, dict(comp_copy))
            else:
                img_bytes = await renderer.render_ad(
                    template, params, "1:1", hook_text,
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

    # Filter to requested ad types
    if body.ad_type_ids:
        selected = [t for t in selected if t.id in body.ad_type_ids]

    # Only render static types
    static_types = [t for t in selected if t.format == "static"]
    if not static_types:
        raise HTTPException(status_code=422, detail="No renderable static types selected")

    renderer = get_static_renderer()
    results: list[RenderResult] = []

    for template in static_types:
        hook_text = _resolve_hook(template, params)
        ratios = body.aspect_ratios or template.aspect_ratios

        for ratio in ratios:
            start = time.time()
            try:
                # Competition type → Playwright blog template
                if template.id == "review_static_competition":
                    comp_copy = await generate_competition_copy(template, params)
                    img_bytes = await _render_competition_blog(params, dict(comp_copy))
                else:
                    img_bytes = await renderer.render_ad(
                        template, params, ratio, hook_text,
                    )
                gen_ms = int((time.time() - start) * 1000)

                asset_url = None
                if body.upload_to_s3:
                    asset_url = await _upload_to_s3(
                        img_bytes, template.id, ratio
                    )

                results.append(RenderResult(
                    creative_id=str(uuid.uuid4())[:12],
                    ad_type_id=template.id,
                    aspect_ratio=ratio,
                    asset_url=asset_url,
                    generation_time_ms=gen_ms,
                ))
            except Exception as e:
                logger.error(f"Render failed {template.id}@{ratio}: {e}")
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

        w = body.width or ASPECT_RATIO_SIZES.get(template.aspect_ratio, (1080, 1080))[0]
        h = body.height or ASPECT_RATIO_SIZES.get(template.aspect_ratio, (1080, 1080))[1]

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


# Import ASPECT_RATIO_SIZES for template render endpoint
from app.services.v2.static_renderer import ASPECT_RATIO_SIZES


# --- Helper functions ---

def _resolve_hook(template: AdTypeDefinition, params: CreativeParameters) -> str | None:
    """Pick a random hook from hook_templates and resolve variables.
    Prefers saas_* keys when business_type == 'saas'."""
    if not template.hook_templates:
        return None

    variants = list(template.hook_templates.keys())

    # Prefer SaaS-specific hooks when applicable
    if params.business_type == "saas":
        saas_keys = [k for k in variants if k.startswith("saas_")]
        if saas_keys:
            variants = saas_keys

    key = random.choice(variants)
    hooks = template.hook_templates[key]
    if not hooks:
        return None

    hook = random.choice(hooks)
    return _resolve_variable(hook, params)


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


async def _render_competition_blog(
    params: CreativeParameters,
    comp_copy: dict,
) -> bytes:
    """Render competition creative as blog review card via Playwright."""
    from app.services.v2.social_templates.blog_review import BlogReviewParams, render_blog_review

    product_name = params.product_name or "this product"
    category = params.product_category or "tools"

    testimonial = comp_copy.get("competition_testimonial", "")
    complaint = comp_copy.get("competitor_complaint", "")

    # Build natural blog body from competition copy fields
    if complaint and testimonial:
        body = (
            f"I've been using various {category} for years and honestly "
            f"most of them are terrible. {complaint}.\n\n"
            f"{testimonial}\n\n"
            f"If you're still dealing with {complaint.lower()}, "
            f"just try {product_name}. It's not even close."
        )
    elif testimonial:
        body = testimonial
    else:
        body = comp_copy.get("primary_text", f"After switching to {product_name}, everything changed.")

    # Derive accent color from brand (skip near-white primaries)
    accent = "#3B82F6"
    if params.brand_colors:
        bc = params.brand_colors
        for c in [bc.secondary, bc.accent, bc.primary]:
            if c and c.startswith("#") and c.lower() not in ("#ffffff", "#f7f7f7", "#fafafa"):
                accent = c
                break

    blog_params = BlogReviewParams(
        author_name="Sarah Chen",
        author_title="Marketing Lead",
        blog_title=f"Why I switched to {product_name} (and never looked back)",
        body=body,
        read_time="3 min read",
        date=datetime.now().strftime("%b %Y"),
        accent_color=accent,
        claps=random.randint(150, 400),
    )

    return await render_blog_review(blog_params)


async def _render_static_creatives(
    creatives: list[GeneratedCreative],
    templates: list[AdTypeDefinition],
    params: CreativeParameters,
) -> list[GeneratedCreative]:
    """Render images for static creatives and attach asset_url."""
    renderer = get_static_renderer()
    template_map = {t.id: t for t in templates}

    for creative in creatives:
        if creative.format != "static":
            continue

        template = template_map.get(creative.ad_type_id)
        if not template:
            continue

        start = time.time()
        try:
            # Competition type → Playwright blog template
            if creative.ad_type_id == "review_static_competition":
                comp_copy = _competition_copy_store.get(creative.id, {})
                img_bytes = await _render_competition_blog(params, comp_copy)
            else:
                hook_text = _resolve_hook(template, params)
                img_bytes = await renderer.render_ad(
                    template, params, creative.aspect_ratio, hook_text,
                )
            creative.generation_time_ms = int((time.time() - start) * 1000)

            # Try S3 upload, fall back to no URL
            try:
                url = await _upload_to_s3(
                    img_bytes, creative.ad_type_id, creative.aspect_ratio
                )
                creative.asset_url = url
            except Exception as e:
                logger.warning(f"S3 upload skipped: {e}")

        except Exception as e:
            logger.error(f"Render failed {creative.ad_type_id}@{creative.aspect_ratio}: {e}")

    return creatives


async def _upload_to_s3(
    img_bytes: bytes, ad_type_id: str, aspect_ratio: str
) -> str | None:
    """Upload rendered image to S3 and return URL."""
    try:
        from app.services.s3 import get_s3_service
        s3 = get_s3_service()
        ratio_slug = aspect_ratio.replace(":", "x").replace(".", "_")
        filename = f"v2/{ad_type_id}_{ratio_slug}_{uuid.uuid4().hex[:8]}.png"
        result = s3.upload_image(img_bytes, "v2-renders", filename)
        if result.get("success"):
            return result["url"]
    except Exception as e:
        logger.warning(f"S3 upload failed: {e}")
    return None


def _build_targeting(params: CreativeParameters) -> TargetingSpec:
    """Derive targeting spec from persona analysis (Smart Broad strategy)."""
    persona = params.persona_primary

    if persona:
        demo = persona.demographics
        rationale = (
            f"Targeting adults {demo.age_min}-{demo.age_max} "
            f"based on {persona.label}. "
            f"Using Advantage+ broad targeting to let Meta's algorithm optimize."
        )
        return TargetingSpec(
            age_min=demo.age_min,
            age_max=demo.age_max,
            genders=None if demo.gender_skew == "neutral" else (
                [1] if demo.gender_skew == "male" else [2]
            ),
            targeting_rationale=rationale,
        )

    return TargetingSpec(
        targeting_rationale="Using broad targeting — no persona data available.",
    )
