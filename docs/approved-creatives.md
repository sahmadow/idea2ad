# Approved Creatives

Statics use **Approach 4**: inline HTML/CSS → Playwright screenshot at 2x DPR. No LLM calls. No external CDN.
Videos use **Remotion**: React compositions → headless Chrome → H.264 MP4. No LLM calls.
UGC avatar videos use **HeyGen**: AI avatar + TTS → MP4 via REST API.

**AI Led (9 types):**

| #   | Creative               | ID                       | Format | Renderer                                   | Business Type | Status |
| --- | ---------------------- | ------------------------ | ------ | ------------------------------------------ | ------------- | ------ |
| 1   | Branded Static         | `branded_static`         | Static | `scripts/ad_approach_comparison.py`         | All           | Active |
| 2   | Organic Static — Reddit | `organic_static_reddit` | Static | `social_templates/reddit_post.py`           | All           | Active |
| 3   | Problem Statement Text | `problem_statement_text` | Static | `social_templates/problem_statement.py`     | All           | Active |
| 4   | Review Static          | `review_static`          | Static | `social_templates/review_static.py`         | All           | Active |
| 4b  | Review Static (Competition) | `review_static_competition` | Static | Reuses `review_static` templates + Gemini LLM copy | All | Active |
| 5   | Service Hero           | `service_hero`           | Static | `social_templates/service_hero.py`          | Service       | Active |
| 6   | Service Hero Video     | `service_hero_video`     | Video  | `remotion/src/compositions/ServiceHero.tsx` | Service       | Active |
| 7   | Branded Static Video   | `branded_static_video`   | Video  | `remotion/src/compositions/BrandedStatic.tsx` | All         | Active |
| 8   | UGC Avatar Video       | `ugc_avatar_video`       | Video  | HeyGen API → `ugc_avatar_renderer.py`         | All         | **OFF** |

**Manual Upload (1 type):**

| #   | Creative             | ID                     | Format | Renderer                         | Business Type | Status |
| --- | -------------------- | ---------------------- | ------ | -------------------------------- | ------------- | ------ |
| 9   | Manual Image Upload  | `manual_image_upload`  | Static | Gemini edit + Playwright overlay | All           | Active |

**Product aware vs unaware** is a copy distinction, not a template distinction. Any template can carry either tone — "Tired of slow ad workflows?" (unaware) or "peec.ai generates ads in 30 seconds" (aware). The copy generator decides awareness level based on funnel stage; templates are visual containers only.

---

## Landing Page Modes

The frontend offers two landing page modes that determine how creatives are generated:

- **AI Led** — User provides a landing page URL. The system scrapes the page, extracts design tokens and copy, then generates creatives #1–#8 automatically. No user-supplied images needed (except Service Hero which uses a scraped/generated scene image).
- **Manual Upload** — User uploads their own product/brand image. The system uses Gemini 2.5 Flash to edit the image (background removal, enhancement) and optionally overlays text via Playwright. Produces creative #9.

---

## 1. Branded Static

**ID:** `branded_static`
**Renderer:** `scripts/ad_approach_comparison.py` (reference), production TBD
**Aspect ratios:** 1:1 (1080x1080)

Scrapes the user's landing page, extracts design tokens (colors, fonts, gradients, button styles), and generates a branded ad that matches their site's visual identity.

**Inputs:**
- Landing page URL (scraped automatically)

**Extracted from scrape:**
- Brand colors (bg, accent, text)
- Font family + weights
- Gradients
- Button styles (bg, color, radius, padding)
- Headline, description

**Visual structure:**
- Accent bar (top)
- Brand name (top-left)
- Headline (centered, large)
- Divider line
- Description text
- CTA button (scraped button style)

**Output:** PNG, ~80-120KB

---

## 2. Organic Static — Reddit

**ID:** `organic_static_reddit`
**Renderer:** `app/services/v2/social_templates/reddit_post.py`
**Aspect ratios:** 1:1 (1080x1080)

Generates a pixel-perfect Reddit post image. Looks like a real Reddit post screenshot — used for organic-looking ad creatives.

**Inputs (`RedditPostParams`):**
| Param | Type | Default |
|-------|------|---------|
| `username` | str | `"reddit_user"` |
| `body` | str | `"This is a sample post"` |
| `subreddit` | str | `"r/technology"` |
| `upvotes` | int | `249` |
| `comments` | int | `57` |
| `avatar_url` | str \| None | Snoo SVG |
| `dark_mode` | bool | `False` |
| `show_awards` | bool | `True` |
| `show_share` | bool | `True` |
| `time_ago` | str | `"2h"` |

**Visual structure:**
- Reddit background (`#DAE0E6` light / `#030303` dark)
- White/dark card with vote sidebar (upvote, count, downvote)
- Meta line: Snoo avatar, subreddit, username, timestamp
- Body text (pre-wrap, multi-paragraph)
- Action bar: Comments, Award, Share (with inline SVG icons)
- 1.5x scale factor for ad readability

**Output:** PNG, ~90-165KB

---

## 3. Problem Statement Text

**ID:** `problem_statement_text`
**Renderer:** `app/services/v2/social_templates/problem_statement.py`
**Aspect ratios:** 1:1 (1080x1080)

Bold, text-only problem statement. No product image, no branding — raw and attention-grabbing. Optional subtext and accent divider.

**Inputs (`ProblemStatementParams`):**
| Param | Type | Default |
|-------|------|---------|
| `headline` | str | `"Your biggest problem"` |
| `subtext` | str \| None | None |
| `bg_color` | str | `"#1A202C"` |
| `bg_gradient` | str \| None | None |
| `text_color` | str | `"#FFFFFF"` |
| `accent_color` | str \| None | None |
| `font_style` | str | `"bold"` |
| `alignment` | str | `"center"` |

**Output:** PNG, ~60-110KB

---

## 4. Review Static

**ID:** `review_static`
**Renderer:** `app/services/v2/social_templates/review_static.py`
**Aspect ratios:** 1:1 (1080x1080)

Review/testimonial card with quote icon, star rating, review text, reviewer info (name, title, avatar initials), and verified badge.

**Inputs (`ReviewStaticParams`):**
| Param | Type | Default |
|-------|------|---------|
| `reviewer_name` | str | `"Sarah K."` |
| `review_text` | str | `"Absolutely love this product..."` |
| `rating` | int | `5` |
| `product_name` | str | `"Product"` |
| `variant` | str | `"card"` |
| `verified` | bool | `True` |
| `reviewer_title` | str \| None | None |
| `avatar_url` | str \| None | Initials circle |
| `dark_mode` | bool | `False` |
| `accent_color` | str | `"#FF6B35"` |

**Output:** PNG, ~100-200KB

---

## 4b. Review Static (Competition)

**ID:** `review_static_competition`
**Renderer:** Reuses `review_static` Fabric.js templates + Gemini LLM for copy
**Aspect ratios:** 1:1 (1080x1080), 9:16 (1080x1920)
**Strategy:** product_aware
**External deps:** `competitor_intelligence`

Same visual layout as Review Static (#4) but with competition-focused copy. The system auto-researches competitor pain points via Gemini and generates "switch to us" messaging. No manual competitor input needed.

**Pipeline:**
1. Template selector picks this type when `has_social_proof()` is true (same gate as #4)
2. `generate_competition_copy()` calls Gemini 2.0 Flash to research competitors
3. LLM returns: `competition_testimonial`, `primary_text`, `headline`, `competitor_complaint`
4. Visual renders using `review_static` seed templates (via `TEMPLATE_FALLBACK_MAP`)
5. The `competition_testimonial` populates the review card's `{{testimonial_text}}`

**Copy style:**
- Primary text leads with competitor frustration, pivots to product as solution
- Headline: "Switch to {product_name}" / "Try {product_name} instead"
- CTA type: `LEARN_MORE`
- Testimonial sounds like a real user who switched from a competitor
- Never names specific competitor brands (uses generic references)

**LLM prompt inputs (from `CreativeParameters`):**
- `product_name`, `product_category`, `key_benefit`, `key_differentiator`, `social_proof`

**Fallback:** If Gemini fails (3 retries with exponential backoff), falls back to template-fill with generic competition copy.

**Key files:**
- `app/services/v2/copy_generator.py` — `generate_competition_copy()` + `_competition_fallback()`
- `app/services/v2/ad_type_registry.py` — `REVIEW_STATIC_COMPETITION` definition
- `app/services/v2/static_renderer.py` — `TEMPLATE_FALLBACK_MAP` for template reuse

**Output:** PNG, ~100-200KB (same as review_static)

---

## 5. Service Hero

**ID:** `service_hero`
**Renderer:** `app/services/v2/social_templates/service_hero.py`
**Aspect ratios:** 1:1 (1080x1080)
**Business Type:** Service

Full-bleed scene photo with headline overlay + gradient scrim. Designed for service businesses (lawyers, consultants, agencies, etc.) where showing people/scenes is key.

**Inputs (`ServiceHeroParams`):**
| Param | Type | Default |
|-------|------|---------|
| `scene_image_url` | str | `""` (required) |
| `headline` | str | `"We fight for you."` |
| `subtext` | str \| None | None |
| `cta_text` | str \| None | None |
| `brand_name` | str \| None | None |
| `text_position` | str | `"bottom"` |
| `overlay_opacity` | float | `0.55` |
| `accent_color` | str | `"#FFFFFF"` |
| `headline_color` | str | `"#FFFFFF"` |
| `subtext_color` | str | `"rgba(255,255,255,0.85)"` |

**Visual structure:**
- Full-bleed scene photo (fetched from URL during render)
- Gradient scrim overlay (direction follows `text_position`)
- Brand name (top-left, uppercase)
- Headline (large, bold, text-shadow)
- Subtext (smaller, semi-transparent)
- CTA button (accent color background)

**Output:** PNG, ~2000-3100KB (photo-heavy)

---

## 6. Service Hero Video

**ID:** `service_hero_video`
**Renderer:** `remotion/src/compositions/ServiceHero.tsx`
**Format:** MP4 (H.264), 1080x1080, 30fps, 8s (240 frames)
**Business Type:** Service

Animated version of Service Hero (#5). Same visual design — full-bleed scene photo, gradient scrim, headline, subtext, CTA — with sequenced motion.

**Animation timeline:**
| Time | Frames | Animation |
|------|--------|-----------|
| 0-1s | 0-30 | Scene photo fades in from black |
| 1-2.3s | 30-70 | Gradient scrim + brand name fade in |
| 3-5s | 90-150 | Headline slides up (spring physics) |
| 5-6.5s | 150-195 | Subtext fades in |
| 6.5-8s | 195-240 | CTA scales in with pulse, hold |

**Inputs (`ServiceHeroProps`):**
| Param | Type | Default |
|-------|------|---------|
| `sceneImageUrl` | string | (required) |
| `headline` | string | `"Your rights.\nOur fight."` |
| `subtext` | string? | undefined |
| `ctaText` | string? | undefined |
| `brandName` | string? | undefined |
| `accentColor` | string? | `"#FFFFFF"` |

**Reusable components:** `FadeIn`, `SlideUp` (in `remotion/src/components/`)

**Output:** MP4, ~1.5MB

**Usage:**
```bash
cd remotion && npm run dev     # Remotion Studio (preview)
cd remotion && npm run render  # Export MP4 → scripts/output/service_hero_video.mp4
```

---

## 7. Branded Static Video

**ID:** `branded_static_video`
**Renderer:** `remotion/src/compositions/BrandedStatic.tsx`
**Format:** MP4 (H.264), 1080x1080, 30fps, 8s (240 frames)
**Business Type:** All

Animated version of Branded Static (#1). Same layout — accent bar, brand name, headline, divider, description, CTA — with sequenced motion.

**Animation timeline:**
| Time | Frames | Animation |
|------|--------|-----------|
| 0-0.5s | 0-15 | Background fades in from black |
| 0.5-1.5s | 15-45 | Accent bar slides in from left |
| 1.5-2.5s | 45-75 | Brand name fades in |
| 2.5-4s | 75-120 | Headline slides up (spring physics) |
| 4-4.5s | 120-135 | Divider expands from center |
| 4.5-5.5s | 135-165 | Description fades in |
| 5.5-7s | 165-210 | CTA scales in (spring physics) |
| 7-8s | 210-240 | Hold |

**Inputs (`BrandedStaticProps`):**
| Param | Type | Default |
|-------|------|---------|
| `brandName` | string | (required) |
| `headline` | string | (required) |
| `description` | string | (required) |
| `ctaText` | string | (required) |
| `bgColor` | string? | `"#0f172a"` |
| `accentColor` | string? | `"#3b82f6"` |
| `textColor` | string? | `"#FFFFFF"` |
| `ctaBgColor` | string? | = accentColor |
| `ctaTextColor` | string? | `"#FFFFFF"` |
| `ctaBorderRadius` | number? | `12` |

**Reusable components:** `FadeIn`, `SlideUp`, `ExpandFromCenter` (in `remotion/src/components/`)

**Output:** MP4, ~1MB

**Usage:**
```bash
cd remotion && npm run dev                      # Remotion Studio (preview)
cd remotion && npx tsx src/render.ts BrandedStatic  # Export single composition
cd remotion && npx tsx src/render.ts                 # Export all compositions
```

---

## 8. UGC Avatar Video (OFF)

**ID:** `ugc_avatar_video`
**Renderer:** HeyGen API → `app/services/v2/ugc_avatar_renderer.py`
**Format:** MP4 (H.264), 1080x1080, ~30s
**Business Type:** All
**Status:** OFF — disabled pending HeyGen cost/quality evaluation

UGC-style avatar video. An AI avatar speaks a generated script directly to camera. Script is assembled from the ad type's frame definitions, with variables resolved from `CreativeParameters`.

**Pipeline:**
1. Copy generator builds script from `frames` templates (~80 words, 30s)
2. `ugc_avatar_renderer.py` submits to HeyGen V2 API
3. Polls for completion (~2-8 min)
4. Downloads MP4, uploads to S3

**Script structure (3 frames):**
| Frame | Duration | Content |
|-------|----------|---------|
| Hook | 5s | Attention-grabbing opener referencing customer pain |
| Pitch | 15s | Product name, key benefit, differentiator, social proof |
| CTA | 10s | Direct call to action |

**Inputs (resolved from `CreativeParameters`):**
- `product_name`, `key_benefit` (required)
- `customer_pains`, `key_differentiator`, `social_proof` (optional, with fallbacks)

**HeyGen config:**
- Avatar: auto-picked stock avatar (default: `Angela-inTshirt-20220820`)
- Voice: auto-picked (default: Sara, natural US English)
- Free tier to start; quota errors surface in UI for user action

**Env vars:**
- `HEYGEN_API_KEY` — required for render (skipped gracefully if missing)

**Output:** MP4, ~2-5MB

---

## Rendering Approaches

### Statics (Approach 4): HTML → Playwright → PNG

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page(
        viewport={"width": 1080, "height": 1080},
        device_scale_factor=2,
    )
    await page.set_content(html, wait_until="load")
    png_bytes = await page.screenshot(
        type="png",
        clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
    )
    await browser.close()
```

**Key constraints:**
- Self-contained HTML — no external resources, no CDN
- System fonts only (platform native stacks)
- All icons as inline SVG
- 2x DPR for retina output (actual image: 2160x2160px)

### Videos: Remotion → Headless Chrome → MP4

```typescript
const bundleLocation = await bundle({ entryPoint: "./src/index.ts" });
const composition = await selectComposition({ serveUrl: bundleLocation, id: "ServiceHero" });
await renderMedia({ composition, serveUrl: bundleLocation, codec: "h264", outputLocation });
```

**Key constraints:**
- Standalone `remotion/` directory with own React/TS toolchain
- System fonts only (same as statics)
- `Img` component for remote image loading
- Reusable animation components (`FadeIn`, `SlideUp`) for future video creatives

### UGC Avatar: HeyGen API → MP4

```python
video_id = await generate_video(script=script, avatar_id=avatar_id, voice_id=voice_id)
status = await poll_video_status(video_id)  # polls every 30s, max 10 min
video_bytes = await download_video(status["video_url"])
```

**Key constraints:**
- Async — render takes 2-8 min, runs in background job
- Free tier has limited credits; quota errors surfaced for UI prompting
- Requires `HEYGEN_API_KEY` env var
- Avatar and voice auto-picked (no user selection)

### Manual Upload: Gemini Edit + Playwright Overlay

```python
# 1. Gemini 2.5 Flash edits user-uploaded image
edited = await image_editor.edit_image(image_bytes, prompt="remove background, enhance")
# 2. Optional text overlay via Playwright
html = build_overlay_html(edited_image_b64, headline, cta_text, colors)
png = await playwright_screenshot(html, width=1080, height=1080)
```

**Key constraints:**
- Requires `GEMINI_API_KEY` env var
- 1 Gemini call for image editing, 0 for render
- Text overlay is optional (user can skip)
- Same Playwright pipeline as statics (2x DPR)

---

## 9. Manual Image Upload

**ID:** `manual_image_upload`
**Renderer:** Gemini 2.5 Flash image edit → Playwright text overlay
**Format:** Static PNG, 1080x1080
**Business Type:** All

User uploads their own product/brand image. Gemini edits the image (background removal, enhancement, style transfer). Optional text overlay (headline, CTA) rendered via Playwright.

**Pipeline:**
1. User uploads image via frontend
2. `image_editor.py` sends to Gemini 2.5 Flash with edit prompt
3. Edited image returned as base64
4. If text overlay requested: `product_showcase.py` builds HTML with image + text
5. Playwright screenshots at 2x DPR → final PNG

**Inputs:**
| Param | Type | Required |
|-------|------|----------|
| `image` | file upload | Yes |
| `edit_prompt` | str | No (default: enhance) |
| `headline` | str | No |
| `cta_text` | str | No |
| `bg_color` | str | No |
| `accent_color` | str | No |

**Key files:**
- `app/services/v2/image_editor.py` — Gemini image editing wrapper
- `app/services/v2/social_templates/product_showcase.py` — text overlay HTML builder

**Output:** PNG, ~100-300KB
