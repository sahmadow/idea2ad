"""
Test script for new ad generation logic.
Does NOT modify production files.

Usage: python scripts/test_new_ad_gen.py [--generate-image]
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai

# Config
TEST_URL = "https://journeylauncher.com"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GENERATE_IMAGE = "--generate-image" in sys.argv

# Initialize Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")


async def scrape_page(url: str) -> dict:
    """Scrape page content and extract CTA color."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass

        # Extract page content
        content = await page.evaluate("""() => {
            const getText = (el) => el?.innerText?.trim() || '';
            return {
                title: document.title,
                h1: getText(document.querySelector('h1')),
                h2s: Array.from(document.querySelectorAll('h2')).map(el => getText(el)).slice(0, 5),
                paragraphs: Array.from(document.querySelectorAll('p')).map(el => getText(el)).filter(t => t.length > 20).slice(0, 10),
                metaDesc: document.querySelector('meta[name="description"]')?.content || '',
            }
        }""")

        # Extract CTA button color - comprehensive detection
        cta_color = await page.evaluate("""() => {
            const result = { color: null, source: null };

            // 1. Check CSS custom properties first (most reliable)
            const root = document.documentElement;
            const rootStyles = getComputedStyle(root);

            const cssVarNames = [
                '--accent', '--brand', '--primary', '--cta',
                '--color-primary', '--color-accent', '--primary-color',
                '--btn-primary-bg', '--button-color'
            ];

            for (const varName of cssVarNames) {
                const val = rootStyles.getPropertyValue(varName).trim();
                if (val && val.startsWith('#')) {
                    result.color = val;
                    result.source = 'css-var:' + varName;
                    return result;
                }
            }

            // 2. Check .btn-primary gradient/background for dominant color
            const btnPrimary = document.querySelector('.btn-primary, .btn.btn-primary, [class*="btn-primary"]');
            if (btnPrimary) {
                const style = getComputedStyle(btnPrimary);

                // Check for gradient - extract first color
                const bgImage = style.backgroundImage;
                if (bgImage && bgImage.includes('gradient')) {
                    // Extract rgba values from gradient
                    const rgbaMatch = bgImage.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/g);
                    if (rgbaMatch && rgbaMatch.length > 0) {
                        // Use the first color in gradient (usually the brand color)
                        const match = rgbaMatch[0].match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
                        if (match) {
                            const [_, r, g, b] = match;
                            // Convert to full opacity hex
                            const hex = '#' + [r, g, b].map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
                            result.color = hex;
                            result.source = 'gradient';
                            return result;
                        }
                    }
                }

                // Check border color (often matches brand)
                const borderColor = style.borderColor;
                if (borderColor && borderColor !== 'rgba(0, 0, 0, 0)') {
                    const match = borderColor.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
                    if (match) {
                        const [_, r, g, b] = match;
                        const hex = '#' + [r, g, b].map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
                        if (hex !== '#000000' && hex !== '#ffffff') {
                            result.color = hex;
                            result.source = 'border';
                            return result;
                        }
                    }
                }
            }

            // 3. Look for accent-colored elements (pulse indicators, highlights)
            const accentSelectors = ['.pulse', '.accent', '[class*="accent"]', '.highlight'];
            for (const sel of accentSelectors) {
                const el = document.querySelector(sel);
                if (el) {
                    const bg = getComputedStyle(el).backgroundColor;
                    if (bg && bg !== 'rgba(0, 0, 0, 0)' && !bg.includes('255, 255, 255')) {
                        result.color = bg;
                        result.source = 'accent-element';
                        return result;
                    }
                }
            }

            // 4. Fallback: scan for prominent non-neutral colors
            const allElements = document.querySelectorAll('a, button, span, div');
            for (const el of allElements) {
                const style = getComputedStyle(el);
                const bg = style.backgroundColor;

                if (bg && bg !== 'rgba(0, 0, 0, 0)') {
                    const match = bg.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
                    if (match) {
                        const [_, r, g, b] = match.map(Number);
                        // Skip near-white, near-black, and grays
                        const isGray = Math.abs(r - g) < 20 && Math.abs(g - b) < 20;
                        const isNearWhite = r > 230 && g > 230 && b > 230;
                        const isNearBlack = r < 30 && g < 30 && b < 30;

                        if (!isGray && !isNearWhite && !isNearBlack) {
                            result.color = bg;
                            result.source = 'fallback';
                            return result;
                        }
                    }
                }
            }

            return result;
        }""")

        # Extract brand colors from CSS
        brand_colors = await page.evaluate("""() => {
            const colors = [];
            // Check CSS custom properties
            const root = document.documentElement;
            const style = getComputedStyle(root);

            // Common CSS variable names for brand colors
            const varNames = ['--primary', '--brand', '--accent', '--main-color', '--primary-color'];
            for (const name of varNames) {
                const val = style.getPropertyValue(name);
                if (val) colors.push(val.trim());
            }

            return colors;
        }""")

        await browser.close()

        # Extract color from result object
        detected_color = cta_color.get('color') if isinstance(cta_color, dict) else cta_color
        color_source = cta_color.get('source') if isinstance(cta_color, dict) else 'unknown'

        return {
            "content": content,
            "cta_color": detected_color,
            "cta_source": color_source,
            "brand_colors": brand_colors,
            "url": url
        }


def rgb_to_hex(rgb_string: str) -> str:
    """Convert rgb(r, g, b) to #RRGGBB."""
    if not rgb_string:
        return "#4F46E5"  # Default indigo

    if rgb_string.startswith("#"):
        return rgb_string

    import re
    match = re.search(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', rgb_string)
    if match:
        r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return f"#{r:02x}{g:02x}{b:02x}"

    return "#4F46E5"


async def generate_ad_copy(page_data: dict) -> dict:
    """Generate ad copy using Ad Summary Generator structure."""

    content = page_data["content"]

    prompt = f"""Analyze this landing page and create a Facebook ad following this EXACT structure.

LANDING PAGE CONTENT:
Title: {content['title']}
Headline: {content['h1']}
Subheadlines: {json.dumps(content['h2s'])}
Key paragraphs: {json.dumps(content['paragraphs'][:5])}
Meta description: {content['metaDesc']}

EXTRACT FIRST:
* What it does, who it's for, what pain it solves, what outcome it delivers, proof points, how it works

THEN WRITE AD COPY WITH THIS STRUCTURE:

1. Hook: First-person result statement with specific number. "I [achieved X] from [method] I [unexpected twist]."
2. Pattern interrupt: What WASN'T required. "No X. No Y. Just Z."
3. Pain mirror: "I was drowning." + 3 specific pressures your audience feels daily.
4. Dismiss old way: Why traditional solutions don't work for busy people.
5. Solution intro: Product name + one sentence on what it does.
6. Simple mechanism: "I [minimal input]. It [handles everything]."
7. Benefits stack: 5-6 checkmarks covering time, effort, status, automation, quality.
8. Depth contrast: Compare meaningful engagement vs. shallow alternative.
9. Competitive fear: "Your competitors are doing this. Your ideal clients are listening. Will they hear you or someone else?"
10. CTA: 👉 Action + benefit + now

Return JSON:
{{
    "product_name": "...",
    "target_audience": "...",
    "main_pain_point": "...",
    "key_outcome": "...",
    "ad_copy": "full ad copy here with all 10 sections",
    "hook_headline": "5-8 word headline for image",
    "secondary_line": "short follow-up line"
}}"""

    result = model.generate_content(prompt)
    text = result.text

    # Extract JSON
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    return json.loads(text)


async def generate_image_prompt(ad_copy: dict, cta_color: str) -> str:
    """Generate Ideogram prompt using Ad Visual structure."""

    cta_hex = rgb_to_hex(cta_color)

    # Extract CTA text from ad copy
    ad_text = ad_copy.get('ad_copy', '')
    cta_button_text = "Get Started Now"
    for line in ad_text.split('\n'):
        if '👉' in line:
            # Extract short CTA (3-4 words max)
            words = line.replace('👉', '').strip().split()[:4]
            cta_button_text = ' '.join(words)
            break

    prompt = f"""Create an image prompt for a Facebook ad.

PRODUCT: {ad_copy['product_name']}
TARGET: {ad_copy['target_audience']}

IMAGE STRUCTURE:
"[Person matching target demographic] in [environment representing outcome], [activity/pose showing success], professional but approachable aesthetic, [relevant props in background].

Text overlay at top: '{ad_copy['hook_headline']}' in bold white sans-serif 48px on semi-transparent dark bar.
Below: '{ad_copy['secondary_line']}' in italic 29px.
Bottom strip: CTA button '{cta_button_text}' in 24px bold white text on solid {cta_hex} banner."

Return ONLY the image prompt. Be specific and vivid about the person and scene."""

    result = model.generate_content(prompt)
    return result.text.strip()


async def generate_image(prompt: str) -> Tuple[str, bytes]:
    """Generate image using Vertex AI Imagen (production system)."""
    try:
        from app.services.image_gen import get_image_generator
        from app.services.s3 import get_s3_service

        generator = get_image_generator()
        print("   Generating with Vertex AI Imagen...")
        image_bytes = await generator.generate_image(prompt=prompt, aspect_ratio="1:1")

        # Upload to S3
        print("   Uploading base image to S3...")
        s3 = get_s3_service()
        result = s3.upload_image(image_bytes, "test_new_ad")
        return result["url"], image_bytes

    except Exception as e:
        print(f"   ⚠️  Image generation failed: {e}")
        return None, None


async def render_ad_with_template(
    headline: str,
    secondary: str,
    cta_text: str,
    cta_color: str,
    primary_color: str = "#1a1a2e"
) -> bytes:
    """Render ad using production HTML template method."""
    from app.services.template_renderer import get_template_renderer

    renderer = get_template_renderer()

    # Build brand CSS matching production
    brand_css = {
        "font_faces": [],
        "css_variables": {},
        "primary_colors": [primary_color],
        "secondary_colors": [cta_color],
        "font_families": ["Inter"],
        "button_styles": {
            "backgroundColor": cta_color,
            "color": "#FFFFFF",
            "borderRadius": "12px"
        }
    }

    # Build context for template
    context = {
        "font_faces": brand_css.get("font_faces", []),
        "css_variables": brand_css.get("css_variables", {}),
        "primary_color": primary_color,
        "accent_color": cta_color,
        "text_color": "#FFFFFF",
        "gradient": None,
        "font_family": "Inter",
        "button_styles": brand_css.get("button_styles", {}),
        "border_radius": "12px",
        "headline": headline,
        "subheadline": secondary,
        "cta_text": cta_text,
        "logo_url": None,
        "text_overlays": [],
        "pain_point": None,
        "product_image_url": None,
    }

    # Render using production template
    image_bytes = await renderer.render_template(
        template_name="product_focused.html",
        context=context,
        dimensions=(1080, 1080)
    )

    return image_bytes


async def main():
    print(f"\n{'='*60}")
    print(f"Testing New Ad Generation Logic")
    print(f"URL: {TEST_URL}")
    print(f"{'='*60}\n")

    # Step 1: Scrape
    print("📄 Scraping landing page...")
    page_data = await scrape_page(TEST_URL)
    print(f"   Title: {page_data['content']['title']}")
    print(f"   H1: {page_data['content']['h1']}")
    print(f"   CTA Color: {page_data['cta_color']} (from {page_data.get('cta_source', 'unknown')})")

    cta_hex = rgb_to_hex(page_data['cta_color'])
    print(f"   CTA Hex: {cta_hex}")

    # Step 2: Generate ad copy
    print("\n✍️  Generating ad copy...")
    ad_copy = await generate_ad_copy(page_data)
    print(f"   Product: {ad_copy['product_name']}")
    print(f"   Target: {ad_copy['target_audience']}")
    print(f"   Headline: {ad_copy['hook_headline']}")
    print(f"   Secondary: {ad_copy['secondary_line']}")

    # Step 3: Generate image prompt
    print("\n🎨 Generating image prompt...")
    image_prompt = await generate_image_prompt(ad_copy, page_data['cta_color'])
    print(f"   Prompt: {image_prompt[:200]}...")

    # Step 4: Generate image (optional)
    image_url = None
    final_image_url = None
    if GENERATE_IMAGE:
        print("\n🖼️  Generating image (this takes ~30s)...")
        image_url, image_bytes = await generate_image(image_prompt)
        if image_url and image_bytes:
            print(f"   Base Image URL: {image_url}")

            # Step 5: Render with HTML template (production method)
            print("\n✨ Rendering with HTML template...")
            print(f"   Headline (72px): {ad_copy['hook_headline']}")
            print(f"   Secondary (32px): {ad_copy['secondary_line']}")

            # Extract CTA text
            cta_text = "Get Started Now"
            for line in ad_copy['ad_copy'].split('\n'):
                if '👉' in line:
                    words = line.replace('👉', '').strip().split()[:4]
                    cta_text = ' '.join(words)
                    break
            print(f"   CTA (28px): {cta_text}")
            print(f"   CTA Color: {cta_hex}")

            composited_bytes = await render_ad_with_template(
                headline=ad_copy['hook_headline'],
                secondary=ad_copy['secondary_line'],
                cta_text=cta_text,
                cta_color=cta_hex
            )

            # Upload composited image
            print("   Uploading final image to S3...")
            from app.services.s3 import get_s3_service
            s3 = get_s3_service()
            result = s3.upload_image(composited_bytes, "test_new_ad_final")
            final_image_url = result["url"]
            print(f"   Final Image URL: {final_image_url}")
    else:
        print("\n🖼️  Image generation skipped (use --generate-image to enable)")

    # Output results
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")

    print("\n📝 AD COPY:")
    print("-" * 40)
    print(ad_copy['ad_copy'])

    print("\n🖼️  IMAGE PROMPT:")
    print("-" * 40)
    print(image_prompt)
    print(f"\nCTA Color Used: {cta_hex}")
    if image_url:
        print(f"Base Image URL: {image_url}")
    if final_image_url:
        print(f"Final Image (with text): {final_image_url}")

    # Save results to file
    results = {
        "url": TEST_URL,
        "cta_color": cta_hex,
        "ad_copy": ad_copy,
        "image_prompt": image_prompt,
        "base_image_url": image_url,
        "final_image_url": final_image_url
    }

    output_path = Path(__file__).parent / "test_output.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Full results saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
