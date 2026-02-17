/**
 * Publish Campaign View
 */
import { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Facebook,
  CheckCircle,
  XCircle,
  ExternalLink,
  RefreshCw,
  Target,
  Layers,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { MetaAdPreview } from './ui/MetaAdPreview';
import { StepIndicator } from './ui/StepIndicator';
import { ErrorBanner } from './ui/ErrorBanner';
import { Skeleton } from './ui/Skeleton';
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

const STEPS = [
  { label: 'Connect' },
  { label: 'Configure' },
  { label: 'Publish' },
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

  const [selectedPageId, setSelectedPageId] = useState<string>('');
  const [selectedAdAccountId, setSelectedAdAccountId] = useState<string>('');
  const [budget, setBudget] = useState<number>(50);
  const [durationDays, setDurationDays] = useState<number>(7);
  const [callToAction, setCallToAction] = useState<string>('LEARN_MORE');
  const [publishAllAds, setPublishAllAds] = useState<boolean>(false);
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatusResponse | null>(null);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [publishLoading, setPublishLoading] = useState(false);
  const [publishError, setPublishError] = useState<string | null>(null);

  // Check if there are multiple ads available
  const allAds = campaignData.ads || [];
  const hasMultipleAds = allAds.length > 1;

  let pageName = 'your site';
  try {
    pageName = new URL(campaignData.project_url).hostname.replace('www.', '');
  } catch {
    // quick mode may have empty project_url
  }

  // Determine current step
  const currentStep = !isConnected ? 0 : (!selectedPageId || !selectedAdAccountId) ? 1 : 2;

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
      // Build ad data for the request
      const primaryAd = {
        imageUrl: selectedAd.imageUrl,
        primaryText: selectedAd.primaryText,
        headline: selectedAd.headline,
        description: selectedAd.description,
      };

      // If publishing all ads, include them
      const adsToPublish = publishAllAds && hasMultipleAds
        ? allAds.map(ad => ({
            imageUrl: ad.imageUrl,
            primaryText: ad.primaryText,
            headline: ad.headline,
            description: ad.description,
          }))
        : undefined;

      const result = await publishCampaign({
        page_id: selectedPageId,
        ad_account_id: selectedAdAccountId,
        ad: primaryAd,
        ads: adsToPublish,
        campaign_data: {
          project_url: campaignData.project_url,
          targeting: {
            geo_locations: campaignData.targeting.geo_locations,
            age_min: campaignData.targeting.age_min,
            age_max: campaignData.targeting.age_max,
          },
        },
        settings: {
          budget: budget * 100,
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

  const selectedPage = status?.pages?.find((p: FBPage) => p.id === selectedPageId);
  const estimatedTotal = budget * durationDays;

  return (
    <div className="min-h-screen bg-brand-dark text-white py-12">
      <div className="max-w-6xl mx-auto px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-mono text-sm">Back to Results</span>
          </button>
          <h1 className="text-2xl font-display font-bold">Publish Campaign</h1>
        </div>

        {/* Step Indicator */}
        <StepIndicator steps={STEPS} currentStep={currentStep} className="mb-10" />

        <div className="grid lg:grid-cols-5 gap-8">
          {/* Left Column (3/5) */}
          <div className="lg:col-span-3 space-y-6">
            {/* Connection */}
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <Facebook className="w-5 h-5 text-blue-500" />
                  Facebook Connection
                </h2>

                {authLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-4 w-32" />
                  </div>
                ) : isConnected && status?.user ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-600 flex items-center justify-center text-white font-bold">
                        {status.user.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="font-medium">{status.user.name}</div>
                        <div className="text-sm text-gray-400">Connected</div>
                      </div>
                      <CheckCircle className="w-5 h-5 text-status-success ml-auto" />
                    </div>
                    <div className="flex items-center gap-4">
                      <button onClick={disconnect} className="text-sm text-status-error hover:opacity-80 transition-opacity">
                        Disconnect
                      </button>
                      <button onClick={refreshStatus} className="text-sm text-gray-400 hover:text-white flex items-center gap-1 transition-colors">
                        <RefreshCw className="w-3 h-3" /> Refresh
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {authError && <ErrorBanner message={authError} />}
                    <button
                      onClick={connect}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 flex items-center justify-center gap-2 transition-colors"
                    >
                      <Facebook className="w-5 h-5" />
                      Connect with Facebook
                    </button>
                  </div>
                )}
              </div>
            </Card>

            {/* Account Selection */}
            {isConnected && (
              <Card>
                <div className="p-6">
                  <h2 className="text-lg font-bold mb-4">Account Selection</h2>
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="page-select" className="block text-sm text-gray-400 mb-2">Facebook Page</label>
                      <select
                        id="page-select"
                        value={selectedPageId}
                        onChange={(e) => setSelectedPageId(e.target.value)}
                        aria-label="Facebook Page"
                        className="w-full bg-brand-dark border border-white/10 px-3 py-2 text-white focus:outline-none focus:border-brand-lime"
                      >
                        <option value="">Select a page...</option>
                        {status?.pages?.map((page: FBPage) => (
                          <option key={page.id} value={page.id}>
                            {page.name} ({page.category || 'Page'})
                          </option>
                        ))}
                      </select>
                      {status?.pages?.length === 0 && (
                        <ErrorBanner message="No pages found. Create a Facebook Page first." variant="warning" className="mt-2" />
                      )}
                    </div>

                    <div>
                      <label htmlFor="ad-account-select" className="block text-sm text-gray-400 mb-2">Ad Account</label>
                      <select
                        id="ad-account-select"
                        value={selectedAdAccountId}
                        onChange={(e) => setSelectedAdAccountId(e.target.value)}
                        aria-label="Ad Account"
                        className="w-full bg-brand-dark border border-white/10 px-3 py-2 text-white focus:outline-none focus:border-brand-lime"
                      >
                        <option value="">Select an ad account...</option>
                        {status?.adAccounts?.map((account: FBAdAccount) => (
                          <option key={account.id} value={account.id}>
                            {account.name || account.id} ({account.currency})
                          </option>
                        ))}
                      </select>
                      {status?.adAccounts?.length === 0 && (
                        <ErrorBanner message="No ad accounts found. Create one in Meta Business Manager." variant="warning" className="mt-2" />
                      )}
                    </div>

                    {/* Payment */}
                    {selectedAdAccountId && (
                      <div className="flex items-center justify-between p-3 bg-brand-dark border border-white/5">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-400">Payment Method:</span>
                          {paymentLoading ? (
                            <Skeleton className="h-4 w-16" />
                          ) : paymentStatus?.has_payment_method ? (
                            <span className="flex items-center gap-1 text-status-success text-sm">
                              <CheckCircle className="w-4 h-4" /> Valid
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-status-error text-sm">
                              <XCircle className="w-4 h-4" /> Not Set
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <button onClick={checkPaymentStatus} disabled={paymentLoading} className="text-gray-400 hover:text-white transition-colors">
                            <RefreshCw className={`w-4 h-4 ${paymentLoading ? 'animate-spin' : ''}`} />
                          </button>
                          {paymentStatus?.add_payment_url && !paymentStatus.has_payment_method && (
                            <a href={paymentStatus.add_payment_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1">
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

            {/* Campaign Settings */}
            {isConnected && selectedPageId && selectedAdAccountId && (
              <Card>
                <div className="p-6">
                  <h2 className="text-lg font-bold mb-4">Campaign Settings</h2>
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="budget-input" className="block text-sm text-gray-400 mb-2">Daily Budget (USD)</label>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                        <input
                          id="budget-input"
                          type="number"
                          min={5}
                          value={budget}
                          onChange={(e) => setBudget(Math.max(5, Number(e.target.value)))}
                          aria-label="Daily budget in USD"
                          className="w-full bg-brand-dark border border-white/10 px-3 py-2 pl-7 text-white focus:outline-none focus:border-brand-lime"
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">Minimum $5/day</p>
                    </div>

                    <div>
                      <label htmlFor="duration-select" className="block text-sm text-gray-400 mb-2">Duration</label>
                      <select
                        id="duration-select"
                        value={durationDays}
                        onChange={(e) => setDurationDays(Number(e.target.value))}
                        aria-label="Campaign duration"
                        className="w-full bg-brand-dark border border-white/10 px-3 py-2 text-white focus:outline-none focus:border-brand-lime"
                      >
                        {DURATION_OPTIONS.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label htmlFor="cta-select" className="block text-sm text-gray-400 mb-2">Call to Action</label>
                      <select
                        id="cta-select"
                        value={callToAction}
                        onChange={(e) => setCallToAction(e.target.value)}
                        aria-label="Call to action button"
                        className="w-full bg-brand-dark border border-white/10 px-3 py-2 text-white focus:outline-none focus:border-brand-lime"
                      >
                        {CTA_OPTIONS.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </div>

                    {/* Multi-ad toggle */}
                    {hasMultipleAds && (
                      <div className="flex items-center justify-between p-3 bg-brand-dark border border-white/5">
                        <div className="flex items-center gap-2">
                          <Layers className="w-4 h-4 text-brand-lime" />
                          <div>
                            <span className="text-sm text-white">Publish all {allAds.length} ads</span>
                            <p className="text-xs text-gray-500">Meta will test both ads and optimize delivery</p>
                          </div>
                        </div>
                        <button
                          onClick={() => setPublishAllAds(!publishAllAds)}
                          className={`relative w-10 h-6 rounded-full transition-colors ${
                            publishAllAds ? 'bg-brand-lime' : 'bg-white/10'
                          }`}
                          aria-label="Publish all ads"
                        >
                          <span
                            className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
                              publishAllAds ? 'translate-x-5' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                    )}

                    {/* Estimated Total */}
                    <div className="p-4 bg-brand-lime/10 border border-brand-lime/30">
                      <div className="text-sm text-gray-400 mb-1">Estimated Total</div>
                      <motion.div
                        key={estimatedTotal}
                        initial={{ scale: 1.1 }}
                        animate={{ scale: 1 }}
                        className="text-2xl font-bold text-brand-lime"
                      >
                        ${estimatedTotal}
                      </motion.div>
                      <div className="text-xs text-gray-400 mt-1">${budget}/day x {durationDays} days</div>
                    </div>

                    <Button
                      variant="primary"
                      onClick={handlePublish}
                      loading={publishLoading}
                      disabled={!paymentStatus?.has_payment_method}
                      className="w-full py-3"
                    >
                      {publishAllAds && hasMultipleAds
                        ? `Publish ${allAds.length} Ads`
                        : 'Publish Campaign'
                      }
                    </Button>

                    {!paymentStatus?.has_payment_method && (
                      <ErrorBanner
                        message="Add a payment method to publish ads"
                        variant="warning"
                      />
                    )}

                    {publishError && (
                      <ErrorBanner
                        message={publishError}
                        onDismiss={() => setPublishError(null)}
                      />
                    )}

                    <p className="text-xs text-gray-500 text-center font-mono">
                      Campaign will be created in PAUSED status
                    </p>
                  </div>
                </div>
              </Card>
            )}
          </div>

          {/* Right Column (2/5) */}
          <div className="lg:col-span-2 space-y-6">
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
                        <span key={i} className="px-2 py-0.5 bg-brand-gray border border-white/10 text-xs text-gray-300">
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
