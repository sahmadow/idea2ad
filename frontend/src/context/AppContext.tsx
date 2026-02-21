/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  type ReactNode,
  type ChangeEvent,
} from 'react';
import { toast } from 'sonner';
import { useAuth } from '../hooks/useAuth';
import { useCampaigns } from '../hooks/useCampaigns';
import { uploadProductImage, type CampaignDraft, type Ad, type CompetitorIntelligence } from '../api';
import { prepareCampaign, generateFromPrepared } from '../api/adpack';
import type { PublishCampaignResponse } from '../types/facebook';
import type { AdPack, PreparedCampaign } from '../types/adpack';

// --- localStorage TTL helpers ---
const STORAGE_KEYS = {
  RESULT: 'idea2ad_result',
  SELECTED_AD: 'idea2ad_selectedAd',
  INPUT: 'idea2ad_input',
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

  // Unified input
  input: string;
  setInput: (val: string) => void;
  isInputUrl: boolean;

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

  // Prepared campaign (from /v2/prepare)
  preparedCampaign: PreparedCampaign | null;
  setPreparedCampaign: (pc: PreparedCampaign | null) => void;

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
  isAnalyzing: boolean;
  isGenerating: boolean;
  loadingStage: number;

  // Actions
  startAnalysis: () => Promise<void>;
  startGeneration: (overrides: {
    language: string;
    product_summary?: string;
    target_audience?: string;
    main_pain_point?: string;
    messaging_unaware?: string;
    messaging_aware?: string;
    competitors?: { name: string; weakness: string }[];
  }) => Promise<void>;
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

/** Detect if input looks like a URL */
function looksLikeUrl(s: string): boolean {
  const t = s.trim();
  if (t.match(/^https?:\/\//i)) return true;
  // Has a dot followed by TLD-like chars + optional path
  if (t.match(/^[a-z0-9-]+\.[a-z]{2,}/i)) return true;
  return false;
}

export function AppProvider({ children }: { children: ReactNode }) {
  // Auth
  const auth = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);

  // Campaigns
  const campaignsHook = useCampaigns();
  const [isSaving, setIsSaving] = useState(false);

  // Unified input (persisted without TTL)
  const [input, setInput] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEYS.INPUT) || ''; } catch { return ''; }
  });

  const isInputUrl = looksLikeUrl(input);

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

  // Prepared campaign (in-memory only, no localStorage)
  const [preparedCampaign, setPreparedCampaign] = useState<PreparedCampaign | null>(null);

  // Image state
  const [productImageFile, setProductImageFile] = useState<File | null>(null);
  const [productImagePreview, setProductImagePreview] = useState<string | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Competitor state
  const [competitors, setCompetitors] = useState<string[]>([]);
  const [competitorData, setCompetitorData] = useState<CompetitorIntelligence | null>(null);

  // Loading state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);

  // Confirm dialog
  const [confirmOpen, setConfirmOpen] = useState(false);

  // --- Persist to localStorage ---
  useEffect(() => { try { localStorage.setItem(STORAGE_KEYS.INPUT, input); } catch { /* */ } }, [input]);
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

  // Loading stage progression (for generation phase)
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
  const normalizeUrl = (val: string): string => {
    let normalized = val.trim();
    if (!normalized.match(/^https?:\/\//i)) {
      normalized = 'https://' + normalized;
    }
    return normalized;
  };

  // --- Step 1: Analyze (prepare) ---
  const startAnalysis = async () => {
    if (!input.trim()) return;

    setIsAnalyzing(true);
    setError(null);
    setPreparedCampaign(null);

    try {
      const isUrl = looksLikeUrl(input);
      const prepared = await prepareCampaign({
        url: isUrl ? normalizeUrl(input) : undefined,
        description: isUrl ? undefined : input.trim(),
        image_url: uploadedImageUrl || undefined,
      });

      setPreparedCampaign(prepared);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // --- Step 2: Generate creatives ---
  const startGeneration = async (overrides: {
    language: string;
    product_summary?: string;
    target_audience?: string;
    main_pain_point?: string;
    messaging_unaware?: string;
    messaging_aware?: string;
    competitors?: { name: string; weakness: string }[];
  }) => {
    if (!preparedCampaign) return;

    setIsGenerating(true);
    setError(null);
    setResult(null);
    setSelectedAd(null);
    setAdPack(null);

    try {
      const pack = await generateFromPrepared({
        session_id: preparedCampaign.session_id,
        language: overrides.language,
        product_summary: overrides.product_summary,
        target_audience: overrides.target_audience,
        main_pain_point: overrides.main_pain_point,
        messaging_unaware: overrides.messaging_unaware,
        messaging_aware: overrides.messaging_aware,
        competitors: overrides.competitors,
      });

      setAdPack(pack);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setIsGenerating(false);
    }
  };

  const cancelGeneration = () => {
    setIsGenerating(false);
    setIsAnalyzing(false);
  };

  const resetSession = () => {
    setResult(null);
    setSelectedAd(null);
    setAdPack(null);
    setPublishResult(null);
    setCompetitorData(null);
    setCompetitors([]);
    setPreparedCampaign(null);
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

    input, setInput,
    isInputUrl,

    productImageFile,
    productImagePreview,
    uploadedImageUrl,
    isUploading,
    fileInputRef,
    handleImageSelect,
    clearProductImage,

    competitors, setCompetitors,
    competitorData,

    preparedCampaign, setPreparedCampaign,

    result, setResult,
    selectedAd, setSelectedAd,
    adPack, setAdPack,
    publishResult, setPublishResult,
    error, setError,

    isAnalyzing,
    isGenerating,
    loadingStage,

    startAnalysis,
    startGeneration,
    cancelGeneration,
    resetSession,

    confirmOpen, setConfirmOpen,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
