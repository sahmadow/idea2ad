
import { Button } from '../ui/Button';

export function Navbar() {
    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-brand-dark/90 backdrop-blur border-b border-white/10">
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                {/* Logo */}
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-brand-lime flex items-center justify-center font-display font-bold text-xl text-brand-dark">
                        L
                    </div>
                    <span className="font-display font-bold text-xl tracking-tight text-white">
                        LAUNCHAD
                    </span>
                </div>

                {/* Links */}
                <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
                    <a href="#" className="hover:text-brand-lime transition-colors">Features</a>
                    <a href="#" className="hover:text-brand-lime transition-colors">Pricing</a>
                    <a href="#" className="hover:text-brand-lime transition-colors">Docs</a>
                </div>

                {/* CTA - hidden on mobile */}
                <div className="hidden md:flex items-center gap-4">
                    <a href="#" className="text-sm font-medium text-white hover:text-brand-lime">Sign In</a>
                    <Button size="sm" variant="primary">
                        Start Building
                    </Button>
                </div>
            </div>
        </nav>
    );
}
