import { Github, Twitter, Linkedin, ArrowRight } from 'lucide-react';
import { Button } from '../ui/Button';

interface FooterProps {
    onCta?: () => void;
}

export function Footer({ onCta }: FooterProps) {
    return (
        <footer>
            {/* CTA Banner */}
            <div className="bg-brand-lime">
                <div className="max-w-7xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-6">
                    <div>
                        <h3 className="font-display font-bold text-2xl text-brand-dark">Ready to launch?</h3>
                        <p className="text-brand-dark/70 text-sm mt-1">Turn your landing page into ads in 60 seconds.</p>
                    </div>
                    <Button
                        variant="secondary"
                        size="lg"
                        onClick={onCta}
                        className="bg-brand-dark text-brand-lime hover:bg-brand-dark/90 hover:text-brand-lime whitespace-nowrap"
                    >
                        Get Started <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                </div>
            </div>

            {/* Main footer */}
            <div className="bg-gray-100 dark:bg-brand-gray border-t border-gray-200 dark:border-white/10">
                <div className="max-w-7xl mx-auto px-6 pt-16 pb-8 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-12">
                    {/* Brand */}
                    <div className="col-span-1 sm:col-span-2">
                        <div className="flex items-center gap-2 mb-6">
                            <div className="w-8 h-8 bg-brand-lime flex items-center justify-center font-display font-bold text-xl text-brand-dark">
                                L
                            </div>
                            <span className="font-display font-bold text-xl tracking-tight text-gray-900 dark:text-white">
                                LAUNCHAD
                            </span>
                        </div>
                        <p className="text-gray-500 dark:text-white/60 max-w-sm mb-6 text-sm">
                            Turn any landing page into a high-converting Meta Ads campaign in 60 seconds.
                            Built by makers, for makers.
                        </p>
                        <div className="flex gap-3">
                            <a href="#" className="p-2 bg-gray-200 dark:bg-white/10 hover:bg-brand-lime hover:text-brand-dark text-gray-500 dark:text-white/60 transition-colors" aria-label="Twitter">
                                <Twitter className="w-5 h-5" />
                            </a>
                            <a href="#" className="p-2 bg-gray-200 dark:bg-white/10 hover:bg-brand-lime hover:text-brand-dark text-gray-500 dark:text-white/60 transition-colors" aria-label="GitHub">
                                <Github className="w-5 h-5" />
                            </a>
                            <a href="#" className="p-2 bg-gray-200 dark:bg-white/10 hover:bg-brand-lime hover:text-brand-dark text-gray-500 dark:text-white/60 transition-colors" aria-label="LinkedIn">
                                <Linkedin className="w-5 h-5" />
                            </a>
                        </div>
                    </div>

                    {/* Product */}
                    <div>
                        <h4 className="font-mono font-bold mb-6 text-gray-900 dark:text-white uppercase tracking-wider text-xs">Product</h4>
                        <ul className="space-y-3 text-sm text-gray-500 dark:text-white/60">
                            <li><a href="#features" className="hover:text-brand-lime transition-colors">Features</a></li>
                            <li><a href="#pricing" className="hover:text-brand-lime transition-colors">Pricing</a></li>
                            <li><a href="#" className="hover:text-brand-lime transition-colors">Changelog</a></li>
                            <li><a href="#" className="hover:text-brand-lime transition-colors">Docs</a></li>
                        </ul>
                    </div>

                    {/* Company */}
                    <div>
                        <h4 className="font-mono font-bold mb-6 text-gray-900 dark:text-white uppercase tracking-wider text-xs">Company</h4>
                        <ul className="space-y-3 text-sm text-gray-500 dark:text-white/60">
                            <li><a href="#" className="hover:text-brand-lime transition-colors">About</a></li>
                            <li><a href="#" className="hover:text-brand-lime transition-colors">Blog</a></li>
                            <li><a href="#" className="hover:text-brand-lime transition-colors">Contact</a></li>
                            <li><a href="mailto:hello@launchad.com" className="hover:text-brand-lime transition-colors">hello@launchad.com</a></li>
                        </ul>
                    </div>
                </div>

                {/* Bottom */}
                <div className="max-w-7xl mx-auto px-6 py-6 border-t border-gray-200 dark:border-white/5 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs text-gray-400 dark:text-white/40">
                    <div>&copy; 2026 LaunchAd Inc.</div>
                    <div className="flex gap-6">
                        <a href="#" className="hover:text-gray-900 dark:hover:text-white transition-colors">Privacy Policy</a>
                        <a href="#" className="hover:text-gray-900 dark:hover:text-white transition-colors">Terms of Service</a>
                    </div>
                </div>
            </div>
        </footer>
    );
}
