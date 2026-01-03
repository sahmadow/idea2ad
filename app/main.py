from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.models import Project, CampaignDraft, AdSetTargeting
from app.services.scraper import scrape_landing_page
from app.services.analyzer import analyze_landing_page_content
from app.services.creative import generate_creatives, generate_image_briefs
from app.services.meta_api import get_meta_manager, BUSINESS_VERTICALS
from app.db import connect_db, disconnect_db
from app.routers import auth_router, images_router, campaigns_router
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
    title="Idea2Ad Concierge API",
    version="1.0.0",
    lifespan=lifespan
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if settings.environment == "production":
    cors_origins = ["https://idea2ad.com"]  # Update with production domain

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(images_router)
app.include_router(campaigns_router)


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
    return {"message": "Idea2Ad API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
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
    """
    # 1. Scrape URL
    try:
        scraped_data = await scrape_landing_page(project.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not scraped_data["full_text"]:
        raise HTTPException(status_code=400, detail="Failed to scrape URL or empty content")

    # 2. Analyze Content (LLM) with styling data
    analysis_result = await analyze_landing_page_content(
        scraped_data["full_text"],
        scraped_data.get("styling", {"colors": [], "fonts": []})
    )

    # 3. Generate Creatives (headlines, copy)
    creatives = await generate_creatives(analysis_result)

    # 4. Generate Image Briefs (3 distinct approaches with text overlays)
    image_briefs = await generate_image_briefs(analysis_result)

    # 5. Construct Campaign Draft
    return CampaignDraft(
        project_url=project.url,
        analysis=analysis_result,
        targeting=AdSetTargeting(
            interests=analysis_result.keywords[:5]
        ),
        suggested_creatives=creatives,
        image_briefs=image_briefs,
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
