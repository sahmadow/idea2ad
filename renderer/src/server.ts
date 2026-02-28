/**
 * Renderer microservice — Express server exposing /render, /render/batch, /health.
 * Accepts Fabric.js JSON canvas definitions and returns rendered PNG/JPEG images.
 */

import express from "express";
import { renderCanvas, renderBatch, warmup } from "./renderer.js";
import { optimizeImage } from "./optimizer.js";
import { warmupBundle, renderVideo } from "./video-renderer.js";

const app = express();
const PORT = parseInt(process.env.PORT || "3100", 10);
const API_KEY = process.env.RENDERER_API_KEY || "";

// Parse JSON bodies up to 10MB (canvas JSON can be large with embedded images)
app.use(express.json({ limit: "10mb" }));

// --- Auth middleware ---
function authMiddleware(
  req: express.Request,
  res: express.Response,
  next: express.NextFunction
): void {
  if (!API_KEY) {
    // No key configured — allow in dev
    next();
    return;
  }
  const provided = req.headers["x-api-key"];
  if (provided !== API_KEY) {
    res.status(401).json({ error: "Invalid or missing API key" });
    return;
  }
  next();
}

// Apply auth to render endpoints
app.use("/render", authMiddleware);

// --- Health check (no auth) ---
app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "idea2ad-renderer" });
});

// --- Single render ---
interface RenderBody {
  canvas_json: object;
  width?: number;
  height?: number;
  format?: "png" | "jpeg";
  quality?: number;
}

app.post("/render", async (req, res) => {
  const body = req.body as RenderBody;

  if (!body.canvas_json) {
    res.status(400).json({ error: "canvas_json is required" });
    return;
  }

  const width = body.width || 1080;
  const height = body.height || 1080;
  const format = body.format || "png";
  const quality = body.quality || 90;

  try {
    const raw = await renderCanvas(body.canvas_json, width, height);
    const optimized = await optimizeImage(raw, format, quality);

    res.set("Content-Type", format === "png" ? "image/png" : "image/jpeg");
    res.set("X-Render-Width", String(width));
    res.set("X-Render-Height", String(height));
    res.send(optimized);
  } catch (err) {
    console.error("[render] Failed:", err);
    res.status(500).json({ error: "Render failed", detail: String(err) });
  }
});

// --- Batch render ---
interface BatchItem {
  id: string;
  canvas_json: object;
  width?: number;
  height?: number;
  format?: "png" | "jpeg";
  quality?: number;
}

interface BatchBody {
  items: BatchItem[];
}

app.post("/render/batch", async (req, res) => {
  const body = req.body as BatchBody;

  if (!body.items?.length) {
    res.status(400).json({ error: "items array is required" });
    return;
  }

  if (body.items.length > 24) {
    res.status(400).json({ error: "Max 24 items per batch" });
    return;
  }

  try {
    const results = await renderBatch(body.items);

    // Return as JSON with base64-encoded images
    const output = results.map((r) => ({
      id: r.id,
      success: r.success,
      image_base64: r.image ? r.image.toString("base64") : null,
      format: r.format,
      error: r.error || null,
    }));

    res.json({ results: output });
  } catch (err) {
    console.error("[render/batch] Failed:", err);
    res.status(500).json({ error: "Batch render failed", detail: String(err) });
  }
});

// --- Video render ---
interface VideoRenderBody {
  composition_id: string;
  input_props: Record<string, unknown>;
  codec?: "h264" | "h265";
}

app.post("/render/video", async (req, res) => {
  const body = req.body as VideoRenderBody;

  if (!body.composition_id) {
    res.status(400).json({ error: "composition_id is required" });
    return;
  }
  if (!body.input_props || typeof body.input_props !== "object") {
    res.status(400).json({ error: "input_props object is required" });
    return;
  }

  try {
    const videoBuffer = await renderVideo({
      compositionId: body.composition_id,
      inputProps: body.input_props,
      codec: body.codec,
    });

    res.json({
      success: true,
      video_base64: videoBuffer.toString("base64"),
      size_bytes: videoBuffer.length,
      composition_id: body.composition_id,
      format: "mp4",
    });
  } catch (err) {
    console.error("[render/video] Failed:", err);
    res.status(500).json({
      success: false,
      error: "Video render failed",
      detail: String(err),
    });
  }
});

// --- Start ---
app.listen(PORT, async () => {
  console.log(`[renderer] Listening on port ${PORT}`);
  try {
    await warmup();
    console.log("[renderer] Puppeteer warmed up");
  } catch (err) {
    console.error("[renderer] Warmup failed:", err);
  }
  // Warmup Remotion bundle in background (non-blocking)
  warmupBundle().catch((err) => {
    console.error("[renderer] Remotion bundle warmup failed:", err);
  });
});
