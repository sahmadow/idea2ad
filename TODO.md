# Idea2Ad - New Requirements (04/01/2025)

## Overview
Streamlined UX: URL → AI Analysis → 2 Meta Ad Previews → Select Ad → Launch Page → OAuth + Settings → Publish

---

## Tasks

### Phase 1: UI Restructure
- [x] 1.1 Rename "Strategic Analysis" to "Summary" in App.jsx
- [x] 1.2 Keep Summary + Brand Style + Audience Targeting side-by-side (already done)
- [x] 1.3 Hide/remove Creative Strategy section, Image Briefs section, current Meta Publishing section

### Phase 2: Meta Ad Preview Component
- [x] 2.1 Create MetaAdPreview.jsx component matching example format:
  - Page avatar + name + "Sponsored"
  - Primary text (above image)
  - Generated image (1:1 ratio)
  - URL display + Headline + Description
  - CTA button ("Learn more")
  - Like/Comment/Share footer
- [x] 2.2 Update backend /analyze to auto-generate 2 Imagen images
- [x] 2.3 Display Ad 1 and Ad 2 as selectable cards
- [x] 2.4 Add "Launch My Campaign" button (enabled when ad selected)

### Phase 3: Campaign Launch Page
- [x] 3.1 Create CampaignLaunchPage.jsx component (new view)
- [x] 3.2 Implement Facebook OAuth (Sign in with Facebook)
- [x] 3.3 Fetch and display user's Facebook Pages after OAuth
- [x] 3.4 Add budget input (max budget field)
- [x] 3.5 Add duration selector (default: 3 days)
- [x] 3.6 Add CTA dropdown (default: "Learn More")
- [x] 3.7 Add "Publish Now" button

### Phase 4: Backend Updates
- [x] 4.1 Update /analyze endpoint to generate 2 images automatically
- [x] 4.2 Add /auth/facebook endpoint (OAuth initiation)
- [x] 4.3 Add /auth/facebook/callback endpoint (token exchange)
- [x] 4.4 Add /meta/pages endpoint (list user's FB pages)
- [x] 4.5 Update /meta/publish-campaign to use user's access token

### Phase 5: Testing & Validation
- [x] 5.1 Test analyze with image generation (graceful fallback when GCP not configured)
- [x] 5.2 Backend tests: 30 passed
- [x] 5.3 Frontend tests: 8 passed
- [ ] 5.4 End-to-end browser test (manual)

---

## Answers Applied
1. FB OAuth: Server-side OAuth ✓
2. Image gen: During /analyze ✓
3. FB token: Session-only (in-memory) ✓
4. Budget: Total campaign budget ✓

---

## Files Modified/Created

### Frontend
- `src/App.jsx` - Restructured UI, added ad selection, launch view
- `src/MetaAdPreview.jsx` - NEW: Meta ad preview component
- `src/CampaignLaunchPage.jsx` - NEW: Launch page with OAuth + settings

### Backend
- `app/main.py` - Updated /analyze to generate ads with images
- `app/models.py` - Added Ad model
- `app/routers/facebook.py` - NEW: Facebook OAuth + page management

---

## To Test End-to-End

1. Open http://localhost:5173
2. Enter a URL (e.g., https://stripe.com)
3. Click "Generate Campaign"
4. Wait for analysis + ad generation
5. Select an ad (Ad 1 or Ad 2)
6. Click "Launch My Campaign"
7. Connect Facebook (requires META_APP_ID, META_APP_SECRET in .env)
8. Select a Facebook Page
9. Configure budget/duration/CTA
10. Click "Publish Now"

## Missing for Full E2E
- META_APP_SECRET (for OAuth token exchange)
- GOOGLE_CLOUD_PROJECT + credentials (for Imagen image generation)
- AWS credentials (for S3 image upload)
