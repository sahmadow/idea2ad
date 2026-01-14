from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uuid

from app.models import Project, CampaignDraft, AdSetTargeting, Ad
from app.services.scraper import scrape_landing_page
from app.services.analyzer import analyze_landing_page_content, AnalysisError
from app.services.creative import generate_creatives, generate_image_briefs, CreativeGenerationError
from app.services.meta_api import get_meta_manager, BUSINESS_VERTICALS
from app.db import connect_db, disconnect_db
from app.routers import auth_router, images_router, campaigns_router
from app.routers.facebook import router as facebook_router, auth_router as facebook_auth_router
from app.config import get_settings
from app.logging_config import setup_logging, get_logger

# Initialize logging
settings = get_settings()
setup_logging(
    level="DEBUG" if settings.debug else "INFO",
    json_format=settings.environment == "production"
)

# Initialize Sentry if configured
if settings.sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.1,
        environment=settings.environment,
    )

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    async def dispatch(self, request: Request, call_next):
        # Add request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        response: Response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Request-ID"] = request_id

        # CSP for API responses
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup/shutdown events"""
    # Startup
    logger.info("Starting application...")
    await connect_db()
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await disconnect_db()


app = FastAPI(
    title="LaunchAd Concierge API",
    version="1.0.0",
    lifespan=lifespan
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if settings.environment == "production":
    cors_origins = [
        "https://launchad.io",
        "https://www.launchad.io",
        # Vercel preview deployments
        "https://frontend-salehs-projects-f9732e89.vercel.app",
    ]
cors_origin_regex = r"https://frontend-[a-z0-9]+-salehs-projects-f9732e89\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers + request ID tracing
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(images_router)
app.include_router(campaigns_router)
app.include_router(facebook_router)
app.include_router(facebook_auth_router)


# Request models for Meta API endpoints
class MetaPublishRequest(BaseModel):
    campaign_draft: dict
    page_id: str


class ClientOnboardingRequest(BaseModel):
    client_name: str
    primary_page_id: str
    vertical: str = "ECOMMERCE"
    initial_budget: float = 20.0


class MetaTestRequest(BaseModel):
    page_id: str


@app.get("/")
async def root():
    return {"message": "LaunchAd API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint - returns 200 if app is running"""
    return {"status": "ok"}


@app.get("/health/detailed")
async def health_check_detailed():
    """Detailed health check with service status"""
    from app.db import db
    try:
        await db.execute_raw("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "services": {"database": db_status}
    }


@app.post("/analyze", response_model=CampaignDraft)
@limiter.limit("10/minute")
async def analyze_url(request: Request, project: Project):
    """
    Analyze landing page URL and return campaign draft with creatives.
    Rate limited: 10 requests per minute.

    This endpoint will fail gracefully if analysis or creative generation fails,
    rather than returning ads with invalid/placeholder content.
    """
    # 1. Scrape URL
    try:
        scraped_data = await scrape_landing_page(project.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not scraped_data["full_text"]:
        raise HTTPException(status_code=400, detail="Failed to scrape URL or empty content")

    # 2. Analyze Content (LLM) with styling data
    # This will retry up to 3 times with exponential backoff
    try:
        analysis_result = await analyze_landing_page_content(
            scraped_data["full_text"],
            scraped_data.get("styling", {"colors": [], "fonts": []})
        )
    except AnalysisError as e:
        logger.error(f"Analysis failed for URL {project.url}: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to analyze landing page content. Please try again. Error: {str(e)}"
        )

    # 3. Generate Creatives (headlines, copy)
    # This will validate the analysis input and retry up to 3 times
    try:
        creatives = await generate_creatives(analysis_result)
    except CreativeGenerationError as e:
        logger.error(f"Creative generation failed for URL {project.url}: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to generate ad creatives. Please try again. Error: {str(e)}"
        )

    # 4. Generate Image Briefs (3 distinct approaches with text overlays)
    # This will validate the analysis input and retry up to 3 times
    try:
        image_briefs = await generate_image_briefs(analysis_result)
    except CreativeGenerationError as e:
        logger.error(f"Image brief generation failed for URL {project.url}: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to generate image briefs. Please try again. Error: {str(e)}"
        )

    # 5. Generate 2 images from briefs (if Vertex AI configured)
    ads = []
    headlines = [c for c in creatives if c.type == "headline"]
    primary_texts = [c for c in creatives if c.type == "copy_primary"]

    # Final validation: ensure we have required creatives before proceeding
    if not headlines or not primary_texts:
        logger.error(f"Missing required creatives for URL {project.url}: headlines={len(headlines)}, primary_texts={len(primary_texts)}")
        raise HTTPException(
            status_code=422,
            detail="Failed to generate required ad copy (headlines and primary text). Please try again."
        )

    if len(image_briefs) < 2:
        logger.error(f"Insufficient image briefs for URL {project.url}: count={len(image_briefs)}")
        raise HTTPException(
            status_code=422,
            detail="Failed to generate sufficient image briefs. Please try again."
        )

    # Skip image generation if disabled (for testing/cost savings)
    if settings.skip_image_generation:
        logger.info("Image generation disabled, using placeholder")
        for i, brief in enumerate(image_briefs[:2]):
            brief.image_url = settings.placeholder_image_url
            ad = Ad(
                id=i + 1,
                imageUrl=settings.placeholder_image_url,
                primaryText=primary_texts[i].content if i < len(primary_texts) else primary_texts[0].content,
                headline=headlines[i].content if i < len(headlines) else headlines[0].content,
                description=analysis_result.summary[:90] + "..." if len(analysis_result.summary) > 90 else analysis_result.summary,
                imageBrief=brief
            )
            ads.append(ad)
    else:
        try:
            from app.services.image_gen import get_image_generator
            from app.services.s3 import get_s3_service
            import uuid

            generator = get_image_generator()
            s3_service = get_s3_service()

            for i, brief in enumerate(image_briefs[:2]):  # Generate 2 images
                try:
                    # Generate image
                    image_bytes = await generator.generate_ad_image(
                        visual_description=brief.visual_description,
                        styling_notes=brief.styling_notes,
                        approach=brief.approach
                    )

                    # Upload to S3
                    campaign_id = str(uuid.uuid4())[:8]
                    result = s3_service.upload_image(image_bytes, campaign_id)
                    if result.get("success"):
                        image_url = result["url"]
                        brief.image_url = image_url
                    else:
                        raise ValueError(result.get("error", "S3 upload failed"))

                    # Create Ad object
                    ad = Ad(
                        id=i + 1,
                        imageUrl=image_url,
                        primaryText=primary_texts[i].content if i < len(primary_texts) else primary_texts[0].content,
                        headline=headlines[i].content if i < len(headlines) else headlines[0].content,
                        description=analysis_result.summary[:90] + "..." if len(analysis_result.summary) > 90 else analysis_result.summary,
                        imageBrief=brief
                    )
                    ads.append(ad)
                    logger.info(f"Generated ad {i + 1} with image: {image_url}")

                except Exception as e:
                    logger.warning(f"Image generation failed for brief {i + 1}: {e}")
                    # Create ad without image
                    ad = Ad(
                        id=i + 1,
                        imageUrl=None,
                        primaryText=primary_texts[i].content if i < len(primary_texts) else primary_texts[0].content,
                        headline=headlines[i].content if i < len(headlines) else headlines[0].content,
                        description=analysis_result.summary[:90] + "..." if len(analysis_result.summary) > 90 else analysis_result.summary,
                        imageBrief=brief
                    )
                    ads.append(ad)

        except Exception as e:
            logger.warning(f"Image generation service not available: {e}")
            # Create ads without images
            for i, brief in enumerate(image_briefs[:2]):
                ad = Ad(
                    id=i + 1,
                    imageUrl=None,
                    primaryText=primary_texts[i].content if i < len(primary_texts) else primary_texts[0].content,
                    headline=headlines[i].content if i < len(headlines) else headlines[0].content,
                    description=analysis_result.summary[:90] + "..." if len(analysis_result.summary) > 90 else analysis_result.summary,
                    imageBrief=brief
                )
                ads.append(ad)

    # 6. Construct Campaign Draft
    return CampaignDraft(
        project_url=project.url,
        analysis=analysis_result,
        targeting=AdSetTargeting(
            interests=analysis_result.keywords[:5]
        ),
        suggested_creatives=creatives,
        image_briefs=image_briefs,
        ads=ads,
        status="ANALYZED"
    )


# =====================================
# META ADS API ENDPOINTS
# =====================================

@app.post("/meta/publish")
@limiter.limit("5/minute")
async def publish_to_meta(request: Request, data: MetaPublishRequest):
    """
    Publish campaign draft to Meta Ads Manager (Simple Mode).
    Rate limited: 5 requests per minute.
    """
    try:
        meta_manager = get_meta_manager()
        result = meta_manager.publish_complete_campaign(
            data.campaign_draft,
            page_id=data.page_id
        )
        return {
            "success": result.get("success", False),
            "message": "Campaign published to Meta Ads Manager" if result.get("success") else "Failed to publish campaign",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Meta publish failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish campaign: {str(e)}")


@app.post("/meta/client/onboard")
async def onboard_client(request: ClientOnboardingRequest):
    """
    Onboard new client with 2-Tier Business Manager Solution.
    Creates Child Business Manager + Ad Account.
    """
    try:
        meta_manager = get_meta_manager()
        result = meta_manager.setup_client_onboarding_flow(
            client_name=request.client_name,
            primary_page_id=request.primary_page_id,
            vertical=request.vertical,
            initial_budget=request.initial_budget
        )
        return {
            "success": result.get("success", False),
            "message": "Client onboarded successfully" if result.get("success") else "Failed to onboard client",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Client onboarding failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to onboard client: {str(e)}")


@app.get("/meta/clients")
async def list_clients():
    """List all Child Business Managers (clients) under Parent BM."""
    try:
        meta_manager = get_meta_manager()
        result = meta_manager.get_client_business_managers()
        return {
            "success": result.get("success", False),
            "clients": result.get("child_businesses", []),
            "count": result.get("count", 0)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"List clients failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch clients: {str(e)}")


@app.get("/meta/config")
async def get_meta_config():
    """Get Meta API configuration status and available business verticals."""
    settings = get_settings()
    return {
        "simple_mode": {
            "enabled": bool(settings.meta_ad_account_id and settings.meta_access_token),
            "requires": ["META_ACCESS_TOKEN", "META_APP_SECRET", "META_APP_ID", "META_AD_ACCOUNT_ID"]
        },
        "two_tier_mode": {
            "enabled": False,  # Disabled per requirements
            "requires": ["META_PARENT_BUSINESS_ID"]
        },
        "business_verticals": list(BUSINESS_VERTICALS.keys()),
        "note": "Configure credentials in .env file"
    }


# =====================================
# META API TEST ENDPOINTS
# =====================================

@app.get("/meta/test/connection")
async def test_meta_connection():
    """Test basic Meta API connectivity and credentials."""
    try:
        meta_manager = get_meta_manager()
        return meta_manager.test_connection()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@app.get("/meta/test/permissions")
async def test_meta_permissions():
    """Test Meta API access token permissions."""
    try:
        meta_manager = get_meta_manager()
        return meta_manager.test_permissions()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Permissions test failed: {str(e)}")


@app.get("/meta/test/page/{page_id}")
async def test_meta_page_access(page_id: str):
    """Test access to a specific Facebook Page."""
    try:
        meta_manager = get_meta_manager()
        return meta_manager.test_page_access(page_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Page access test failed: {str(e)}")


@app.post("/meta/test/all")
async def test_meta_all(request: MetaTestRequest):
    """Run comprehensive Meta API tests."""
    try:
        meta_manager = get_meta_manager()
        return meta_manager.run_all_tests(page_id=request.page_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comprehensive tests failed: {str(e)}")
