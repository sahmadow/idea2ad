"""Replica ad creative generation API endpoints."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List
import uuid
import logging

from app.models import ReplicaData, ReplicaCreative, ReplicaResponse
from app.services.replica_scraper import scrape_for_replica
from app.services.template_renderer import get_template_renderer
from app.services.s3 import get_s3_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/replica", tags=["replica"])
limiter = Limiter(key_func=get_remote_address)


class ReplicaRequest(BaseModel):
    url: str


@router.post("/generate", response_model=ReplicaResponse)
@limiter.limit("5/minute")
async def generate_replica_creatives(request: Request, data: ReplicaRequest):
    """
    Generate hero replica ad creatives from landing page.
    Returns 3 images (hero × 3 aspect ratios).
    """
    try:
        # 1. Scrape landing page for replica data
        logger.info(f"Scraping {data.url} for replica creatives")
        replica_data = await scrape_for_replica(data.url)

        # 2. Generate all variations
        creatives = []
        template_renderer = get_template_renderer()
        s3_service = get_s3_service()

        # Define all variations to generate
        variations = _build_variations(replica_data)

        # Generate each variation in all 3 aspect ratios
        for variation in variations:
            for aspect_ratio in ["1:1", "4:5", "9:16"]:
                try:
                    # Render template
                    image_bytes = await template_renderer.render_replica_creative(
                        template_type=variation["type"],
                        replica_data=replica_data,
                        variation_data=variation["data"],
                        aspect_ratio=aspect_ratio
                    )

                    # Upload to S3
                    campaign_id = f"replica_{str(uuid.uuid4())[:8]}"
                    result = s3_service.upload_image(image_bytes, campaign_id)

                    if result.get("success"):
                        creative = ReplicaCreative(
                            variation_type=variation["type"],
                            aspect_ratio=aspect_ratio,
                            image_url=result["url"],
                            extracted_content=variation.get("extracted", {})
                        )
                        creatives.append(creative)
                        logger.info(f"Generated {variation['type']} ({aspect_ratio})")
                    else:
                        logger.warning(f"S3 upload failed for {variation['type']}: {result.get('error')}")

                except Exception as e:
                    logger.error(f"Failed to render {variation['type']} ({aspect_ratio}): {e}")
                    continue

        if not creatives:
            raise HTTPException(status_code=500, detail="Failed to generate any creatives")

        return ReplicaResponse(
            url=data.url,
            creatives=creatives,
            replica_data=replica_data
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Replica generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate replica creatives: {str(e)}")


def _build_variations(replica_data: ReplicaData) -> List[dict]:
    """Build hero variation only."""
    return [{
        "type": "hero",
        "data": {
            "headline": replica_data.hero.headline,
            "subheadline": replica_data.hero.subheadline,
            "background_color": replica_data.hero.background_color,
            "background_url": replica_data.hero.background_url,
            "background_screenshot": replica_data.hero.background_screenshot,
            "cta_text": replica_data.hero.cta_text,
            "cta_styles": replica_data.hero.cta_styles,
        },
        "extracted": {
            "headline": replica_data.hero.headline,
            "subheadline": replica_data.hero.subheadline,
            "background_color": replica_data.hero.background_color,
        }
    }]


