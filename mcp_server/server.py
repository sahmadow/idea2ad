"""
LaunchAd Creative Engine — MCP Server

Exposes the ad creative pipeline (URL → scrape → params → copy → render → AdPack)
as MCP tools for external AI agents. Streamable HTTP transport.

7 tools:
  - generate_ad_pack (full pipeline)
  - analyze_product, select_templates, generate_copy, render_creative (step-by-step)
  - list_ad_types, get_ad_type_details (metadata)
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP, Context

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "launchad-creative-engine",
    host="0.0.0.0",
    port=8100,
    stateless_http=True,
    json_response=True,
)


# ── Tool 1: Full Pipeline ──────────────────────────────────────────────


@mcp.tool()
async def generate_ad_pack(
    ctx: Context,
    url: str | None = None,
    description: str | None = None,
    language: str = "en",
    image_url: str | None = None,
) -> dict:
    """Generate a complete AdPack from a URL or product description.

    One-shot: scrape → extract params → select templates → generate copy → render
    all creatives → upload to S3. Returns full AdPack with asset URLs and targeting.

    Takes 30-60s. Provide either url or description (or both).

    Args:
        url: Landing page URL to scrape
        description: Freeform product/business description
        language: ISO 639-1 language code (default "en")
        image_url: Optional product image URL for manual creative
    """
    if not url and not description:
        return {"error": "Provide url or description"}

    from app.services.scraper import scrape_landing_page
    from app.services.v2.parameter_extractor import extract_creative_parameters
    from app.services.v2.template_selector import select_templates
    from app.services.v2.copy_generator import (
        generate_copy_from_template,
        generate_competition_copy,
        translate_copy,
        translate_params,
    )
    from app.services.v2.render_pipeline import (
        render_static_creatives,
        build_targeting,
        add_manual_image_creative,
        competition_copy_store,
    )
    from app.schemas.ad_pack import AdPack, GeneratedCreative, TargetingSpec

    try:
        # Step 1: Scrape or extract from description
        await ctx.report_progress(1, 5, "Scraping / analyzing input")
        scraped_data = {}

        if url:
            scraped_data = await scrape_landing_page(url)
            if not scraped_data.get("full_text"):
                return {"error": "Failed to scrape URL or empty content"}
            params = await extract_creative_parameters(scraped_data, source_url=url)
        else:
            # Import description extraction from v2 router
            from app.routers.v2 import _extract_params_from_description
            result = await _extract_params_from_description(description)
            params = result[0]

        # Step 2: Extract parameters
        await ctx.report_progress(2, 5, "Extracting creative parameters")

        if language and language != "en":
            params.language = language
            params = await translate_params(params, force=True)
        elif params.language and params.language != "en":
            params = await translate_params(params)

        # Step 3: Select templates + generate copy
        await ctx.report_progress(3, 5, "Generating ad copy")

        selected = select_templates(params)
        if not selected:
            return {"error": "No templates could be selected from available data"}

        creatives: list[GeneratedCreative] = []
        needs_translation = params.language and params.language != "en"

        for template in selected:
            if template.id == "review_static_competition":
                base_copy = await generate_competition_copy(template, params, None)
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

        # Step 4: Render all creatives
        await ctx.report_progress(4, 5, "Rendering creatives")
        creatives = await render_static_creatives(creatives, selected, params, scraped_data)

        # Optional manual image creative
        if image_url:
            await add_manual_image_creative(creatives, image_url, None, params)

        # Step 5: Assemble AdPack
        await ctx.report_progress(5, 5, "Assembling AdPack")

        targeting = build_targeting(params)
        pack = AdPack(
            id=str(uuid.uuid4())[:12],
            created_at=datetime.now(timezone.utc),
            source_url=url,
            product_name=params.product_name,
            brand_logo_url=params.brand_logo_url,
            language=params.language or "en",
            creatives=creatives,
            targeting=targeting,
            budget_daily_cents=1500,
            duration_days=3,
            campaign_name=f"{params.product_name} — {datetime.now().strftime('%b %Y')}",
            status="draft",
        )

        return {
            "ad_pack": pack.model_dump(mode="json"),
            "parameters": params.model_dump(mode="json"),
        }

    except Exception as e:
        logger.error(f"generate_ad_pack failed: {e}", exc_info=True)
        return {"error": str(e)}


# ── Tool 2: Analyze Product ────────────────────────────────────────────


@mcp.tool()
async def analyze_product(
    url: str | None = None,
    description: str | None = None,
) -> dict:
    """Scrape a URL or parse a description to extract CreativeParameters.

    Returns structured product data: name, pains, desires, brand colors,
    personas, scenes, etc. Use this as input for other step-by-step tools.

    Args:
        url: Landing page URL to scrape and analyze
        description: Freeform product/business description
    """
    if not url and not description:
        return {"error": "Provide url or description"}

    from app.services.scraper import scrape_landing_page
    from app.services.v2.parameter_extractor import extract_creative_parameters

    try:
        scraped_data = {}
        if url:
            scraped_data = await scrape_landing_page(url)
            if not scraped_data.get("full_text"):
                return {"error": "Failed to scrape URL or empty content"}
            params = await extract_creative_parameters(scraped_data, source_url=url)
        else:
            from app.routers.v2 import _extract_params_from_description
            result = await _extract_params_from_description(description)
            params = result[0]

        return {
            "parameters": params.model_dump(mode="json"),
            "scraped_data_keys": list(scraped_data.keys()) if scraped_data else [],
        }

    except Exception as e:
        logger.error(f"analyze_product failed: {e}", exc_info=True)
        return {"error": str(e)}


# ── Tool 3: Select Templates ──────────────────────────────────────────


@mcp.tool()
def select_ad_templates(
    params_json: str,
) -> dict:
    """Given CreativeParameters JSON, return which ad types will be generated.

    Returns list of selected ad type definitions with reasons for selection.

    Args:
        params_json: CreativeParameters as JSON string (from analyze_product output)
    """
    from app.schemas.creative_params import CreativeParameters
    from app.services.v2.template_selector import select_templates

    try:
        params = CreativeParameters(**json.loads(params_json))
        selected = select_templates(params)

        return {
            "selected_count": len(selected),
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "strategy": t.strategy,
                    "format": t.format,
                    "aspect_ratios": t.aspect_ratios,
                }
                for t in selected
            ],
        }

    except Exception as e:
        logger.error(f"select_ad_templates failed: {e}", exc_info=True)
        return {"error": str(e)}


# ── Tool 4: Generate Copy ─────────────────────────────────────────────


@mcp.tool()
async def generate_copy(
    params_json: str,
    ad_type_id: str | None = None,
) -> dict:
    """Generate ad copy for selected templates.

    If ad_type_id is provided, generates copy for that specific type only.
    Otherwise generates copy for all selected types.

    Args:
        params_json: CreativeParameters as JSON string
        ad_type_id: Optional specific ad type to generate copy for
    """
    from app.schemas.creative_params import CreativeParameters
    from app.services.v2.template_selector import select_templates
    from app.services.v2.ad_type_registry import get_ad_type
    from app.services.v2.copy_generator import (
        generate_copy_from_template,
        generate_competition_copy,
        translate_copy,
    )

    try:
        params = CreativeParameters(**json.loads(params_json))
        needs_translation = params.language and params.language != "en"

        if ad_type_id:
            ad_type = get_ad_type(ad_type_id)
            if not ad_type:
                return {"error": f"Unknown ad type: {ad_type_id}"}
            templates = [ad_type]
        else:
            templates = select_templates(params)

        copies = []
        for template in templates:
            if template.id == "review_static_competition":
                copy = await generate_competition_copy(template, params, None)
            else:
                copy = generate_copy_from_template(template, params)
                if needs_translation:
                    copy = await translate_copy(copy, params)

            copies.append({
                "ad_type_id": template.id,
                "primary_text": copy["primary_text"],
                "headline": copy["headline"],
                "description": copy.get("description"),
                "cta_type": copy["cta_type"],
            })

        return {"copies": copies}

    except Exception as e:
        logger.error(f"generate_copy failed: {e}", exc_info=True)
        return {"error": str(e)}


# ── Tool 5: Render Creative ───────────────────────────────────────────


@mcp.tool()
async def render_creative(
    params_json: str,
    ad_type_id: str,
    scraped_data_json: str | None = None,
) -> dict:
    """Render a single creative (static PNG or video MP4).

    Returns the S3 asset URL and generation time.

    Args:
        params_json: CreativeParameters as JSON string
        ad_type_id: The ad type to render (e.g. "branded_static", "organic_static_reddit")
        scraped_data_json: Optional scraped page data as JSON (needed for branded_static, product_centric)
    """
    from app.schemas.creative_params import CreativeParameters
    from app.services.v2.ad_type_registry import get_ad_type
    from app.services.v2.copy_generator import (
        generate_copy_from_template,
        generate_competition_copy,
    )
    from app.services.v2.render_pipeline import (
        dispatch_render,
        upload_to_s3,
        upload_video_to_s3,
    )

    try:
        params = CreativeParameters(**json.loads(params_json))
        scraped_data = json.loads(scraped_data_json) if scraped_data_json else {}

        ad_type = get_ad_type(ad_type_id)
        if not ad_type:
            return {"error": f"Unknown ad type: {ad_type_id}"}

        # Generate copy
        if ad_type_id == "review_static_competition":
            copy = await generate_competition_copy(ad_type, params, None)
        else:
            copy = generate_copy_from_template(ad_type, params)

        # Render
        start = time.time()
        rendered_bytes = await dispatch_render(
            ad_type_id, params, dict(copy), scraped_data, None
        )
        gen_ms = int((time.time() - start) * 1000)

        # Upload to S3
        if ad_type.format == "video":
            asset_url = await upload_video_to_s3(rendered_bytes, ad_type_id, "1:1")
        else:
            asset_url = await upload_to_s3(rendered_bytes, ad_type_id, "1:1")

        return {
            "ad_type_id": ad_type_id,
            "asset_url": asset_url,
            "generation_time_ms": gen_ms,
            "format": ad_type.format,
        }

    except Exception as e:
        logger.error(f"render_creative failed: {e}", exc_info=True)
        return {"error": str(e)}


# ── Tool 6: List Ad Types ─────────────────────────────────────────────


@mcp.tool()
def list_ad_types() -> dict:
    """List all available ad creative types with metadata.

    Returns 10 ad types (8 static + 2 video) with their IDs, names,
    strategies, formats, and supported aspect ratios.
    """
    from app.services.v2.ad_type_registry import get_registry

    registry = get_registry()
    return {
        "ad_types": [
            {
                "id": t.id,
                "name": t.name,
                "strategy": t.strategy,
                "format": t.format,
                "aspect_ratios": t.aspect_ratios,
                "required_params": t.required_params,
                "skip_condition": t.skip_condition,
            }
            for t in registry.values()
        ],
        "total": len(registry),
    }


# ── Tool 7: Get Ad Type Details ───────────────────────────────────────


@mcp.tool()
def get_ad_type_details(ad_type_id: str) -> dict:
    """Get full details for one ad type including copy template.

    Returns the complete AdTypeDefinition with copy template variables,
    required/optional params, and variant rules.

    Args:
        ad_type_id: The ad type ID (e.g. "branded_static", "person_centric")
    """
    from app.services.v2.ad_type_registry import get_ad_type

    ad_type = get_ad_type(ad_type_id)
    if not ad_type:
        return {"error": f"Unknown ad type: {ad_type_id}"}

    result = ad_type.model_dump(mode="json")
    return result
