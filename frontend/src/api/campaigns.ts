/**
 * Campaign API client
 */
import type { Campaign, CampaignDetail, CampaignCreateRequest, CampaignUpdateRequest } from '../types/campaign';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function listCampaigns(
  status?: string,
  limit = 20,
  offset = 0
): Promise<Campaign[]> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  params.set('limit', String(limit));
  params.set('offset', String(offset));

  const response = await fetch(`${API_URL}/campaigns?${params.toString()}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) throw new Error('Not authenticated');
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch campaigns' }));
    throw new Error(error.detail || 'Failed to fetch campaigns');
  }

  return response.json();
}

export async function getCampaign(campaignId: string): Promise<CampaignDetail> {
  const response = await fetch(`${API_URL}/campaigns/${campaignId}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) throw new Error('Not authenticated');
    if (response.status === 404) throw new Error('Campaign not found');
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch campaign' }));
    throw new Error(error.detail || 'Failed to fetch campaign');
  }

  return response.json();
}

export async function saveCampaign(request: CampaignCreateRequest): Promise<Campaign> {
  const response = await fetch(`${API_URL}/campaigns`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    if (response.status === 401) throw new Error('Not authenticated');
    const error = await response.json().catch(() => ({ detail: 'Failed to save campaign' }));
    throw new Error(error.detail || 'Failed to save campaign');
  }

  return response.json();
}

export async function updateCampaign(
  campaignId: string,
  request: CampaignUpdateRequest
): Promise<Campaign> {
  const response = await fetch(`${API_URL}/campaigns/${campaignId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    if (response.status === 401) throw new Error('Not authenticated');
    if (response.status === 404) throw new Error('Campaign not found');
    const error = await response.json().catch(() => ({ detail: 'Failed to update campaign' }));
    throw new Error(error.detail || 'Failed to update campaign');
  }

  return response.json();
}

export async function deleteCampaign(campaignId: string): Promise<void> {
  const response = await fetch(`${API_URL}/campaigns/${campaignId}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) throw new Error('Not authenticated');
    if (response.status === 404) throw new Error('Campaign not found');
    const error = await response.json().catch(() => ({ detail: 'Failed to delete campaign' }));
    throw new Error(error.detail || 'Failed to delete campaign');
  }
}
