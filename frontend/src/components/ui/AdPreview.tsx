
import { MoreHorizontal, ThumbsUp, MessageCircle, Share2, Globe, X, ArrowRight } from 'lucide-react';

export function AdPreview() {
    return (
        <div className="relative group perspective-1000">
            {/* Decorative background glow */}
            <div className="absolute inset-0 bg-brand-lime/20 blur-xl rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            {/* Facebook/Meta Style Ad Card */}
            <div className="relative bg-[#242526] text-white rounded-xl overflow-hidden max-w-sm w-full font-sans shadow-2xl border border-white/5 mx-auto">

                {/* Header */}
                <div className="p-3 flex items-start justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-10 h-10 rounded-full bg-white p-0.5 overflow-hidden">
                            <div className="w-full h-full bg-brand-lime flex items-center justify-center text-brand-dark font-bold text-lg">L</div>
                        </div>
                        <div>
                            <div className="flex items-center gap-1">
                                <span className="font-semibold text-sm text-[#E4E6EB]">LaunchAd</span>
                                <div className="w-[10px] h-[10px] bg-blue-500 rounded-full flex items-center justify-center text-[8px] text-white">✓</div>
                            </div>
                            <div className="flex items-center gap-1 text-[#B0B3B8] text-xs">
                                <span>Sponsored</span>
                                <span aria-hidden="true">·</span>
                                <Globe className="w-3 h-3" />
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 text-[#B0B3B8]">
                        <MoreHorizontal className="w-5 h-5" />
                        <X className="w-5 h-5" />
                    </div>
                </div>

                {/* Ad Copy */}
                <div className="px-3 pb-3 text-[#E4E6EB] text-sm whitespace-pre-line leading-relaxed">
                    Stop wasting hours on manual ad creation. 🛑 <br />
                    Turn any URL into high-converting campaigns in seconds.
                </div>

                {/* Main Media - Shorter Height & Custom "Ad for Ad" Design */}
                <div className="h-48 bg-brand-dark relative flex flex-col items-center justify-center overflow-hidden border-y border-white/5 group-hover:border-brand-lime/30 transition-colors">
                    {/* Background Pattern */}
                    <div className="absolute inset-0 bg-grid-pattern opacity-10" />
                    <div className="absolute inset-0 bg-gradient-to-br from-black/50 to-transparent" />

                    {/* Content: "Ad for the Page" */}
                    <div className="relative z-10 text-center px-6">
                        <div className="inline-block px-2 py-0.5 rounded bg-white/10 text-[10px] font-mono text-brand-lime mb-2 border border-white/5">
                            AI-GENERATED
                        </div>
                        <h3 className="font-display font-bold text-2xl text-white leading-tight mb-3">
                            YOUR ADS <br /> <span className="text-brand-lime">ON AUTOPILOT</span>
                        </h3>
                        <button className="bg-brand-lime text-brand-dark px-4 py-1.5 rounded text-xs font-bold flex items-center gap-1 mx-auto hover:bg-white transition-colors">
                            Try It Free <ArrowRight className="w-3 h-3" />
                        </button>
                    </div>
                </div>

                {/* CTA Bar (Shopify/Plancraft Style) */}
                <div className="bg-[#3A3B3C] p-3 flex items-center justify-between">
                    <div className="flex-1 min-w-0 pr-4">
                        <div className="text-[#B0B3B8] text-xs uppercase tracking-wide truncate">launchad.com</div>
                        <div className="text-[#E4E6EB] font-bold text-sm truncate">Scale your ads with AI</div>
                    </div>
                    <button className="bg-[#4B4C4F] hover:bg-[#5C5D60] text-[#E4E6EB] px-4 py-1.5 rounded-md text-sm font-semibold border border-white/5 transition-colors whitespace-nowrap">
                        Sign Up
                    </button>
                </div>

                {/* Engagement Bar */}
                <div className="p-2 border-t border-white/5 flex items-center justify-between text-[#B0B3B8] text-xs font-medium">
                    <div className="flex items-center gap-1.5 pl-1">
                        <div className="flex -space-x-1">
                            <div className="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center border border-[#242526]"><ThumbsUp className="w-2 h-2 text-white" /></div>
                            <div className="w-4 h-4 rounded-full bg-red-500 flex items-center justify-center border border-[#242526]"><span className="text-[8px] text-white">❤️</span></div>
                        </div>
                        <span>2.4K</span>
                    </div>
                    <div className="flex gap-3 pr-1">
                        <span>458 comments</span>
                        <span>129 shares</span>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="px-2 py-1 flex items-center justify-between border-t border-white/5">
                    <button className="flex-1 py-1.5 flex items-center justify-center gap-2 text-[#B0B3B8] hover:bg-white/5 rounded transition-colors font-semibold text-sm">
                        <ThumbsUp className="w-4 h-4" /> Like
                    </button>
                    <button className="flex-1 py-1.5 flex items-center justify-center gap-2 text-[#B0B3B8] hover:bg-white/5 rounded transition-colors font-semibold text-sm">
                        <MessageCircle className="w-4 h-4" /> Comment
                    </button>
                    <button className="flex-1 py-1.5 flex items-center justify-center gap-2 text-[#B0B3B8] hover:bg-white/5 rounded transition-colors font-semibold text-sm">
                        <Share2 className="w-4 h-4" /> Share
                    </button>
                </div>

            </div>
        </div>
    );
}
