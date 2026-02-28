/**
 * Video Renderer — Remotion bundle + render logic.
 *
 * Pre-bundles the Remotion project on startup via webpack, then renders
 * individual compositions to MP4 on demand.
 */

import path from "path";
import fs from "fs/promises";
import os from "os";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

const ALLOWED_COMPOSITIONS = new Set(["BrandedStatic", "ServiceHero"]);

// Remotion entry point — source TSX, bundled by Remotion's webpack (not tsc).
// Resolves to src/remotion/index.ts whether running from src/ (dev) or dist/ (prod).
const ENTRY_POINT = path.resolve(
  import.meta.dirname,
  "..",
  "src",
  "remotion",
  "index.ts",
);

let bundlePath: string | null = null;
let bundlePromise: Promise<string> | null = null;

/**
 * Pre-bundle Remotion project via webpack. Call once on startup.
 * Subsequent calls return cached bundle path.
 */
export async function warmupBundle(): Promise<void> {
  if (bundlePath) return;
  if (bundlePromise) {
    await bundlePromise;
    return;
  }

  console.log("[video-renderer] Bundling Remotion project...");
  const start = Date.now();

  bundlePromise = bundle({
    entryPoint: ENTRY_POINT,
    onProgress: (pct: number) => {
      if (pct % 25 === 0) {
        console.log(`[video-renderer] Bundle progress: ${pct}%`);
      }
    },
  });

  bundlePath = await bundlePromise;
  console.log(
    `[video-renderer] Bundle ready in ${Date.now() - start}ms: ${bundlePath}`,
  );
}

interface RenderVideoOptions {
  compositionId: string;
  inputProps: Record<string, unknown>;
  codec?: "h264" | "h265";
}

/**
 * Render a Remotion composition to MP4 and return the video bytes.
 */
export async function renderVideo({
  compositionId,
  inputProps,
  codec = "h264",
}: RenderVideoOptions): Promise<Buffer> {
  if (!ALLOWED_COMPOSITIONS.has(compositionId)) {
    throw new Error(
      `Unknown composition: ${compositionId}. Allowed: ${[...ALLOWED_COMPOSITIONS].join(", ")}`,
    );
  }

  if (!bundlePath) {
    await warmupBundle();
  }

  const outputPath = path.join(
    os.tmpdir(),
    `remotion-${compositionId}-${Date.now()}.mp4`,
  );

  try {
    const composition = await selectComposition({
      serveUrl: bundlePath!,
      id: compositionId,
      inputProps,
    });

    console.log(
      `[video-renderer] Rendering ${compositionId} (${composition.durationInFrames} frames @ ${composition.fps}fps)`,
    );
    const start = Date.now();

    await renderMedia({
      composition,
      serveUrl: bundlePath!,
      codec,
      outputLocation: outputPath,
      inputProps,
    });

    const videoBytes = await fs.readFile(outputPath);
    console.log(
      `[video-renderer] Render complete: ${compositionId} (${videoBytes.length} bytes, ${Date.now() - start}ms)`,
    );

    return Buffer.from(videoBytes);
  } finally {
    // Cleanup temp file
    try {
      await fs.unlink(outputPath);
    } catch {
      // ignore cleanup errors
    }
  }
}
