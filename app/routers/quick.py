"""Quick Mode ad generation API endpoint."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
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
