"""Carousel ad generation API endpoints."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
import logging

from app.models import CarouselResponse
from app.services.scraper import scrape_landing_page
from app.services.analyzer import analyze_landing_page_content, AnalysisError
from app.services.carousel import generate_carousel
from app.models import LogoInfo, DesignTokens

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/carousel", tags=["carousel"])
limiter = Limiter(key_func=get_remote_address)


class CarouselRequest(BaseModel):
    url: str = Field(..., min_length=5)
    product_image_url: Optional[str] = None


@router.post("/generate", response_model=CarouselResponse)
@limiter.limit("5/minute")
async def generate_carousel_ad(request: Request, data: CarouselRequest):
    """Generate a carousel ad from a landing page URL.

    Scrapes the URL, analyzes content, and produces a 3-5 card
    carousel with hook, value prop, and CTA cards.

    Returns carousel data + Meta API-ready JSON.
    """
    try:
        # 1. Scrape
        logger.info(f"Carousel: scraping {data.url}")
        scraped_data = await scrape_landing_page(data.url)

        if not scraped_data.get("full_text"):
            raise HTTPException(status_code=400, detail="Failed to scrape URL or empty content")

        # 2. Analyze
        analysis = await analyze_landing_page_content(
            scraped_data["full_text"],
            scraped_data.get("styling", {"colors": [], "fonts": []}),
        )

        # Add logo info
        logo_data = scraped_data.get("logo")
        if logo_data:
            try:
                analysis.logo = LogoInfo(**logo_data)
            except Exception:
                pass

        # Add design tokens
        dt_data = scraped_data.get("design_tokens")
        if dt_data:
            try:
                analysis.design_tokens = DesignTokens(**dt_data)
            except Exception:
                pass

        # 3. Generate carousel
        carousel_ad, meta_json = await generate_carousel(
            analysis=analysis,
            scraped_data=scraped_data,
            product_image_url=data.product_image_url,
            destination_url=data.url,
        )

        return CarouselResponse(
            url=data.url,
            carousel=carousel_ad,
            meta_carousel_json=meta_json,
        )

    except AnalysisError as e:
        logger.error(f"Carousel analysis failed for {data.url}: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to analyze landing page. Error: {e}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Carousel generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate carousel: {e}",
        )
