/**
 * AdPack API client (Phase 5 + V2 pipeline)
 */

import type { AdPack, AdCreative, AdPackUpdateRequest } from '../types/adpack';
import type { CampaignDraft } from '../api';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Polling config for V2 async jobs
const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 90;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

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


// =====================================================================
// V2 On-Demand Rendering
// =====================================================================

interface RenderPackItem {
  ad_type_id: string;
  aspect_ratio: string;
  image_url: string;
  generation_time_ms: number;
}

export async function renderPackImages(packId: string): Promise<RenderPackItem[]> {
  const response = await fetch(`${API_URL}/v2/render/pack`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pack_id: packId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to render images');
  }

  const data = await response.json();
  // Return full URLs so consumers don't need API_URL
  return (data.renders as RenderPackItem[]).map((r) => ({
    ...r,
    image_url: `${API_URL}${r.image_url}`,
  }));
}

// =====================================================================
// V2 Pipeline
// =====================================================================

/** Map V2 backend creative → frontend AdCreative */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapV2Creative(c: any): AdCreative {
  return {
    id: c.id,
    ad_type_id: c.ad_type_id,
    strategy: c.strategy,
    format: c.format,
    aspect_ratio: c.aspect_ratio || '1:1',
    primary_text: c.primary_text || '',
    headline: c.headline || '',
    description: c.description || '',
    image_url: c.asset_url || undefined,
    asset_url: c.asset_url || undefined,
    call_to_action: c.cta_type || 'LEARN_MORE',
  };
}

/** Map V2 backend AdPack → frontend AdPack */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapV2AdPack(raw: any, url: string): AdPack {
  const targeting = raw.targeting || {};
  const genderMap: Record<number, string> = { 1: 'male', 2: 'female' };

  return {
    id: raw.id,
    project_url: raw.source_url || url,
    creatives: (raw.creatives || []).map(mapV2Creative),
    targeting: {
      age_min: targeting.age_min ?? 18,
      age_max: targeting.age_max ?? 65,
      genders: targeting.genders
        ? targeting.genders.map((g: number) => genderMap[g] || 'all')
        : ['all'],
      geo_locations: targeting.geo_locations?.countries || ['US'],
      excluded_geo_locations: [],
      exclusions: [],
      rationale: {
        age_range_reason: targeting.targeting_rationale || '',
        geo_reason: 'Smart Broad targeting',
        methodology: 'smart_broad',
      },
    },
    budget_daily: (raw.budget_daily_cents ?? 1500) / 100,
    duration_days: raw.duration_days ?? 3,
    campaign_structure: {
      campaign_name: raw.campaign_name || 'Campaign',
      objective: raw.campaign_objective || 'OUTCOME_TRAFFIC',
      adset_name: `${raw.product_name || 'Campaign'} — Smart Broad`,
      ad_count: (raw.creatives || []).length,
    },
    status: raw.status || 'draft',
    brand_logo_url: raw.brand_logo_url || undefined,
    language: raw.language || 'en',
  };
}

// =====================================================================
// Quick Mode V2
// =====================================================================

interface QuickV2Params {
  description?: string;
  image_url?: string;
  edit_prompt?: string;
  product_name?: string;
}

export async function quickGenerateV2(params: QuickV2Params): Promise<AdPack> {
  const res = await fetch(`${API_URL}/quick/generate/v2`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Quick V2 generation failed');
  }

  const data = await res.json();
  const raw = data.ad_pack;
  return mapV2AdPack(raw, '');
}

/**
 * Run V2 analysis pipeline — returns AdPack directly (no CampaignDraft).
 * Optionally pass image_url + edit_prompt for manual_image_upload creative.
 */
export async function analyzeV2(
  url: string,
  onProgress?: (status: string) => void,
  options?: { image_url?: string; edit_prompt?: string },
): Promise<AdPack> {
  // 1. Start async job
  const startRes = await fetch(`${API_URL}/v2/analyze/async`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      image_url: options?.image_url,
      edit_prompt: options?.edit_prompt,
    }),
  });

  if (!startRes.ok) {
    const err = await startRes.json();
    throw new Error(err.detail || 'Failed to start V2 analysis');
  }

  const { job_id } = await startRes.json();
  onProgress?.('pending');

  // 2. Poll for completion
  let attempts = 0;
  while (attempts < MAX_POLL_ATTEMPTS) {
    const res = await fetch(`${API_URL}/jobs/${job_id}`);
    if (!res.ok) throw new Error('Failed to check job status');

    const job = await res.json();
    onProgress?.(job.status);

    if (job.status === 'complete' && job.result?.ad_pack) {
      return mapV2AdPack(job.result.ad_pack, url);
    }
    if (job.status === 'failed') {
      throw new Error(job.error || 'V2 analysis failed');
    }

    await sleep(POLL_INTERVAL_MS);
    attempts++;
  }

  throw new Error('Analysis timed out');
}
