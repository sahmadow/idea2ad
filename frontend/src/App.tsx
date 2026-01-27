import { useState, useEffect, useRef, type FormEvent, type ChangeEvent } from 'react';
import { ArrowRight, Check, Sparkles, Target, Zap, Layout, Upload, X } from 'lucide-react';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { Button } from './components/ui/Button';
import { Card } from './components/ui/Card';
import { Terminal } from './components/ui/Terminal';
import { AdPreview } from './components/ui/AdPreview';
import { ResultsView } from './components/ResultsView';
import { PublishView } from './components/PublishView';
import { SuccessView } from './components/SuccessView';
import { analyzeUrl, uploadProductImage, generateQuickAd, type CampaignDraft, type Ad, type BusinessType, type ToneOption, type QuickAdResponse } from './api';
import { FBAuthTest } from './pages/FBAuthTest';
import type { PublishCampaignResponse } from './types/facebook';

type View = 'landing' | 'loading' | 'results' | 'publish' | 'success';
type GenerationMode = 'full' | 'quick';

// LocalStorage keys for state persistence
const STORAGE_KEYS = {
  VIEW: 'idea2ad_view',
  RESULT: 'idea2ad_result',
  SELECTED_AD: 'idea2ad_selectedAd',
  URL: 'idea2ad_url',
  BUSINESS_TYPE: 'idea2ad_businessType',
  GENERATION_MODE: 'idea2ad_generationMode',
};

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

function App() {
  const hash = useHashRoute();

  // Initialize state from localStorage for persistence across refreshes
  const [url, setUrl] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEYS.URL) || '';
    } catch {
      return '';
    }
  });
  const [view, setView] = useState<View>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.VIEW) as View;
      // Don't restore 'loading' view - start at landing or results
      if (stored === 'loading') return 'landing';
      return stored || 'landing';
    } catch {
      return 'landing';
    }
  });
  const [result, setResult] = useState<CampaignDraft | null>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.RESULT);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [selectedAd, setSelectedAd] = useState<Ad | null>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.SELECTED_AD);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [error, setError] = useState<string | null>(null);
  const [publishResult, setPublishResult] = useState<PublishCampaignResponse | null>(null);

  // Business type state
  const [businessType, setBusinessType] = useState<BusinessType>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.BUSINESS_TYPE);
      return (stored === 'commerce' ? 'commerce' : 'saas') as BusinessType;
    } catch {
      return 'saas';
    }
  });

  // Generation mode state
  const [generationMode, setGenerationMode] = useState<GenerationMode>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.GENERATION_MODE);
      return (stored === 'quick' ? 'quick' : 'full') as GenerationMode;
    } catch {
      return 'full';
    }
  });

  // Quick mode state
  const [quickIdea, setQuickIdea] = useState('');
  const [quickTone, setQuickTone] = useState<ToneOption>('professional');
  const [quickResult, setQuickResult] = useState<QuickAdResponse | null>(null);

  // Commerce-specific product state
  const [productDescription, setProductDescription] = useState('');
  const [productImageFile, setProductImageFile] = useState<File | null>(null);
  const [productImagePreview, setProductImagePreview] = useState<string | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Persist state to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.URL, url);
    } catch { /* ignore */ }
  }, [url]);

  useEffect(() => {
    try {
      // Don't persist 'loading' state
      if (view !== 'loading') {
        localStorage.setItem(STORAGE_KEYS.VIEW, view);
      }
    } catch { /* ignore */ }
  }, [view]);

  useEffect(() => {
    try {
      if (result) {
        localStorage.setItem(STORAGE_KEYS.RESULT, JSON.stringify(result));
      } else {
        localStorage.removeItem(STORAGE_KEYS.RESULT);
      }
    } catch { /* ignore */ }
  }, [result]);

  useEffect(() => {
    try {
      if (selectedAd) {
        localStorage.setItem(STORAGE_KEYS.SELECTED_AD, JSON.stringify(selectedAd));
      } else {
        localStorage.removeItem(STORAGE_KEYS.SELECTED_AD);
      }
    } catch { /* ignore */ }
  }, [selectedAd]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.BUSINESS_TYPE, businessType);
    } catch { /* ignore */ }
  }, [businessType]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.GENERATION_MODE, generationMode);
    } catch { /* ignore */ }
  }, [generationMode]);

  // Handle product image selection
  const handleImageSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setError('Please upload a JPEG, PNG, or WebP image');
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setError('Image must be smaller than 10MB');
      return;
    }

    setProductImageFile(file);
    setProductImagePreview(URL.createObjectURL(file));
    setError(null);

    // Upload immediately
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
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Route to test pages
  if (hash === '#/test/fb-auth') {
    return <FBAuthTest />;
  }

  const normalizeUrl = (input: string): string => {
    let normalized = input.trim();
    if (!normalized.match(/^https?:\/\//i)) {
      normalized = 'https://' + normalized;
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
      setQuickResult(null);

      try {
        const data = await generateQuickAd(quickIdea.trim(), quickTone);
        setQuickResult(data);
        // Convert to CampaignDraft shape for ResultsView compatibility
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
        setView('results');
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

    try {
      const normalizedUrl = normalizeUrl(url);
      const data = await analyzeUrl(normalizedUrl, undefined, {
        businessType,
        productDescription: businessType === 'commerce' ? productDescription || undefined : undefined,
        productImageUrl: businessType === 'commerce' ? uploadedImageUrl || undefined : undefined,
      });
      setResult(data);
      setView('results');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      setView('landing');
    }
  };

  const handleBack = () => {
    setView('landing');
    setResult(null);
    setSelectedAd(null);
    setPublishResult(null);
    setQuickResult(null);
    // Clear product state
    setProductDescription('');
    clearProductImage();
    // Clear persisted state
    try {
      localStorage.removeItem(STORAGE_KEYS.VIEW);
      localStorage.removeItem(STORAGE_KEYS.RESULT);
      localStorage.removeItem(STORAGE_KEYS.SELECTED_AD);
    } catch { /* ignore */ }
  };

  // Loading View
  if (view === 'loading') {
    return (
      <div className="min-h-screen bg-brand-dark text-white flex flex-col items-center justify-center">
        <div className="text-center space-y-8">
          <div className="w-16 h-16 border-2 border-brand-lime/30 border-t-brand-lime rounded-full animate-spin mx-auto" />
          <div>
            <h2 className="text-2xl font-display font-bold mb-2">
              {generationMode === 'quick' ? 'Generating Your Ad' : 'Analyzing Your Page'}
            </h2>
            <p className="text-gray-400 font-mono text-sm">
              {generationMode === 'quick' ? quickIdea.slice(0, 80) + (quickIdea.length > 80 ? '...' : '') : url}
            </p>
          </div>
          <div className="max-w-md mx-auto">
            <Terminal />
          </div>
        </div>
      </div>
    );
  }

  // Results View
  if (view === 'results' && result) {
    return (
      <ResultsView
        result={result}
        selectedAd={selectedAd}
        onSelectAd={setSelectedAd}
        onBack={handleBack}
        onNext={() => selectedAd && setView('publish')}
      />
    );
  }

  // Publish View
  if (view === 'publish' && result && selectedAd) {
    return (
      <PublishView
        campaignData={result}
        selectedAd={selectedAd}
        onBack={() => setView('results')}
        onSuccess={(res) => {
          setPublishResult(res);
          setView('success');
        }}
      />
    );
  }

  // Success View
  if (view === 'success' && publishResult) {
    return (
      <SuccessView
        result={publishResult}
        onNewCampaign={() => {
          setUrl('');
          setView('landing');
          setResult(null);
          setSelectedAd(null);
          setPublishResult(null);
          // Clear persisted state
          try {
            Object.values(STORAGE_KEYS).forEach(key => localStorage.removeItem(key));
          } catch { /* ignore */ }
        }}
      />
    );
  }

  // Landing View
  return (
    <div className="min-h-screen bg-brand-dark text-white selection:bg-brand-lime selection:text-brand-dark">
      <Navbar />

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        {/* Background Grid */}
        <div className="absolute inset-0 bg-grid-pattern opacity-[0.03] pointer-events-none" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-brand-lime/5 blur-[120px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6 relative">

          {/* TOP: Centered Headline & Input (First View) */}
          <div className="max-w-3xl mx-auto text-center space-y-8 mb-24 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-gray border border-white/10 text-xs font-mono text-brand-lime uppercase tracking-wider">
              <span className="w-2 h-2 bg-brand-lime animate-pulse" />
              AI-Powered Ad Generation
            </div>

            <h1 className="text-5xl lg:text-7xl font-display font-bold leading-[0.9] text-white">
              SAY GOODBYE TO <span className="text-brand-lime">MANUAL</span> AD CREATION
            </h1>

            <p className="text-xl text-gray-400 max-w-xl mx-auto leading-relaxed">
              Turn any landing page into a <span className="text-white font-medium">Meta Ads campaign</span> in 60 seconds.
            </p>

            {/* Generation Mode Toggle */}
            <div className="flex justify-center gap-2 mb-2">
              <button
                type="button"
                onClick={() => setGenerationMode('full')}
                className={`px-6 py-2 text-sm font-mono transition-all border ${
                  generationMode === 'full'
                    ? 'bg-brand-lime text-brand-dark border-brand-lime'
                    : 'bg-transparent text-gray-400 border-white/20 hover:border-white/40'
                }`}
              >
                Full Mode
              </button>
              <button
                type="button"
                onClick={() => setGenerationMode('quick')}
                className={`px-6 py-2 text-sm font-mono transition-all border ${
                  generationMode === 'quick'
                    ? 'bg-brand-lime text-brand-dark border-brand-lime'
                    : 'bg-transparent text-gray-400 border-white/20 hover:border-white/40'
                }`}
              >
                Quick Mode
              </button>
            </div>
            <p className="text-xs text-gray-500 font-mono">
              {generationMode === 'quick'
                ? 'Describe your idea, get an ad instantly'
                : 'Analyze a landing page for brand-matched creatives'}
            </p>

            {/* Quick Mode Form */}
            {generationMode === 'quick' ? (
              <form onSubmit={handleSubmit} className="flex flex-col gap-4 max-w-lg mx-auto">
                <textarea
                  value={quickIdea}
                  onChange={(e) => setQuickIdea(e.target.value)}
                  placeholder="Describe your business or product idea..."
                  rows={3}
                  className="w-full bg-brand-gray border border-white/10 px-6 py-4 text-white focus:outline-none focus:border-brand-lime font-mono text-sm placeholder:text-gray-600 transition-colors resize-none"
                />
                <div className="flex gap-4">
                  <select
                    value={quickTone}
                    onChange={(e) => setQuickTone(e.target.value as ToneOption)}
                    className="flex-1 h-14 bg-brand-gray border border-white/10 px-4 text-white focus:outline-none focus:border-brand-lime font-mono text-sm transition-colors appearance-none cursor-pointer"
                  >
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="playful">Playful</option>
                    <option value="urgent">Urgent</option>
                    <option value="friendly">Friendly</option>
                  </select>
                  <Button type="submit" size="lg" className="shrink-0 group" disabled={quickIdea.trim().length < 10}>
                    Generate Ad
                    <Zap className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </form>
            ) : (
              <>
                {/* Full Mode: Business Type Toggle */}
                <div className="flex justify-center gap-2 mb-2">
                  <button
                    type="button"
                    onClick={() => setBusinessType('saas')}
                    className={`px-6 py-2 text-sm font-mono transition-all border ${
                      businessType === 'saas'
                        ? 'bg-white/10 text-white border-white/30'
                        : 'bg-transparent text-gray-400 border-white/20 hover:border-white/40'
                    }`}
                  >
                    SaaS
                  </button>
                  <button
                    type="button"
                    onClick={() => setBusinessType('commerce')}
                    className={`px-6 py-2 text-sm font-mono transition-all border ${
                      businessType === 'commerce'
                        ? 'bg-white/10 text-white border-white/30'
                        : 'bg-transparent text-gray-400 border-white/20 hover:border-white/40'
                    }`}
                  >
                    Commerce
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 max-w-lg mx-auto">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="Paste your landing page URL..."
                      className="w-full h-14 bg-brand-gray border border-white/10 px-6 text-white focus:outline-none focus:border-brand-lime font-mono text-sm placeholder:text-gray-600 transition-colors"
                    />
                  </div>
                  <Button type="submit" size="lg" className="shrink-0 group" disabled={!url.trim()}>
                    Generate Ad
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </form>
              </>
            )}

            {error && (
              <div className="text-red-400 text-sm font-mono bg-red-500/10 border border-red-500/20 px-4 py-2 rounded">
                {error}
              </div>
            )}

            {/* Commerce Product Section (Full Mode only) */}
            {generationMode === 'full' && businessType === 'commerce' && (
              <div className="max-w-lg mx-auto space-y-4 pt-4 border-t border-white/10">
                <p className="text-xs text-gray-500 font-mono text-center">
                  Optional: Provide product details for better creatives
                </p>

                {/* Product Description */}
                <div>
                  <input
                    type="text"
                    value={productDescription}
                    onChange={(e) => setProductDescription(e.target.value)}
                    placeholder="Describe your product (e.g., &quot;Premium leather wallet with RFID protection&quot;)"
                    className="w-full h-12 bg-brand-gray border border-white/10 px-4 text-white focus:outline-none focus:border-brand-lime font-mono text-sm placeholder:text-gray-600 transition-colors"
                  />
                </div>

                {/* Product Image Upload */}
                <div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleImageSelect}
                    className="hidden"
                    id="product-image-upload"
                  />

                  {!productImagePreview ? (
                    <label
                      htmlFor="product-image-upload"
                      className="flex items-center justify-center gap-2 w-full h-12 bg-brand-gray border border-dashed border-white/20 hover:border-brand-lime/50 cursor-pointer transition-colors"
                    >
                      <Upload className="w-4 h-4 text-gray-400" />
                      <span className="text-sm font-mono text-gray-400">Upload product image</span>
                    </label>
                  ) : (
                    <div className="flex items-center gap-4 p-3 bg-brand-gray border border-white/10">
                      <img
                        src={productImagePreview}
                        alt="Product preview"
                        className="w-12 h-12 object-cover rounded"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-mono text-white truncate">
                          {productImageFile?.name}
                        </p>
                        <p className="text-xs text-gray-500 font-mono">
                          {isUploading ? 'Uploading...' : uploadedImageUrl ? 'Uploaded' : 'Ready'}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={clearProductImage}
                        className="p-1 hover:bg-white/10 rounded transition-colors"
                      >
                        <X className="w-4 h-4 text-gray-400" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="flex items-center justify-center gap-4 text-sm text-gray-500 font-mono">
              <div className="flex -space-x-2">
                {[1, 2, 3].map(i => (
                  <div key={i} className="w-8 h-8 rounded-full bg-brand-gray border border-brand-dark flex items-center justify-center text-xs text-white">
                    {i}
                  </div>
                ))}
              </div>
              <span>Join 500+ marketers shipping ads faster</span>
            </div>
          </div>

          {/* BOTTOM: Visual Flow (Terminal -> Arrow -> Ad) */}
          <div className="grid lg:grid-cols-2 gap-8 items-center relative">

            {/* LEFT: Terminal */}
            <div className="relative z-10">
              <div className="bg-brand-gray/50 border border-white/10 rounded-lg p-2 backdrop-blur-sm mb-4 inline-flex items-center gap-2">
                <div className="w-2 h-2 bg-brand-lime rounded-full animate-pulse" />
                <span className="text-xs font-mono text-gray-400">Processing URL...</span>
              </div>
              <Terminal />

              {/* Funky Hand-Drawn Arrow Connection */}
              <svg className="absolute top-1/2 -right-16 lg:-right-32 w-48 h-48 text-brand-lime hidden lg:block pointer-events-none z-20" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M 20 60 C 50 60, 60 40, 90 40 C 130 40, 140 80, 120 100 C 100 120, 60 110, 80 140 C 90 155, 140 150, 170 140"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeDasharray="4 8"
                  className="opacity-70"
                  markerEnd="url(#arrowhead)"
                />
                <defs>
                  <marker id="arrowhead" markerWidth="14" markerHeight="14" refX="12" refY="6" orient="auto">
                    <path d="M0 0 L14 6 L0 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </marker>
                </defs>
              </svg>
            </div>

            {/* Mobile Arrow - Animated dotted line (vertical, shown below lg) */}
            <div className="flex justify-center py-4 lg:hidden">
              <svg
                width="20"
                height="100"
                viewBox="0 0 20 100"
                fill="none"
                className="text-brand-lime"
              >
                {/* Dots appearing sequentially in a straight line */}
                <circle cx="10" cy="4" r="3" fill="currentColor" className="animate-dot animate-dot-1" />
                <circle cx="10" cy="14" r="3" fill="currentColor" className="animate-dot animate-dot-2" />
                <circle cx="10" cy="24" r="3" fill="currentColor" className="animate-dot animate-dot-3" />
                <circle cx="10" cy="34" r="3" fill="currentColor" className="animate-dot animate-dot-4" />
                <circle cx="10" cy="44" r="3" fill="currentColor" className="animate-dot animate-dot-5" />
                <circle cx="10" cy="54" r="3" fill="currentColor" className="animate-dot animate-dot-6" />
                <circle cx="10" cy="64" r="3" fill="currentColor" className="animate-dot animate-dot-7" />
                <circle cx="10" cy="74" r="3" fill="currentColor" className="animate-dot animate-dot-8" />
                {/* Arrowhead */}
                <path
                  d="M 3 78 L 10 92 L 17 78"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  fill="none"
                  className="animate-arrowhead"
                />
              </svg>
            </div>

            {/* RIGHT: Ad Preview */}
            <div className="relative flex justify-center lg:justify-end">
              <div className="relative transform hover:scale-105 transition-transform duration-500 z-10 w-full max-w-md">
                <div className="absolute -top-6 -right-6 bg-brand-lime text-brand-dark px-3 py-1 font-bold font-mono text-xs shadow-lg rotate-3 z-30">
                  GENERATED!
                </div>
                {/* Abstract tech decoration behind ad */}
                <div className="absolute -inset-4 bg-brand-lime/5 rounded-2xl blur-xl" />
                <AdPreview />
              </div>
            </div>

          </div>
        </div>
      </section>


      {/* Features Section */}
      <section className="py-24 border-y border-white/5 bg-[#111]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-16">
            <div className="max-w-2xl">
              <h2 className="text-4xl font-display font-bold mb-4">ENGINEERED FOR <span className="text-brand-lime">GROWTH</span></h2>
              <p className="text-gray-400 text-lg">Everything you need to scale your campaigns without the manual grunt work.</p>
            </div>
            <Button variant="outline">View All Features</Button>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: Target,
                title: "Smart Analysis",
                desc: "Automatically extracts specific brand colors, fonts, unique selling points, and customer pain points."
              },
              {
                icon: Layout,
                title: "Brand-Matched Creatives",
                desc: "Generates high-fidelity image and video assets that perfectly match your brand's aesthetic."
              },
              {
                icon: Zap,
                title: "One-Click Launch",
                desc: "Direct integration with Meta Ads Manager allows you to publish campaigns instantly."
              }
            ].map((feature, i) => (
              <Card key={i} className="group hover:border-brand-lime/50 transition-colors">
                <div className="p-8 h-full flex flex-col">
                  <div className="w-12 h-12 bg-brand-gray border border-white/10 flex items-center justify-center mb-6 text-brand-lime group-hover:bg-brand-lime group-hover:text-brand-dark transition-colors">
                    <feature.icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-bold mb-3 font-display tracking-wide">{feature.title}</h3>
                  <p className="text-gray-400 leading-relaxed">{feature.desc}</p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-24 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-display font-bold mb-4">SIMPLE, TRANSPARENT PRICING</h2>
            <p className="text-gray-400 text-lg">No hidden fees. Cancel anytime.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Free/Single Tier */}
            <Card className="hover:border-white/20 transition-colors">
              <div className="p-8">
                <div className="mb-8">
                  <h3 className="text-xl font-bold mb-2">Single Campaign</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-display font-bold text-brand-lime">$29</span>
                    <span className="text-gray-500">/one-time</span>
                  </div>
                  <p className="text-sm text-gray-400 mt-2">Perfect for validting a new idea.</p>
                </div>

                <ul className="space-y-4 mb-8">
                  {['Full Landing Page Analysis', '3 Ad Creative Variations', 'Ad Copy Generation', 'Export to JSON/TXT'].map((item) => (
                    <li key={item} className="flex items-center gap-3 text-sm text-gray-300">
                      <Check className="w-4 h-4 text-brand-lime" />
                      {item}
                    </li>
                  ))}
                </ul>

                <Button variant="secondary" className="w-full">Get Started</Button>
              </div>
            </Card>

            {/* Pro Tier */}
            <Card className="border-brand-lime bg-brand-gray/30 relative">
              <div className="absolute top-0 right-0 bg-brand-lime text-brand-dark text-xs font-bold px-3 py-1 font-mono uppercase">
                Best Value
              </div>
              <div className="p-8">
                <div className="mb-8">
                  <h3 className="text-xl font-bold mb-2">Pro Monthly</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-display font-bold text-white">$129</span>
                    <span className="text-gray-500">/month</span>
                  </div>
                  <p className="text-sm text-gray-400 mt-2">For agencies and power users.</p>
                </div>

                <ul className="space-y-4 mb-8">
                  {['Unlimited Campaigns', 'Direct Meta Integration', 'Priority Support', 'Advanced Analytics'].map((item) => (
                    <li key={item} className="flex items-center gap-3 text-sm text-white">
                      <div className="w-4 h-4 rounded-full bg-brand-lime flex items-center justify-center">
                        <Check className="w-3 h-3 text-brand-dark" />
                      </div>
                      {item}
                    </li>
                  ))}
                </ul>

                <Button variant="primary" className="w-full">
                  Go Pro
                  <Sparkles className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

export default App;
