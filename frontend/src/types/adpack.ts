/**
 * AdPack types (Phase 5)
 */

export type AdStrategy = 'product_aware' | 'product_unaware';

export interface AdCreative {
  id: string;
  ad_type_id: string;
  strategy: AdStrategy;
  format: 'static' | 'video' | 'carousel';
  aspect_ratio: string;
  primary_text: string;
  headline: string;
  description: string;
  image_url?: string;
  asset_url?: string;
  image_brief?: {
    approach: string;
    creative_type?: string;
  };
  call_to_action: string;
}

export interface TargetingRationale {
  age_range_reason: string;
  geo_reason: string;
  exclusion_reason?: string;
  methodology: string;
}

export interface SmartBroadTargeting {
  age_min: number;
  age_max: number;
  genders: string[];
  geo_locations: string[];
  excluded_geo_locations: string[];
  exclusions: string[];
  rationale: TargetingRationale;
}

export interface CampaignStructure {
  campaign_name: string;
  objective: string;
  adset_name: string;
  ad_count: number;
}

export interface AdPack {
  id: string;
  project_url: string;
  creatives: AdCreative[];
  targeting: SmartBroadTargeting;
  budget_daily: number;
  duration_days: number;
  campaign_structure: CampaignStructure;
  status: string;
  meta_campaign_id?: string;
  meta_adset_id?: string;
  created_from?: string;
}

export interface AdPackUpdateRequest {
  creative_id?: string;
  primary_text?: string;
  headline?: string;
  description?: string;
  budget_daily?: number;
  duration_days?: number;
}
