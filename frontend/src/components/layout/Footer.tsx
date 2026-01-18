
import { Github, Twitter, Linkedin } from 'lucide-react';

export function Footer() {
    return (
        <footer className="bg-brand-lime text-brand-dark pt-20 pb-10">
            <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12">
                {/* Brand */}
                <div className="col-span-1 md:col-span-2">
                    <div className="flex items-center gap-2 mb-6">
                        <div className="w-8 h-8 bg-brand-dark flex items-center justify-center font-display font-bold text-xl text-brand-lime">
                            L
                        </div>
                        <span className="font-display font-bold text-xl tracking-tight text-brand-dark">
                            LAUNCHAD
                        </span>
                    </div>
                    <p className="text-brand-dark/80 max-w-sm mb-6 font-medium">
                        Turn any landing page into a high-converting Meta Ads campaign in 60 seconds.
                        Built by makers, for makers.
                    </p>
                    <div className="flex gap-4">
                        <a href="#" className="p-2 bg-brand-dark/10 hover:bg-brand-dark/20 transition-colors rounded-none">
                            <Twitter className="w-5 h-5" />
                        </a>
                        <a href="#" className="p-2 bg-brand-dark/10 hover:bg-brand-dark/20 transition-colors rounded-none">
                            <Github className="w-5 h-5" />
                        </a>
                        <a href="#" className="p-2 bg-brand-dark/10 hover:bg-brand-dark/20 transition-colors rounded-none">
                            <Linkedin className="w-5 h-5" />
                        </a>
                    </div>
                </div>

                {/* Links */}
                <div>
                    <h4 className="font-bold mb-6 text-brand-dark uppercase tracking-wider text-sm">Product</h4>
                    <ul className="space-y-4 font-medium text-brand-dark/80">
                        <li><a href="#" className="hover:text-brand-dark hover:underline decoration-2 underline-offset-4">Features</a></li>
                        <li><a href="#" className="hover:text-brand-dark hover:underline decoration-2 underline-offset-4">Pricing</a></li>
                        <li><a href="#" className="hover:text-brand-dark hover:underline decoration-2 underline-offset-4">Changelog</a></li>
                        <li><a href="#" className="hover:text-brand-dark hover:underline decoration-2 underline-offset-4">Docs</a></li>
                    </ul>
                </div>

                <div>
                    <h4 className="font-bold mb-6 text-brand-dark uppercase tracking-wider text-sm">Company</h4>
                    <ul className="space-y-4 font-medium text-brand-dark/80">
                        <li><a href="#" className="hover:text-brand-dark hover:underline decoration-2 underline-offset-4">About</a></li>
                        <li><a href="#" className="hover:text-brand-dark hover:underline decoration-2 underline-offset-4">Blog</a></li>
                        <li><a href="#" className="hover:text-brand-dark hover:underline decoration-2 underline-offset-4">Contact</a></li>
                        <li><a href="mailto:hello@launchad.com" className="hover:text-brand-dark hover:underline decoration-2 underline-offset-4">hello@launchad.com</a></li>
                    </ul>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-6 mt-20 pt-8 border-t border-brand-dark/10 flex flex-col md:flex-row justify-between items-center gap-4 text-sm font-medium text-brand-dark/60">
                <div>© 2026 LaunchAd Inc.</div>
                <div className="flex gap-8">
                    <a href="#" className="hover:text-brand-dark">Privacy Policy</a>
                    <a href="#" className="hover:text-brand-dark">Terms of Service</a>
                </div>
            </div>
        </footer>
    );
}
