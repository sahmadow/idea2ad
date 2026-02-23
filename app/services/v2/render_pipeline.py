"""
Render Pipeline — shared render + upload logic for V2 creatives.

Used by both the FastAPI router (app/routers/v2.py) and the MCP server.
Extracts: dispatch_render, render_static_creatives, upload helpers, build_targeting.
"""

import asyncio
import logging
import random
import time
import uuid
from datetime import datetime, timezone

from app.schemas.creative_params import CreativeParameters
from app.schemas.ad_types import AdTypeDefinition
from app.schemas.ad_pack import GeneratedCreative, TargetingSpec
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

logger = logging.getLogger(__name__)

# Competition copy store — shared between router and pipeline
competition_copy_store: dict[str, dict] = {}


async def dispatch_render(
    ad_type_id: str,
    params: CreativeParameters,
    copy: dict,
    scraped_data: dict,
    creative_id: str | None = None,
) -> bytes:
    """Dispatch rendering to the correct social template renderer."""
    if ad_type_id == "branded_static":
        from app.services.v2.social_templates.branded_static import render_branded_static
        return await render_branded_static(bridge_branded_static(params, scraped_data, copy))

    if ad_type_id == "organic_static_reddit":
        from app.services.v2.social_templates.reddit_post import render_reddit_post
        return await render_reddit_post(bridge_reddit(params, copy))

    if ad_type_id == "problem_statement_text":
        from app.services.v2.social_templates.problem_statement import render_problem_statement
        return await render_problem_statement(bridge_problem_statement(params, copy))

    if ad_type_id == "review_static":
        from app.services.v2.social_templates.review_static import render_review_static
        return await render_review_static(bridge_review_static(params, copy))

    if ad_type_id == "review_static_competition":
        comp_copy = competition_copy_store.get(creative_id, {}) if creative_id else {}
        return await render_competition_blog(params, comp_copy)

    if ad_type_id == "service_hero":
        from app.services.v2.social_templates.service_hero import render_service_hero
        return await render_service_hero(bridge_service_hero(params, copy))

    if ad_type_id == "product_centric":
        from app.services.v2.social_templates.product_centric import render_product_centric
        return await render_product_centric(bridge_product_centric(params, scraped_data, copy))

    if ad_type_id == "person_centric":
        from app.services.v2.social_templates.person_centric import (
            render_person_centric, generate_person_image,
        )
        bridged = bridge_person_centric(params, copy)
        person_bytes = await generate_person_image(params)
        bridged.person_image_bytes = person_bytes
        return await render_person_centric(bridged)

    # Video types (Remotion-rendered)
    if ad_type_id == "branded_static_video":
        from app.services.v2.remotion_renderer import render_remotion_video
        props = bridge_branded_static_video(params, scraped_data, copy)
        return await render_remotion_video("BrandedStatic", props)

    if ad_type_id == "service_hero_video":
        from app.services.v2.remotion_renderer import render_remotion_video
        props = bridge_service_hero_video(params, copy)
        return await render_remotion_video("ServiceHero", props)

    raise ValueError(f"Unknown ad type for rendering: {ad_type_id}")


async def render_competition_blog(
    params: CreativeParameters,
    comp_copy: dict,
) -> bytes:
    """Render competition creative as blog review card via Playwright."""
    from app.services.v2.social_templates.blog_review import BlogReviewParams, render_blog_review

    product_name = params.product_name or "this product"

    testimonial = comp_copy.get("competition_testimonial", "")
    complaint = comp_copy.get("competitor_complaint", "")

    if comp_copy.get("primary_text"):
        body = comp_copy["primary_text"]
    elif complaint and testimonial:
        body = f"{testimonial}\n\n{complaint}."
    elif testimonial:
        body = testimonial
    else:
        body = product_name

    accent = "#3B82F6"
    if params.brand_colors:
        bc = params.brand_colors
        for c in [bc.secondary, bc.accent, bc.primary]:
            if c and c.startswith("#") and c.lower() not in ("#ffffff", "#f7f7f7", "#fafafa"):
                accent = c
                break

    blog_title = comp_copy.get("headline") or f"Why I switched to {product_name}"

    blog_params = BlogReviewParams(
        author_name="Sarah Chen",
        author_title="Marketing Lead",
        blog_title=blog_title,
        body=body,
        read_time="3 min",
        date=datetime.now().strftime("%b %Y"),
        accent_color=accent,
        claps=random.randint(150, 400),
    )

    return await render_blog_review(blog_params)


async def render_static_creatives(
    creatives: list[GeneratedCreative],
    templates: list[AdTypeDefinition],
    params: CreativeParameters,
    scraped_data: dict | None = None,
) -> list[GeneratedCreative]:
    """Render statics (Playwright) and videos (Remotion) for all creatives."""

    async def _render_one(creative: GeneratedCreative) -> None:
        if creative.format not in ("static", "video"):
            return

        start = time.time()
        try:
            copy = {
                "primary_text": creative.primary_text or "",
                "headline": creative.headline or "",
                "description": creative.description or "",
                "cta_type": creative.cta_type or "LEARN_MORE",
            }
            rendered_bytes = await dispatch_render(
                creative.ad_type_id, params, copy, scraped_data or {}, creative.id
            )
            creative.generation_time_ms = int((time.time() - start) * 1000)

            try:
                if creative.format == "video":
                    url = await upload_video_to_s3(
                        rendered_bytes, creative.ad_type_id, creative.aspect_ratio
                    )
                else:
                    url = await upload_to_s3(
                        rendered_bytes, creative.ad_type_id, creative.aspect_ratio
                    )
                creative.asset_url = url
            except Exception as e:
                logger.warning(f"S3 upload skipped: {e}")

        except Exception as e:
            logger.error(f"Render failed {creative.ad_type_id}: {e}", exc_info=True)

    # Render statics sequentially (shared Playwright browser), videos in parallel
    static_creatives = [c for c in creatives if c.format == "static"]
    video_creatives = [c for c in creatives if c.format == "video"]

    for c in static_creatives:
        await _render_one(c)

    if video_creatives:
        await asyncio.gather(*[_render_one(c) for c in video_creatives])

    return creatives


async def upload_to_s3(
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


async def upload_video_to_s3(
    video_bytes: bytes, ad_type_id: str, aspect_ratio: str
) -> str | None:
    """Upload rendered video to S3 and return URL."""
    try:
        from app.services.s3 import get_s3_service
        s3 = get_s3_service()
        ratio_slug = aspect_ratio.replace(":", "x").replace(".", "_")
        filename = f"v2/{ad_type_id}_{ratio_slug}_{uuid.uuid4().hex[:8]}.mp4"
        result = s3.upload_image(
            video_bytes, "v2-renders", filename, content_type="video/mp4"
        )
        if result.get("success"):
            return result["url"]
    except Exception as e:
        logger.warning(f"S3 video upload failed: {e}")
    return None


def build_targeting(params: CreativeParameters) -> TargetingSpec:
    """Derive targeting spec from persona analysis (Smart Broad strategy)."""
    persona = params.persona_primary
    geo = {"countries": params.target_countries} if params.target_countries else {"countries": ["US"]}

    if persona:
        demo = persona.demographics
        countries_str = ", ".join(params.target_countries) if params.target_countries else "US"
        rationale = (
            f"Targeting adults {demo.age_min}-{demo.age_max} in {countries_str} "
            f"based on {persona.label}. "
            f"Using Advantage+ broad targeting to let Meta's algorithm optimize."
        )
        return TargetingSpec(
            geo_locations=geo,
            age_min=demo.age_min,
            age_max=demo.age_max,
            genders=None if demo.gender_skew == "neutral" else (
                [1] if demo.gender_skew == "male" else [2]
            ),
            targeting_rationale=rationale,
        )

    return TargetingSpec(
        geo_locations=geo,
        targeting_rationale="Using broad targeting — no persona data available.",
    )


async def add_manual_image_creative(
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

        _validate_image_url(image_url)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            image_bytes = resp.content

        if edit_prompt:
            from app.services.v2.image_editor import edit_image
            logger.info(f"Editing user image with prompt: {edit_prompt[:80]}")
            image_bytes = await edit_image(image_bytes, edit_prompt)

        from app.services.v2.social_templates.product_showcase import (
            render_product_showcase, ProductShowcaseParams,
        )

        s3 = get_s3_service()

        temp_id = f"v2_manual_{uuid.uuid4().hex[:8]}"
        temp_result = s3.upload_image(image_bytes, temp_id)
        showcase_url = temp_result["url"] if temp_result.get("success") else image_url

        showcase_bytes = await render_product_showcase(
            ProductShowcaseParams(product_image_url=showcase_url)
        )

        render_id = f"v2_manual_showcase_{uuid.uuid4().hex[:8]}"
        render_result = s3.upload_image(showcase_bytes, render_id)
        asset_url = render_result["url"] if render_result.get("success") else None

        for strategy in ["product_aware", "product_unaware"]:
            copy = build_manual_copy(params, strategy)
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


def build_manual_copy(params: CreativeParameters, strategy: str) -> dict:
    """Build simple copy for manual_image_upload creative."""
    if strategy == "product_aware":
        primary = f"Discover {params.product_name}"
        if params.key_benefit:
            primary += f" — {params.key_benefit}"
        headline = params.headline or params.product_name
    else:
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
