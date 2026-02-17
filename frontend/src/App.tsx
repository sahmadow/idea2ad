import { useState, useEffect, useRef, lazy, Suspense, type FormEvent, type ChangeEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { LandingView } from './components/LandingView';
import { DashboardView } from './components/DashboardView';
import { CampaignDetailView } from './components/CampaignDetailView';
import { AuthModal } from './components/AuthModal';
import { Terminal } from './components/ui/Terminal';
import { Button } from './components/ui/Button';
import { ConfirmDialog } from './components/ui/ConfirmDialog';
import { Skeleton } from './components/ui/Skeleton';
import { useAuth } from './hooks/useAuth';
import { useCampaigns } from './hooks/useCampaigns';
import { analyzeUrl, uploadProductImage, generateQuickAd, type CampaignDraft, type Ad, type BusinessType, type ToneOption, type QuickAdResponse } from './api';
import { assembleAdPack } from './api/adpack';
import { FBAuthTest } from './pages/FBAuthTest';
import type { PublishCampaignResponse } from './types/facebook';
import type { AdPack } from './types/adpack';

// Lazy-loaded views
const ResultsView = lazy(() => import('./components/ResultsView').then(m => ({ default: m.ResultsView })));
const AdPackView = lazy(() => import('./components/AdPackView').then(m => ({ default: m.AdPackView })));
const PublishView = lazy(() => import('./components/PublishView').then(m => ({ default: m.PublishView })));
const SuccessView = lazy(() => import('./components/SuccessView').then(m => ({ default: m.SuccessView })));

type View = 'landing' | 'loading' | 'results' | 'adpack' | 'publish' | 'success' | 'dashboard' | 'campaign-detail';
type GenerationMode = 'full' | 'quick';

const STORAGE_KEYS = {
  VIEW: 'idea2ad_view',
  RESULT: 'idea2ad_result',
  SELECTED_AD: 'idea2ad_selectedAd',
  URL: 'idea2ad_url',
  BUSINESS_TYPE: 'idea2ad_businessType',
  GENERATION_MODE: 'idea2ad_generationMode',
  AD_PACK: 'idea2ad_adPack',
};

const LOADING_STAGES = [
  'Analyzing',
  'Generating Copy',
  'Creating Images',
  'Building Ad Pack',
];

// Hash-based routing for test pages
function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const handleHashChange = () => setHash(window.location.hash);
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);
  return hash;
}

const pageTransition = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
  transition: { duration: 0.25 },
};

function ViewSkeleton() {
  return (
    <div className="min-h-screen bg-brand-dark flex items-center justify-center">
      <div className="space-y-4 w-full max-w-md px-6">
        <Skeleton className="h-8 w-48 mx-auto" />
        <Skeleton className="h-4 w-64 mx-auto" />
        <Skeleton className="h-64 w-full" />
      </div>
    </div>
  );
}

function App() {
  const hash = useHashRoute();

  // Auth
  const auth = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);

  // Campaigns
  const campaignsHook = useCampaigns();
  const [viewingCampaignId, setViewingCampaignId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // State (with localStorage persistence)
  const [url, setUrl] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEYS.URL) || ''; } catch { return ''; }
  });
  const [view, setView] = useState<View>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.VIEW) as View;
      if (stored === 'loading') return 'landing';
      // Don't restore dashboard/campaign-detail views from storage
      if (stored === 'dashboard' || stored === 'campaign-detail') return 'landing';
      return stored || 'landing';
    } catch { return 'landing'; }
  });
  const [result, setResult] = useState<CampaignDraft | null>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.RESULT);
      return stored ? JSON.parse(stored) : null;
    } catch { return null; }
  });
  const [selectedAd, setSelectedAd] = useState<Ad | null>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.SELECTED_AD);
      return stored ? JSON.parse(stored) : null;
    } catch { return null; }
  });
  const [adPack, setAdPack] = useState<AdPack | null>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.AD_PACK);
      return stored ? JSON.parse(stored) : null;
    } catch { return null; }
  });
  const [error, setError] = useState<string | null>(null);
  const [publishResult, setPublishResult] = useState<PublishCampaignResponse | null>(null);
  const [businessType, setBusinessType] = useState<BusinessType>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.BUSINESS_TYPE);
      return (stored === 'commerce' ? 'commerce' : 'saas') as BusinessType;
    } catch { return 'saas'; }
  });
  const [generationMode, setGenerationMode] = useState<GenerationMode>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.GENERATION_MODE);
      return (stored === 'quick' ? 'quick' : 'full') as GenerationMode;
    } catch { return 'full'; }
  });

  // Quick mode state
  const [quickIdea, setQuickIdea] = useState('');
  const [quickTone, setQuickTone] = useState<ToneOption>('professional');
  const [, setQuickResult] = useState<QuickAdResponse | null>(null);

  // Commerce state
  const [productDescription, setProductDescription] = useState('');
  const [productImageFile, setProductImageFile] = useState<File | null>(null);
  const [productImagePreview, setProductImagePreview] = useState<string | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Loading state
  const [loadingStage, setLoadingStage] = useState(0);

  // Confirm dialog
  const [confirmOpen, setConfirmOpen] = useState(false);

  // Persist to localStorage
  useEffect(() => { try { localStorage.setItem(STORAGE_KEYS.URL, url); } catch { /* */ } }, [url]);
  useEffect(() => {
    try {
      // Don't persist dashboard/campaign-detail views
      if (view !== 'loading' && view !== 'dashboard' && view !== 'campaign-detail') {
        localStorage.setItem(STORAGE_KEYS.VIEW, view);
      }
    } catch { /* */ }
  }, [view]);
  useEffect(() => {
    try {
      if (result) localStorage.setItem(STORAGE_KEYS.RESULT, JSON.stringify(result));
      else localStorage.removeItem(STORAGE_KEYS.RESULT);
    } catch { /* */ }
  }, [result]);
  useEffect(() => {
    try {
      if (selectedAd) localStorage.setItem(STORAGE_KEYS.SELECTED_AD, JSON.stringify(selectedAd));
      else localStorage.removeItem(STORAGE_KEYS.SELECTED_AD);
    } catch { /* */ }
  }, [selectedAd]);
  useEffect(() => {
    try {
      if (adPack) localStorage.setItem(STORAGE_KEYS.AD_PACK, JSON.stringify(adPack));
      else localStorage.removeItem(STORAGE_KEYS.AD_PACK);
    } catch { /* */ }
  }, [adPack]);
  useEffect(() => { try { localStorage.setItem(STORAGE_KEYS.BUSINESS_TYPE, businessType); } catch { /* */ } }, [businessType]);
  useEffect(() => { try { localStorage.setItem(STORAGE_KEYS.GENERATION_MODE, generationMode); } catch { /* */ } }, [generationMode]);

  // Loading stage progression
  useEffect(() => {
    if (view !== 'loading') return;
    setLoadingStage(0);
    const intervals = [3000, 6000, 9000];
    const ids = intervals.map((delay, i) =>
      setTimeout(() => setLoadingStage(i + 1), delay)
    );
    return () => ids.forEach(clearTimeout);
  }, [view]);

  // Image handling
  const handleImageSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setError('Please upload a JPEG, PNG, or WebP image');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('Image must be smaller than 10MB');
      return;
    }

    setProductImageFile(file);
    setProductImagePreview(URL.createObjectURL(file));
    setError(null);

    setIsUploading(true);
    try {
      const imageUrl = await uploadProductImage(file);
      setUploadedImageUrl(imageUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload image');
      setProductImageFile(null);
      setProductImagePreview(null);
    } finally {
      setIsUploading(false);
    }
  };

  const clearProductImage = () => {
    setProductImageFile(null);
    setProductImagePreview(null);
    setUploadedImageUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Route to test pages
  if (hash === '#/test/fb-auth') return <FBAuthTest />;

  const normalizeUrl = (input: string): string => {
    let normalized = input.trim();
    if (!normalized.match(/^https?:\/\//i)) {
      normalized = 'https://' + normalized;
      toast.info('URL normalized to https://');
    }
    return normalized;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (generationMode === 'quick') {
      if (!quickIdea.trim() || quickIdea.trim().length < 10) {
        setError('Please describe your idea (at least 10 characters)');
        return;
      }
      setView('loading');
      setError(null);
      setResult(null);
      setSelectedAd(null);
      setAdPack(null);
      setQuickResult(null);
      try {
        const data = await generateQuickAd(quickIdea.trim(), quickTone);
        setQuickResult(data);
        const ads: Ad[] = data.ads.map((a, i) => ({
          id: i + 1,
          imageUrl: a.imageUrl || undefined,
          primaryText: a.primaryText,
          headline: a.headline,
          description: a.description,
        }));
        const campaignDraft: CampaignDraft = {
          project_url: '',
          analysis: {
            summary: quickIdea,
            unique_selling_proposition: data.ads[0]?.headline || '',
            pain_points: [],
            call_to_action: data.ads[0]?.cta || 'Learn More',
            buyer_persona: {},
            keywords: [],
            styling_guide: {
              primary_colors: [], secondary_colors: [],
              font_families: [], design_style: '', mood: '',
            },
          },
          targeting: {
            age_min: 18, age_max: 65, genders: [],
            geo_locations: [], interests: [],
          },
          suggested_creatives: [],
          image_briefs: [],
          ads,
          status: 'ANALYZED',
        };
        setResult(campaignDraft);

        // Assemble AdPack from quick mode result
        try {
          const pack = await assembleAdPack(campaignDraft);
          setAdPack(pack);
          setView('adpack');
        } catch {
          // Fallback to results view if AdPack assembly fails
          setView('results');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Quick generation failed');
        setView('landing');
      }
      return;
    }

    // Full mode
    if (!url.trim()) return;
    setView('loading');
    setError(null);
    setResult(null);
    setSelectedAd(null);
    setAdPack(null);
    try {
      const normalizedUrl = normalizeUrl(url);
      const data = await analyzeUrl(normalizedUrl, undefined, {
        businessType,
        productDescription: businessType === 'commerce' ? productDescription || undefined : undefined,
        productImageUrl: businessType === 'commerce' ? uploadedImageUrl || undefined : undefined,
      });
      setResult(data);

      // Assemble AdPack from full mode result
      try {
        const pack = await assembleAdPack(data);
        setAdPack(pack);
        setView('adpack');
      } catch {
        // Fallback to results view if AdPack assembly fails
        setView('results');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      setView('landing');
    }
  };

  const handleBack = () => {
    if (result && (view === 'results' || view === 'adpack' || view === 'publish')) {
      setConfirmOpen(true);
      return;
    }
    resetToLanding();
  };

  const resetToLanding = () => {
    setView('landing');
    setResult(null);
    setSelectedAd(null);
    setAdPack(null);
    setPublishResult(null);
    setQuickResult(null);
    setProductDescription('');
    clearProductImage();
    try {
      localStorage.removeItem(STORAGE_KEYS.VIEW);
      localStorage.removeItem(STORAGE_KEYS.RESULT);
      localStorage.removeItem(STORAGE_KEYS.SELECTED_AD);
      localStorage.removeItem(STORAGE_KEYS.AD_PACK);
    } catch { /* */ }
  };

  const handleCancelLoading = () => {
    setView('landing');
  };

  // Dashboard navigation
  const handleDashboardClick = () => {
    if (!auth.isAuthenticated) {
      setAuthModalOpen(true);
      return;
    }
    setView('dashboard');
  };

  const handleViewCampaign = (id: string) => {
    setViewingCampaignId(id);
    setView('campaign-detail');
  };

  const handleSignInClick = () => {
    setAuthModalOpen(true);
  };

  const handleLogout = async () => {
    await auth.logout();
    if (view === 'dashboard' || view === 'campaign-detail') {
      setView('landing');
    }
    toast.success('Signed out');
  };

  // Save campaign
  const handleSaveCampaign = async () => {
    if (!auth.isAuthenticated || !result) {
      if (!auth.isAuthenticated) {
        setAuthModalOpen(true);
      }
      return;
    }

    setIsSaving(true);
    try {
      const campaignName = result.project_url
        ? new URL(result.project_url).hostname.replace('www.', '')
        : `Campaign ${new Date().toLocaleDateString()}`;

      await campaignsHook.saveCampaign(campaignName, result);
      toast.success('Campaign saved to your dashboard');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save campaign');
    } finally {
      setIsSaving(false);
    }
  };

  // Render current view
  const renderView = () => {
    // Dashboard view
    if (view === 'dashboard') {
      return (
        <motion.div key="dashboard" {...pageTransition}>
          <DashboardView
            campaigns={campaignsHook.campaigns}
            isLoading={campaignsHook.isLoading}
            error={campaignsHook.error}
            userName={auth.user?.name || auth.user?.email || null}
            onFetchCampaigns={campaignsHook.fetchCampaigns}
            onViewCampaign={handleViewCampaign}
            onDeleteCampaign={campaignsHook.removeCampaign}
            onNewCampaign={resetToLanding}
            onLogoClick={resetToLanding}
            onDashboardClick={handleDashboardClick}
            onLogout={handleLogout}
            onDismissError={campaignsHook.clearError}
          />
        </motion.div>
      );
    }

    // Campaign detail view
    if (view === 'campaign-detail' && viewingCampaignId) {
      return (
        <motion.div key="campaign-detail" {...pageTransition}>
          <CampaignDetailView
            campaign={campaignsHook.selectedCampaign}
            isLoading={campaignsHook.isLoading}
            error={campaignsHook.error}
            campaignId={viewingCampaignId}
            userName={auth.user?.name || auth.user?.email || null}
            onFetchCampaign={campaignsHook.fetchCampaign}
            onBack={() => setView('dashboard')}
            onLogoClick={resetToLanding}
            onDashboardClick={handleDashboardClick}
            onLogout={handleLogout}
            onDismissError={campaignsHook.clearError}
          />
        </motion.div>
      );
    }

    if (view === 'loading') {
      return (
        <motion.div key="loading" {...pageTransition}>
          <div className="min-h-screen bg-brand-dark text-white flex flex-col items-center justify-center px-6">
            <div className="text-center space-y-8 max-w-md w-full">
              <div className="w-16 h-16 border-2 border-brand-lime/30 border-t-brand-lime rounded-full animate-spin mx-auto" />
              <div>
                <h2 className="text-2xl font-display font-bold mb-2">
                  {generationMode === 'quick' ? 'Generating Your Ad' : 'Analyzing Your Page'}
                </h2>
                <p className="text-gray-400 font-mono text-sm truncate">
                  {generationMode === 'quick' ? quickIdea.slice(0, 80) + (quickIdea.length > 80 ? '...' : '') : url}
                </p>
              </div>

              {/* Stage indicator */}
              <div className="flex justify-center gap-3">
                {LOADING_STAGES.map((stage, i) => (
                  <div key={stage} className="flex items-center gap-2">
                    <div className={`w-2 h-2 ${i <= loadingStage ? 'bg-brand-lime' : 'bg-white/20'} transition-colors`} />
                    <span className={`text-xs font-mono ${i <= loadingStage ? 'text-white' : 'text-gray-600'} hidden sm:inline transition-colors`}>
                      {stage}
                    </span>
                  </div>
                ))}
              </div>

              <Terminal />

              <Button variant="ghost" size="sm" onClick={handleCancelLoading}>
                Cancel
              </Button>
            </div>
          </div>
        </motion.div>
      );
    }

    if (view === 'adpack' && adPack) {
      return (
        <motion.div key="adpack" {...pageTransition}>
          <Suspense fallback={<ViewSkeleton />}>
            <AdPackView
              adPack={adPack}
              onAdPackChange={setAdPack}
              onBack={handleBack}
              onPublish={(ad) => {
                setSelectedAd(ad);
                setView('publish');
              }}
            />
          </Suspense>
        </motion.div>
      );
    }

    if (view === 'results' && result) {
      return (
        <motion.div key="results" {...pageTransition}>
          <Suspense fallback={<ViewSkeleton />}>
            <ResultsView
              result={result}
              selectedAd={selectedAd}
              onSelectAd={setSelectedAd}
              onBack={handleBack}
              onNext={() => selectedAd && setView('publish')}
              onRegenerate={() => handleSubmit(new Event('submit') as unknown as FormEvent)}
              onSave={handleSaveCampaign}
              isSaving={isSaving}
              isAuthenticated={auth.isAuthenticated}
            />
          </Suspense>
        </motion.div>
      );
    }

    if (view === 'publish' && result && selectedAd) {
      return (
        <motion.div key="publish" {...pageTransition}>
          <Suspense fallback={<ViewSkeleton />}>
            <PublishView
              campaignData={result}
              selectedAd={selectedAd}
              onBack={() => setView(adPack ? 'adpack' : 'results')}
              onSuccess={(res) => {
                setPublishResult(res);
                setView('success');
              }}
            />
          </Suspense>
        </motion.div>
      );
    }

    if (view === 'success' && publishResult) {
      return (
        <motion.div key="success" {...pageTransition}>
          <Suspense fallback={<ViewSkeleton />}>
            <SuccessView
              result={publishResult}
              onNewCampaign={() => {
                setUrl('');
                resetToLanding();
                try {
                  Object.values(STORAGE_KEYS).forEach(key => localStorage.removeItem(key));
                } catch { /* */ }
              }}
            />
          </Suspense>
        </motion.div>
      );
    }

    // Landing
    return (
      <motion.div key="landing" {...pageTransition}>
        <LandingView
          url={url}
          onUrlChange={setUrl}
          quickIdea={quickIdea}
          onQuickIdeaChange={setQuickIdea}
          quickTone={quickTone}
          onQuickToneChange={setQuickTone}
          generationMode={generationMode}
          onGenerationModeChange={setGenerationMode}
          businessType={businessType}
          onBusinessTypeChange={setBusinessType}
          productDescription={productDescription}
          onProductDescriptionChange={setProductDescription}
          productImagePreview={productImagePreview}
          productImageFileName={productImageFile?.name || null}
          isUploading={isUploading}
          uploadedImageUrl={uploadedImageUrl}
          onImageSelect={handleImageSelect}
          onClearImage={clearProductImage}
          onSubmit={handleSubmit}
          error={error}
          onDismissError={() => setError(null)}
          userName={auth.user?.name || auth.user?.email || null}
          onSignInClick={handleSignInClick}
          onDashboardClick={handleDashboardClick}
          onLogout={handleLogout}
        />
      </motion.div>
    );
  };

  return (
    <main>
      <AnimatePresence mode="wait">
        {renderView()}
      </AnimatePresence>

      <ConfirmDialog
        open={confirmOpen}
        title="Discard results?"
        message="You'll lose the generated campaign. This can't be undone."
        confirmLabel="Discard"
        cancelLabel="Keep"
        onConfirm={() => {
          setConfirmOpen(false);
          resetToLanding();
        }}
        onCancel={() => setConfirmOpen(false)}
      />

      <AuthModal
        open={authModalOpen}
        onClose={() => {
          setAuthModalOpen(false);
          auth.clearError();
        }}
        onLogin={auth.login}
        onRegister={auth.register}
        error={auth.error}
        isLoading={auth.isLoading}
      />
    </main>
  );
}

export default App;
