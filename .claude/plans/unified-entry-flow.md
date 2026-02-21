# Unified Entry Flow

**Overall Progress:** `100%`

## TLDR
Replace the 3-tab input (AI Led/Quick Mode + SaaS/Service) with a single unified 4-step flow: input → upload & extras → editable review (logo, product summary, targeting, budget) → CONFIRM → generation. Backend auto-classifies which pipeline to use. No image editing feature.

## Critical Decisions
- **Two-step backend**: New `POST /v2/prepare` extracts params + targeting WITHOUT generating creatives. New `POST /v2/generate` takes confirmed params and runs creative pipeline.
- **Auto-classification**: URL provided → AI Led (scrape + full templates). Text only → Quick mode (Gemini copy + image gen). `business_type` auto-detected by LLM, no user tabs.
- **No image editing**: Users can edit copy, targeting, budget — NOT visuals. Remove Gemini edit_prompt feature.
- **4-page flow**: `/` (input) → `/upload` (image + competitors, optional) → `/review` (confirm params) → `/adpack` (creatives).
- **Session storage**: In-memory dict with 30min TTL for PreparedCampaign (sufficient for MVP).
- **Back navigation**: Preserve state when going back (keep input + uploads in context).

## Flow Diagram

```
Page 1: /
  [Single Input: URL or describe your idea]
  → "Continue"

Page 2: /upload
  [Optional product image upload]
  [Optional competitor URLs]
  → "Analyze" (calls POST /v2/prepare, shows loading)

Page 3: /review
  [Brand logo (or placeholder) + product name]
  [Product summary — editable]
  [Targeting: age, geo, gender — editable]
  [Budget & duration — editable]
  → "CONFIRM" (calls POST /v2/generate, shows loading)

Page 4: /adpack
  [Creative grid — edit copy only, no visual editing]
  [Select for publish → /publish]
```

## Tasks:

- [x] 🟩 **Step 1: Backend — Pydantic schemas**
  - [x] 🟩 `PrepareRequest`: url?, description?, image_url?, competitor_urls?
  - [x] 🟩 `PreparedCampaign` response: session_id, product_name, product_summary, brand_logo_url?, targeting, budget_daily, duration_days, language, business_type, target_countries
  - [x] 🟩 `GenerateRequest`: session_id, targeting overrides, budget/duration overrides, product_summary override

- [x] 🟩 **Step 2: Backend — `POST /v2/prepare` endpoint**
  - [x] 🟩 Accepts PrepareRequest
  - [x] 🟩 If URL: scrape page, extract CreativeParameters (language, geo, business_type, brand_logo, etc.)
  - [x] 🟩 If description only: Gemini call to extract product_name, category, business_type, key_benefit, pains from freeform text
  - [x] 🟩 Build suggested targeting from params
  - [x] 🟩 Generate product_summary (1-2 sentence description for review page)
  - [x] 🟩 Store full CreativeParameters + scraped_data in memory cache (keyed by session_id, 30min TTL)
  - [x] 🟩 Return PreparedCampaign (lightweight summary for frontend)

- [x] 🟩 **Step 3: Backend — `POST /v2/generate` endpoint**
  - [x] 🟩 Accepts GenerateRequest (session_id + user overrides)
  - [x] 🟩 Retrieve cached CreativeParameters + scraped_data
  - [x] 🟩 Apply user overrides (targeting, budget, duration, product_summary)
  - [x] 🟩 Run existing pipeline: translate_params → template select → copy gen → render → AdPack
  - [x] 🟩 Return AdPack (same shape as current /v2/analyze response)

- [x] 🟩 **Step 4: Frontend — Unified Landing Page (`/`)**
  - [x] 🟩 Remove SegmentedControl (AI Led / Quick Mode toggle)
  - [x] 🟩 Remove business type tabs (SaaS / Service)
  - [x] 🟩 Single input: large text field — "Enter your product URL or describe your idea"
  - [x] 🟩 Auto-detect URL vs freeform text
  - [x] 🟩 "Continue" button → navigate to `/upload`

- [x] 🟩 **Step 5: Frontend — Upload & Extras Page (`/upload`)**
  - [x] 🟩 New route + component
  - [x] 🟩 Product image upload (optional, skip button)
  - [x] 🟩 Competitor URLs input (optional, expandable)
  - [x] 🟩 "Analyze" button → calls `POST /v2/prepare` → loading spinner → navigate to `/review`
  - [x] 🟩 Back button → `/` with preserved input

- [x] 🟩 **Step 6: Frontend — Review & Confirm Page (`/review`)**
  - [x] 🟩 New route + component `ReviewPage.tsx`
  - [x] 🟩 Header: brand logo (or placeholder) + product name
  - [x] 🟩 Product summary (editable textarea)
  - [x] 🟩 Targeting: age range, countries, gender — editable inputs
  - [x] 🟩 Budget & duration inputs
  - [x] 🟩 "CONFIRM" button → calls `POST /v2/generate` → loading screen → `/adpack`
  - [x] 🟩 Back button → `/upload` with preserved state

- [x] 🟩 **Step 7: Frontend — Simplify AdPackView**
  - [x] 🟩 Remove targeting summary section (confirmed on /review)
  - [x] 🟩 Remove budget/duration controls (confirmed on /review)
  - [x] 🟩 Remove image editing UI (edit_prompt field, ImageOverlayEditor)
  - [x] 🟩 Keep: creative grid, filters, expand/edit modal (copy only), select for publish
  - [x] 🟩 Compact read-only summary of confirmed targeting + budget at top

- [x] 🟩 **Step 8: Frontend — AppContext + API layer**
  - [x] 🟩 Add `preparedCampaign` state to AppContext
  - [x] 🟩 New API: `prepareCampaign()`, `generateFromPrepared()`
  - [x] 🟩 Remove `generationMode`, `businessType`, `editPrompt` from context
  - [x] 🟩 Add `/upload` and `/review` routes to AppRoutes.tsx
  - [x] 🟩 Preserve input + upload state across page navigation (context, not localStorage)

- [x] 🟩 **Step 9: Cleanup**
  - [x] 🟩 Remove edit_prompt / ImageOverlayEditor references
  - [x] 🟩 Remove Quick Mode endpoint references from frontend
  - [x] 🟩 Clean up unused localStorage keys
  - [x] 🟩 Verify `npm run build` passes

## Client Feedback Refinements (Post-MVP)

- [x] 🟩 **Step 10: Backend — Enhance PreparedCampaign schema**
  - [x] 🟩 Remove `targeting`, `budget_daily_cents`, `duration_days` from PreparedCampaign
  - [x] 🟩 Add `target_audience`, `main_pain_point`, `messaging_aware`, `messaging_unaware`
  - [x] 🟩 Add `competitors: list[CompetitorInsight]` (name + weakness, max 3)
  - [x] 🟩 Remove `competitor_urls` from PrepareRequest
  - [x] 🟩 Simplify GenerateRequest (remove targeting/budget, add competitor edits)

- [x] 🟩 **Step 11: Backend — Auto-detect competitors in /v2/prepare**
  - [x] 🟩 Add competitor auto-detection via REVIEW_ANALYSIS_PROMPT (URL path) + DESCRIPTION_EXTRACTION_PROMPT
  - [x] 🟩 Extract target_audience, main_pain_point, messaging for aware/unaware users
  - [x] 🟩 Return competitors with weaknesses in PreparedCampaign

- [x] 🟩 **Step 12: Frontend — Update types + API**
  - [x] 🟩 Update PreparedCampaign TS type (remove targeting/budget, add new fields)
  - [x] 🟩 Update GenerateParams (remove targeting/budget overrides, add competitors)

- [x] 🟩 **Step 13: Frontend — Redesign ReviewPage**
  - [x] 🟩 Remove targeting section
  - [x] 🟩 Remove budget & duration section
  - [x] 🟩 Enhance product summary display (target audience, pain point, messaging)
  - [x] 🟩 Add Competitive Landscape section (edit/delete, max 3, no add)

- [x] 🟩 **Step 14: Frontend — Simplify UploadPage**
  - [x] 🟩 Remove CompetitorInput component
  - [x] 🟩 Update AppContext (remove competitor state from analysis)

- [x] 🟩 **Step 15: Verify build**
  - [x] 🟩 `npm run build` passes

## Complexity: MEDIUM
