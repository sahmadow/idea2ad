/**
 * Toolbar — add objects, undo/redo, zoom controls for the template editor.
 */

import {
  Type,
  Square,
  Undo2,
  Redo2,
  ZoomIn,
  ZoomOut,
  Maximize,
  Trash2,
} from 'lucide-react';

interface ToolbarProps {
  onAddText: () => void;
  onAddRect: () => void;
  onDelete: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onZoomReset: () => void;
  canUndo: boolean;
  canRedo: boolean;
  hasSelection: boolean;
  zoom: number;
}

function ToolBtn({
  onClick,
  disabled,
  title,
  children,
}: {
  onClick: () => void;
  disabled?: boolean;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className="p-2 text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
    >
      {children}
    </button>
  );
}

export function Toolbar({
  onAddText,
  onAddRect,
  onDelete,
  onUndo,
  onRedo,
  onZoomIn,
  onZoomOut,
  onZoomReset,
  canUndo,
  canRedo,
  hasSelection,
  zoom,
}: ToolbarProps) {
  return (
    <div className="flex items-center gap-1 px-3 py-2 bg-brand-dark border-b border-white/10">
      {/* Add objects */}
      <div className="flex items-center gap-1 pr-3 border-r border-white/10">
        <ToolBtn onClick={onAddText} title="Add text">
          <Type className="w-4 h-4" />
        </ToolBtn>
        <ToolBtn onClick={onAddRect} title="Add rectangle">
          <Square className="w-4 h-4" />
        </ToolBtn>
      </div>

      {/* History */}
      <div className="flex items-center gap-1 px-3 border-r border-white/10">
        <ToolBtn onClick={onUndo} disabled={!canUndo} title="Undo">
          <Undo2 className="w-4 h-4" />
        </ToolBtn>
        <ToolBtn onClick={onRedo} disabled={!canRedo} title="Redo">
          <Redo2 className="w-4 h-4" />
        </ToolBtn>
      </div>

      {/* Zoom */}
      <div className="flex items-center gap-1 px-3 border-r border-white/10">
        <ToolBtn onClick={onZoomOut} title="Zoom out">
          <ZoomOut className="w-4 h-4" />
        </ToolBtn>
        <span className="text-xs text-gray-500 font-mono w-12 text-center">
          {Math.round(zoom * 100)}%
        </span>
        <ToolBtn onClick={onZoomIn} title="Zoom in">
          <ZoomIn className="w-4 h-4" />
        </ToolBtn>
        <ToolBtn onClick={onZoomReset} title="Reset zoom">
          <Maximize className="w-4 h-4" />
        </ToolBtn>
      </div>

      {/* Delete */}
      <div className="flex items-center gap-1 px-3">
        <ToolBtn onClick={onDelete} disabled={!hasSelection} title="Delete selected">
          <Trash2 className="w-4 h-4" />
        </ToolBtn>
      </div>
    </div>
  );
}
