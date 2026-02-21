/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  type ReactNode,
  type FormEvent,
  type ChangeEvent,
} from 'react';
import { toast } from 'sonner';
import { useAuth } from '../hooks/useAuth';
import { useCampaigns } from '../hooks/useCampaigns';
import { uploadProductImage, analyzeCompetitors, type CampaignDraft, type Ad, type BusinessType, type CompetitorIntelligence } from '../api';
import { analyzeV2, quickGenerateV2 } from '../api/adpack';
import type { PublishCampaignResponse } from '../types/facebook';
import type { AdPack } from '../types/adpack';

type GenerationMode = 'full' | 'quick';

// --- localStorage TTL helpers ---
const STORAGE_KEYS = {
  RESULT: 'idea2ad_result',
  SELECTED_AD: 'idea2ad_selectedAd',
  URL: 'idea2ad_url',
  BUSINESS_TYPE: 'idea2ad_businessType',
  GENERATION_MODE: 'idea2ad_generationMode',
  AD_PACK: 'idea2ad_adPack',
};

const SESSION_TTL_MS = 4 * 60 * 60 * 1000; // 4 hours

function setWithTTL(key: string, value: string): void {
  localStorage.setItem(key, JSON.stringify({ value, ts: Date.now() }));
}

function getWithTTL(key: string, ttlMs: number): string | null {
  const raw = localStorage.getItem(key);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed.ts) return raw; // legacy format
    if (Date.now() - parsed.ts > ttlMs) {
      localStorage.removeItem(key);
      return null;
    }
    return parsed.value;
  } catch {
    return raw;
  }
}

// --- Context shape ---
interface AppContextValue {
  // Auth
  auth: ReturnType<typeof useAuth>;
  authModalOpen: boolean;
  setAuthModalOpen: (open: boolean) => void;
  handleSignInClick: () => void;
  handleLogout: () => Promise<void>;

  // Campaigns
  campaignsHook: ReturnType<typeof useCampaigns>;
  isSaving: boolean;
  handleSaveCampaign: () => Promise<void>;

  // Form state
  url: string;
  setUrl: (url: string) => void;
  quickIdea: string;
  setQuickIdea: (idea: string) => void;
  generationMode: GenerationMode;
  setGenerationMode: (mode: GenerationMode) => void;
  businessType: BusinessType;
  setBusinessType: (type: BusinessType) => void;
  editPrompt: string;
  setEditPrompt: (prompt: string) => void;
  productDescription: string;
  setProductDescription: (desc: string) => void;

  // Image handling
  productImageFile: File | null;
  productImagePreview: string | null;
  uploadedImageUrl: string | null;
  isUploading: boolean;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  handleImageSelect: (e: ChangeEvent<HTMLInputElement>) => void;
  clearProductImage: () => void;

  // Competitor state
  competitors: string[];
  setCompetitors: (c: string[]) => void;
  competitorData: CompetitorIntelligence | null;

  // Session data
  result: CampaignDraft | null;
  setResult: (r: CampaignDraft | null) => void;
  selectedAd: Ad | null;
  setSelectedAd: (ad: Ad | null) => void;
  adPack: AdPack | null;
  setAdPack: (pack: AdPack | null) => void;
  publishResult: PublishCampaignResponse | null;
  setPublishResult: (r: PublishCampaignResponse | null) => void;
  error: string | null;
  setError: (e: string | null) => void;

  // Loading
  isGenerating: boolean;
  loadingStage: number;

  // Generation
  startGeneration: (e: FormEvent) => Promise<void>;
  cancelGeneration: () => void;
  resetSession: () => void;

  // Confirm dialog
  confirmOpen: boolean;
  setConfirmOpen: (open: boolean) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useAppContext must be used within AppProvider');
  return ctx;
}

export function AppProvider({ children }: { children: ReactNode }) {
  // Auth
  const auth = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);

  // Campaigns
  const campaignsHook = useCampaigns();
  const [isSaving, setIsSaving] = useState(false);

  // Form state (persisted without TTL)
  const [url, setUrl] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEYS.URL) || ''; } catch { return ''; }
  });
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

  // Session data (persisted with TTL)
  const [result, setResult] = useState<CampaignDraft | null>(() => {
    try {
      const stored = getWithTTL(STORAGE_KEYS.RESULT, SESSION_TTL_MS);
      return stored ? JSON.parse(stored) : null;
    } catch { return null; }
  });
  const [selectedAd, setSelectedAd] = useState<Ad | null>(() => {
    try {
      const stored = getWithTTL(STORAGE_KEYS.SELECTED_AD, SESSION_TTL_MS);
      return stored ? JSON.parse(stored) : null;
    } catch { return null; }
  });
  const [adPack, setAdPack] = useState<AdPack | null>(() => {
    try {
      const stored = getWithTTL(STORAGE_KEYS.AD_PACK, SESSION_TTL_MS);
      return stored ? JSON.parse(stored) : null;
    } catch { return null; }
  });

  const [publishResult, setPublishResult] = useState<PublishCampaignResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Quick mode state
  const [quickIdea, setQuickIdea] = useState('');
  const [editPrompt, setEditPrompt] = useState('');
  const [productDescription, setProductDescription] = useState('');

  // Commerce / image state
  const [productImageFile, setProductImageFile] = useState<File | null>(null);
  const [productImagePreview, setProductImagePreview] = useState<string | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Competitor state
  const [competitors, setCompetitors] = useState<string[]>([]);
  const [competitorData, setCompetitorData] = useState<CompetitorIntelligence | null>(null);

  // Loading state
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);

  // Confirm dialog
  const [confirmOpen, setConfirmOpen] = useState(false);

  // --- Persist to localStorage ---
  useEffect(() => { try { localStorage.setItem(STORAGE_KEYS.URL, url); } catch { /* */ } }, [url]);
  useEffect(() => {
    try {
      if (result) setWithTTL(STORAGE_KEYS.RESULT, JSON.stringify(result));
      else localStorage.removeItem(STORAGE_KEYS.RESULT);
    } catch { /* */ }
  }, [result]);
  useEffect(() => {
    try {
      if (selectedAd) setWithTTL(STORAGE_KEYS.SELECTED_AD, JSON.stringify(selectedAd));
      else localStorage.removeItem(STORAGE_KEYS.SELECTED_AD);
    } catch { /* */ }
  }, [selectedAd]);
  useEffect(() => {
    try {
      if (adPack) setWithTTL(STORAGE_KEYS.AD_PACK, JSON.stringify(adPack));
      else localStorage.removeItem(STORAGE_KEYS.AD_PACK);
    } catch { /* */ }
  }, [adPack]);
  useEffect(() => { try { localStorage.setItem(STORAGE_KEYS.BUSINESS_TYPE, businessType); } catch { /* */ } }, [businessType]);
  useEffect(() => { try { localStorage.setItem(STORAGE_KEYS.GENERATION_MODE, generationMode); } catch { /* */ } }, [generationMode]);

  // Loading stage progression
  useEffect(() => {
    if (!isGenerating) return;
    setLoadingStage(0);
    const intervals = [3000, 6000, 9000];
    const ids = intervals.map((delay, i) =>
      setTimeout(() => setLoadingStage(i + 1), delay)
    );
    return () => ids.forEach(clearTimeout);
  }, [isGenerating]);

  // --- Image handling ---
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

  // --- URL normalizer ---
  const normalizeUrl = (input: string): string => {
    let normalized = input.trim();
    if (!normalized.match(/^https?:\/\//i)) {
      normalized = 'https://' + normalized;
      toast.info('URL normalized to https://');
    }
    return normalized;
  };

  // --- Generation (returns true on success for navigation) ---
  const startGeneration = async (e: FormEvent) => {
    e.preventDefault();

    if (generationMode === 'quick') {
      const hasDescription = quickIdea.trim().length > 0;
      const hasImage = !!uploadedImageUrl;
      if (!hasDescription && !hasImage) {
        setError('Provide a description and/or upload an image');
        return;
      }

      setIsGenerating(true);
      setError(null);
      setResult(null);
      setSelectedAd(null);
      setAdPack(null);

      try {
        const pack = await quickGenerateV2({
          description: hasDescription ? quickIdea.trim() : undefined,
          image_url: hasImage ? uploadedImageUrl! : undefined,
          edit_prompt: editPrompt.trim() || undefined,
        });

        setAdPack(pack);
        setIsGenerating(false);
        // Caller (LandingPage) handles navigation
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Quick generation failed');
        setIsGenerating(false);
      }
      return;
    }

    // Full mode
    if (!url.trim()) return;
    setIsGenerating(true);
    setError(null);
    setResult(null);
    setSelectedAd(null);
    setCompetitorData(null);
    setAdPack(null);
    try {
      const normalizedUrl = normalizeUrl(url);

      const v2Promise = analyzeV2(normalizedUrl, undefined, {
        image_url: uploadedImageUrl || undefined,
        edit_prompt: editPrompt.trim() || undefined,
      });

      const competitorPromise = competitors.length > 0
        ? analyzeCompetitors(competitors, normalizedUrl).catch((err) => {
            console.warn('Competitor analysis failed:', err);
            toast.error('Competitor analysis failed - showing results without competitor intel');
            return null;
          })
        : Promise.resolve(null);

      const [pack, compData] = await Promise.all([v2Promise, competitorPromise]);

      setCompetitorData(compData);
      setAdPack(pack);
      setIsGenerating(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      setIsGenerating(false);
    }
  };

  const cancelGeneration = () => {
    setIsGenerating(false);
  };

  const resetSession = () => {
    setResult(null);
    setSelectedAd(null);
    setAdPack(null);
    setPublishResult(null);
    setCompetitorData(null);
    setCompetitors([]);
    setProductDescription('');
    setEditPrompt('');
    clearProductImage();
    try {
      localStorage.removeItem(STORAGE_KEYS.RESULT);
      localStorage.removeItem(STORAGE_KEYS.SELECTED_AD);
      localStorage.removeItem(STORAGE_KEYS.AD_PACK);
    } catch { /* */ }
  };

  // --- Auth helpers ---
  const handleSignInClick = () => {
    setAuthModalOpen(true);
  };

  const handleLogout = async () => {
    await auth.logout();
    toast.success('Signed out');
  };

  // --- Save campaign ---
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

  const value: AppContextValue = {
    auth,
    authModalOpen,
    setAuthModalOpen,
    handleSignInClick,
    handleLogout,

    campaignsHook,
    isSaving,
    handleSaveCampaign,

    url, setUrl,
    quickIdea, setQuickIdea,
    generationMode, setGenerationMode,
    businessType, setBusinessType,
    editPrompt, setEditPrompt,
    productDescription, setProductDescription,

    productImageFile,
    productImagePreview,
    uploadedImageUrl,
    isUploading,
    fileInputRef,
    handleImageSelect,
    clearProductImage,

    competitors, setCompetitors,
    competitorData,

    result, setResult,
    selectedAd, setSelectedAd,
    adPack, setAdPack,
    publishResult, setPublishResult,
    error, setError,

    isGenerating,
    loadingStage,

    startGeneration,
    cancelGeneration,
    resetSession,

    confirmOpen, setConfirmOpen,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
