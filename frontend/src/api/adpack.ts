/**
 * AdPack API client (Phase 5)
 */

import type { AdPack, AdPackUpdateRequest } from '../types/adpack';
import type { CampaignDraft } from '../api';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

interface AdPackResponse {
  success: boolean;
  ad_pack?: AdPack;
  message?: string;
}

interface AdPackListResponse {
  success: boolean;
  ad_packs: AdPack[];
  count: number;
}

export async function assembleAdPack(
  campaignDraft: CampaignDraft,
  jobId?: string
): Promise<AdPack> {
  const response = await fetch(`${API_URL}/adpack`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      campaign_draft: campaignDraft,
      job_id: jobId,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to assemble ad pack');
  }

  const data: AdPackResponse = await response.json();
  if (!data.success || !data.ad_pack) {
    throw new Error('Failed to assemble ad pack');
  }
  return data.ad_pack;
}

export async function getAdPack(packId: string): Promise<AdPack> {
  const response = await fetch(`${API_URL}/adpack/${packId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch ad pack');
  }

  const data: AdPackResponse = await response.json();
  if (!data.success || !data.ad_pack) {
    throw new Error('Failed to fetch ad pack');
  }
  return data.ad_pack;
}

export async function updateAdPack(
  packId: string,
  update: AdPackUpdateRequest
): Promise<AdPack> {
  const response = await fetch(`${API_URL}/adpack/${packId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update ad pack');
  }

  const data: AdPackResponse = await response.json();
  if (!data.success || !data.ad_pack) {
    throw new Error('Failed to update ad pack');
  }
  return data.ad_pack;
}

export async function listAdPacks(): Promise<AdPack[]> {
  const response = await fetch(`${API_URL}/adpack`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to list ad packs');
  }

  const data: AdPackListResponse = await response.json();
  return data.ad_packs;
}

export async function deleteAdPack(packId: string): Promise<void> {
  const response = await fetch(`${API_URL}/adpack/${packId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete ad pack');
  }
}
