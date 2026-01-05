"""
Facebook OAuth and Page Management Router
Handles server-side OAuth flow for Facebook/Meta integration
"""
import logging
from datetime import datetime, timedelta
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


@router.get("/location-search")
async def search_locations(request: Request, q: str = Query(..., min_length=2)):
    """Search for cities using Meta's ad geolocation API"""
    session = get_fb_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Not connected to Facebook")

    access_token = session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="No access token available")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.facebook.com/v18.0/search",
                params={
                    "type": "adgeolocation",
                    "location_types": '["city"]',
                    "q": q,
                    "access_token": access_token
                }
            )
            data = response.json()

            if "error" in data:
                logger.error(f"Meta location search error: {data['error']}")
                raise HTTPException(status_code=400, detail=data["error"].get("message", "Location search failed"))

            # Format results for frontend - filter to cities only (exclude subcity, neighborhood, etc.)
            cities = []
            for loc in data.get("data", []):
                # Only include actual cities, not districts/subcities/neighborhoods
                if loc.get("type") != "city":
                    continue
                cities.append({
                    "key": loc.get("key"),
                    "name": loc.get("name"),
                    "region": loc.get("region"),
                    "country_name": loc.get("country_name"),
                    "country_code": loc.get("country_code"),
                    "type": loc.get("type")
                })

            # Sort results: exact match first, then starts-with, then by name length
            q_lower = q.lower()
            cities.sort(key=lambda c: (
                0 if c["name"].lower() == q_lower else 1,           # Exact match first
                0 if c["name"].lower().startswith(q_lower) else 1,  # Starts with query
                len(c["name"])                                       # Shorter names first (major cities)
            ))

            return {"cities": cities}

    except httpx.HTTPError as e:
        logger.error(f"Location search HTTP error: {e}")
        raise HTTPException(status_code=500, detail="Failed to search locations")


@router.post("/publish-campaign")
async def publish_campaign(request: Request, data: PublishCampaignRequest):
    """Publish campaign using user's Facebook access token"""
    session = get_fb_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Not connected to Facebook")

    settings = get_settings()
    user_access_token = session.get("access_token")
    page_access_token = None

    # Find the page access token and page name
    page_name = None
    for page in session.get("pages", []):
        if page["id"] == data.page_id:
            page_access_token = page.get("access_token")
            page_name = page.get("name", "Advertiser")
            break

    if not page_access_token:
        raise HTTPException(status_code=400, detail="Page not found or no access token")

    try:
        # Create campaign using Meta Marketing API
        from facebook_business.api import FacebookAdsApi
        from facebook_business.adobjects.adaccount import AdAccount
        from facebook_business.adobjects.campaign import Campaign
        from facebook_business.adobjects.adset import AdSet
        from facebook_business.adobjects.adcreative import AdCreative
        from facebook_business.adobjects.ad import Ad
        from facebook_business.adobjects.adimage import AdImage

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
        duration_days = data.settings.get("duration_days", 3)
        daily_budget = data.settings.get("budget", 5000) // duration_days

        # Calculate end time (72 hours = 3 days from now)
        end_time = datetime.now() + timedelta(days=duration_days)
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")

        # Build geo_locations targeting
        locations = data.settings.get("locations", [])
        if locations:
            # Use cities if provided
            geo_locations = {
                "cities": [{"key": loc["key"]} for loc in locations]
            }
        else:
            # Fallback to countries from campaign_data
            geo_locations = {
                "countries": data.campaign_data.get("targeting", {}).get("geo_locations", ["US"])
            }

        # Create ad set with DSA compliance fields (EU Digital Services Act)
        ad_set = AdAccount(ad_account_id).create_ad_set(params={
            AdSet.Field.name: "Idea2Ad Ad Set",
            AdSet.Field.campaign_id: campaign.get_id(),
            AdSet.Field.daily_budget: daily_budget,
            AdSet.Field.billing_event: AdSet.BillingEvent.impressions,
            AdSet.Field.optimization_goal: AdSet.OptimizationGoal.link_clicks,
            AdSet.Field.bid_strategy: AdSet.BidStrategy.lowest_cost_without_cap,
            AdSet.Field.targeting: {
                "geo_locations": geo_locations,
                "age_min": data.campaign_data.get("targeting", {}).get("age_min", 18),
                "age_max": data.campaign_data.get("targeting", {}).get("age_max", 65),
            },
            AdSet.Field.end_time: end_time_str,
            AdSet.Field.status: AdSet.Status.paused,
            "dsa_beneficiary": page_name,  # Who benefits from the ad (DSA compliance)
            "dsa_payor": page_name,        # Who pays for the ad (DSA compliance)
        })

        logger.info(f"Campaign created: {campaign.get_id()}, AdSet: {ad_set.get_id()}")

        # Step 3: Upload image to Meta (download bytes first for reliability)
        image_hash = None
        ad_image_url = data.ad.get("imageUrl")
        if ad_image_url:
            try:
                import tempfile
                import os

                # Download image bytes first
                async with httpx.AsyncClient() as img_client:
                    img_response = await img_client.get(ad_image_url, timeout=30.0)
                    img_response.raise_for_status()
                    image_bytes = img_response.content

                # Save to temp file and upload
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                    tmp_file.write(image_bytes)
                    tmp_path = tmp_file.name

                try:
                    ad_image = AdImage(parent_id=ad_account_id)
                    ad_image[AdImage.Field.filename] = tmp_path
                    ad_image.remote_create()
                    image_hash = ad_image.get(AdImage.Field.hash)
                    logger.info(f"Image uploaded to Meta, hash: {image_hash}")
                finally:
                    # Clean up temp file
                    os.unlink(tmp_path)

            except Exception as img_err:
                logger.error(f"Image upload failed: {img_err}")
                # Continue without image - don't fail the whole campaign

        # Step 4: Create Ad Creative
        creative_id = None
        project_url = data.campaign_data.get("project_url", "https://example.com")
        cta_type = data.settings.get("call_to_action", "LEARN_MORE")

        # Build object_story_spec for the ad creative
        link_data = {
            "link": project_url,
            "message": data.ad.get("primaryText", "Check this out!"),
            "name": data.ad.get("headline", "Learn More"),
            "description": data.ad.get("description", ""),
            "call_to_action": {
                "type": cta_type,
                "value": {"link": project_url}
            }
        }

        # Add image hash if available
        if image_hash:
            link_data["image_hash"] = image_hash
            logger.info(f"Adding image_hash to creative: {image_hash}")
        else:
            logger.warning("No image_hash available - creative will be without image")

        object_story_spec = {
            "page_id": data.page_id,
            "link_data": link_data
        }

        logger.info(f"Creating Ad Creative with object_story_spec: page_id={data.page_id}, link={project_url}")

        try:
            creative = AdAccount(ad_account_id).create_ad_creative(params={
                AdCreative.Field.name: f"Idea2Ad Creative - {project_url[:30]}",
                AdCreative.Field.object_story_spec: object_story_spec,
            })
            creative_id = creative.get_id()
            logger.info(f"Ad Creative created successfully: {creative_id}")
        except Exception as creative_err:
            logger.error(f"Creative creation failed: {creative_err}")
            # Return failure - don't pretend success
            return {
                "success": False,
                "campaign_id": campaign.get_id(),
                "ad_set_id": ad_set.get_id(),
                "creative_id": None,
                "ad_id": None,
                "error": f"Creative creation failed: {creative_err}"
            }

        # Step 5: Create Ad linking creative to ad set
        ad_id = None
        logger.info(f"Creating Ad with creative_id={creative_id}, adset_id={ad_set.get_id()}")
        try:
            ad = AdAccount(ad_account_id).create_ad(params={
                Ad.Field.name: f"Idea2Ad Ad - {data.ad.get('headline', 'Ad')[:30]}",
                Ad.Field.adset_id: ad_set.get_id(),
                Ad.Field.creative: {"creative_id": creative_id},
                Ad.Field.status: "PAUSED",
            })
            ad_id = ad.get_id()
            logger.info(f"Ad created successfully: {ad_id}")
        except Exception as ad_err:
            logger.error(f"Ad creation failed: {ad_err}")
            return {
                "success": False,
                "campaign_id": campaign.get_id(),
                "ad_set_id": ad_set.get_id(),
                "creative_id": creative_id,
                "ad_id": None,
                "error": f"Ad creation failed: {ad_err}"
            }

        return {
            "success": True,
            "campaign_id": campaign.get_id(),
            "ad_set_id": ad_set.get_id(),
            "creative_id": creative_id,
            "ad_id": ad_id,
            "message": "Campaign published successfully with Ad in PAUSED status"
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
