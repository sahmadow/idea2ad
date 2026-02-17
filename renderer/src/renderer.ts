/**
 * Renderer core — Puppeteer + Fabric.js canvas rendering.
 *
 * Launches a headless Chrome instance, loads a minimal HTML page with Fabric.js,
 * injects the canvas JSON, and captures a screenshot.
 */

import puppeteer, { type Browser, type Page } from "puppeteer";
import path from "path";
import { fileURLToPath } from "url";
import { optimizeImage } from "./optimizer.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CANVAS_HTML = path.resolve(__dirname, "templates", "canvas.html");

let browser: Browser | null = null;

// Pool of reusable pages for performance
const pagePool: Page[] = [];
const MAX_POOL_SIZE = 4;

async function getBrowser(): Promise<Browser> {
  if (!browser || !browser.connected) {
    browser = await puppeteer.launch({
      headless: true,
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--font-render-hinting=none",
      ],
    });
  }
  return browser;
}

async function getPage(): Promise<Page> {
  if (pagePool.length > 0) {
    return pagePool.pop()!;
  }
  const b = await getBrowser();
  const page = await b.newPage();
  await page.goto(`file://${CANVAS_HTML}`, { waitUntil: "domcontentloaded" });
  return page;
}

function returnPage(page: Page): void {
  if (pagePool.length < MAX_POOL_SIZE) {
    pagePool.push(page);
  } else {
    page.close().catch(() => {});
  }
}

/**
 * Render a single Fabric.js canvas JSON to PNG bytes.
 */
export async function renderCanvas(
  canvasJson: object,
  width: number,
  height: number
): Promise<Buffer> {
  const page = await getPage();
  try {
    // Set viewport to match canvas dimensions
    await page.setViewport({ width, height, deviceScaleFactor: 2 });

    // Inject canvas JSON and render via Fabric.js
    const screenshot = await page.evaluate(
      async (json: string, w: number, h: number) => {
        // @ts-expect-error - fabric is loaded globally in canvas.html
        const canvas = window.__fabricCanvas;
        if (!canvas) throw new Error("Fabric canvas not initialized");

        canvas.setWidth(w);
        canvas.setHeight(h);
        canvas.clear();

        // Load from JSON
        await new Promise<void>((resolve, reject) => {
          canvas.loadFromJSON(json, () => {
            canvas.renderAll();
            resolve();
          });
        });

        // Export as data URL
        return canvas.toDataURL({
          format: "png",
          multiplier: 1,
          quality: 1,
        });
      },
      JSON.stringify(canvasJson),
      width,
      height
    );

    // Convert data URL to Buffer
    const base64 = (screenshot as string).replace(
      /^data:image\/\w+;base64,/,
      ""
    );
    return Buffer.from(base64, "base64");
  } finally {
    returnPage(page);
  }
}

/**
 * Render a batch of canvases. Returns results in same order as input.
 */
export interface BatchInput {
  id: string;
  canvas_json: object;
  width?: number;
  height?: number;
  format?: "png" | "jpeg";
  quality?: number;
}

export interface BatchResult {
  id: string;
  success: boolean;
  image?: Buffer;
  format: string;
  error?: string;
}

export async function renderBatch(items: BatchInput[]): Promise<BatchResult[]> {
  // Process sequentially to avoid overloading the browser
  const results: BatchResult[] = [];

  for (const item of items) {
    const w = item.width || 1080;
    const h = item.height || 1080;
    const fmt = item.format || "png";
    const q = item.quality || 90;

    try {
      const raw = await renderCanvas(item.canvas_json, w, h);
      const optimized = await optimizeImage(raw, fmt, q);
      results.push({
        id: item.id,
        success: true,
        image: optimized,
        format: fmt,
      });
    } catch (err) {
      results.push({
        id: item.id,
        success: false,
        format: fmt,
        error: String(err),
      });
    }
  }

  return results;
}

/**
 * Pre-launch browser and prime a page for faster first render.
 */
export async function warmup(): Promise<void> {
  const page = await getPage();
  returnPage(page);
}
