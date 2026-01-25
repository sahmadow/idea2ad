/**
 * Publish Campaign View
 * Production flow for publishing campaigns to Meta Ads
 */
import { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Facebook,
  CheckCircle,
  XCircle,
  ExternalLink,
  Loader2,
  RefreshCw,
  AlertCircle,
  Target,
} from 'lucide-react';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { MetaAdPreview } from './ui/MetaAdPreview';
import { useFacebookAuth } from '../hooks/useFacebookAuth';
import { getPaymentStatus, publishCampaign } from '../api/facebook';
import type { CampaignDraft, Ad } from '../api';
import type { FBPage, FBAdAccount, PaymentStatusResponse, PublishCampaignResponse } from '../types/facebook';

interface PublishViewProps {
  campaignData: CampaignDraft;
  selectedAd: Ad;
  onBack: () => void;
  onSuccess: (result: PublishCampaignResponse) => void;
}

const CTA_OPTIONS = [
  { value: 'LEARN_MORE', label: 'Learn More' },
  { value: 'SHOP_NOW', label: 'Shop Now' },
  { value: 'SIGN_UP', label: 'Sign Up' },
  { value: 'DOWNLOAD', label: 'Download' },
  { value: 'CONTACT_US', label: 'Contact Us' },
  { value: 'GET_QUOTE', label: 'Get Quote' },
  { value: 'SUBSCRIBE', label: 'Subscribe' },
];

const DURATION_OPTIONS = [
  { value: 3, label: '3 days' },
  { value: 7, label: '7 days' },
  { value: 14, label: '14 days' },
  { value: 30, label: '30 days' },
];

export function PublishView({ campaignData, selectedAd, onBack, onSuccess }: PublishViewProps) {
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

  // Campaign settings
  const [budget, setBudget] = useState<number>(50);
  const [durationDays, setDurationDays] = useState<number>(7);
  const [callToAction, setCallToAction] = useState<string>('LEARN_MORE');

  // Payment status
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatusResponse | null>(null);
  const [paymentLoading, setPaymentLoading] = useState(false);

  // Publish state
  const [publishLoading, setPublishLoading] = useState(false);
  const [publishError, setPublishError] = useState<string | null>(null);

  const pageName = new URL(campaignData.project_url).hostname.replace('www.', '');

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

    try {
      const result = await publishCampaign({
        page_id: selectedPageId,
        ad_account_id: selectedAdAccountId,
        ad: {
          imageUrl: selectedAd.imageUrl,
          primaryText: selectedAd.primaryText,
          headline: selectedAd.headline,
          description: selectedAd.description,
        },
        campaign_data: {
          project_url: campaignData.project_url,
          targeting: {
            geo_locations: campaignData.targeting.geo_locations,
            age_min: campaignData.targeting.age_min,
            age_max: campaignData.targeting.age_max,
          },
        },
        settings: {
          budget: budget * 100, // Convert to cents
          duration_days: durationDays,
          call_to_action: callToAction,
        },
      }, sessionId || undefined);

      if (result.success) {
        onSuccess(result);
      } else {
        setPublishError(result.error || 'Failed to publish campaign');
      }
    } catch (err) {
      setPublishError(err instanceof Error ? err.message : 'Failed to publish');
    } finally {
      setPublishLoading(false);
    }
  };

  const selectedPage = status?.pages?.find(p => p.id === selectedPageId);
  const estimatedTotal = budget * durationDays;

  return (
    <div className="min-h-screen bg-brand-dark text-white py-12">
      <div className="max-w-6xl mx-auto px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-mono text-sm">Back to Results</span>
          </button>
          <h1 className="text-2xl font-display font-bold">Publish Campaign</h1>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Controls */}
          <div className="space-y-6">
            {/* Connection Card */}
            <Card>
              <div className="p-6">
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
                        <div className="text-sm text-gray-400">Connected</div>
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
            </Card>

            {/* Account Selection Card */}
            {isConnected && (
              <Card>
                <div className="p-6">
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
              </Card>
            )}

            {/* Campaign Settings Card */}
            {isConnected && selectedPageId && selectedAdAccountId && (
              <Card>
                <div className="p-6">
                  <h2 className="text-lg font-bold mb-4">Campaign Settings</h2>

                  <div className="space-y-4">
                    {/* Budget */}
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Daily Budget (USD)</label>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                        <input
                          type="number"
                          min={5}
                          value={budget}
                          onChange={(e) => setBudget(Math.max(5, Number(e.target.value)))}
                          className="w-full bg-brand-dark border border-white/10 rounded px-3 py-2 pl-7 text-white focus:outline-none focus:border-brand-lime"
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">Minimum $5/day</p>
                    </div>

                    {/* Duration */}
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Duration</label>
                      <select
                        value={durationDays}
                        onChange={(e) => setDurationDays(Number(e.target.value))}
                        className="w-full bg-brand-dark border border-white/10 rounded px-3 py-2 text-white focus:outline-none focus:border-brand-lime"
                      >
                        {DURATION_OPTIONS.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </div>

                    {/* Call to Action */}
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Call to Action</label>
                      <select
                        value={callToAction}
                        onChange={(e) => setCallToAction(e.target.value)}
                        className="w-full bg-brand-dark border border-white/10 rounded px-3 py-2 text-white focus:outline-none focus:border-brand-lime"
                      >
                        {CTA_OPTIONS.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </div>

                    {/* Estimated Total */}
                    <div className="p-4 bg-brand-lime/10 border border-brand-lime/30 rounded">
                      <div className="text-sm text-gray-400 mb-1">Estimated Total</div>
                      <div className="text-2xl font-bold text-brand-lime">
                        ${estimatedTotal}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        ${budget}/day x {durationDays} days
                      </div>
                    </div>

                    {/* Publish Button */}
                    <Button
                      variant="primary"
                      onClick={handlePublish}
                      disabled={publishLoading || !paymentStatus?.has_payment_method}
                      className="w-full py-3"
                    >
                      {publishLoading ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin mr-2" />
                          Publishing...
                        </>
                      ) : (
                        'Publish Campaign'
                      )}
                    </Button>

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

                    {/* Status note */}
                    <p className="text-xs text-gray-500 text-center">
                      Campaign will be created in PAUSED status
                    </p>
                  </div>
                </div>
              </Card>
            )}
          </div>

          {/* Right Column - Preview & Targeting */}
          <div className="space-y-6">
            {/* Ad Preview */}
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-bold mb-4">Selected Ad</h2>
                <div className="flex justify-center">
                  <MetaAdPreview
                    ad={selectedAd}
                    pageName={selectedPage?.name || pageName}
                    websiteUrl={campaignData.project_url}
                  />
                </div>
              </div>
            </Card>

            {/* Targeting Summary */}
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <Target className="w-5 h-5 text-brand-lime" />
                  Targeting Summary
                </h2>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Age Range</span>
                    <span className="text-white">{campaignData.targeting.age_min} - {campaignData.targeting.age_max}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Locations</span>
                    <span className="text-white">{campaignData.targeting.geo_locations.join(', ')}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Interests</span>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {campaignData.targeting.interests.slice(0, 6).map((interest, i) => (
                        <span key={i} className="px-2 py-0.5 bg-brand-gray border border-white/10 text-xs text-gray-300 rounded">
                          {interest}
                        </span>
                      ))}
                      {campaignData.targeting.interests.length > 6 && (
                        <span className="px-2 py-0.5 text-xs text-gray-500">
                          +{campaignData.targeting.interests.length - 6} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
