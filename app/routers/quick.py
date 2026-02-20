"""Quick Mode ad generation API endpoint."""

import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
import uuid
import logging

from app.services.quick_mode import (
    generate_quick_copy,
    generate_quick_image,
    QuickModeError,
    TONE_OPTIONS,
)
from app.services.s3 import get_s3_service
from app.schemas.ad_pack import AdPack, GeneratedCreative, TargetingSpec

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quick", tags=["quick"])
limiter = Limiter(key_func=get_remote_address)


class QuickRequest(BaseModel):
    idea: str = Field(..., min_length=10, max_length=2000)
    tone: str = Field(default="professional")

    def validate_tone(self):
        if self.tone.lower() not in TONE_OPTIONS:
            raise ValueError(f"Invalid tone. Must be one of: {TONE_OPTIONS}")
        return self.tone.lower()


class QuickAd(BaseModel):
    imageUrl: Optional[str] = None
    primaryText: str
    headline: str
    description: str
    cta: str


class QuickResponse(BaseModel):
    ads: list[QuickAd]
    targeting: str
    campaignName: str


@router.post("/generate", response_model=QuickResponse)
@limiter.limit("5/minute")
async def generate_quick_ad(request: Request, data: QuickRequest):
    """
    Generate a single ad from a business idea.
    No scraping, no templates - direct Gemini copy + image generation.
    """
    try:
        # Validate tone
        tone = data.validate_tone()

        # 1. Generate ad copy
        logger.info(f"Quick mode: generating copy for idea ({len(data.idea)} chars), tone={tone}")
        copy_data = await generate_quick_copy(data.idea, tone)

        # 2. Generate image
        image_url = None
        try:
            image_bytes = await generate_quick_image(copy_data["visualPrompt"])

            # 3. Upload to S3
            s3_service = get_s3_service()
            campaign_id = f"quick_{str(uuid.uuid4())[:8]}"
            upload_result = s3_service.upload_image(image_bytes, campaign_id)

            if upload_result.get("success"):
                image_url = upload_result["url"]
                logger.info(f"Quick mode image uploaded: {image_url}")
            else:
                logger.warning(f"Quick mode S3 upload failed: {upload_result.get('error')}")

        except Exception as e:
            logger.warning(f"Quick mode image generation failed: {e}")
            # Continue without image - copy is still valuable

        # 4. Build response
        ad = QuickAd(
            imageUrl=image_url,
            primaryText=copy_data["primaryText"],
            headline=copy_data["headline"],
            description=copy_data.get("description", copy_data["headline"]),
            cta=copy_data["cta"],
        )

        return QuickResponse(
            ads=[ad],
            targeting=copy_data["targetAudience"],
            campaignName=copy_data["campaignName"],
        )

    except QuickModeError as e:
        logger.error(f"Quick mode generation failed: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quick mode unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Quick mode generation failed: {str(e)}")


# =====================================================================
# Quick Mode V2 — returns AdPack with aware/unaware copy variants
# =====================================================================

class QuickV2Request(BaseModel):
    description: str | None = Field(default=None, max_length=2000)
    image_url: str | None = None
    edit_prompt: str | None = Field(default=None, max_length=500)
    product_name: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def at_least_one_input(self):
        if not self.description and not self.image_url:
            raise ValueError("At least one of description or image_url is required")
        return self


async def _generate_quick_v2_copy(description: str) -> dict:
    """Generate aware + unaware copy from description via Gemini."""
    import os
    import json
    from google import genai

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise QuickModeError("GOOGLE_API_KEY not configured")

    client = genai.Client(api_key=api_key)

    prompt = f"""You are an expert Facebook ad copywriter. Generate TWO ad copy variants for this product/service.

PRODUCT DESCRIPTION: {description}

Variant 1 — PRODUCT AWARE: The audience already knows the product category and is comparing options.
Variant 2 — PRODUCT UNAWARE: The audience doesn't know this product exists; lead with pain/desire.

Return JSON with this exact structure:
{{
  "product_aware": {{
    "headline": "5-8 word headline (max 40 chars)",
    "primaryText": "Compelling copy, 2-3 sentences (max 300 chars). Feature-focused.",
    "description": "One-line value proposition (max 90 chars)",
    "cta": "Call-to-action button text"
  }},
  "product_unaware": {{
    "headline": "5-8 word headline (max 40 chars)",
    "primaryText": "Compelling copy, 2-3 sentences (max 300 chars). Pain/desire-focused.",
    "description": "One-line value proposition (max 90 chars)",
    "cta": "Call-to-action button text"
  }},
  "visualPrompt": "Detailed image generation prompt for a professional ad visual. No text in image.",
  "targetAudience": "Brief target audience description",
  "campaignName": "Short campaign name (max 30 chars)",
  "productName": "Inferred product name (max 50 chars)"
}}"""

    for attempt in range(3):
        try:
            result = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            data = json.loads(result.text)
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            if not isinstance(data, dict) or "product_aware" not in data:
                raise ValueError("Invalid response structure")
            return data
        except Exception as e:
            logger.warning(f"Quick V2 copy attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                await asyncio.sleep(attempt + 1)

    raise QuickModeError("Quick V2 copy generation failed after retries")


def _validate_image_url(url: str) -> None:
    """Reject non-HTTPS and private/internal URLs to prevent SSRF."""
    from urllib.parse import urlparse
    import ipaddress

    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

    hostname = parsed.hostname or ""
    # Block obvious private ranges
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError("URL points to private/internal address")
    except ValueError as e:
        if "private" in str(e) or "internal" in str(e):
            raise
        # Not an IP — hostname is fine


async def _download_image(url: str) -> bytes:
    """Download image bytes from URL (validates against SSRF)."""
    _validate_image_url(url)
    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


@router.post("/generate/v2")
@limiter.limit("5/minute")
async def generate_quick_v2(request: Request, data: QuickV2Request):
    """
    Quick Mode V2: description and/or image → AdPack with aware/unaware copy.

    Path A (description only): Gemini copy + image generation
    Path B (image provided ± description): optional Gemini edit → product showcase
    """
    try:
        creatives: list[GeneratedCreative] = []
        product_name = data.product_name or "Quick Ad"
        s3_service = get_s3_service()

        if data.image_url:
            # --- Path B: Image provided ---
            image_bytes = await _download_image(data.image_url)

            # Optionally edit with Gemini if edit_prompt provided
            if data.edit_prompt:
                from app.services.v2.image_editor import edit_image
                logger.info(f"Quick V2: editing image with prompt: {data.edit_prompt[:80]}")
                image_bytes = await edit_image(image_bytes, data.edit_prompt)

            # Render product showcase
            from app.services.v2.social_templates.product_showcase import (
                render_product_showcase, ProductShowcaseParams,
            )

            # Upload the (possibly edited) image to S3 first for showcase
            temp_id = f"quick_v2_{uuid.uuid4().hex[:8]}"
            temp_result = s3_service.upload_image(image_bytes, temp_id)
            showcase_image_url = temp_result["url"] if temp_result.get("success") else data.image_url

            showcase_bytes = await render_product_showcase(
                ProductShowcaseParams(product_image_url=showcase_image_url)
            )

            # Upload showcase render
            render_id = f"quick_v2_showcase_{uuid.uuid4().hex[:8]}"
            render_result = s3_service.upload_image(showcase_bytes, render_id)
            asset_url = render_result["url"] if render_result.get("success") else None

            # Generate copy if description provided, else minimal copy
            if data.description:
                copy_data = await _generate_quick_v2_copy(data.description)
                product_name = data.product_name or copy_data.get("productName", "Quick Ad")

                for strategy_key in ["product_aware", "product_unaware"]:
                    variant = copy_data[strategy_key]
                    creatives.append(GeneratedCreative(
                        id=uuid.uuid4().hex[:12],
                        ad_type_id="manual_image_upload",
                        strategy=strategy_key,
                        format="static",
                        aspect_ratio="1:1",
                        asset_url=asset_url,
                        primary_text=variant["primaryText"],
                        headline=variant["headline"],
                        description=variant.get("description"),
                        cta_type=variant.get("cta", "LEARN_MORE"),
                        created_at=datetime.now(timezone.utc),
                    ))
            else:
                # Image only — create minimal creatives
                for strategy in ["product_aware", "product_unaware"]:
                    creatives.append(GeneratedCreative(
                        id=uuid.uuid4().hex[:12],
                        ad_type_id="manual_image_upload",
                        strategy=strategy,
                        format="static",
                        aspect_ratio="1:1",
                        asset_url=asset_url,
                        primary_text="Check this out" if strategy == "product_aware" else "Discover something new",
                        headline=product_name,
                        description=None,
                        cta_type="LEARN_MORE",
                        created_at=datetime.now(timezone.utc),
                    ))

        elif data.description:
            # --- Path A: Description only ---
            copy_data = await _generate_quick_v2_copy(data.description)
            product_name = data.product_name or copy_data.get("productName", "Quick Ad")

            # Generate image from visual prompt
            image_url = None
            try:
                image_bytes = await generate_quick_image(copy_data["visualPrompt"])
                campaign_id = f"quick_v2_{uuid.uuid4().hex[:8]}"
                upload_result = s3_service.upload_image(image_bytes, campaign_id)
                if upload_result.get("success"):
                    image_url = upload_result["url"]
            except Exception as e:
                logger.warning(f"Quick V2 image gen failed: {e}")

            for strategy_key in ["product_aware", "product_unaware"]:
                variant = copy_data[strategy_key]
                creatives.append(GeneratedCreative(
                    id=uuid.uuid4().hex[:12],
                    ad_type_id="manual_image_upload",
                    strategy=strategy_key,
                    format="static",
                    aspect_ratio="1:1",
                    asset_url=image_url,
                    primary_text=variant["primaryText"],
                    headline=variant["headline"],
                    description=variant.get("description"),
                    cta_type=variant.get("cta", "LEARN_MORE"),
                    created_at=datetime.now(timezone.utc),
                ))

        # Build AdPack
        pack = AdPack(
            id=uuid.uuid4().hex[:12],
            created_at=datetime.now(timezone.utc),
            product_name=product_name,
            creatives=creatives,
            targeting=TargetingSpec(),
            campaign_name=f"{product_name} — Quick",
            status="draft",
        )

        return {
            "ad_pack": pack.model_dump(mode="json"),
        }

    except QuickModeError as e:
        logger.error(f"Quick V2 failed: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quick V2 unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Quick mode generation failed")
