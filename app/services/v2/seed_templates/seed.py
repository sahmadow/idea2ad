"""
Seed Script — load generated Fabric.js JSON templates into the AdTemplate table.

Run: python -m app.services.v2.seed_templates.seed
"""

import asyncio
import json
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent

# Display names for ad types
AD_TYPE_NAMES = {
    "product_benefits_static": "Product Benefits Static",
    "review_static": "Review Static",
    "us_vs_them_solution": "Us vs Them (Solution)",
    "organic_static_solution": "Organic Static (Solution)",
    "problem_statement_text": "Problem Statement Text",
    "problem_statement_image": "Problem Statement Image",
    "organic_static_problem": "Organic Static (Problem)",
    "us_vs_them_problem": "Us vs Them (Before/After)",
}


async def seed_templates():
    """Load all JSON template files into DB."""
    from prisma import Prisma

    db = Prisma()
    await db.connect()

    json_files = sorted(TEMPLATE_DIR.glob("*.json"))
    if not json_files:
        print("No template JSON files found. Run generate.py first.")
        return

    created = 0
    skipped = 0

    for filepath in json_files:
        # Parse filename: {ad_type_id}_{ratio_slug}.json
        stem = filepath.stem  # e.g. "product_benefits_static_1x1"
        # Find ratio slug at end
        for ratio, slug in [("1:1", "1x1"), ("9:16", "9x16"), ("1.91:1", "1_91x1")]:
            if stem.endswith(f"_{slug}"):
                ad_type_id = stem[: -(len(slug) + 1)]
                aspect_ratio = ratio
                break
        else:
            print(f"  Skipping unrecognized file: {filepath.name}")
            continue

        name = AD_TYPE_NAMES.get(ad_type_id, ad_type_id)
        ratio_label = {"1:1": "Square", "9:16": "Story", "1.91:1": "Landscape"}
        full_name = f"{name} — {ratio_label.get(aspect_ratio, aspect_ratio)}"

        with open(filepath) as f:
            canvas_json = json.load(f)

        # Upsert: check if exists first
        existing = await db.adtemplate.find_first(
            where={
                "ad_type_id": ad_type_id,
                "aspect_ratio": aspect_ratio,
                "is_default": True,
            }
        )

        if existing:
            await db.adtemplate.update(
                where={"id": existing.id},
                data={"canvas_json": json.dumps(canvas_json), "name": full_name},
            )
            skipped += 1
            print(f"  Updated: {full_name}")
        else:
            await db.adtemplate.create(
                data={
                    "ad_type_id": ad_type_id,
                    "aspect_ratio": aspect_ratio,
                    "name": full_name,
                    "canvas_json": json.dumps(canvas_json),
                    "is_default": True,
                }
            )
            created += 1
            print(f"  Created: {full_name}")

    await db.disconnect()
    print(f"\nDone: {created} created, {skipped} updated")


if __name__ == "__main__":
    asyncio.run(seed_templates())
