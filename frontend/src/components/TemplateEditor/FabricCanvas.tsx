/**
 * FabricCanvas — React wrapper for Fabric.js canvas element.
 * Renders the canvas at a scaled-down display size while maintaining
 * the actual canvas dimensions for high-quality export.
 */

import { useRef } from 'react';

interface FabricCanvasProps {
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  width: number;
  height: number;
  displayScale?: number;
}

export function FabricCanvas({
  canvasRef,
  width,
  height,
  displayScale = 0.5,
}: FabricCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Scale the canvas container for display
  const displayWidth = width * displayScale;
  const displayHeight = height * displayScale;

  return (
    <div
      ref={containerRef}
      className="relative bg-[#0a0a0a] border border-white/10 overflow-hidden"
      style={{
        width: displayWidth,
        height: displayHeight,
      }}
    >
      <div
        style={{
          transform: `scale(${displayScale})`,
          transformOrigin: 'top left',
          width,
          height,
        }}
      >
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
}
