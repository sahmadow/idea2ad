import { useState, type FormEvent } from 'react';
import { ArrowRight, Check, Sparkles, Target, Zap, Layout } from 'lucide-react';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { Button } from './components/ui/Button';
import { Card } from './components/ui/Card';
import { Terminal } from './components/ui/Terminal';
import { AdPreview } from './components/ui/AdPreview';
import { ResultsView } from './components/ResultsView';
import { analyzeUrl, type CampaignDraft, type Ad } from './api';

type View = 'landing' | 'loading' | 'results';

function App() {
  const [url, setUrl] = useState('');
  const [view, setView] = useState<View>('landing');
  const [result, setResult] = useState<CampaignDraft | null>(null);
  const [selectedAd, setSelectedAd] = useState<Ad | null>(null);
  const [error, setError] = useState<string | null>(null);

  const normalizeUrl = (input: string): string => {
    let normalized = input.trim();
    if (!normalized.match(/^https?:\/\//i)) {
      normalized = 'https://' + normalized;
    }
    return normalized;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setView('loading');
    setError(null);
    setResult(null);
    setSelectedAd(null);

    try {
      const normalizedUrl = normalizeUrl(url);
      const data = await analyzeUrl(normalizedUrl);
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
  };

  // Loading View
  if (view === 'loading') {
    return (
      <div className="min-h-screen bg-brand-dark text-white flex flex-col items-center justify-center">
        <div className="text-center space-y-8">
          <div className="w-16 h-16 border-2 border-brand-lime/30 border-t-brand-lime rounded-full animate-spin mx-auto" />
          <div>
            <h2 className="text-2xl font-display font-bold mb-2">Analyzing Your Page</h2>
            <p className="text-gray-400 font-mono text-sm">{url}</p>
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

            {error && (
              <div className="text-red-400 text-sm font-mono bg-red-500/10 border border-red-500/20 px-4 py-2 rounded">
                {error}
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

            {/* Mobile Arrow (vertical, shown below lg) */}
            <div className="flex justify-center py-6 lg:hidden">
              <ArrowRight className="w-8 h-8 text-brand-lime rotate-90" />
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
