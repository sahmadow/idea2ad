import { useState, useEffect } from 'react';
import { MoreHorizontal, X, Globe, ThumbsUp, MessageCircle, Share2 } from 'lucide-react';
import type { Ad } from '../../api';

interface MetaAdPreviewProps {
  ad: Ad;
  pageName?: string;
  websiteUrl?: string;
  selected?: boolean;
  onSelect?: () => void;
}

export function MetaAdPreview({
  ad,
  pageName = "Your Page",
  websiteUrl = "yourwebsite.com",
  selected = false,
  onSelect,
}: MetaAdPreviewProps) {
  const [imageState, setImageState] = useState({ loaded: false, error: false, url: ad.imageUrl });

  const imageLoaded = imageState.url === ad.imageUrl ? imageState.loaded : false;
  const imageError = imageState.url === ad.imageUrl ? imageState.error : false;

  const setImageLoaded = (loaded: boolean) => setImageState({ loaded, error: false, url: ad.imageUrl });
  const setImageError = (error: boolean) => setImageState({ loaded: false, error, url: ad.imageUrl });

  useEffect(() => {
    if (ad.imageUrl && !imageLoaded && !imageError) {
      const timeout = setTimeout(() => {
        if (!imageLoaded) setImageError(true);
      }, 30000);
      return () => clearTimeout(timeout);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ad.imageUrl, imageLoaded, imageError]);

  const handleRetry = (e: React.MouseEvent) => {
    e.stopPropagation();
    setImageError(false);
    setImageLoaded(false);
  };

  const displayUrl = websiteUrl.replace(/^https?:\/\//, '').replace(/\/$/, '').split('/')[0];

  return (
    <div
      onClick={onSelect}
      className={`
        relative bg-[#242526] text-white rounded-xl overflow-hidden max-w-sm w-full font-sans
        shadow-2xl border transition-all duration-200 cursor-pointer
        ${selected ? 'border-brand-lime scale-[1.02] shadow-[0_0_0_3px_rgba(212,255,49,0.3)]' : 'border-white/5 hover:border-white/20'}
      `}
    >
      {/* Selection indicator */}
      {selected && (
        <div className="absolute top-3 right-3 z-10 bg-brand-lime text-brand-dark rounded-full w-7 h-7 flex items-center justify-center text-sm font-bold shadow-lg">
          ✓
        </div>
      )}

      {/* Header */}
      <div className="p-3 flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-full bg-white p-0.5 overflow-hidden">
            <div className="w-full h-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
              {pageName.charAt(0).toUpperCase()}
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1">
              <span className="font-semibold text-sm text-[#E4E6EB]">{pageName}</span>
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

      {/* Primary Text */}
      <div className="px-3 pb-3 text-[#E4E6EB] text-sm whitespace-pre-line leading-relaxed">
        {ad.primaryText}
      </div>

      {/* Image */}
      <div className="relative w-full aspect-square bg-brand-gray overflow-hidden">
        {ad.imageUrl && !imageError ? (
          <img
            src={ad.imageUrl}
            alt="Ad creative"
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
          />
        ) : imageError ? (
          <div className="absolute inset-0 flex items-center justify-center bg-red-900/30 text-red-300">
            <div className="text-center">
              <div className="text-3xl mb-2">⚠️</div>
              <div className="text-sm mb-3">Image failed to load</div>
              <button
                onClick={handleRetry}
                className="bg-red-500 text-white px-4 py-2 rounded text-sm font-semibold hover:bg-red-600 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-violet-600 to-purple-700 text-white">
            <div className="text-center">
              <div className="text-5xl mb-2">🖼️</div>
              <div className="text-sm opacity-80">Generating image...</div>
            </div>
          </div>
        )}

        {/* Loading overlay */}
        {ad.imageUrl && !imageLoaded && !imageError && (
          <div className="absolute inset-0 flex items-center justify-center bg-brand-gray">
            <div className="w-8 h-8 border-2 border-brand-lime/30 border-t-brand-lime rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* CTA Bar */}
      <div className="bg-[#3A3B3C] p-3 flex items-center justify-between">
        <div className="flex-1 min-w-0 pr-4">
          <div className="text-[#B0B3B8] text-xs uppercase tracking-wide truncate">{displayUrl}</div>
          <div className="text-[#E4E6EB] font-bold text-sm truncate">{ad.headline}</div>
          <div className="text-[#B0B3B8] text-xs truncate">{ad.description}</div>
        </div>
        <button className="bg-[#4B4C4F] hover:bg-[#5C5D60] text-[#E4E6EB] px-4 py-1.5 rounded-md text-sm font-semibold border border-white/5 transition-colors whitespace-nowrap">
          Learn more
        </button>
      </div>

      {/* Engagement Bar */}
      <div className="p-2 border-t border-white/5 flex items-center justify-between text-[#B0B3B8] text-xs font-medium">
        <div className="flex items-center gap-1.5 pl-1">
          <div className="flex -space-x-1">
            <div className="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center border border-[#242526]">
              <ThumbsUp className="w-2 h-2 text-white" />
            </div>
            <div className="w-4 h-4 rounded-full bg-red-500 flex items-center justify-center border border-[#242526]">
              <span className="text-[8px] text-white">❤️</span>
            </div>
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
  );
}
