/**
 * Facebook/Meta OAuth and API types
 */

// User info from Facebook
export interface FBUser {
  id: string;
  name: string;
}

// Facebook Page
export interface FBPage {
  id: string;
  name: string;
  category?: string;
  access_token?: string;
}

// Ad Account
export interface FBAdAccount {
  id: string;
  name: string;
  account_status: number;
  currency: string;
}

// Connection status response from /meta/fb-status
export interface FBStatusResponse {
  connected: boolean;
  user?: FBUser;
  pages?: FBPage[];
  adAccounts?: FBAdAccount[];
  selectedAdAccountId?: string;
}

// Payment status response from /meta/payment-status
export interface PaymentStatusResponse {
  has_payment_method: boolean;
  account_status?: number;
  is_active?: boolean;
  add_payment_url?: string;
  error?: string;
}

// Publish campaign request
export interface PublishCampaignRequest {
  page_id: string;
  ad_account_id?: string;
  ad: {
    imageUrl?: string;
    primaryText: string;
    headline: string;
    description: string;
  };
  campaign_data: {
    project_url: string;
    targeting?: {
      geo_locations?: string[];
      age_min?: number;
      age_max?: number;
    };
  };
  settings: {
    budget: number; // in cents
    duration_days?: number;
    call_to_action?: string;
    locations?: Array<{ key: string; name?: string }>;
  };
}

// Publish campaign response from /meta/publish-campaign
export interface PublishCampaignResponse {
  success: boolean;
  campaign_id?: string;
  ad_set_id?: string;
  creative_id?: string;
  ad_id?: string;
  message?: string;
  error?: string;
}

// OAuth message types from popup
export interface FBAuthSuccessMessage {
  type: 'FB_AUTH_SUCCESS';
  session_id: string;
}

export interface FBAuthErrorMessage {
  type: 'FB_AUTH_ERROR';
  error: string;
}

export type FBAuthMessage = FBAuthSuccessMessage | FBAuthErrorMessage;
