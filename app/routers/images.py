from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.image_gen import get_image_generator
from app.services.s3 import get_s3_service
from app.auth.dependencies import get_current_user
from app.db import get_db
from prisma import Prisma
from prisma.models import User

router = APIRouter(prefix="/images", tags=["images"])
logger = logging.getLogger(__name__)

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ImageGenerateRequest(BaseModel):
    brief_id: str
    aspect_ratio: str = "1:1"


class ImageGenerateFromPromptRequest(BaseModel):
    prompt: str
    campaign_id: str
    aspect_ratio: str = "1:1"
    negative_prompt: Optional[str] = None


class ImageGenerateResponse(BaseModel):
    success: bool
    image_url: Optional[str] = None
    s3_key: Optional[str] = None
    error: Optional[str] = None


class ImageUploadResponse(BaseModel):
    url: str
    filename: str
    size: int


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_product_image(
    file: UploadFile = File(...)
):
    """
    Upload a product image for use in ad creatives.

    - Accepts JPEG, PNG, WebP
    - Max file size: 10MB
    - Returns S3 URL for use in analysis
    """
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: JPEG, PNG, WebP"
        )

    # Read file and validate size
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size: 10MB"
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file not allowed"
        )

    try:
        s3 = get_s3_service()
        result = s3.upload_product_image(
            image_bytes=content,
            content_type=file.content_type,
            original_filename=file.filename or "product.png"
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Upload failed: {result.get('error')}"
            )

        logger.info(f"Product image uploaded: {result['url']}")

        return ImageUploadResponse(
            url=result["url"],
            filename=result["filename"],
            size=result["size"]
        )

    except ValueError as e:
        logger.error(f"S3 config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image storage not configured"
        )
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed"
        )


@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image_from_brief(
    request: ImageGenerateRequest,
    user: User = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """
    Generate image from image brief and upload to S3.
    Updates the image brief with the generated image URL.
    """
    # Get image brief
    brief = await db.imagebrief.find_unique(
        where={"id": request.brief_id},
        include={"campaign": True}
    )

    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image brief not found"
        )

    if brief.campaign.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign"
        )

    try:
        # Generate image
        generator = get_image_generator()
        image_bytes = await generator.generate_ad_image(
            visual_description=brief.visual_description,
            styling_notes=brief.styling_notes,
            approach=brief.approach
        )

        # Upload to S3
        s3 = get_s3_service()
        upload_result = s3.upload_image(
            image_bytes=image_bytes,
            campaign_id=brief.campaign_id
        )

        if not upload_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {upload_result.get('error')}"
            )

        # Update brief with image URL
        await db.imagebrief.update(
            where={"id": brief.id},
            data={
                "image_url": upload_result["url"],
                "s3_key": upload_result["s3_key"]
            }
        )

        logger.info(f"Image generated for brief {brief.id}")

        return ImageGenerateResponse(
            success=True,
            image_url=upload_result["url"],
            s3_key=upload_result["s3_key"]
        )

    except ValueError as e:
        logger.error(f"Image generation config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image generation failed"
        )


@router.post("/generate-prompt", response_model=ImageGenerateResponse)
async def generate_image_from_prompt(
    request: ImageGenerateFromPromptRequest,
    user: User = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """
    Generate image from custom prompt and upload to S3.
    """
    # Verify campaign ownership
    campaign = await db.campaign.find_unique(where={"id": request.campaign_id})

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    if campaign.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign"
        )

    try:
        # Generate image
        generator = get_image_generator()
        image_bytes = await generator.generate_image(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            negative_prompt=request.negative_prompt
        )

        # Upload to S3
        s3 = get_s3_service()
        upload_result = s3.upload_image(
            image_bytes=image_bytes,
            campaign_id=request.campaign_id
        )

        if not upload_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {upload_result.get('error')}"
            )

        logger.info(f"Image generated from prompt for campaign {campaign.id}")

        return ImageGenerateResponse(
            success=True,
            image_url=upload_result["url"],
            s3_key=upload_result["s3_key"]
        )

    except ValueError as e:
        logger.error(f"Image generation config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image generation failed"
        )


@router.post("/generate-all/{campaign_id}")
async def generate_all_images(
    campaign_id: str,
    user: User = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """
    Generate images for all image briefs in a campaign.
    """
    # Verify campaign ownership
    campaign = await db.campaign.find_unique(
        where={"id": campaign_id},
        include={"image_briefs": True}
    )

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    if campaign.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign"
        )

    if not campaign.image_briefs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image briefs found for this campaign"
        )

    # Update campaign status
    await db.campaign.update(
        where={"id": campaign_id},
        data={"status": "GENERATING_IMAGES"}
    )

    results = []
    generator = get_image_generator()
    s3 = get_s3_service()

    for brief in campaign.image_briefs:
        try:
            # Generate image
            image_bytes = await generator.generate_ad_image(
                visual_description=brief.visual_description,
                styling_notes=brief.styling_notes,
                approach=brief.approach
            )

            # Upload to S3
            upload_result = s3.upload_image(
                image_bytes=image_bytes,
                campaign_id=campaign_id
            )

            if upload_result["success"]:
                # Update brief
                await db.imagebrief.update(
                    where={"id": brief.id},
                    data={
                        "image_url": upload_result["url"],
                        "s3_key": upload_result["s3_key"]
                    }
                )

                results.append({
                    "brief_id": brief.id,
                    "success": True,
                    "image_url": upload_result["url"]
                })
            else:
                results.append({
                    "brief_id": brief.id,
                    "success": False,
                    "error": upload_result.get("error")
                })

        except Exception as e:
            logger.error(f"Failed to generate image for brief {brief.id}: {e}")
            results.append({
                "brief_id": brief.id,
                "success": False,
                "error": str(e)
            })

    # Update campaign status
    all_success = all(r["success"] for r in results)
    await db.campaign.update(
        where={"id": campaign_id},
        data={"status": "READY" if all_success else "ANALYZED"}
    )

    return {
        "success": all_success,
        "total": len(results),
        "successful": sum(1 for r in results if r["success"]),
        "results": results
    }
