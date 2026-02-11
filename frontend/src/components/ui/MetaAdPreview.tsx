import { useState, useEffect } from 'react';
import { MoreHorizontal, X, Globe, ThumbsUp, MessageCircle, Share2, AlertTriangle, RefreshCw } from 'lucide-react';
import { cn } from '../../lib/cn';
import { Skeleton } from './Skeleton';
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

  const handleRetry = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
    setImageError(false);
    setImageLoaded(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect?.();
    }
  };

  const displayUrl = websiteUrl.replace(/^https?:\/\//, '').replace(/\/$/, '').split('/')[0];

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`Ad: ${ad.headline}${selected ? ' (selected)' : ''}`}
      onClick={onSelect}
      onKeyDown={handleKeyDown}
      className={cn(
        'relative bg-meta-surface text-white rounded-sm overflow-hidden max-w-sm w-full font-sans',
        'shadow-2xl border transition-all duration-200 cursor-pointer',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-lime focus-visible:ring-offset-2 focus-visible:ring-offset-brand-dark',
        selected
          ? 'border-brand-lime scale-[1.02] shadow-[0_0_0_3px_rgba(212,255,49,0.3)]'
          : 'border-white/10 hover:border-white/20'
      )}
    >
      {/* Selection indicator */}
      {selected && (
        <div className="absolute top-3 right-3 z-10 bg-brand-lime text-brand-dark w-7 h-7 flex items-center justify-center text-sm font-bold shadow-lg">
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
              <span className="font-semibold text-sm text-meta-text">{pageName}</span>
              <div className="w-[10px] h-[10px] bg-blue-500 rounded-full flex items-center justify-center text-[8px] text-white">✓</div>
            </div>
            <div className="flex items-center gap-1 text-meta-text-muted text-xs">
              <span>Sponsored</span>
              <span aria-hidden="true">·</span>
              <Globe className="w-3 h-3" />
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4 text-meta-text-muted">
          <MoreHorizontal className="w-5 h-5" />
          <X className="w-5 h-5" />
        </div>
      </div>

      {/* Primary Text */}
      <div className="px-3 pb-3 text-meta-text text-sm whitespace-pre-line leading-relaxed">
        {ad.primaryText}
      </div>

      {/* Image */}
      <div className="relative w-full aspect-square bg-brand-gray overflow-hidden">
        {ad.imageUrl && !imageError ? (
          <img
            src={ad.imageUrl}
            alt={`Ad creative for ${ad.headline}`}
            loading="lazy"
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
            className={cn(
              'absolute inset-0 w-full h-full object-cover transition-opacity duration-300',
              imageLoaded ? 'opacity-100' : 'opacity-0'
            )}
          />
        ) : imageError ? (
          <div className="absolute inset-0 flex items-center justify-center bg-status-error/10">
            <div className="text-center px-4">
              <AlertTriangle className="w-8 h-8 text-status-error mx-auto mb-2" />
              <div className="text-sm text-status-error mb-1">Image failed to load</div>
              <div className="text-xs text-meta-text-muted mb-3">Check your connection and try again</div>
              <button
                onClick={handleRetry}
                className="inline-flex items-center gap-1.5 bg-white/10 text-white px-3 py-1.5 rounded-sm text-xs font-medium hover:bg-white/15 transition-colors"
              >
                <RefreshCw className="w-3 h-3" /> Retry
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

        {/* Loading shimmer */}
        {ad.imageUrl && !imageLoaded && !imageError && (
          <div className="absolute inset-0">
            <Skeleton className="w-full h-full rounded-none" />
          </div>
        )}
      </div>

      {/* CTA Bar */}
      <div className="bg-meta-hover p-3 flex items-center justify-between">
        <div className="flex-1 min-w-0 pr-4">
          <div className="text-meta-text-muted text-xs uppercase tracking-wide truncate">{displayUrl}</div>
          <div className="text-meta-text font-bold text-sm truncate">{ad.headline}</div>
          <div className="text-meta-text-muted text-xs truncate">{ad.description}</div>
        </div>
        <button className="bg-white/10 hover:bg-white/15 text-meta-text px-4 py-1.5 rounded-sm text-sm font-semibold border border-white/5 transition-colors whitespace-nowrap">
          Learn more
        </button>
      </div>

      {/* Engagement */}
      <div className="p-2 border-t border-white/5 flex items-center justify-between text-meta-text-muted text-xs font-medium">
        <div className="flex items-center gap-1.5 pl-1">
          <div className="flex -space-x-1">
            <div className="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center border border-meta-surface">
              <ThumbsUp className="w-2 h-2 text-white" />
            </div>
            <div className="w-4 h-4 rounded-full bg-red-500 flex items-center justify-center border border-meta-surface">
              <span className="text-[8px]">❤️</span>
            </div>
          </div>
          <span>2.4K</span>
        </div>
        <div className="flex gap-3 pr-1">
          <span>458 comments</span>
          <span>129 shares</span>
        </div>
      </div>

      {/* Actions */}
      <div className="px-2 py-1 flex items-center justify-between border-t border-white/5">
        <div className="flex-1 py-1.5 flex items-center justify-center gap-2 text-meta-text-muted font-semibold text-sm">
          <ThumbsUp className="w-4 h-4" /> Like
        </div>
        <div className="flex-1 py-1.5 flex items-center justify-center gap-2 text-meta-text-muted font-semibold text-sm">
          <MessageCircle className="w-4 h-4" /> Comment
        </div>
        <div className="flex-1 py-1.5 flex items-center justify-center gap-2 text-meta-text-muted font-semibold text-sm">
          <Share2 className="w-4 h-4" /> Share
        </div>
      </div>
    </div>
  );
}
