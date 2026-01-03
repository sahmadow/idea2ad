from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db import db
from app.auth.dependencies import get_current_user
from app.models import CampaignDraft, AnalysisResult, CreativeAsset, ImageBrief
from app.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CampaignResponse(BaseModel):
    id: str
    name: str
    project_url: str
    status: str
    objective: str
    budget_daily: float
    meta_campaign_id: Optional[str] = None
    meta_adset_id: Optional[str] = None
    meta_ad_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CampaignDetailResponse(CampaignResponse):
    analysis: Optional[dict] = None
    creatives: List[dict] = []
    image_briefs: List[dict] = []


class CampaignCreateRequest(BaseModel):
    name: str
    campaign_draft: dict


class CampaignUpdateRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    objective: Optional[str] = None
    budget_daily: Optional[float] = None


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List all campaigns for authenticated user."""
    try:
        where_clause = {"user_id": current_user["id"], "deleted_at": None}
        if status:
            where_clause["status"] = status

        campaigns = await db.campaign.find_many(
            where=where_clause,
            order={"created_at": "desc"},
            take=limit,
            skip=offset
        )

        return [
            CampaignResponse(
                id=c.id,
                name=c.name,
                project_url=c.project_url,
                status=c.status,
                objective=c.objective,
                budget_daily=c.budget_daily,
                meta_campaign_id=c.meta_campaign_id,
                meta_adset_id=c.meta_adset_id,
                meta_ad_id=c.meta_ad_id,
                created_at=c.created_at,
                updated_at=c.updated_at
            )
            for c in campaigns
        ]
    except Exception as e:
        logger.error(f"Failed to list campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaigns")


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get campaign details with analysis, creatives, and image briefs."""
    try:
        campaign = await db.campaign.find_first(
            where={
                "id": campaign_id,
                "user_id": current_user["id"],
                "deleted_at": None
            },
            include={
                "analysis": True,
                "creatives": True,
                "image_briefs": True
            }
        )

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return CampaignDetailResponse(
            id=campaign.id,
            name=campaign.name,
            project_url=campaign.project_url,
            status=campaign.status,
            objective=campaign.objective,
            budget_daily=campaign.budget_daily,
            meta_campaign_id=campaign.meta_campaign_id,
            meta_adset_id=campaign.meta_adset_id,
            meta_ad_id=campaign.meta_ad_id,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            analysis=campaign.analysis.__dict__ if campaign.analysis else None,
            creatives=[c.__dict__ for c in campaign.creatives] if campaign.creatives else [],
            image_briefs=[ib.__dict__ for ib in campaign.image_briefs] if campaign.image_briefs else []
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaign")


@router.post("", response_model=CampaignResponse)
async def save_campaign(
    request: CampaignCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Save a campaign draft to the database."""
    try:
        draft = request.campaign_draft

        # Create campaign
        campaign = await db.campaign.create(
            data={
                "user_id": current_user["id"],
                "name": request.name,
                "project_url": draft.get("project_url", ""),
                "status": draft.get("status", "ANALYZED"),
                "objective": draft.get("analysis", {}).get("objective", "OUTCOME_SALES"),
                "budget_daily": draft.get("targeting", {}).get("budget_daily", 20.0)
            }
        )

        # Save analysis
        analysis = draft.get("analysis")
        if analysis:
            styling = analysis.get("styling_guide", {})
            await db.analysis.create(
                data={
                    "campaign_id": campaign.id,
                    "summary": analysis.get("summary", ""),
                    "unique_selling_proposition": analysis.get("unique_selling_proposition", ""),
                    "pain_points": analysis.get("pain_points", []),
                    "call_to_action": analysis.get("call_to_action", ""),
                    "buyer_persona": analysis.get("buyer_persona", {}),
                    "keywords": analysis.get("keywords", []),
                    "styling_guide": styling
                }
            )

        # Save creatives
        creatives = draft.get("suggested_creatives", [])
        for creative in creatives:
            await db.creative.create(
                data={
                    "campaign_id": campaign.id,
                    "type": creative.get("type", ""),
                    "content": creative.get("content", ""),
                    "rationale": creative.get("rationale")
                }
            )

        # Save image briefs
        image_briefs = draft.get("image_briefs", [])
        for brief in image_briefs:
            await db.imagebrief.create(
                data={
                    "campaign_id": campaign.id,
                    "approach": brief.get("approach", ""),
                    "visual_description": brief.get("visual_description", ""),
                    "styling_notes": brief.get("styling_notes", ""),
                    "text_overlays": brief.get("text_overlays", []),
                    "meta_best_practices": brief.get("meta_best_practices", []),
                    "rationale": brief.get("rationale", ""),
                    "image_url": brief.get("image_url"),
                    "s3_key": brief.get("s3_key")
                }
            )

        logger.info(f"Campaign saved: {campaign.id} by user {current_user['id']}")

        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            project_url=campaign.project_url,
            status=campaign.status,
            objective=campaign.objective,
            budget_daily=campaign.budget_daily,
            meta_campaign_id=campaign.meta_campaign_id,
            meta_adset_id=campaign.meta_adset_id,
            meta_ad_id=campaign.meta_ad_id,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at
        )
    except Exception as e:
        logger.error(f"Failed to save campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to save campaign")


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    request: CampaignUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update campaign metadata."""
    try:
        # Check ownership
        campaign = await db.campaign.find_first(
            where={
                "id": campaign_id,
                "user_id": current_user["id"],
                "deleted_at": None
            }
        )

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Build update data
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.status is not None:
            update_data["status"] = request.status
        if request.objective is not None:
            update_data["objective"] = request.objective
        if request.budget_daily is not None:
            update_data["budget_daily"] = request.budget_daily

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        updated = await db.campaign.update(
            where={"id": campaign_id},
            data=update_data
        )

        return CampaignResponse(
            id=updated.id,
            name=updated.name,
            project_url=updated.project_url,
            status=updated.status,
            objective=updated.objective,
            budget_daily=updated.budget_daily,
            meta_campaign_id=updated.meta_campaign_id,
            meta_adset_id=updated.meta_adset_id,
            meta_ad_id=updated.meta_ad_id,
            created_at=updated.created_at,
            updated_at=updated.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update campaign")


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a campaign."""
    try:
        # Check ownership
        campaign = await db.campaign.find_first(
            where={
                "id": campaign_id,
                "user_id": current_user["id"],
                "deleted_at": None
            }
        )

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Soft delete
        from datetime import datetime
        await db.campaign.update(
            where={"id": campaign_id},
            data={"deleted_at": datetime.utcnow()}
        )

        logger.info(f"Campaign deleted: {campaign_id} by user {current_user['id']}")

        return {"message": "Campaign deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete campaign")


@router.post("/{campaign_id}/publish")
async def publish_campaign(
    campaign_id: str,
    page_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Publish a saved campaign to Meta Ads."""
    try:
        # Get campaign with all data
        campaign = await db.campaign.find_first(
            where={
                "id": campaign_id,
                "user_id": current_user["id"],
                "deleted_at": None
            },
            include={
                "analysis": True,
                "creatives": True,
                "image_briefs": True
            }
        )

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.status == "PUBLISHED":
            raise HTTPException(status_code=400, detail="Campaign already published")

        # Reconstruct campaign draft for Meta API
        from app.services.meta_api import get_meta_manager

        campaign_draft = {
            "project_url": campaign.project_url,
            "analysis": {
                "summary": campaign.analysis.summary if campaign.analysis else "",
                "unique_selling_proposition": campaign.analysis.unique_selling_proposition if campaign.analysis else "",
                "pain_points": campaign.analysis.pain_points if campaign.analysis else [],
                "call_to_action": campaign.analysis.call_to_action if campaign.analysis else "",
                "buyer_persona": campaign.analysis.buyer_persona if campaign.analysis else {},
                "keywords": campaign.analysis.keywords if campaign.analysis else []
            },
            "suggested_creatives": [
                {"type": c.type, "content": c.content, "rationale": c.rationale}
                for c in campaign.creatives
            ] if campaign.creatives else [],
            "image_briefs": [
                {
                    "approach": ib.approach,
                    "visual_description": ib.visual_description,
                    "image_url": ib.image_url
                }
                for ib in campaign.image_briefs
            ] if campaign.image_briefs else []
        }

        meta_manager = get_meta_manager()
        result = meta_manager.publish_complete_campaign(campaign_draft, page_id=page_id)

        if result.get("success"):
            # Update campaign with Meta IDs
            await db.campaign.update(
                where={"id": campaign_id},
                data={
                    "status": "PUBLISHED",
                    "meta_campaign_id": result.get("campaign_id"),
                    "meta_adset_id": result.get("adset_id"),
                    "meta_ad_id": result.get("ad_id"),
                    "meta_creative_id": result.get("creative_id")
                }
            )

        return {
            "success": result.get("success", False),
            "message": "Campaign published to Meta" if result.get("success") else "Failed to publish",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish campaign: {str(e)}")
