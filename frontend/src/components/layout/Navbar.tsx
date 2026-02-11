import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';

interface NavbarProps {
    onLogoClick?: () => void;
}

export function Navbar({ onLogoClick }: NavbarProps) {
    const [mobileOpen, setMobileOpen] = useState(false);

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-brand-dark/90 backdrop-blur-md border-b border-white/5" aria-label="Main navigation">
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                {/* Logo */}
                <button
                    onClick={onLogoClick}
                    className="flex items-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-lime"
                >
                    <div className="w-8 h-8 bg-brand-lime flex items-center justify-center font-display font-bold text-xl text-brand-dark">
                        L
                    </div>
                    <span className="font-display font-bold text-xl tracking-tight text-white">
                        LAUNCHAD
                    </span>
                </button>

                {/* Desktop links */}
                <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
                    <a href="#features" className="hover:text-brand-lime transition-colors">Features</a>
                    <a href="#pricing" className="hover:text-brand-lime transition-colors">Pricing</a>
                    <a href="#" className="hover:text-brand-lime transition-colors">Docs</a>
                </div>

                {/* Desktop CTA */}
                <div className="hidden md:flex items-center gap-4">
                    <a href="#" className="text-sm font-medium text-white hover:text-brand-lime transition-colors">Sign In</a>
                    <Button size="sm" variant="primary">
                        Start Building
                    </Button>
                </div>

                {/* Mobile hamburger */}
                <button
                    className="md:hidden p-2 text-white hover:text-brand-lime transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-lime"
                    onClick={() => setMobileOpen(!mobileOpen)}
                    aria-expanded={mobileOpen}
                    aria-label="Toggle menu"
                >
                    {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                </button>
            </div>

            {/* Mobile menu */}
            <AnimatePresence>
                {mobileOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="md:hidden overflow-hidden border-t border-white/5 bg-brand-dark/95 backdrop-blur-md"
                    >
                        <div className="px-6 py-4 flex flex-col gap-4">
                            <a href="#features" onClick={() => setMobileOpen(false)} className="text-sm font-medium text-gray-400 hover:text-brand-lime transition-colors py-2">Features</a>
                            <a href="#pricing" onClick={() => setMobileOpen(false)} className="text-sm font-medium text-gray-400 hover:text-brand-lime transition-colors py-2">Pricing</a>
                            <a href="#" onClick={() => setMobileOpen(false)} className="text-sm font-medium text-gray-400 hover:text-brand-lime transition-colors py-2">Docs</a>
                            <div className="border-t border-white/5 pt-4 flex flex-col gap-3">
                                <a href="#" className="text-sm font-medium text-white hover:text-brand-lime transition-colors py-2">Sign In</a>
                                <Button size="sm" variant="primary" className="w-full">
                                    Start Building
                                </Button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </nav>
    );
}
