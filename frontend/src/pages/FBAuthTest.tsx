/**
 * FB OAuth Test Page (DEV ONLY)
 * Test page for Facebook OAuth + ad publishing flow
 * Access at: #/test/fb-auth
 *
 * NOTE: This is a development/debugging tool only.
 * Production publish flow uses PublishView component.
 */
import { useState, useEffect } from 'react';
import {
  Facebook,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Loader2,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { useFacebookAuth } from '../hooks/useFacebookAuth';
import { getPaymentStatus, publishCampaign } from '../api/facebook';
import { MetaAdPreview } from '../components/ui/MetaAdPreview';
import type { FBPage, FBAdAccount, PaymentStatusResponse, PublishCampaignResponse } from '../types/facebook';

// Sample ad data from plan
const SAMPLE_AD = {
  id: 1,
  imageUrl: "https://idea2ad-images-1767533248.s3.us-east-1.amazonaws.com/campaigns/25c9cc88/20260116_221755_38423e92.png",
  primaryText: "Tired of slow CI/CD pipelines and high GitHub runner costs? Blacksmith is a drop-in replacement that makes your GitHub Actions 2x-40x faster and cuts runner costs by 75%.",
  headline: "Faster GitHub Actions: 2x-40x!",
  description: "Blacksmith speeds up GitHub Actions...",
};

const SAMPLE_CONFIG = {
  project_url: "https://blacksmith.sh",
  targeting: {
    geo_locations: ["US"],
    age_min: 25,
    age_max: 55
  },
  budget: 5000, // $50 in cents
  call_to_action: "LEARN_MORE",
};

export function FBAuthTest() {
  const {
    isConnected,
    isLoading: authLoading,
    error: authError,
    status,
    sessionId,
    connect,
    disconnect,
    refreshStatus
  } = useFacebookAuth();

  // Selection state
  const [selectedPageId, setSelectedPageId] = useState<string>('');
  const [selectedAdAccountId, setSelectedAdAccountId] = useState<string>('');

  // Payment status
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatusResponse | null>(null);
  const [paymentLoading, setPaymentLoading] = useState(false);

  // Publish state
  const [publishResult, setPublishResult] = useState<PublishCampaignResponse | null>(null);
  const [publishLoading, setPublishLoading] = useState(false);
  const [publishError, setPublishError] = useState<string | null>(null);

  // Debug panel
  const [showDebug, setShowDebug] = useState(false);
  const [debugData, setDebugData] = useState<Record<string, unknown>>({});

  // Auto-select first page/ad account when connected
  useEffect(() => {
    if (status?.connected) {
      if (status.pages?.length && !selectedPageId) {
        setSelectedPageId(status.pages[0].id);
      }
      if (status.adAccounts?.length && !selectedAdAccountId) {
        setSelectedAdAccountId(status.adAccounts[0].id);
      }
    }
  }, [status, selectedPageId, selectedAdAccountId]);

  // Check payment status when ad account changes
  useEffect(() => {
    if (selectedAdAccountId && sessionId) {
      checkPaymentStatus();
    }
  }, [selectedAdAccountId, sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  const checkPaymentStatus = async () => {
    if (!selectedAdAccountId) return;

    setPaymentLoading(true);
    try {
      const result = await getPaymentStatus(sessionId || undefined, selectedAdAccountId);
      setPaymentStatus(result);
      updateDebug('paymentStatus', result);
    } catch (err) {
      setPaymentStatus({ has_payment_method: false, error: err instanceof Error ? err.message : 'Failed' });
    } finally {
      setPaymentLoading(false);
    }
  };

  const handlePublish = async () => {
    if (!selectedPageId || !selectedAdAccountId) return;

    setPublishLoading(true);
    setPublishError(null);
    setPublishResult(null);

    try {
      const result = await publishCampaign({
        page_id: selectedPageId,
        ad_account_id: selectedAdAccountId,
        ad: {
          imageUrl: SAMPLE_AD.imageUrl,
          primaryText: SAMPLE_AD.primaryText,
          headline: SAMPLE_AD.headline,
          description: SAMPLE_AD.description,
        },
        campaign_data: {
          project_url: SAMPLE_CONFIG.project_url,
          targeting: SAMPLE_CONFIG.targeting,
        },
        settings: {
          budget: SAMPLE_CONFIG.budget,
          duration_days: 3,
          call_to_action: SAMPLE_CONFIG.call_to_action,
        },
      }, sessionId || undefined);

      setPublishResult(result);
      updateDebug('publishResult', result);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Failed to publish';
      setPublishError(errMsg);
      updateDebug('publishError', errMsg);
    } finally {
      setPublishLoading(false);
    }
  };

  const updateDebug = (key: string, value: unknown) => {
    setDebugData(prev => ({ ...prev, [key]: value, timestamp: new Date().toISOString() }));
  };

  // Update debug with status changes
  useEffect(() => {
    if (status) {
      updateDebug('fbStatus', status);
    }
  }, [status]);

  const selectedPage = status?.pages?.find(p => p.id === selectedPageId);
  const selectedAdAccount = status?.adAccounts?.find(a => a.id === selectedAdAccountId);

  return (
    <div className="min-h-screen bg-brand-dark text-white p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-display font-bold">FB OAuth Test</h1>
            <p className="text-gray-400 text-sm mt-1">Test Facebook OAuth + Ad Publishing Flow</p>
          </div>
          <a
            href="#/"
            className="text-gray-400 hover:text-white text-sm font-mono"
          >
            ← Back to Home
          </a>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Connection Card */}
            <div className="bg-brand-gray border border-white/10 rounded-lg p-6">
              <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Facebook className="w-5 h-5 text-blue-500" />
                Facebook Connection
              </h2>

              {authLoading ? (
                <div className="flex items-center gap-2 text-gray-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Checking connection...
                </div>
              ) : isConnected && status?.user ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                      {status.user.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-medium">{status.user.name}</div>
                      <div className="text-sm text-gray-400">ID: {status.user.id}</div>
                    </div>
                    <CheckCircle className="w-5 h-5 text-green-500 ml-auto" />
                  </div>
                  <div className="flex items-center gap-4">
                    <button
                      onClick={disconnect}
                      className="text-sm text-red-400 hover:text-red-300"
                    >
                      Disconnect
                    </button>
                    <button
                      onClick={refreshStatus}
                      className="text-sm text-gray-400 hover:text-white flex items-center gap-1"
                    >
                      <RefreshCw className="w-3 h-3" />
                      Refresh
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {authError && (
                    <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 p-3 rounded">
                      {authError}
                    </div>
                  )}
                  <button
                    onClick={connect}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
                  >
                    <Facebook className="w-5 h-5" />
                    Connect with Facebook
                  </button>
                </div>
              )}
            </div>

            {/* Account Selection Card */}
            {isConnected && (
              <div className="bg-brand-gray border border-white/10 rounded-lg p-6">
                <h2 className="text-lg font-bold mb-4">Account Selection</h2>

                <div className="space-y-4">
                  {/* Page Selector */}
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Facebook Page</label>
                    <select
                      value={selectedPageId}
                      onChange={(e) => setSelectedPageId(e.target.value)}
                      className="w-full bg-brand-dark border border-white/10 rounded px-3 py-2 text-white focus:outline-none focus:border-brand-lime"
                    >
                      <option value="">Select a page...</option>
                      {status?.pages?.map((page: FBPage) => (
                        <option key={page.id} value={page.id}>
                          {page.name} ({page.category || 'Page'})
                        </option>
                      ))}
                    </select>
                    {status?.pages?.length === 0 && (
                      <p className="text-yellow-400 text-sm mt-1">No pages found. Create a Facebook Page first.</p>
                    )}
                  </div>

                  {/* Ad Account Selector */}
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Ad Account</label>
                    <select
                      value={selectedAdAccountId}
                      onChange={(e) => setSelectedAdAccountId(e.target.value)}
                      className="w-full bg-brand-dark border border-white/10 rounded px-3 py-2 text-white focus:outline-none focus:border-brand-lime"
                    >
                      <option value="">Select an ad account...</option>
                      {status?.adAccounts?.map((account: FBAdAccount) => (
                        <option key={account.id} value={account.id}>
                          {account.name || account.id} ({account.currency})
                        </option>
                      ))}
                    </select>
                    {status?.adAccounts?.length === 0 && (
                      <p className="text-yellow-400 text-sm mt-1">No ad accounts found. Create one in Meta Business Manager.</p>
                    )}
                  </div>

                  {/* Payment Status */}
                  {selectedAdAccountId && (
                    <div className="flex items-center justify-between p-3 bg-brand-dark rounded border border-white/5">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-400">Payment Method:</span>
                        {paymentLoading ? (
                          <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                        ) : paymentStatus?.has_payment_method ? (
                          <span className="flex items-center gap-1 text-green-400 text-sm">
                            <CheckCircle className="w-4 h-4" />
                            Valid
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-red-400 text-sm">
                            <XCircle className="w-4 h-4" />
                            Not Set
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={checkPaymentStatus}
                          disabled={paymentLoading}
                          className="text-gray-400 hover:text-white"
                        >
                          <RefreshCw className={`w-4 h-4 ${paymentLoading ? 'animate-spin' : ''}`} />
                        </button>
                        {paymentStatus?.add_payment_url && !paymentStatus.has_payment_method && (
                          <a
                            href={paymentStatus.add_payment_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1"
                          >
                            Add Payment <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Publish Card */}
            {isConnected && selectedPageId && selectedAdAccountId && (
              <div className="bg-brand-gray border border-white/10 rounded-lg p-6">
                <h2 className="text-lg font-bold mb-4">Publish Test Ad</h2>

                <div className="space-y-4">
                  {/* Config Summary */}
                  <div className="text-sm space-y-1 text-gray-400">
                    <div>Page: <span className="text-white">{selectedPage?.name}</span></div>
                    <div>Ad Account: <span className="text-white">{selectedAdAccount?.name || selectedAdAccountId}</span></div>
                    <div>Budget: <span className="text-white">${SAMPLE_CONFIG.budget / 100}</span> (3 days)</div>
                    <div>Status: <span className="text-yellow-400">PAUSED</span></div>
                  </div>

                  {/* Publish Button */}
                  <button
                    onClick={handlePublish}
                    disabled={publishLoading || !paymentStatus?.has_payment_method}
                    className="w-full bg-brand-lime hover:bg-brand-lime/90 text-brand-dark font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {publishLoading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Publishing...
                      </>
                    ) : (
                      'Publish Test Ad'
                    )}
                  </button>

                  {!paymentStatus?.has_payment_method && (
                    <p className="text-yellow-400 text-sm flex items-center gap-1">
                      <AlertCircle className="w-4 h-4" />
                      Add a payment method to publish ads
                    </p>
                  )}

                  {/* Publish Error */}
                  {publishError && (
                    <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 p-3 rounded">
                      {publishError}
                    </div>
                  )}

                  {/* Publish Result */}
                  {publishResult && (
                    <div className={`p-4 rounded border ${publishResult.success ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
                      <div className={`font-bold mb-2 ${publishResult.success ? 'text-green-400' : 'text-red-400'}`}>
                        {publishResult.success ? 'Published Successfully!' : 'Publish Failed'}
                      </div>

                      {publishResult.success && (
                        <div className="space-y-2 text-sm">
                          {publishResult.campaign_id && (
                            <div className="flex items-center justify-between">
                              <span className="text-gray-400">Campaign ID:</span>
                              <a
                                href={`https://www.facebook.com/adsmanager/manage/campaigns?act=${selectedAdAccountId.replace('act_', '')}&campaign_ids=${publishResult.campaign_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-400 hover:text-blue-300 flex items-center gap-1 font-mono"
                              >
                                {publishResult.campaign_id} <ExternalLink className="w-3 h-3" />
                              </a>
                            </div>
                          )}
                          {publishResult.ad_set_id && (
                            <div className="flex items-center justify-between">
                              <span className="text-gray-400">Ad Set ID:</span>
                              <span className="font-mono text-white">{publishResult.ad_set_id}</span>
                            </div>
                          )}
                          {publishResult.ad_id && (
                            <div className="flex items-center justify-between">
                              <span className="text-gray-400">Ad ID:</span>
                              <a
                                href={`https://www.facebook.com/adsmanager/manage/ads?act=${selectedAdAccountId.replace('act_', '')}&selected_ad_ids=${publishResult.ad_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-400 hover:text-blue-300 flex items-center gap-1 font-mono"
                              >
                                {publishResult.ad_id} <ExternalLink className="w-3 h-3" />
                              </a>
                            </div>
                          )}
                        </div>
                      )}

                      {publishResult.error && (
                        <div className="text-red-400 text-sm mt-2">{publishResult.error}</div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Ad Preview */}
          <div className="space-y-6">
            <div className="bg-brand-gray border border-white/10 rounded-lg p-6">
              <h2 className="text-lg font-bold mb-4">Ad Preview</h2>
              <div className="flex justify-center">
                <MetaAdPreview
                  ad={SAMPLE_AD}
                  pageName={selectedPage?.name || "Your Page"}
                  websiteUrl={SAMPLE_CONFIG.project_url}
                />
              </div>
            </div>

            {/* Debug Panel */}
            <div className="bg-brand-gray border border-white/10 rounded-lg overflow-hidden">
              <button
                onClick={() => setShowDebug(!showDebug)}
                className="w-full p-4 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
              >
                <span className="font-bold text-sm">Debug Panel</span>
                {showDebug ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showDebug && (
                <div className="p-4 border-t border-white/10">
                  <div className="space-y-2 text-xs font-mono">
                    <div className="text-gray-400">Session ID: {sessionId || 'none'}</div>
                    <div className="text-gray-400">Connected: {String(isConnected)}</div>
                  </div>
                  <pre className="mt-4 p-3 bg-brand-dark rounded text-xs overflow-auto max-h-96 text-gray-300">
                    {JSON.stringify(debugData, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
