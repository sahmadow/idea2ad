# V2 Creative Engine — Template Editor + Renderer + Content Pipeline

**Overall Progress:** `0%`

## TLDR
Replace Pillow-based renderer (produces unusable ads) with Fabric.js template system: Node.js Puppeteer renderer microservice, Fabric.js canvas editor in frontend, and content pipeline connecting existing scraper/AI to template population. Also fix copy interpolation bugs.

## Critical Decisions
- **Renderer arch**: Separate Node.js microservice (not Python) — Fabric.js is JS-native, Puppeteer gives pixel-perfect screenshots
- **Template storage**: New `AdTemplate` Prisma model stores Fabric.js JSON per ad_type + aspect_ratio
- **Editor approach**: Fabric.js React canvas in frontend — client-side preview only (no renderer calls on every edit, only on final render)
- **Renderer auth**: API key shared via env var `RENDERER_API_KEY` (simple, sufficient for internal service)
- **Seed templates**: Programmatically generated JSON (faster than hand-designing 24 templates)
- **No template versioning** for now — keep scope minimal

## Tasks:

### Phase 1: Renderer Microservice

- [ ] 🟥 **Step 1: Scaffold renderer project**
  - [ ] 🟥 Create `renderer/` directory with package.json, tsconfig.json, railway.toml
  - [ ] 🟥 Install deps: express, fabric, puppeteer, sharp, typescript, tsx

- [ ] 🟥 **Step 2: Implement renderer core**
  - [ ] 🟥 Create `renderer/src/server.ts` — Express app with `/render`, `/render/batch`, `/health`
  - [ ] 🟥 Create `renderer/src/renderer.ts` — Puppeteer + Fabric.js render logic (launch browser, load canvas.html, loadFromJSON, screenshot)
  - [ ] 🟥 Create `renderer/src/optimizer.ts` — Sharp post-processing (strip metadata, optimize PNG/JPEG)
  - [ ] 🟥 Create `renderer/src/templates/canvas.html` — minimal HTML page loading fabric.min.js with `<canvas>`
  - [ ] 🟥 Add API key auth middleware (check `X-API-Key` header)

- [ ] 🟥 **Step 3: Dockerize renderer**
  - [ ] 🟥 Create `renderer/Dockerfile` (Node + Puppeteer Chrome)
  - [ ] 🟥 Create `renderer/railway.toml` deployment config
  - [ ] 🟥 Test locally with hardcoded Fabric.js JSON

### Phase 2: DB + Backend Integration

- [ ] 🟥 **Step 4: Add AdTemplate model**
  - [ ] 🟥 Add `AdTemplate` model to `prisma/schema.prisma` with indexes
  - [ ] 🟥 Run migration

- [ ] 🟥 **Step 5: Backend renderer client**
  - [ ] 🟥 Create `app/services/v2/renderer_client.py` — async HTTP client calling Node.js renderer `/render` and `/render/batch`

- [ ] 🟥 **Step 6: Rewrite static_renderer.py**
  - [ ] 🟥 Replace Pillow logic with: load template JSON from DB → populate `{{variables}}` → call renderer client → return bytes
  - [ ] 🟥 Keep same `StaticAdRenderer` interface so `v2.py` router doesn't break

- [ ] 🟥 **Step 7: Template CRUD endpoints**
  - [ ] 🟥 Add to `app/routers/v2.py`: `GET /v2/templates`, `GET /v2/templates/{ad_type_id}`, `POST /v2/templates`, `PUT /v2/templates/{id}`, `POST /v2/templates/{id}/render`

- [ ] 🟥 **Step 8: Seed templates**
  - [ ] 🟥 Create `app/services/v2/seed_templates/` with Fabric.js JSON files for all 8 static ad types × 3 aspect ratios (24 files)
  - [ ] 🟥 Create seed script to load templates into DB

- [ ] 🟥 **Step 9: Fix copy interpolation bugs**
  - [ ] 🟥 Strip trailing punctuation from `customer_pains[]` before interpolation
  - [ ] 🟥 Lowercase first char of interpolated values when mid-sentence
  - [ ] 🟥 Remove duplicate punctuation after interpolation (`.?` → `?`, `..` → `.`)

### Phase 3: Template Editor Frontend

- [ ] 🟥 **Step 10: Install Fabric.js + scaffolding**
  - [ ] 🟥 `npm install fabric` in frontend
  - [ ] 🟥 Create `frontend/src/components/TemplateEditor/` directory structure

- [ ] 🟥 **Step 11: Core canvas component**
  - [ ] 🟥 Build `FabricCanvas.tsx` — Fabric.js canvas React wrapper (init, sync, JSON export/import)
  - [ ] 🟥 Build `hooks/useFabricCanvas.ts` — Fabric.js lifecycle, object CRUD

- [ ] 🟥 **Step 12: Editor UI components**
  - [ ] 🟥 Build `Toolbar.tsx` — add text, image, shape, undo/redo, zoom
  - [ ] 🟥 Build `PropertiesPanel.tsx` — selected object properties (font, color, size, position)
  - [ ] 🟥 Build `LayersPanel.tsx` — object list, reorder, visibility, lock

- [ ] 🟥 **Step 13: Template gallery + main wrapper**
  - [ ] 🟥 Build `TemplateGallery.tsx` — browse/select seed templates per ad type
  - [ ] 🟥 Build `TemplateEditor.tsx` — main wrapper combining canvas + toolbar + panels

- [ ] 🟥 **Step 14: Variable preview + aspect ratio**
  - [ ] 🟥 Add `{{variable}}` ↔ resolved value preview toggle
  - [ ] 🟥 Add aspect ratio tabs (1:1, 9:16, 1.91:1) saving separate canvas JSON
  - [ ] 🟥 Build `hooks/useTemplateSync.ts` — auto-save, sync with backend

- [ ] 🟥 **Step 15: Integrate into AdPackView**
  - [ ] 🟥 Add "Edit Template" button on each creative card
  - [ ] 🟥 Wire editor open/close flow in AdPackView
  - [ ] 🟥 On save → call backend render → update creative asset_url

### Phase 4: Polish + E2E Test

- [ ] 🟥 **Step 16: Visual QA all templates**
  - [ ] 🟥 Test render quality for all 8 static ad types × 3 ratios
  - [ ] 🟥 Verify copy interpolation fixes with real data (peec.ai test case)

- [ ] 🟥 **Step 17: Full flow test**
  - [ ] 🟥 URL → analyze → edit template → render → S3 upload
  - [ ] 🟥 Verify AdPack renders display correctly in MetaAdPreview

## Env Vars Needed
- `RENDERER_URL` — Node.js renderer URL (e.g. `https://renderer-production.up.railway.app`)
- `RENDERER_API_KEY` — shared secret for renderer auth

## Static Ad Types (8 types, 24 seed templates)
| Ad Type | ID | Strategy |
|---|---|---|
| Product Benefits Static | `product_benefits_static` | product_aware |
| Review Static | `review_static` | product_aware |
| Us vs Them (Solution) | `us_vs_them_solution` | product_aware |
| Organic Static (Solution) | `organic_static_solution` | product_aware |
| Problem Statement Text | `problem_statement_text` | product_unaware |
| Problem Statement Image | `problem_statement_image` | product_unaware |
| Organic Static (Problem) | `organic_static_problem` | product_unaware |
| Us vs Them (Before/After) | `us_vs_them_problem` | product_unaware |

## Files Summary
| Action | Path |
|---|---|
| CREATE | `renderer/` (entire microservice) |
| CREATE | `renderer/src/server.ts` |
| CREATE | `renderer/src/renderer.ts` |
| CREATE | `renderer/src/optimizer.ts` |
| CREATE | `renderer/src/templates/canvas.html` |
| CREATE | `renderer/Dockerfile` |
| CREATE | `renderer/railway.toml` |
| EDIT | `prisma/schema.prisma` — add AdTemplate model |
| CREATE | `app/services/v2/renderer_client.py` |
| REWRITE | `app/services/v2/static_renderer.py` |
| EDIT | `app/routers/v2.py` — add template CRUD endpoints |
| EDIT | `app/services/v2/copy_generator.py` — fix interpolation |
| CREATE | `app/services/v2/seed_templates/` (24 JSON files) |
| CREATE | `frontend/src/components/TemplateEditor/` (7 files) |
| EDIT | `frontend/src/components/AdPackView.tsx` — add Edit button |
| EDIT | `frontend/package.json` — add fabric dep |
