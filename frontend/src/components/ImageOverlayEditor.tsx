import { useState, useRef } from 'react';
import { Type, MapPin, Download, Loader2, X, Sparkles, ImageIcon } from 'lucide-react';
import { motion } from 'framer-motion';

export interface OverlayEditorResult {
  overlayText: string | null;
  overlayPosition: OverlayPosition;
  description: string | null;
}

interface ImageOverlayEditorProps {
  imageUrl: string;
  initialText?: string;
  initialPosition?: OverlayPosition;
  onRender?: (params: OverlayEditorResult) => Promise<void>;
  onEditImage?: (params: { description: string }) => Promise<string | void>;
  onClose?: () => void;
}

type OverlayPosition = 'bottom-left' | 'bottom-right' | 'top-left' | 'top-right' | 'center';

const POSITIONS: { value: OverlayPosition; label: string }[] = [
  { value: 'bottom-left', label: 'Bottom Left' },
  { value: 'bottom-right', label: 'Bottom Right' },
  { value: 'top-left', label: 'Top Left' },
  { value: 'top-right', label: 'Top Right' },
  { value: 'center', label: 'Center' },
];

const positionStyles: Record<OverlayPosition, React.CSSProperties> = {
  'bottom-left':  { bottom: '3.5%', left: '3.5%' },
  'bottom-right': { bottom: '3.5%', right: '3.5%' },
  'top-left':     { top: '3.5%', left: '3.5%' },
  'top-right':    { top: '3.5%', right: '3.5%' },
  'center':       { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' },
};

export function ImageOverlayEditor({
  imageUrl: initialImageUrl,
  initialText = '',
  initialPosition = 'bottom-left',
  onRender,
  onEditImage,
  onClose,
}: ImageOverlayEditorProps) {
  const [overlayText, setOverlayText] = useState(initialText);
  const [position, setPosition] = useState<OverlayPosition>(initialPosition);
  const [description, setDescription] = useState('');
  const [rendering, setRendering] = useState(false);
  const [editing, setEditing] = useState(false);
  const [currentImageUrl, setCurrentImageUrl] = useState(initialImageUrl);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleEditImage = async () => {
    if (!onEditImage || !description.trim()) return;
    setEditing(true);
    try {
      const newUrl = await onEditImage({ description: description.trim() });
      if (newUrl) {
        setCurrentImageUrl(newUrl);
      }
    } finally {
      setEditing(false);
    }
  };

  const handleRender = async () => {
    if (!onRender) return;
    setRendering(true);
    try {
      await onRender({
        overlayText: overlayText.trim() || null,
        overlayPosition: position,
        description: description.trim() || null,
      });
    } finally {
      setRendering(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col gap-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-mono uppercase tracking-wider text-gray-400">
          Image Editor
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-300 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Live Preview */}
      <div className="relative w-full aspect-square bg-brand-gray overflow-hidden rounded-sm border border-white/10">
        <img
          src={currentImageUrl}
          alt="Creative preview"
          className="absolute inset-0 w-full h-full object-cover"
        />

        {/* Live overlay */}
        {overlayText.trim() && (
          <div
            className="absolute px-4 py-2 bg-black/65 text-white font-extrabold text-lg rounded-md whitespace-nowrap backdrop-blur-sm"
            style={positionStyles[position]}
          >
            {overlayText}
          </div>
        )}

        {/* Editing indicator */}
        {editing && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <div className="flex items-center gap-2 bg-black/80 px-4 py-2 rounded-md">
              <Loader2 className="w-5 h-5 animate-spin text-brand-lime" />
              <span className="text-white text-sm font-medium">AI editing image...</span>
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="space-y-3">
        {/* AI Description / Edit prompt */}
        <div>
          <label className="flex items-center gap-1.5 text-xs text-gray-500 uppercase tracking-wide mb-1.5">
            <Sparkles className="w-3 h-3" /> AI Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder='e.g. "Use this taxi but in Paris background"'
            rows={2}
            className="w-full bg-brand-gray border border-white/20 text-white text-sm p-2.5 focus:border-brand-lime focus:outline-none placeholder:text-gray-600 resize-y min-h-[56px]"
          />
          {onEditImage && description.trim() && (
            <button
              onClick={handleEditImage}
              disabled={editing}
              className="mt-1.5 w-full flex items-center justify-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white font-mono text-xs uppercase tracking-wider disabled:opacity-50 transition-all"
            >
              {editing ? (
                <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Generating...</>
              ) : (
                <><ImageIcon className="w-3.5 h-3.5" /> Generate with AI</>
              )}
            </button>
          )}
        </div>

        {/* Text input */}
        <div>
          <label className="flex items-center gap-1.5 text-xs text-gray-500 uppercase tracking-wide mb-1.5">
            <Type className="w-3 h-3" /> Overlay Text
          </label>
          <input
            ref={inputRef}
            type="text"
            value={overlayText}
            onChange={(e) => setOverlayText(e.target.value)}
            placeholder="e.g. 150,000 AZN"
            className="w-full bg-brand-gray border border-white/20 text-white text-sm p-2.5 focus:border-brand-lime focus:outline-none placeholder:text-gray-600 font-medium"
          />
        </div>

        {/* Position selector */}
        {overlayText.trim() && (
          <div>
            <label className="flex items-center gap-1.5 text-xs text-gray-500 uppercase tracking-wide mb-1.5">
              <MapPin className="w-3 h-3" /> Position
            </label>
            <div className="flex flex-wrap gap-1.5">
              {POSITIONS.map((pos) => (
                <button
                  key={pos.value}
                  onClick={() => setPosition(pos.value)}
                  className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider transition-colors ${
                    position === pos.value
                      ? 'bg-brand-lime text-brand-dark'
                      : 'bg-white/10 text-gray-400 hover:bg-white/15'
                  }`}
                >
                  {pos.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Render button */}
        {onRender && (
          <button
            onClick={handleRender}
            disabled={rendering || editing}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-brand-lime text-brand-dark font-mono text-sm uppercase tracking-wider hover:brightness-110 disabled:opacity-50 transition-all"
          >
            {rendering ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Rendering...</>
            ) : (
              <><Download className="w-4 h-4" /> Render Final Image</>
            )}
          </button>
        )}
      </div>
    </motion.div>
  );
}
