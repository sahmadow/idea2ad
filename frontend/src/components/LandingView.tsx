import { type FormEvent, type ChangeEvent, useRef } from 'react';
import { ArrowRight, Check, Sparkles, Target, Zap, Layout, Upload, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { Navbar } from './layout/Navbar';
import { Footer } from './layout/Footer';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Terminal } from './ui/Terminal';
import { AdPreview } from './ui/AdPreview';
import { SegmentedControl } from './ui/SegmentedControl';
import { ErrorBanner } from './ui/ErrorBanner';
import { CompetitorInput } from './CompetitorInput';
import type { BusinessType, ToneOption } from '../api';

type GenerationMode = 'full' | 'quick';

interface LandingViewProps {
  // Form state
  url: string;
  onUrlChange: (url: string) => void;
  quickIdea: string;
  onQuickIdeaChange: (idea: string) => void;
  quickTone: ToneOption;
  onQuickToneChange: (tone: ToneOption) => void;
  generationMode: GenerationMode;
  onGenerationModeChange: (mode: GenerationMode) => void;
  businessType: BusinessType;
  onBusinessTypeChange: (type: BusinessType) => void;

  // Commerce product state
  productDescription: string;
  onProductDescriptionChange: (desc: string) => void;
  productImagePreview: string | null;
  productImageFileName: string | null;
  isUploading: boolean;
  uploadedImageUrl: string | null;
  onImageSelect: (e: ChangeEvent<HTMLInputElement>) => void;
  onClearImage: () => void;

  // Competitor intel
  competitors: string[];
  onCompetitorsChange: (competitors: string[]) => void;

  // Actions
  onSubmit: (e: FormEvent) => void;
  error: string | null;
  onDismissError: () => void;
}

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};

const slideUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' as const } },
};

export function LandingView({
  url,
  onUrlChange,
  quickIdea,
  onQuickIdeaChange,
  quickTone,
  onQuickToneChange,
  generationMode,
  onGenerationModeChange,
  businessType,
  onBusinessTypeChange,
  productDescription,
  onProductDescriptionChange,
  productImagePreview,
  productImageFileName,
  isUploading,
  uploadedImageUrl,
  onImageSelect,
  competitors,
  onCompetitorsChange,
  onClearImage,
  onSubmit,
  error,
  onDismissError,
}: LandingViewProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-brand-dark text-white selection:bg-brand-lime selection:text-brand-dark">
      <Navbar onLogoClick={scrollToTop} />

      {/* Hero */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern opacity-[0.03] pointer-events-none" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-brand-lime/5 blur-[120px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6 relative">
          <div className="max-w-3xl mx-auto text-center space-y-8 mb-24 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-gray border border-white/10 text-xs font-mono text-brand-lime uppercase tracking-wider">
              <span className="w-2 h-2 bg-brand-lime animate-pulse" />
              AI-Powered Ad Generation
            </div>

            <h1 className="text-3xl xs:text-4xl sm:text-5xl lg:text-6xl font-display font-bold leading-[0.9] text-white text-balance">
              SAY GOODBYE TO <span className="text-brand-lime">MANUAL</span> AD CREATION
            </h1>

            <p className="text-lg sm:text-xl text-gray-400 max-w-xl mx-auto leading-relaxed">
              Turn any landing page into a <span className="text-white font-medium">Meta Ads campaign</span> in 60 seconds.
            </p>

            {/* Mode Toggle */}
            <SegmentedControl
              options={[
                { value: 'full' as GenerationMode, label: 'Full Mode' },
                { value: 'quick' as GenerationMode, label: 'Quick Mode' },
              ]}
              value={generationMode}
              onChange={onGenerationModeChange}
            />
            <p className="text-xs text-gray-500 font-mono">
              {generationMode === 'quick'
                ? 'Describe your idea, get an ad instantly'
                : 'Analyze a landing page for brand-matched creatives'}
            </p>

            {/* Quick Mode Form */}
            {generationMode === 'quick' ? (
              <form onSubmit={onSubmit} className="flex flex-col gap-4 max-w-lg mx-auto">
                <div className="relative">
                  <textarea
                    value={quickIdea}
                    onChange={(e) => onQuickIdeaChange(e.target.value)}
                    placeholder="Describe your business or product idea..."
                    rows={3}
                    maxLength={500}
                    aria-label="Business idea description"
                    className="w-full bg-brand-gray border border-white/10 px-6 py-4 text-white focus:outline-none focus:border-brand-lime focus:border-l-4 focus:border-l-brand-lime font-mono text-sm placeholder:text-gray-600 transition-colors resize-none"
                  />
                  <span className="absolute bottom-2 right-3 text-xs text-gray-600 font-mono">
                    {quickIdea.length}/500
                  </span>
                </div>
                <div className="flex gap-4">
                  <select
                    value={quickTone}
                    onChange={(e) => onQuickToneChange(e.target.value as ToneOption)}
                    aria-label="Tone"
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
                {/* Business Type Tabs */}
                <div className="flex justify-center gap-6 mb-2">
                  <button
                    type="button"
                    onClick={() => onBusinessTypeChange('saas')}
                    className={`pb-1 text-sm font-mono transition-all border-b-2 ${
                      businessType === 'saas'
                        ? 'text-white border-brand-lime'
                        : 'text-gray-500 border-transparent hover:text-gray-300'
                    }`}
                  >
                    SaaS
                  </button>
                  <button
                    type="button"
                    onClick={() => onBusinessTypeChange('commerce')}
                    className={`pb-1 text-sm font-mono transition-all border-b-2 ${
                      businessType === 'commerce'
                        ? 'text-white border-brand-lime'
                        : 'text-gray-500 border-transparent hover:text-gray-300'
                    }`}
                  >
                    Commerce
                  </button>
                </div>

                <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-4 max-w-lg mx-auto">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={url}
                      onChange={(e) => onUrlChange(e.target.value)}
                      placeholder="Paste your landing page URL..."
                      aria-label="Landing page URL"
                      className="w-full h-14 bg-brand-gray border border-white/10 px-6 text-white focus:outline-none focus:border-brand-lime focus:border-l-4 focus:border-l-brand-lime font-mono text-sm placeholder:text-gray-600 transition-colors"
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
              <ErrorBanner message={error} onDismiss={onDismissError} className="max-w-lg mx-auto" />
            )}

            {/* Commerce Upload */}
            {generationMode === 'full' && businessType === 'commerce' && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="max-w-lg mx-auto space-y-4 pt-4 border-t border-white/10"
              >
                <p className="text-xs text-gray-500 font-mono text-center">
                  Optional: Provide product details for better creatives
                </p>

                <input
                  type="text"
                  value={productDescription}
                  onChange={(e) => onProductDescriptionChange(e.target.value)}
                  placeholder="Describe your product..."
                  aria-label="Product description"
                  className="w-full h-12 bg-brand-gray border border-white/10 px-4 text-white focus:outline-none focus:border-brand-lime font-mono text-sm placeholder:text-gray-600 transition-colors"
                />

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={onImageSelect}
                  className="hidden"
                  id="product-image-upload"
                />

                {!productImagePreview ? (
                  <label
                    htmlFor="product-image-upload"
                    className="flex items-center justify-center gap-2 w-full h-24 bg-brand-gray border border-dashed border-white/20 hover:border-brand-lime/50 cursor-pointer transition-colors"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        fileInputRef.current?.click();
                      }
                    }}
                  >
                    <Upload className="w-5 h-5 text-gray-400" />
                    <span className="text-sm font-mono text-gray-400">Upload product image</span>
                  </label>
                ) : (
                  <div className="flex items-center gap-4 p-3 bg-brand-gray border border-white/10">
                    <img src={productImagePreview} alt="Product preview" className="w-12 h-12 object-cover" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-mono text-white truncate">{productImageFileName}</p>
                      <p className="text-xs text-gray-500 font-mono">
                        {isUploading ? 'Uploading...' : uploadedImageUrl ? 'Uploaded' : 'Ready'}
                      </p>
                    </div>
                    <button type="button" onClick={onClearImage} className="p-1 hover:bg-white/10 transition-colors">
                      <X className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                )}
              </motion.div>
            )}

            {/* Competitor Input (full mode only) */}
            {generationMode === 'full' && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="max-w-lg mx-auto pt-4 border-t border-white/10"
              >
                <CompetitorInput
                  competitors={competitors}
                  onCompetitorsChange={onCompetitorsChange}
                />
              </motion.div>
            )}

            <div className="flex items-center justify-center gap-4 text-sm text-gray-500 font-mono">
              <span>Join 500+ marketers shipping ads faster</span>
            </div>
          </div>

          {/* Visual Flow */}
          <div className="grid lg:grid-cols-2 gap-8 items-center relative">
            <div className="relative z-10">
              <div className="bg-brand-gray/50 border border-white/10 p-2 backdrop-blur-sm mb-4 inline-flex items-center gap-2">
                <div className="w-2 h-2 bg-brand-lime animate-pulse" />
                <span className="text-xs font-mono text-gray-400">Processing URL...</span>
              </div>
              <Terminal />

              {/* Desktop arrow */}
              <svg className="absolute top-1/2 -right-16 lg:-right-32 w-48 h-48 text-brand-lime hidden lg:block pointer-events-none z-20" viewBox="0 0 200 200" fill="none">
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

            {/* Mobile arrow */}
            <div className="flex justify-center py-4 lg:hidden">
              <div className="w-px h-16 bg-gradient-to-b from-brand-lime/50 to-transparent" />
            </div>

            {/* Ad Preview */}
            <div className="relative flex justify-center lg:justify-end">
              <div className="relative z-10 w-full max-w-md">
                <div className="absolute -top-6 -right-6 bg-brand-lime text-brand-dark px-3 py-1 font-bold font-mono text-xs shadow-lg rotate-3 z-30">
                  GENERATED!
                </div>
                <div className="absolute -inset-4 bg-brand-lime/5 blur-xl" />
                <AdPreview />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 border-y border-white/5 bg-[#111]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-16">
            <div className="max-w-2xl">
              <h2 className="text-3xl sm:text-4xl font-display font-bold mb-4">ENGINEERED FOR <span className="text-brand-lime">GROWTH</span></h2>
              <p className="text-gray-400 text-lg">Everything you need to scale your campaigns without the manual grunt work.</p>
            </div>
            <Button variant="outline">View All Features</Button>
          </div>

          <motion.div
            className="grid md:grid-cols-3 gap-6"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-100px' }}
          >
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
              <motion.div key={i} variants={slideUp}>
                <Card className="group hover:border-brand-lime/50 transition-colors h-full">
                  <div className="p-8 h-full flex flex-col">
                    <div className="w-12 h-12 bg-brand-gray border border-white/10 flex items-center justify-center mb-6 text-brand-lime group-hover:bg-brand-lime group-hover:text-brand-dark transition-colors">
                      <feature.icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-bold mb-3 font-display tracking-wide">{feature.title}</h3>
                    <p className="text-gray-400 leading-relaxed">{feature.desc}</p>
                  </div>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-24 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-display font-bold mb-4">SIMPLE, TRANSPARENT PRICING</h2>
            <p className="text-gray-400 text-lg">No hidden fees. Cancel anytime.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <motion.div whileHover={{ y: -4 }} transition={{ type: 'spring', stiffness: 300, damping: 20 }}>
              <Card className="h-full">
                <div className="p-8">
                  <div className="mb-8">
                    <h3 className="text-xl font-bold mb-2">Single Campaign</h3>
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-display font-bold text-brand-lime">$29</span>
                      <span className="text-gray-500">/one-time</span>
                    </div>
                    <p className="text-sm text-gray-400 mt-2">Perfect for validating a new idea.</p>
                  </div>

                  <ul className="space-y-4 mb-8">
                    {['Full Landing Page Analysis', '3 Ad Creative Variations', 'Ad Copy Generation', 'Export to JSON/TXT'].map((item) => (
                      <li key={item} className="flex items-center gap-3 text-sm text-gray-300">
                        <Check className="w-4 h-4 text-brand-lime shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>

                  <Button variant="secondary" className="w-full">Get Started</Button>
                </div>
              </Card>
            </motion.div>

            <motion.div whileHover={{ y: -4 }} transition={{ type: 'spring', stiffness: 300, damping: 20 }}>
              <Card variant="highlighted" className="bg-brand-gray/30 relative h-full">
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
                        <div className="w-4 h-4 bg-brand-lime flex items-center justify-center shrink-0">
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
            </motion.div>
          </div>
        </div>
      </section>

      <Footer onCta={scrollToTop} />
    </div>
  );
}
