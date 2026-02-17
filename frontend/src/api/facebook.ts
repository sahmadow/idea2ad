/**
 * Facebook/Meta API client
 */
import type {
  FBStatusResponse,
  PaymentStatusResponse,
  PublishCampaignRequest,
  PublishCampaignResponse,
  CampaignStatusRequest,
  CampaignStatusResponse,
} from '../types/facebook';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Storage key for session ID
const FB_SESSION_KEY = 'fb_session_id';

/**
 * Get stored session ID from localStorage
 */
export function getStoredSessionId(): string | null {
  return localStorage.getItem(FB_SESSION_KEY);
}

/**
 * Store session ID in localStorage
 */
export function storeSessionId(sessionId: string): void {
  localStorage.setItem(FB_SESSION_KEY, sessionId);
}

/**
 * Clear stored session ID
 */
export function clearSessionId(): void {
  localStorage.removeItem(FB_SESSION_KEY);
}

/**
 * Build headers with session ID
 */
function buildHeaders(sessionId?: string): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  const sid = sessionId || getStoredSessionId();
  if (sid) {
    headers['X-FB-Session'] = sid;
  }
  return headers;
}

/**
 * Check Facebook connection status
 */
export async function getFBStatus(sessionId?: string): Promise<FBStatusResponse> {
  const response = await fetch(`${API_URL}/meta/fb-status`, {
    method: 'GET',
    headers: buildHeaders(sessionId),
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to check status' }));
    throw new Error(error.detail || 'Failed to check Facebook status');
  }

  return response.json();
}

/**
 * Check payment status for an ad account
 */
export async function getPaymentStatus(
  sessionId?: string,
  adAccountId?: string
): Promise<PaymentStatusResponse> {
  const params = new URLSearchParams();
  if (adAccountId) {
    params.set('ad_account_id', adAccountId);
  }

  const url = `${API_URL}/meta/payment-status${params.toString() ? '?' + params.toString() : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: buildHeaders(sessionId),
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to check payment status' }));
    throw new Error(error.detail || 'Failed to check payment status');
  }

  return response.json();
}

/**
 * Publish campaign to Meta
 */
export async function publishCampaign(
  data: PublishCampaignRequest,
  sessionId?: string
): Promise<PublishCampaignResponse> {
  const response = await fetch(`${API_URL}/meta/publish-campaign`, {
    method: 'POST',
    headers: buildHeaders(sessionId),
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to publish campaign' }));
    throw new Error(error.detail || 'Failed to publish campaign');
  }

  return response.json();
}

/**
 * Activate a paused campaign
 */
export async function activateCampaign(
  data: CampaignStatusRequest,
  sessionId?: string
): Promise<CampaignStatusResponse> {
  const response = await fetch(`${API_URL}/meta/activate-campaign`, {
    method: 'POST',
    headers: buildHeaders(sessionId),
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to activate campaign' }));
    throw new Error(error.detail || 'Failed to activate campaign');
  }

  return response.json();
}

/**
 * Pause an active campaign
 */
export async function pauseCampaign(
  data: CampaignStatusRequest,
  sessionId?: string
): Promise<CampaignStatusResponse> {
  const response = await fetch(`${API_URL}/meta/pause-campaign`, {
    method: 'POST',
    headers: buildHeaders(sessionId),
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to pause campaign' }));
    throw new Error(error.detail || 'Failed to pause campaign');
  }

  return response.json();
}

/**
 * Disconnect Facebook session
 */
export async function disconnectFacebook(sessionId?: string): Promise<void> {
  await fetch(`${API_URL}/meta/disconnect`, {
    method: 'POST',
    headers: buildHeaders(sessionId),
    credentials: 'include',
  });
  clearSessionId();
}

/**
 * Get OAuth URL for starting the flow
 */
export function getOAuthUrl(): string {
  return `${API_URL}/auth/facebook`;
}
