"""
AdPack Preview API Router (Phase 5)

Provides endpoints for:
- Assembling ad packs from campaign drafts
- Retrieving ad pack with all creatives
- Updating individual creatives (inline editing)
- Updating budget/duration controls
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.models import AdPack, AdPackUpdateRequest, CampaignDraft
from app.services.adpack import (
    assemble_ad_pack,
    get_ad_pack,
    update_ad_pack,
    list_ad_packs,
    delete_ad_pack,
)

router = APIRouter(prefix="/adpack", tags=["adpack"])


class AssembleRequest(BaseModel):
    campaign_draft: CampaignDraft
    job_id: Optional[str] = None


class AdPackResponse(BaseModel):
    success: bool
    ad_pack: Optional[AdPack] = None
    message: Optional[str] = None


class AdPackListResponse(BaseModel):
    success: bool
    ad_packs: List[AdPack]
    count: int


@router.post("", response_model=AdPackResponse)
async def create_ad_pack(request: AssembleRequest):
    """
    Assemble a new AdPack from a CampaignDraft.

    Consolidates all creatives, derives Smart Broad targeting,
    and sets default budget ($15/day, 3 days).
    """
    try:
        ad_pack = assemble_ad_pack(
            draft=request.campaign_draft,
            job_id=request.job_id,
        )
        return AdPackResponse(success=True, ad_pack=ad_pack)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to assemble ad pack: {str(e)}",
        )


@router.get("/{pack_id}", response_model=AdPackResponse)
async def get_ad_pack_by_id(pack_id: str):
    """
    Retrieve a complete AdPack with all creative assets and metadata.
    """
    ad_pack = get_ad_pack(pack_id)
    if not ad_pack:
        raise HTTPException(status_code=404, detail=f"AdPack {pack_id} not found")
    return AdPackResponse(success=True, ad_pack=ad_pack)


@router.patch("/{pack_id}", response_model=AdPackResponse)
async def patch_ad_pack(pack_id: str, update: AdPackUpdateRequest):
    """
    Update AdPack fields.

    Supports inline editing of:
    - Creative copy (primary_text, headline, description) via creative_id
    - Budget (budget_daily)
    - Duration (duration_days)
    """
    ad_pack = update_ad_pack(pack_id, update)
    if not ad_pack:
        raise HTTPException(status_code=404, detail=f"AdPack {pack_id} not found")
    return AdPackResponse(
        success=True, ad_pack=ad_pack, message="AdPack updated successfully"
    )


@router.get("", response_model=AdPackListResponse)
async def list_all_ad_packs():
    """List all ad packs."""
    packs = list_ad_packs()
    return AdPackListResponse(success=True, ad_packs=packs, count=len(packs))


@router.delete("/{pack_id}")
async def delete_ad_pack_by_id(pack_id: str):
    """Delete an ad pack."""
    deleted = delete_ad_pack(pack_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"AdPack {pack_id} not found")
    return {"success": True, "message": f"AdPack {pack_id} deleted"}
