# LaunchAd - Requirements & Tasks

## Overview
Streamlined UX: URL → AI Analysis → 2 Meta Ad Previews → Select Ad → Launch Page → OAuth + Settings → Publish

Domain: **launchad.io**

---

## Phase 6: LaunchAd.io Deployment (01/06/2025)

### 6.1 Branding Updates
- [x] Update privacy-policy.html (Journeylauncher → LaunchAd, email → info@launchad.io)
- [x] Update terms-of-service.html (Journeylauncher → LaunchAd, email → info@launchad.io)
- [x] Rename Idea2Ad → LaunchAd in App.jsx
- [x] Update index.html title → "LaunchAd - AI-Powered Ad Campaigns"
- [x] Update backend API title → "LaunchAd Concierge API"

### 6.2 Environment Variables
- [x] Add VITE_API_URL env var support to api.js
- [x] Add VITE_API_URL env var support to CampaignLaunchPage.jsx
- [x] Update terms link to https://launchad.io/terms-of-service
- [x] Add FRONTEND_URL and API_URL to backend config.py

### 6.3 Vercel Configuration
- [x] Create vercel.json with SPA routing
- [x] Configure rewrites for /privacy-policy and /terms-of-service

### 6.4 Backend Updates
- [x] Update CORS to allow https://launchad.io
- [x] Update OAuth callback URLs to use configurable env vars
- [x] Make postMessage origins configurable

### 6.5 Deployment Steps
- [ ] Push changes to GitHub
- [ ] Connect frontend/ folder to Vercel
- [ ] Set env var: VITE_API_URL=https://api.launchad.io
- [ ] Add custom domain: launchad.io
- [ ] Deploy backend to api.launchad.io
- [ ] Update Meta Developer Console OAuth URLs
- [ ] Set production env vars: FRONTEND_URL=https://launchad.io, API_URL=https://api.launchad.io

### 6.6 Testing
- [ ] Test legal pages at /privacy-policy and /terms-of-service
- [ ] Test SPA routing (refresh on /dashboard)
- [ ] Test API calls with production backend
- [ ] Test Facebook OAuth flow end-to-end

---

## Previous Phases (Completed)

### Phase 1-4: Core Features (Completed)
- [x] UI restructure with Summary, Brand Style, Audience Targeting
- [x] Meta Ad Preview component
- [x] Campaign Launch Page with OAuth
- [x] Backend /analyze with Imagen image generation
- [x] Location picker with city autocomplete
- [x] 72-hour campaign end date

### Phase 5: Testing
- [x] Backend tests: 8 passed
- [x] Frontend tests: 8 passed
- [ ] E2E browser test (requires production deployment)

---

## Environment Variables Required

### Frontend (Vercel)
```
VITE_API_URL=https://api.launchad.io
```

### Backend (Production)
```
FRONTEND_URL=https://launchad.io
API_URL=https://api.launchad.io
ENVIRONMENT=production

# Meta
META_APP_ID=xxx
META_APP_SECRET=xxx
META_AD_ACCOUNT_ID=act_xxx

# Google Cloud (Imagen)
GOOGLE_CLOUD_PROJECT=xxx
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# AWS S3
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_S3_BUCKET=launchad-images
```

---

## Files Modified (Phase 6)

### Frontend
- `public/privacy-policy.html` - Rebranded to LaunchAd
- `public/terms-of-service.html` - Rebranded to LaunchAd
- `src/App.jsx` - Renamed Idea2Ad → LaunchAd
- `src/api.js` - Added VITE_API_URL env var
- `src/CampaignLaunchPage.jsx` - Added VITE_API_URL, updated terms link
- `index.html` - Updated title
- `vercel.json` - NEW: Vercel deployment config

### Backend
- `app/main.py` - Updated CORS, renamed to LaunchAd
- `app/config.py` - Added frontend_url, api_url settings
- `app/routers/facebook.py` - Made OAuth URLs configurable
