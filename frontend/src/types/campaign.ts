/**
 * Campaign types matching backend Pydantic models
 */

export type CampaignStatus =
  | 'DRAFT'
  | 'ANALYZED'
  | 'GENERATING_IMAGES'
  | 'READY'
  | 'PUBLISHED'
  | 'PAUSED'
  | 'ACTIVE'
  | 'ARCHIVED';

export interface Campaign {
  id: string;
  name: string;
  project_url: string;
  status: CampaignStatus;
  objective: string;
  budget_daily: number;
  meta_campaign_id: string | null;
  meta_adset_id: string | null;
  meta_ad_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CampaignDetail extends Campaign {
  analysis: Record<string, unknown> | null;
  creatives: Record<string, unknown>[];
  image_briefs: Record<string, unknown>[];
}

export interface CampaignCreateRequest {
  name: string;
  campaign_draft: Record<string, unknown>;
}

export interface CampaignUpdateRequest {
  name?: string;
  status?: string;
  objective?: string;
  budget_daily?: number;
}
