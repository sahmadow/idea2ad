# Ad Concept Replica — Approach

**Status:** OFF (validated manually, not wired into pipeline)

## What It Does

Takes a **reference ad image** (any brand's ad) + a **target URL** and produces N variations that replicate the reference ad's visual concept but adapted for the target brand.

The reference ad's visual structure (layout, typography pattern, accent effects, spacing) is preserved. The target brand's identity (logo, colors, font, product messaging) is injected.

## Inputs

| Input | Description |
|-------|-------------|
| **Reference ad image** | PNG/JPG of any brand's ad creative (e.g. a Framer ad, a Notion ad, a Linear ad) |
| **Target URL** | Landing page of the brand to adapt the concept for |
| **Num variations** | How many variations to produce (default: 3) |
| **Aspect ratio** | 1:1, 4:5, 9:16 (default: 1:1) |

## Pipeline

### Step 1: Analyze Reference Ad (Vision → Concept Descriptor)

Extract visual structure from the reference image into a **concept descriptor** — a structured JSON that fully describes the ad's layout, content zones, typography, and effects so the downstream steps can reproduce any visual pattern.

**Concept descriptor schema:**

```json
{
  "category": "stacked-typography | testimonial-card | product-showcase | hero-image | split-layout | gradient-text | quote-card | comparison | ...",
  "layout": {
    "orientation": "vertical | horizontal | split-left | split-right | centered | grid",
    "zones": [
      {
        "id": "zone_id",
        "type": "logo | headline | subheadline | body | cta | image | quote | attribution | decorative | badge | product-image | avatar | rating",
        "position": { "anchor": "top-left | top-center | center | bottom-right | ..." },
        "size": { "width": "percentage or px", "height": "percentage or px" }
      }
    ]
  },
  "typography": {
    "headline": { "weight": 800, "size": "6rem", "transform": "uppercase | none", "letterSpacing": "tight | normal | wide" },
    "body": { "weight": 400, "size": "1rem" },
    "cta": { "weight": 600, "size": "1.1rem", "style": "button | link | pill" }
  },
  "textStructure": {
    "pattern": "stacked-words | headline-body-cta | quote-attribution | headline-subheadline | bullet-list | comparison-columns | single-statement | ...",
    "slots": [
      { "role": "headline", "constraints": "2 stacked single-word verbs" },
      { "role": "tagline", "constraints": "short sentence, under 8 words" }
    ]
  },
  "colors": {
    "background": "#hex",
    "foreground": "#hex",
    "accent": "#hex"
  },
  "effects": [
    { "type": "colored-box | glow | gradient-text | comet-trail | blur | shadow | border | underline | highlight | particle | ...", "target": "zone_id or element", "params": {} }
  ],
  "decorativeElements": [
    { "type": "icon | streak | gradient-blob | grid-pattern | dots | divider | badge | star-rating | ...", "position": "..." }
  ]
}
```

**Implementation options:**
- **Manual** (current): Human describes the visual structure
- **Vision LLM** (future): Gemini/Claude vision analyzes the image and outputs the concept descriptor JSON
- **Hybrid** (recommended first step): Vision LLM proposes descriptor, human reviews/adjusts

### Step 2: Scrape Target Brand

Extract brand tokens from the target URL (reuses existing scraper):

- **Logo**: Favicon SVG or inline logo SVG from page source
- **Brand colors**: Primary, accent, background (from CSS/meta tags)
- **Font family**: Primary font from CSS
- **Product info**: What the product does, key action verbs
- **Tagline**: From meta description or hero section

### Step 3: Generate Copy Variations

For each variation, generate copy that **matches the text structure defined in the concept descriptor**:

- Read `textStructure.slots` to understand what text elements are needed (headline, body, CTA, quote, word pairs, attribution, bullet points, etc.)
- Respect each slot's constraints (word count, tone, format)
- Adapt content to the target brand's product and messaging

**Examples by concept category:**

| Category | Slots | Example output |
|----------|-------|----------------|
| Stacked typography | 2 action verbs + tagline | "Describe / Advertise" + "From idea to ad." |
| Testimonial card | quote + author + role + rating | "Saved us 10 hours/week" + "Jane D." + "Head of Growth" + ★★★★★ |
| Product showcase | headline + feature bullets + CTA | "Ship faster" + ["One-click deploy", "Auto-scaling"] + "Start free" |
| Hero image | headline + subheadline | "The future of design" + "Create without limits" |
| Split layout | left headline + right body + CTA | "Why us?" + "We automate X so you can Y." + "Learn more" |
| Gradient text | single bold statement | "Build something beautiful." |

**Implementation options:**
- **Manual** (current): Human writes copy per slot
- **LLM** (future): Gemini generates N copy sets given product context + slot constraints from the descriptor

### Step 4: Build HTML Variations

For each variation, generate a self-contained HTML file **driven by the concept descriptor**:

1. **Read the descriptor** — layout zones, typography rules, effects, decorative elements
2. **Map zones to HTML elements** — each zone becomes a positioned `<div>` with styles derived from the descriptor
3. **Inject brand tokens** — target brand's logo, colors, and font replace the reference brand's
4. **Fill text slots** — variation-specific copy placed into the correct zones
5. **Apply effects** — accent effects from the descriptor adapted to the target brand's color palette
6. All inline CSS, no external dependencies

The HTML generator is **not a fixed template** — it reads the descriptor and constructs the appropriate structure for any concept category.

### Step 5: Render via Playwright

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page(
        viewport={"width": 1080, "height": 1080},
        device_scale_factor=2,
    )
    await page.set_content(html, wait_until="networkidle")
    await page.wait_for_timeout(2000)  # font loading
    png = await page.screenshot(type="png", clip={...})
```

## Example Concept Descriptors

### Stacked Typography (e.g. Framer "Design / Publish")

```json
{
  "category": "stacked-typography",
  "layout": {
    "orientation": "vertical",
    "zones": [
      { "id": "logo", "type": "logo", "position": { "anchor": "top-left" } },
      { "id": "words", "type": "headline", "position": { "anchor": "center" }, "size": { "width": "90%", "height": "50%" } },
      { "id": "tagline", "type": "subheadline", "position": { "anchor": "bottom-center" } }
    ]
  },
  "typography": { "headline": { "weight": 900, "size": "8rem", "transform": "none", "letterSpacing": "tight" } },
  "textStructure": {
    "pattern": "stacked-words",
    "slots": [
      { "role": "headline", "constraints": "2 stacked single-word action verbs" },
      { "role": "tagline", "constraints": "short sentence, under 8 words" }
    ]
  },
  "colors": { "background": "#0a0a0a", "foreground": "#ffffff", "accent": "#6c5ce7" },
  "effects": [{ "type": "colored-box", "target": "headline-letter-2", "params": { "color": "accent" } }],
  "decorativeElements": [{ "type": "streak", "position": "behind-headline" }]
}
```

### Testimonial Card (e.g. customer quote ad)

```json
{
  "category": "testimonial-card",
  "layout": {
    "orientation": "centered",
    "zones": [
      { "id": "logo", "type": "logo", "position": { "anchor": "top-left" } },
      { "id": "quote", "type": "quote", "position": { "anchor": "center" }, "size": { "width": "80%", "height": "40%" } },
      { "id": "avatar", "type": "avatar", "position": { "anchor": "below-quote-left" } },
      { "id": "author", "type": "attribution", "position": { "anchor": "below-quote-right" } },
      { "id": "stars", "type": "rating", "position": { "anchor": "above-quote-center" } },
      { "id": "cta", "type": "cta", "position": { "anchor": "bottom-center" } }
    ]
  },
  "typography": {
    "headline": { "weight": 500, "size": "1.8rem", "transform": "none", "letterSpacing": "normal" },
    "body": { "weight": 400, "size": "0.9rem" },
    "cta": { "weight": 600, "size": "1rem", "style": "pill" }
  },
  "textStructure": {
    "pattern": "quote-attribution",
    "slots": [
      { "role": "quote", "constraints": "1-2 sentences, first-person, specific result" },
      { "role": "author", "constraints": "full name" },
      { "role": "role", "constraints": "job title + company" },
      { "role": "cta", "constraints": "2-3 words, action verb" }
    ]
  },
  "colors": { "background": "#ffffff", "foreground": "#1a1a1a", "accent": "#4f46e5" },
  "effects": [{ "type": "shadow", "target": "card", "params": { "blur": "20px", "opacity": 0.1 } }],
  "decorativeElements": [{ "type": "star-rating", "position": "above-quote" }]
}
```

### Product Showcase (e.g. feature highlight ad)

```json
{
  "category": "product-showcase",
  "layout": {
    "orientation": "split-left",
    "zones": [
      { "id": "logo", "type": "logo", "position": { "anchor": "top-left" } },
      { "id": "headline", "type": "headline", "position": { "anchor": "left-top" }, "size": { "width": "45%", "height": "20%" } },
      { "id": "features", "type": "body", "position": { "anchor": "left-center" }, "size": { "width": "45%", "height": "30%" } },
      { "id": "cta", "type": "cta", "position": { "anchor": "left-bottom" } },
      { "id": "product-img", "type": "product-image", "position": { "anchor": "right-center" }, "size": { "width": "50%", "height": "80%" } }
    ]
  },
  "typography": {
    "headline": { "weight": 800, "size": "2.5rem", "transform": "none", "letterSpacing": "tight" },
    "body": { "weight": 400, "size": "1rem" },
    "cta": { "weight": 600, "size": "1.1rem", "style": "button" }
  },
  "textStructure": {
    "pattern": "headline-body-cta",
    "slots": [
      { "role": "headline", "constraints": "3-5 words, benefit-driven" },
      { "role": "features", "constraints": "2-4 bullet points, each under 6 words" },
      { "role": "cta", "constraints": "2-3 words, action verb" }
    ]
  },
  "colors": { "background": "#f8fafc", "foreground": "#0f172a", "accent": "#2563eb" },
  "effects": [{ "type": "gradient-text", "target": "headline", "params": { "from": "accent", "to": "#7c3aed" } }],
  "decorativeElements": [{ "type": "gradient-blob", "position": "behind-product-image" }]
}
```

## Proof of Concept

**Reference ad:** Framer "Design / Publish" ad (dark bg, giant stacked verbs, colored letter box, rocket/comet effect, bottom tagline)

**Target brand:** LaunchAd (launchad.io) — AI-powered ad campaign platform

**Extracted brand tokens:**
- Logo: Blue `#38BDF8` rounded square with bold "L" in Space Grotesk
- Brand color: `#38BDF8` (electric sky blue), dark variant `#0EA5E9`
- Font: Space Grotesk
- Background: `#0a0a0a`

**3 Variations produced:**

| # | Words | Accent Effect | Tagline | File |
|---|-------|---------------|---------|------|
| V1 | Describe / Advertise | Blue streak + sparkle | "From idea to ad. Powered by AI." | `launchad_v1_describe_advertise` |
| V2 | Paste / Publish | Comet trail + clipboard icon | "Drop a URL. Get ads instantly." | `launchad_v2_paste_publish` |
| V3 | Brief / Launch | Rocket trail + lightning | "AI-powered ad campaigns in seconds." | `launchad_v3_brief_launch` |

**Files:** `scripts/output/launchad_v{1,2,3}_*.html` (editable) + `.png` (rendered)

Also produced 3 Framer-branded versions as intermediate reference: `scripts/output/framer_v{1,2,3}_*.html` + `.png`

## Cost Estimate

| Step | Cost | Notes |
|------|------|-------|
| Vision analysis | TBD | Free if manual; ~$0.01 if Gemini vision |
| Brand scraping | $0 | Existing Playwright scraper |
| Copy generation | TBD | Free if manual; ~$0.001 if Gemini Flash |
| HTML generation | $0 | Descriptor-driven code, no API |
| Playwright render | $0 | Local compute only |
| **Total per 3 variations** | **~$0 - $0.02** | |

## Future Automation Path

To integrate into the pipeline:

1. **Vision descriptor endpoint**: POST reference image → returns concept descriptor JSON via Gemini vision
2. **Concept adapter**: Takes concept descriptor + brand tokens → generates HTML variations for any category
3. **New ad type in registry**: `ad_concept_replica` with `reference_image` + `target_url` inputs
4. **UI**: Upload reference ad → select target campaign → generate variations
5. **Template library**: Save successful concept descriptors as reusable templates (category-tagged, searchable)

## Open Questions

- Vision LLM accuracy: can it reliably extract concept descriptors from arbitrary ads?
- Effect recreation: some effects (3D, photography, complex illustrations) can't be replicated in CSS alone
- Legal: is recreating another brand's ad concept for a different brand acceptable?
- Quality gate: how to validate output quality before serving to users?
- Descriptor coverage: is the schema flexible enough for edge-case layouts (asymmetric, overlapping zones)?
