/**
 * Image optimizer — Sharp-based post-processing.
 * Strips metadata, optimizes file size for PNG/JPEG output.
 */

import sharp from "sharp";

/**
 * Optimize a raw PNG buffer for the target format.
 */
export async function optimizeImage(
  input: Buffer,
  format: "png" | "jpeg" = "png",
  quality: number = 90
): Promise<Buffer> {
  let pipeline = sharp(input).rotate(); // auto-rotate based on EXIF

  if (format === "jpeg") {
    pipeline = pipeline.jpeg({
      quality,
      mozjpeg: true,
      chromaSubsampling: "4:4:4",
    });
  } else {
    pipeline = pipeline.png({
      compressionLevel: 6,
      adaptiveFiltering: true,
    });
  }

  // Strip all metadata
  return pipeline.withMetadata({}).toBuffer();
}
