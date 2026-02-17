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

import logging
import random
import time
import uuid
from datetime import datetime, timezone

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
from app.services.v2.copy_generator import generate_copy_from_template, _resolve_variable
from app.services.v2.ad_type_registry import get_registry, get_ad_type
from app.services.v2.static_renderer import get_static_renderer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2", tags=["v2"])


# --- Request/Response models ---

class AnalyzeRequest(BaseModel):
    url: str
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
    # 1. Scrape
    try:
        scraped_data = await scrape_landing_page(body.url)
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
        base_copy = generate_copy_from_template(template, params)

        # Resolve hook text for organic/problem types
        hook_text = _resolve_hook(template, params)

        # Generate one creative per aspect ratio
        for ratio in template.aspect_ratios:
            creative = GeneratedCreative(
                id=str(uuid.uuid4())[:12],
                ad_type_id=template.id,
                strategy=template.strategy,
                format=template.format,
                aspect_ratio=ratio,
                primary_text=base_copy["primary_text"],
                headline=base_copy["headline"],
                description=base_copy.get("description"),
                cta_type=base_copy["cta_type"],
                created_at=datetime.now(timezone.utc),
            )
            creatives.append(creative)

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
                img_bytes = await renderer.render_ad(
                    template, params, ratio, hook_text
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
    """Pick a random hook from hook_templates and resolve variables."""
    if not template.hook_templates:
        return None

    # Pick a platform variant or default
    variants = list(template.hook_templates.keys())
    key = random.choice(variants)
    hooks = template.hook_templates[key]
    if not hooks:
        return None

    hook = random.choice(hooks)
    return _resolve_variable(hook, params)


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

        hook_text = _resolve_hook(template, params)
        start = time.time()
        try:
            img_bytes = await renderer.render_ad(
                template, params, creative.aspect_ratio, hook_text
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
