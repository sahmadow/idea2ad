"""
Seed Template Generator — programmatically create Fabric.js JSON templates
for all 8 static ad types × 3 aspect ratios (24 templates total).

Each template uses {{variable}} placeholders that get resolved at render time.
Run: python -m app.services.v2.seed_templates.generate
"""

import json
import os
from pathlib import Path

# Canvas sizes per aspect ratio
SIZES = {
    "1:1": (1080, 1080),
    "9:16": (1080, 1920),
    "1.91:1": (1200, 628),
}

ASPECT_RATIOS = list(SIZES.keys())
OUTPUT_DIR = Path(__file__).parent


def _text(text: str, left: int, top: int, width: int, **kwargs) -> dict:
    """Create a Fabric.js text object."""
    return {
        "type": "textbox",
        "text": text,
        "left": left,
        "top": top,
        "width": width,
        "fontFamily": kwargs.get("fontFamily", "Inter"),
        "fontSize": kwargs.get("fontSize", 40),
        "fontWeight": kwargs.get("fontWeight", "normal"),
        "fill": kwargs.get("fill", "#FFFFFF"),
        "textAlign": kwargs.get("textAlign", "left"),
        "lineHeight": kwargs.get("lineHeight", 1.3),
        "selectable": True,
    }


def _rect(left: int, top: int, width: int, height: int, **kwargs) -> dict:
    """Create a Fabric.js rectangle."""
    return {
        "type": "rect",
        "left": left,
        "top": top,
        "width": width,
        "height": height,
        "fill": kwargs.get("fill", "#1A365D"),
        "rx": kwargs.get("rx", 0),
        "ry": kwargs.get("ry", 0),
        "selectable": True,
    }


def _canvas(w: int, h: int, objects: list, bg: str = "#1A365D") -> dict:
    """Build a complete Fabric.js canvas JSON."""
    return {
        "version": "6.5.1",
        "objects": objects,
        "background": bg,
    }


# =====================================================================
# Template builders — one per ad type
# =====================================================================


def product_benefits_static(w: int, h: int) -> dict:
    """Product benefits with value props grid."""
    pad = 60
    objects = [
        # Background
        _rect(0, 0, w, h, fill="{{brand_colors.primary}}"),
        # Headline
        _text("{{product_name}}", pad, pad, w - 2 * pad,
               fontSize=52, fontWeight="bold"),
        # Subheadline
        _text("{{key_benefit}}", pad, pad + 80, w - 2 * pad,
               fontSize=32, fill="#E2E8F0"),
        # Value prop 1
        _text("{{value_props[0]}}", pad, h * 0.35, (w - 3 * pad) // 2,
               fontSize=28, fill="#FFFFFF"),
        # Value prop 2
        _text("{{value_props[1]}}", w // 2 + pad // 2, h * 0.35, (w - 3 * pad) // 2,
               fontSize=28, fill="#FFFFFF"),
        # Value prop 3
        _text("{{value_props[2]}}", pad, h * 0.55, (w - 3 * pad) // 2,
               fontSize=28, fill="#FFFFFF"),
        # CTA badge
        _rect(pad, int(h * 0.82), 220, 56, fill="#FF6B35", rx=28, ry=28),
        _text("{{cta_text}}", pad + 24, int(h * 0.82) + 12, 180,
               fontSize=24, fontWeight="bold", textAlign="center"),
    ]
    return _canvas(w, h, objects, "{{brand_colors.primary}}")


def review_static(w: int, h: int) -> dict:
    """Testimonial/review card."""
    pad = 60
    card_y = int(h * 0.12)
    card_h = int(h * 0.5)
    card_w = w - 2 * pad
    objects = [
        _rect(0, 0, w, h, fill="{{brand_colors.primary}}"),
        # Review card bg
        _rect(pad, card_y, card_w, card_h, fill="#FFFFFF", rx=20, ry=20),
        # Stars
        _text("\u2605\u2605\u2605\u2605\u2605", pad + 24, card_y + 20, card_w - 48,
               fontSize=28, fill="#F59E0B", fontFamily="Inter"),
        # Testimonial text
        _text("{{testimonials[0]}}", pad + 24, card_y + 70, card_w - 48,
               fontSize=26, fill="#1A202C", lineHeight=1.4),
        # Verified badge
        _text("{{verified_purchase_label}}", pad + 24, card_y + card_h - 50, 200,
               fontSize=16, fill="#48BB78"),
        # Product name below card
        _text("{{product_name}}", pad, card_y + card_h + 40, card_w,
               fontSize=36, fontWeight="bold", textAlign="center"),
        # CTA
        _text("{{cta_text}}", pad, int(h * 0.85), card_w,
               fontSize=24, textAlign="center", fill="#E2E8F0"),
    ]
    return _canvas(w, h, objects, "{{brand_colors.primary}}")


def us_vs_them_solution(w: int, h: int) -> dict:
    """Split comparison — solution-focused."""
    mid = w // 2
    pad = 40
    objects = [
        # Left half (problem — dark)
        _rect(0, 0, mid, h, fill="#1A202C"),
        # Right half (solution — brand color)
        _rect(mid, 0, mid, h, fill="{{brand_colors.primary}}"),
        # Divider
        _rect(mid - 1, 0, 2, h, fill="#4A5568"),
        # Left header
        _text("Without", pad, pad, mid - 2 * pad,
               fontSize=20, fill="#A0AEC0", fontWeight="bold"),
        # Left pain point
        _text("{{customer_pains[0]}}", pad, pad + 50, mid - 2 * pad,
               fontSize=28, fill="#E2E8F0"),
        # Right header
        _text("With {{product_name}}", mid + pad, pad, mid - 2 * pad,
               fontSize=20, fill="#E2E8F0", fontWeight="bold"),
        # Right benefit
        _text("{{key_benefit}}", mid + pad, pad + 50, mid - 2 * pad,
               fontSize=28, fill="#FFFFFF"),
        # CTA on right
        _rect(mid + pad, int(h * 0.82), 220, 56, fill="#FF6B35", rx=28, ry=28),
        _text("{{cta_text}}", mid + pad + 24, int(h * 0.82) + 12, 180,
               fontSize=24, fontWeight="bold", textAlign="center"),
    ]
    return _canvas(w, h, objects, "#1A202C")


def organic_static_solution(w: int, h: int) -> dict:
    """Organic-style post — solution angle."""
    pad = 50
    objects = [
        _rect(0, 0, w, h, fill="#FFFFFF"),
        # Card frame
        _rect(20, 20, w - 40, h - 40, fill="#FFFFFF", rx=16, ry=16),
        # Author line
        _text("Real Person  @real_user", pad, 40, w - 2 * pad,
               fontSize=18, fill="#718096"),
        # Hook text (large)
        _text("{{organic_hook}}", pad, 100, w - 2 * pad,
               fontSize=36, fill="#1A202C", fontWeight="bold", lineHeight=1.3),
        # Body — key benefit
        _text("{{key_benefit}}", pad, int(h * 0.45), w - 2 * pad,
               fontSize=24, fill="#4A5568", lineHeight=1.5),
        # Product mention
        _text("Try {{product_name}}", pad, int(h * 0.75), w - 2 * pad,
               fontSize=22, fill="#2D3748", fontWeight="bold"),
        # Engagement stats
        _text("1.2K    328    42", pad, h - 60, w - 2 * pad,
               fontSize=16, fill="#A0AEC0"),
    ]
    return _canvas(w, h, objects, "#F7FAFC")


def problem_statement_text(w: int, h: int) -> dict:
    """Bold problem statement — text-focused."""
    pad = 80
    objects = [
        _rect(0, 0, w, h, fill="#0F172A"),
        # Problem statement (hero text)
        _text("{{problem_hook}}", pad, int(h * 0.15), w - 2 * pad,
               fontSize=56, fontWeight="bold", fill="#FFFFFF", lineHeight=1.2),
        # Supporting pain
        _text("{{customer_pains[0]}}", pad, int(h * 0.55), w - 2 * pad,
               fontSize=28, fill="#94A3B8", lineHeight=1.4),
        # CTA
        _rect(pad, int(h * 0.82), 280, 60, fill="{{brand_colors.primary}}", rx=30, ry=30),
        _text("Learn More", pad + 40, int(h * 0.82) + 14, 200,
               fontSize=24, fontWeight="bold", textAlign="center"),
    ]
    return _canvas(w, h, objects, "#0F172A")


def problem_statement_image(w: int, h: int) -> dict:
    """Problem statement with scene image background."""
    pad = 60
    objects = [
        # Dark overlay rect (scene image would be behind in actual render)
        _rect(0, 0, w, h, fill="rgba(0,0,0,0.55)"),
        # Problem text
        _text("{{problem_hook}}", pad, int(h * 0.2), w - 2 * pad,
               fontSize=48, fontWeight="bold", fill="#FFFFFF", lineHeight=1.2),
        # Pain point
        _text("{{customer_pains[0]}}", pad, int(h * 0.55), w - 2 * pad,
               fontSize=26, fill="#E2E8F0"),
        # CTA
        _rect(pad, int(h * 0.82), 260, 56, fill="#FF6B35", rx=28, ry=28),
        _text("{{cta_text}}", pad + 30, int(h * 0.82) + 12, 200,
               fontSize=24, fontWeight="bold", textAlign="center"),
    ]
    return _canvas(w, h, objects, "#1A202C")


def organic_static_problem(w: int, h: int) -> dict:
    """Organic-style post — problem angle."""
    pad = 50
    objects = [
        _rect(0, 0, w, h, fill="#FFFFFF"),
        _rect(20, 20, w - 40, h - 40, fill="#FFFFFF", rx=16, ry=16),
        # Author
        _text("Everyday User  @user_2025", pad, 40, w - 2 * pad,
               fontSize=18, fill="#718096"),
        # Problem hook
        _text("{{problem_hook}}", pad, 100, w - 2 * pad,
               fontSize=34, fill="#1A202C", fontWeight="bold", lineHeight=1.3),
        # Pain elaboration
        _text("{{customer_pains[0]}}", pad, int(h * 0.4), w - 2 * pad,
               fontSize=22, fill="#4A5568", lineHeight=1.5),
        # Desire
        _text("{{customer_desires[0]}}", pad, int(h * 0.65), w - 2 * pad,
               fontSize=22, fill="#2D3748"),
        # Engagement
        _text("847    128    35", pad, h - 60, w - 2 * pad,
               fontSize=16, fill="#A0AEC0"),
    ]
    return _canvas(w, h, objects, "#F7FAFC")


def us_vs_them_problem(w: int, h: int) -> dict:
    """Before/After comparison — problem angle."""
    mid = w // 2
    pad = 40
    objects = [
        # Before (left — red-ish)
        _rect(0, 0, mid, h, fill="#7F1D1D"),
        # After (right — green)
        _rect(mid, 0, mid, h, fill="#14532D"),
        _rect(mid - 1, 0, 2, h, fill="#374151"),
        # Before header
        _text("BEFORE", pad, pad, mid - 2 * pad,
               fontSize=18, fill="#FCA5A5", fontWeight="bold"),
        # Before pain
        _text("{{customer_pains[0]}}", pad, pad + 50, mid - 2 * pad,
               fontSize=26, fill="#FECACA"),
        # After header
        _text("AFTER", mid + pad, pad, mid - 2 * pad,
               fontSize=18, fill="#86EFAC", fontWeight="bold"),
        # After desire
        _text("{{customer_desires[0]}}", mid + pad, pad + 50, mid - 2 * pad,
               fontSize=26, fill="#D1FAE5"),
        # Product name centered at bottom
        _text("{{product_name}}", 0, int(h * 0.85), w,
               fontSize=28, fontWeight="bold", fill="#FFFFFF", textAlign="center"),
    ]
    return _canvas(w, h, objects, "#1A1A2E")


# Map ad type IDs to builder functions
AD_TYPE_BUILDERS = {
    "product_benefits_static": product_benefits_static,
    "review_static": review_static,
    "us_vs_them_solution": us_vs_them_solution,
    "organic_static_solution": organic_static_solution,
    "problem_statement_text": problem_statement_text,
    "problem_statement_image": problem_statement_image,
    "organic_static_problem": organic_static_problem,
    "us_vs_them_problem": us_vs_them_problem,
}


def generate_all():
    """Generate all 24 template JSON files."""
    count = 0
    for ad_type_id, builder in AD_TYPE_BUILDERS.items():
        for ratio in ASPECT_RATIOS:
            w, h = SIZES[ratio]
            canvas_json = builder(w, h)

            ratio_slug = ratio.replace(":", "x").replace(".", "_")
            filename = f"{ad_type_id}_{ratio_slug}.json"
            filepath = OUTPUT_DIR / filename

            with open(filepath, "w") as f:
                json.dump(canvas_json, f, indent=2)

            count += 1
            print(f"  Generated: {filename}")

    print(f"\nTotal: {count} templates generated in {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_all()
