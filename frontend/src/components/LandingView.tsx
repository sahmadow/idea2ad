import { type FormEvent, useState, useEffect } from 'react';
import { ArrowRight, Check, Sparkles, Target, Zap, Layout } from 'lucide-react';
import { motion } from 'framer-motion';
import { Navbar } from './layout/Navbar';
import { Footer } from './layout/Footer';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Terminal } from './ui/Terminal';
import { AdPreview } from './ui/AdPreview';
import { ErrorBanner } from './ui/ErrorBanner';

interface LandingViewProps {
  input: string;
  onInputChange: (val: string) => void;
  onSubmit: (e: FormEvent) => void;
  error: string | null;
  onDismissError: () => void;
  userName?: string | null;
  onSignInClick?: () => void;
  onDashboardClick?: () => void;
  onLogout?: () => Promise<void>;
}

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};

const slideUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' as const } },
};

const PLACEHOLDER_EXAMPLES = [
  'https://yourproduct.com',
  'An AI writing assistant for students',
  'https://myshopify.store/products/serum',
  'A fitness app that builds custom meal plans',
  'https://acme.io/pricing',
  'Eco-friendly pet food subscription box',
];

export function LandingView({
  input,
  onInputChange,
  onSubmit,
  error,
  onDismissError,
  userName,
  onSignInClick,
  onDashboardClick,
  onLogout,
}: LandingViewProps) {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const isValid = !!input.trim();

  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(true);
  const [isFocused, setIsFocused] = useState(false);

  const currentExample = PLACEHOLDER_EXAMPLES[placeholderIndex];

  useEffect(() => {
    if (input || isFocused) return;

    let timeout: ReturnType<typeof setTimeout>;

    if (isTyping) {
      if (displayedText.length < currentExample.length) {
        timeout = setTimeout(() => {
          setDisplayedText(currentExample.slice(0, displayedText.length + 1));
        }, 40);
      } else {
        timeout = setTimeout(() => setIsTyping(false), 2000);
      }
    } else {
      if (displayedText.length > 0) {
        timeout = setTimeout(() => {
          setDisplayedText(displayedText.slice(0, -1));
        }, 25);
      } else {
        setPlaceholderIndex((i) => (i + 1) % PLACEHOLDER_EXAMPLES.length);
        setIsTyping(true);
      }
    }

    return () => clearTimeout(timeout);
  }, [displayedText, isTyping, currentExample, input, isFocused]);

  return (
    <div className="min-h-screen bg-white dark:bg-brand-dark text-gray-900 dark:text-white selection:bg-brand-lime selection:text-brand-dark">
      <Navbar
        onLogoClick={scrollToTop}
        userName={userName}
        onSignInClick={onSignInClick}
        onDashboardClick={onDashboardClick}
        onLogout={onLogout}
      />

      {/* Beta banner */}
      <div className="bg-brand-lime/10 border-b border-brand-lime/20">
        <div className="max-w-7xl mx-auto px-6 py-2 text-center text-sm font-mono text-brand-lime">
          <span className="inline-flex items-center gap-2">
            <span className="px-1.5 py-0.5 bg-brand-lime text-brand-dark text-[10px] font-bold uppercase tracking-wider">Beta</span>
            This platform is in active development — features may change and some flows are still being refined.
          </span>
        </div>
      </div>

      {/* Hero */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern opacity-[0.03] dark:opacity-[0.03] pointer-events-none" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-brand-lime/5 blur-[120px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6 relative">
          <div className="max-w-3xl mx-auto text-center space-y-8 mb-24 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-gray-100 dark:bg-brand-gray border border-gray-200 dark:border-white/10 text-xs font-mono text-brand-lime uppercase tracking-wider">
              <span className="w-2 h-2 bg-brand-lime animate-pulse" />
              AI-Powered Ad Generation
            </div>

            <h1 className="text-3xl xs:text-4xl sm:text-5xl lg:text-6xl font-display font-bold leading-[0.9] text-gray-900 dark:text-white text-balance">
              SAY GOODBYE TO <span className="text-brand-lime">MANUAL</span> AD CREATION
            </h1>

            <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-400 max-w-xl mx-auto leading-relaxed">
              Turn any landing page into a <span className="text-gray-900 dark:text-white font-medium">Meta Ads campaign</span> in 60 seconds.
            </p>

            {/* Single unified input */}
            <form onSubmit={onSubmit} className="max-w-2xl mx-auto w-full">
              <div className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-brand-lime/20 via-brand-lime/5 to-brand-lime/20 rounded-lg opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 blur-sm" />
                <div className="relative flex items-center bg-gray-100 dark:bg-brand-gray border border-gray-200 dark:border-white/10 rounded-lg group-focus-within:border-brand-lime/50 transition-colors">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => onInputChange(e.target.value)}
                      onFocus={() => setIsFocused(true)}
                      onBlur={() => setIsFocused(false)}
                      aria-label="Product URL or description"
                      className="w-full h-16 sm:h-[72px] bg-transparent px-6 sm:px-8 text-gray-900 dark:text-white focus:outline-none font-mono text-base sm:text-lg placeholder:text-gray-400 dark:placeholder:text-gray-600 transition-colors"
                    />
                    {!input && (
                      <div className="absolute inset-0 flex items-center px-6 sm:px-8 pointer-events-none">
                        <span className="font-mono text-base sm:text-lg text-gray-400 dark:text-gray-500">
                          {displayedText}
                          <span className="inline-block w-[2px] h-5 bg-brand-lime/70 ml-0.5 animate-pulse align-middle" />
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="pr-3 sm:pr-4">
                    <Button type="submit" size="lg" className="shrink-0 group/btn rounded-md" disabled={!isValid}>
                      <span className="hidden sm:inline">Continue</span>
                      <ArrowRight className="w-5 h-5 sm:ml-2 group-hover/btn:translate-x-1 transition-transform" />
                    </Button>
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-500 font-mono mt-4 text-center">
                Paste a URL to analyze your landing page, or describe your product in your own words
              </p>
            </form>

            {error && (
              <ErrorBanner message={error} onDismiss={onDismissError} className="max-w-lg mx-auto" />
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
      <section id="features" className="py-24 border-y border-gray-200 dark:border-white/5 bg-gray-50 dark:bg-[#111]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-16">
            <div className="max-w-2xl">
              <h2 className="text-3xl sm:text-4xl font-display font-bold mb-4">ENGINEERED FOR <span className="text-brand-lime">GROWTH</span></h2>
              <p className="text-gray-600 dark:text-gray-400 text-lg">Everything you need to scale your campaigns without the manual grunt work.</p>
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
                    <div className="w-12 h-12 bg-gray-100 dark:bg-brand-gray border border-gray-200 dark:border-white/10 flex items-center justify-center mb-6 text-brand-lime group-hover:bg-brand-lime group-hover:text-brand-dark transition-colors">
                      <feature.icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-bold mb-3 font-display tracking-wide">{feature.title}</h3>
                    <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{feature.desc}</p>
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
            <p className="text-gray-600 dark:text-gray-400 text-lg">No hidden fees. Cancel anytime.</p>
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
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">Perfect for validating a new idea.</p>
                  </div>

                  <ul className="space-y-4 mb-8">
                    {['Full Landing Page Analysis', '3 Ad Creative Variations', 'Ad Copy Generation', 'Export to JSON/TXT'].map((item) => (
                      <li key={item} className="flex items-center gap-3 text-sm text-gray-700 dark:text-gray-300">
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
              <Card variant="highlighted" className="bg-gray-50/30 dark:bg-brand-gray/30 relative h-full">
                <div className="absolute top-0 right-0 bg-brand-lime text-brand-dark text-xs font-bold px-3 py-1 font-mono uppercase">
                  Best Value
                </div>
                <div className="p-8">
                  <div className="mb-8">
                    <h3 className="text-xl font-bold mb-2">Pro Monthly</h3>
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-display font-bold text-gray-900 dark:text-white">$129</span>
                      <span className="text-gray-500">/month</span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">For agencies and power users.</p>
                  </div>

                  <ul className="space-y-4 mb-8">
                    {['Unlimited Campaigns', 'Direct Meta Integration', 'Priority Support', 'Advanced Analytics'].map((item) => (
                      <li key={item} className="flex items-center gap-3 text-sm text-gray-900 dark:text-white">
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
