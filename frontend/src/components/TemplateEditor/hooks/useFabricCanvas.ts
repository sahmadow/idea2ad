/**
 * Fabric.js canvas lifecycle hook.
 * Manages canvas initialization, object selection, JSON import/export.
 */

import { useRef, useState, useCallback, useEffect } from 'react';
import * as fabric from 'fabric';

interface UseFabricCanvasOptions {
  width: number;
  height: number;
  onModified?: (json: object) => void;
}

interface UseFabricCanvasReturn {
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  canvas: fabric.Canvas | null;
  selectedObject: fabric.FabricObject | null;
  // Canvas operations
  loadFromJSON: (json: object) => Promise<void>;
  exportJSON: () => object | null;
  addText: (text?: string) => void;
  addRect: (color?: string) => void;
  deleteSelected: () => void;
  // History
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  // Zoom
  zoomIn: () => void;
  zoomOut: () => void;
  zoomReset: () => void;
  zoom: number;
}

const MAX_HISTORY = 50;

export function useFabricCanvas({
  width,
  height,
  onModified,
}: UseFabricCanvasOptions): UseFabricCanvasReturn {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fabricRef = useRef<fabric.Canvas | null>(null);
  const [selectedObject, setSelectedObject] = useState<fabric.FabricObject | null>(null);
  const [zoom, setZoom] = useState(1);

  // History stacks
  const historyRef = useRef<string[]>([]);
  const historyIndexRef = useRef(-1);
  const isRestoringRef = useRef(false);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);

  const pushHistory = useCallback(() => {
    if (isRestoringRef.current || !fabricRef.current) return;
    const json = JSON.stringify(fabricRef.current.toJSON());
    const idx = historyIndexRef.current;
    // Discard future history if we're not at the end
    historyRef.current = historyRef.current.slice(0, idx + 1);
    historyRef.current.push(json);
    if (historyRef.current.length > MAX_HISTORY) {
      historyRef.current.shift();
    }
    historyIndexRef.current = historyRef.current.length - 1;
    setCanUndo(historyIndexRef.current > 0);
    setCanRedo(false);
  }, []);

  // Initialize canvas
  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = new fabric.Canvas(canvasRef.current, {
      width,
      height,
      preserveObjectStacking: true,
      selection: true,
    });

    canvas.on('selection:created', (e) => {
      setSelectedObject(e.selected?.[0] ?? null);
    });
    canvas.on('selection:updated', (e) => {
      setSelectedObject(e.selected?.[0] ?? null);
    });
    canvas.on('selection:cleared', () => {
      setSelectedObject(null);
    });
    canvas.on('object:modified', () => {
      pushHistory();
      onModified?.(canvas.toJSON());
    });

    fabricRef.current = canvas;
    pushHistory(); // save initial state

    return () => {
      canvas.dispose();
      fabricRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update canvas dimensions when width/height change
  useEffect(() => {
    if (!fabricRef.current) return;
    fabricRef.current.setDimensions({ width, height });
    fabricRef.current.renderAll();
  }, [width, height]);

  const loadFromJSON = useCallback(async (json: object) => {
    const canvas = fabricRef.current;
    if (!canvas) return;
    isRestoringRef.current = true;
    await canvas.loadFromJSON(json);
    canvas.renderAll();
    isRestoringRef.current = false;
    pushHistory();
  }, [pushHistory]);

  const exportJSON = useCallback(() => {
    return fabricRef.current?.toJSON() ?? null;
  }, []);

  const addText = useCallback((text: string = 'New Text') => {
    const canvas = fabricRef.current;
    if (!canvas) return;
    const textbox = new fabric.Textbox(text, {
      left: 100,
      top: 100,
      width: 300,
      fontFamily: 'Inter',
      fontSize: 32,
      fill: '#FFFFFF',
    });
    canvas.add(textbox);
    canvas.setActiveObject(textbox);
    canvas.renderAll();
    pushHistory();
    onModified?.(canvas.toJSON());
  }, [pushHistory, onModified]);

  const addRect = useCallback((color: string = '#3B82F6') => {
    const canvas = fabricRef.current;
    if (!canvas) return;
    const rect = new fabric.Rect({
      left: 100,
      top: 100,
      width: 200,
      height: 100,
      fill: color,
      rx: 8,
      ry: 8,
    });
    canvas.add(rect);
    canvas.setActiveObject(rect);
    canvas.renderAll();
    pushHistory();
    onModified?.(canvas.toJSON());
  }, [pushHistory, onModified]);

  const deleteSelected = useCallback(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;
    const active = canvas.getActiveObjects();
    active.forEach((obj) => canvas.remove(obj));
    canvas.discardActiveObject();
    canvas.renderAll();
    pushHistory();
    onModified?.(canvas.toJSON());
  }, [pushHistory, onModified]);

  const undo = useCallback(() => {
    if (historyIndexRef.current <= 0 || !fabricRef.current) return;
    historyIndexRef.current--;
    isRestoringRef.current = true;
    const json = JSON.parse(historyRef.current[historyIndexRef.current]);
    fabricRef.current.loadFromJSON(json).then(() => {
      fabricRef.current?.renderAll();
      isRestoringRef.current = false;
      setCanUndo(historyIndexRef.current > 0);
      setCanRedo(historyIndexRef.current < historyRef.current.length - 1);
    });
  }, []);

  const redo = useCallback(() => {
    if (historyIndexRef.current >= historyRef.current.length - 1 || !fabricRef.current) return;
    historyIndexRef.current++;
    isRestoringRef.current = true;
    const json = JSON.parse(historyRef.current[historyIndexRef.current]);
    fabricRef.current.loadFromJSON(json).then(() => {
      fabricRef.current?.renderAll();
      isRestoringRef.current = false;
      setCanUndo(historyIndexRef.current > 0);
      setCanRedo(historyIndexRef.current < historyRef.current.length - 1);
    });
  }, []);

  const zoomIn = useCallback(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;
    const newZoom = Math.min(zoom * 1.2, 3);
    canvas.setZoom(newZoom);
    setZoom(newZoom);
  }, [zoom]);

  const zoomOut = useCallback(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;
    const newZoom = Math.max(zoom / 1.2, 0.2);
    canvas.setZoom(newZoom);
    setZoom(newZoom);
  }, [zoom]);

  const zoomReset = useCallback(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;
    canvas.setZoom(1);
    setZoom(1);
  }, []);

  return {
    canvasRef,
    canvas: fabricRef.current,
    selectedObject,
    loadFromJSON,
    exportJSON,
    addText,
    addRect,
    deleteSelected,
    undo,
    redo,
    canUndo,
    canRedo,
    zoomIn,
    zoomOut,
    zoomReset,
    zoom,
  };
}
