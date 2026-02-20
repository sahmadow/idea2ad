"""Test product showcase — manual image upload with optional text overlay."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.v2.social_templates.product_showcase import (
    ProductShowcaseParams,
    render_product_showcase,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    # Variant 1 — with price overlay
    params = ProductShowcaseParams(
        product_image_url="file:///Users/salehahmadov/Downloads/Gemini%20Generated%20Image.png",
        overlay_text="150,000 AZN",
        overlay_position="bottom-left",
    )
    img = await render_product_showcase(params)
    out = OUTPUT_DIR / "product_showcase_test.png"
    out.write_bytes(img)
    print(f"With price overlay: {out} ({len(img) // 1024}KB)")

    # Variant 2 — raw image, no overlay
    params2 = ProductShowcaseParams(
        product_image_url="file:///Users/salehahmadov/Downloads/Gemini%20Generated%20Image.png",
    )
    img2 = await render_product_showcase(params2)
    out2 = OUTPUT_DIR / "product_showcase_v2.png"
    out2.write_bytes(img2)
    print(f"No overlay: {out2} ({len(img2) // 1024}KB)")


if __name__ == "__main__":
    asyncio.run(main())
