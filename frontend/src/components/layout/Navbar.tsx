import { useState } from 'react';
import { Menu, X, LayoutDashboard, LogOut, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';

interface NavbarProps {
    onLogoClick?: () => void;
    userName?: string | null;
    onSignInClick?: () => void;
    onDashboardClick?: () => void;
    onLogout?: () => Promise<void>;
}

export function Navbar({ onLogoClick, userName, onSignInClick, onDashboardClick, onLogout }: NavbarProps) {
    const [mobileOpen, setMobileOpen] = useState(false);

    const isAuthenticated = !!userName;

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
                    {isAuthenticated && (
                        <button
                            onClick={onDashboardClick}
                            className="flex items-center gap-1.5 hover:text-brand-lime transition-colors"
                        >
                            <LayoutDashboard className="w-4 h-4" />
                            My Campaigns
                        </button>
                    )}
                    <a href="#" className="hover:text-brand-lime transition-colors">Docs</a>
                </div>

                {/* Desktop CTA */}
                <div className="hidden md:flex items-center gap-4">
                    {isAuthenticated ? (
                        <>
                            <span className="flex items-center gap-1.5 text-sm text-gray-400">
                                <User className="w-4 h-4" />
                                <span className="font-mono">{userName}</span>
                            </span>
                            {onLogout && (
                                <button
                                    onClick={onLogout}
                                    className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-400 transition-colors"
                                    aria-label="Sign out"
                                >
                                    <LogOut className="w-4 h-4" />
                                </button>
                            )}
                        </>
                    ) : (
                        <>
                            <button
                                onClick={onSignInClick}
                                className="text-sm font-medium text-white hover:text-brand-lime transition-colors"
                            >
                                Sign In
                            </button>
                            <Button size="sm" variant="primary" onClick={onSignInClick}>
                                Start Building
                            </Button>
                        </>
                    )}
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
                            {isAuthenticated && (
                                <button
                                    onClick={() => { setMobileOpen(false); onDashboardClick?.(); }}
                                    className="flex items-center gap-1.5 text-sm font-medium text-gray-400 hover:text-brand-lime transition-colors py-2 text-left"
                                >
                                    <LayoutDashboard className="w-4 h-4" />
                                    My Campaigns
                                </button>
                            )}
                            <a href="#" onClick={() => setMobileOpen(false)} className="text-sm font-medium text-gray-400 hover:text-brand-lime transition-colors py-2">Docs</a>
                            <div className="border-t border-white/5 pt-4 flex flex-col gap-3">
                                {isAuthenticated ? (
                                    <>
                                        <span className="flex items-center gap-1.5 text-sm text-gray-400 py-2">
                                            <User className="w-4 h-4" />
                                            <span className="font-mono">{userName}</span>
                                        </span>
                                        {onLogout && (
                                            <button
                                                onClick={() => { setMobileOpen(false); onLogout(); }}
                                                className="flex items-center gap-1.5 text-sm text-red-400 hover:text-red-300 transition-colors py-2 text-left"
                                            >
                                                <LogOut className="w-4 h-4" />
                                                Sign Out
                                            </button>
                                        )}
                                    </>
                                ) : (
                                    <>
                                        <button
                                            onClick={() => { setMobileOpen(false); onSignInClick?.(); }}
                                            className="text-sm font-medium text-white hover:text-brand-lime transition-colors py-2 text-left"
                                        >
                                            Sign In
                                        </button>
                                        <Button size="sm" variant="primary" className="w-full" onClick={() => { setMobileOpen(false); onSignInClick?.(); }}>
                                            Start Building
                                        </Button>
                                    </>
                                )}
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </nav>
    );
}
