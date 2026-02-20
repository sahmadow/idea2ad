"""Test Gemini image editing + product showcase overlay."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.services.v2.image_editor import edit_image_from_file
from app.services.v2.social_templates.product_showcase import (
    ProductShowcaseParams,
    render_product_showcase,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_IMAGE = "/Users/salehahmadov/Downloads/Gemini Generated Image.png"


async def main():
    # Step 1: Edit image with Gemini
    print("Editing image with Gemini...")
    prompt = (
        "Edit this image: Keep the same yellow taxi car but change the background "
        "to Paris, France with the Eiffel Tower visible behind. Keep the taxi "
        "as the main subject in the foreground."
    )
    edited_bytes = await edit_image_from_file(SOURCE_IMAGE, prompt)

    edited_path = OUTPUT_DIR / "taxi_paris_edited.png"
    edited_path.write_bytes(edited_bytes)
    print(f"Edited image saved: {edited_path} ({len(edited_bytes) // 1024}KB)")

    # Step 2: Render with overlay text
    print("Rendering with overlay...")
    params = ProductShowcaseParams(
        product_image_url=f"file://{edited_path}",
        overlay_text="Istanbul Taxi — now in Paris!",
        overlay_position="bottom-left",
    )
    final = await render_product_showcase(params)
    final_path = OUTPUT_DIR / "taxi_paris_final.png"
    final_path.write_bytes(final)
    print(f"Final with overlay: {final_path} ({len(final) // 1024}KB)")

    # Step 3: Also render the edited image without overlay for comparison
    params_clean = ProductShowcaseParams(
        product_image_url=f"file://{edited_path}",
    )
    clean = await render_product_showcase(params_clean)
    clean_path = OUTPUT_DIR / "taxi_paris_clean.png"
    clean_path.write_bytes(clean)
    print(f"Clean (no overlay): {clean_path} ({len(clean) // 1024}KB)")


if __name__ == "__main__":
    asyncio.run(main())
