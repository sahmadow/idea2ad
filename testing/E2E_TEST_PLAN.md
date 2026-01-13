# LaunchAd E2E Test Plan

## Quick Start

```bash
# Run primary test (full campaign flow)
npx playwright test launchad-campaign-flow.spec.ts --headed

# Install browsers if needed
npx playwright install chromium
```

---

## Primary Test: Full Campaign Flow

**File:** `launchad-campaign-flow.spec.ts`

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to launchad.io | Homepage loads |
| 2 | Enter URL: `thebrowser.company` | Input filled |
| 3 | Click "Generate Campaign" | Loading starts |
| 4 | Wait for images (60s timeout) | Campaign images appear |
| 5 | Verify images generated | At least 1 image |
| 6 | Select first image | Image highlighted |
| 7 | Click "Launch My Campaign" | Launch page opens |
| 8 | Facebook OAuth (if needed) | Auth flow handled |
| 9 | Select Ad Account | Account selected |
| 10 | Select Budget ($100) | Budget chosen |
| 11 | Configure Location (Berlin) | City autocomplete |
| 12 | **STOP** before payment | Screenshot taken |

**Screenshots:** Saved to `screenshots/01-homepage.png` through `screenshots/12-payment-highlighted.png`

---

## Secondary Tests: Python/Pytest

| File | Purpose |
|------|---------|
| `tests/e2e/test_auth_flow.py` | Login, register, logout, session |
| `tests/e2e/test_analysis_flow.py` | URL analysis, ad generation |
| `tests/e2e/test_campaign_flow.py` | Dashboard, save/load campaigns |

```bash
pytest tests/e2e/ -v --headed
```

---

## Test Environments

| Environment | Frontend | Backend |
|-------------|----------|---------|
| Production | launchad.io | idea2ad-production.up.railway.app |
| Local | localhost:5173 | localhost:8000 |

---

## Timeouts

| Operation | Timeout |
|-----------|---------|
| Page load | 10s |
| AI Analysis | 90s |
| Image generation | 45s |
| OAuth flow | 30s |

---

## Phase 2 (Future)

- Meta OAuth full flow
- Payment method validation
- Publish to Meta (test account)
