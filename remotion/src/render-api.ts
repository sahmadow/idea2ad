/**
 * CLI entry point for rendering a single Remotion composition to MP4.
 *
 * Usage:
 *   npx tsx src/render-api.ts <compositionId> <propsJsonFile> <outputPath>
 *
 * Example:
 *   npx tsx src/render-api.ts BrandedStatic /tmp/props.json /tmp/out.mp4
 */

import path from "path";
import fs from "fs";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

async function main() {
  const [compositionId, propsJsonFile, outputPath] = process.argv.slice(2);

  if (!compositionId || !propsJsonFile || !outputPath) {
    console.error(
      "Usage: npx tsx src/render-api.ts <compositionId> <propsJsonFile> <outputPath>"
    );
    process.exit(1);
  }

  // Read props from JSON file
  if (!fs.existsSync(propsJsonFile)) {
    console.error(`Props file not found: ${propsJsonFile}`);
    process.exit(1);
  }
  const inputProps = JSON.parse(fs.readFileSync(propsJsonFile, "utf-8"));

  // Ensure output directory exists
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Bundle the Remotion project
  console.log(`Bundling Remotion project...`);
  const bundleLocation = await bundle({
    entryPoint: path.resolve(__dirname, "./index.ts"),
    webpackOverride: (config) => config,
  });

  // Select composition
  console.log(`Selecting composition "${compositionId}"...`);
  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: compositionId,
    inputProps,
  });

  // Render to MP4
  console.log(
    `Rendering ${composition.durationInFrames} frames at ${composition.fps}fps...`
  );
  await renderMedia({
    composition,
    serveUrl: bundleLocation,
    codec: "h264",
    outputLocation: outputPath,
    inputProps,
  });

  console.log(`Done! Output: ${outputPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
