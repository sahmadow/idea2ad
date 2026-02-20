"""Test service hero template with lawyer example."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.v2.social_templates.service_hero import (
    ServiceHeroParams,
    render_service_hero,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    # Lawyer ad — courtroom/defense scene
    params = ServiceHeroParams(
        scene_image_url="https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1200&h=1200&fit=crop",
        headline="Your rights.\nOur fight.",
        subtext="Experienced criminal defense attorneys with a 94% case success rate. Available 24/7.",
        cta_text="Free Consultation",
        brand_name="Morrison & Associates",
        text_position="bottom",
        overlay_opacity=0.6,
        accent_color="#FFFFFF",
    )
    img = await render_service_hero(params)
    out = OUTPUT_DIR / "service_hero_lawyer.png"
    out.write_bytes(img)
    print(f"Lawyer: {out} ({len(img) // 1024}KB)")

    # Variant — center text
    params2 = ServiceHeroParams(
        scene_image_url="https://images.unsplash.com/photo-1521791055366-0d553872125f?w=1200&h=1200&fit=crop",
        headline="Justice doesn't\nwait. Neither do we.",
        subtext="Over 2,000 cases won. Defending clients across all 50 states.",
        cta_text="Call Now",
        brand_name="Sterling Law Group",
        text_position="center",
        overlay_opacity=0.65,
        accent_color="#C9A84C",
    )
    img2 = await render_service_hero(params2)
    out2 = OUTPUT_DIR / "service_hero_lawyer_v2.png"
    out2.write_bytes(img2)
    print(f"Lawyer v2: {out2} ({len(img2) // 1024}KB)")


if __name__ == "__main__":
    asyncio.run(main())
