"""
Facebook OAuth and Page Management Router
Handles server-side OAuth flow for Facebook/Meta integration
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/meta", tags=["facebook"])

# In-memory session store (use Redis in production)
_fb_sessions: dict = {}


class PublishCampaignRequest(BaseModel):
    page_id: str
    ad: dict
    campaign_data: dict
    settings: dict


def get_fb_session(request: Request) -> Optional[dict]:
    """Get Facebook session from cookie"""
    session_id = request.cookies.get("fb_session")
    if session_id and session_id in _fb_sessions:
        return _fb_sessions[session_id]
    return None


@router.get("/fb-status")
async def get_fb_status(request: Request):
    """Check if user has connected Facebook"""
    session = get_fb_session(request)
    if not session:
        return {"connected": False}

    return {
        "connected": True,
        "user": {
            "id": session.get("user_id"),
            "name": session.get("user_name"),
        },
        "pages": session.get("pages", [])
    }


@router.get("/pages")
async def get_user_pages(request: Request):
    """Get user's Facebook pages"""
    session = get_fb_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Not connected to Facebook")

    return {"pages": session.get("pages", [])}


@router.post("/publish-campaign")
async def publish_campaign(request: Request, data: PublishCampaignRequest):
    """Publish campaign using user's Facebook access token"""
    session = get_fb_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Not connected to Facebook")

    settings = get_settings()
    user_access_token = session.get("access_token")
    page_access_token = None

    # Find the page access token
    for page in session.get("pages", []):
        if page["id"] == data.page_id:
            page_access_token = page.get("access_token")
            break

    if not page_access_token:
        raise HTTPException(status_code=400, detail="Page not found or no access token")

    try:
        # Create campaign using Meta Marketing API
        from facebook_business.api import FacebookAdsApi
        from facebook_business.adobjects.adaccount import AdAccount
        from facebook_business.adobjects.campaign import Campaign
        from facebook_business.adobjects.adset import AdSet

        # Initialize with user's token
        FacebookAdsApi.init(
            app_id=settings.meta_app_id,
            app_secret=settings.meta_app_secret,
            access_token=user_access_token,
        )

        ad_account_id = settings.meta_ad_account_id

        # Create campaign
        campaign = AdAccount(ad_account_id).create_campaign(params={
            Campaign.Field.name: f"Idea2Ad - {data.campaign_data.get('project_url', 'Campaign')[:30]}",
            Campaign.Field.objective: "OUTCOME_TRAFFIC",
            Campaign.Field.status: Campaign.Status.paused,
            Campaign.Field.special_ad_categories: [],
            "is_adset_budget_sharing_enabled": False,
        })

        # Calculate daily budget from total budget and duration
        daily_budget = data.settings.get("budget", 5000) // data.settings.get("duration_days", 3)

        # Create ad set
        ad_set = AdAccount(ad_account_id).create_ad_set(params={
            AdSet.Field.name: "Idea2Ad Ad Set",
            AdSet.Field.campaign_id: campaign.get_id(),
            AdSet.Field.daily_budget: daily_budget,
            AdSet.Field.billing_event: AdSet.BillingEvent.impressions,
            AdSet.Field.optimization_goal: AdSet.OptimizationGoal.link_clicks,
            AdSet.Field.bid_strategy: AdSet.BidStrategy.lowest_cost_without_cap,
            AdSet.Field.targeting: {
                "geo_locations": {"countries": data.campaign_data.get("targeting", {}).get("geo_locations", ["US"])},
                "age_min": data.campaign_data.get("targeting", {}).get("age_min", 18),
                "age_max": data.campaign_data.get("targeting", {}).get("age_max", 65),
            },
            AdSet.Field.status: AdSet.Status.paused,
        })

        logger.info(f"Campaign created: {campaign.get_id()}, AdSet: {ad_set.get_id()}")

        return {
            "success": True,
            "campaign_id": campaign.get_id(),
            "ad_set_id": ad_set.get_id(),
            "message": "Campaign created successfully in PAUSED status"
        }

    except Exception as e:
        logger.error(f"Failed to publish campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# OAuth Router (separate prefix for auth)
auth_router = APIRouter(prefix="/auth", tags=["facebook-auth"])


@auth_router.get("/facebook")
async def facebook_login():
    """Initiate Facebook OAuth flow"""
    settings = get_settings()

    if not settings.meta_app_id:
        raise HTTPException(status_code=500, detail="META_APP_ID not configured")

    # OAuth parameters
    redirect_uri = "http://localhost:8000/auth/facebook/callback"
    scope = "pages_show_list,pages_read_engagement,ads_management,business_management"

    oauth_url = (
        f"https://www.facebook.com/v18.0/dialog/oauth?"
        f"client_id={settings.meta_app_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&response_type=code"
    )

    return RedirectResponse(url=oauth_url)


@auth_router.get("/facebook/callback")
async def facebook_callback(
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """Handle Facebook OAuth callback"""
    settings = get_settings()

    if error:
        # Return error to frontend popup
        return HTMLResponse(f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'FB_AUTH_ERROR',
                    error: '{error_description or error}'
                }}, 'http://localhost:5173');
                window.close();
            </script>
            </html>
        """)

    if not code:
        return HTMLResponse("""
            <html>
            <script>
                window.opener.postMessage({
                    type: 'FB_AUTH_ERROR',
                    error: 'No authorization code received'
                }, 'http://localhost:5173');
                window.close();
            </script>
            </html>
        """)

    try:
        # Exchange code for access token
        redirect_uri = "http://localhost:8000/auth/facebook/callback"

        async with httpx.AsyncClient() as client:
            token_response = await client.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "client_id": settings.meta_app_id,
                    "client_secret": settings.meta_app_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                }
            )
            token_data = token_response.json()

            if "error" in token_data:
                raise ValueError(token_data["error"].get("message", "Token exchange failed"))

            access_token = token_data["access_token"]

            # Get user info
            user_response = await client.get(
                "https://graph.facebook.com/v18.0/me",
                params={"access_token": access_token, "fields": "id,name,email"}
            )
            user_data = user_response.json()

            # Get user's pages
            pages_response = await client.get(
                "https://graph.facebook.com/v18.0/me/accounts",
                params={"access_token": access_token, "fields": "id,name,category,access_token"}
            )
            pages_data = pages_response.json()
            pages = pages_data.get("data", [])

        # Create session
        import uuid
        session_id = str(uuid.uuid4())
        _fb_sessions[session_id] = {
            "access_token": access_token,
            "user_id": user_data.get("id"),
            "user_name": user_data.get("name"),
            "pages": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "category": p.get("category", ""),
                    "access_token": p.get("access_token", "")
                }
                for p in pages
            ]
        }

        logger.info(f"Facebook OAuth successful for user {user_data.get('name')}, found {len(pages)} pages")

        # Return success to frontend popup with cookie
        response = HTMLResponse(f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'FB_AUTH_SUCCESS',
                    user: {{
                        id: '{user_data.get("id")}',
                        name: '{user_data.get("name", "").replace("'", "\\'")}'
                    }}
                }}, 'http://localhost:5173');
                window.close();
            </script>
            </html>
        """)
        response.set_cookie(
            key="fb_session",
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=3600 * 24  # 24 hours
        )
        return response

    except Exception as e:
        logger.error(f"Facebook OAuth error: {e}")
        return HTMLResponse(f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'FB_AUTH_ERROR',
                    error: '{str(e).replace("'", "\\'")}'
                }}, 'http://localhost:5173');
                window.close();
            </script>
            </html>
        """)
