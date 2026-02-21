# LaunchAd Frontend

React + TypeScript + Vite SPA for the LaunchAd ad generation platform.

## Routing

Uses `react-router-dom` with `BrowserRouter`. Vercel handles SPA fallback natively.

### Routes

| Path | Page | Lazy | Auth |
|------|------|------|------|
| `/` | LandingPage | No | No |
| `/adpack` | AdPackPage | Yes | No |
| `/results` | ResultsPage | Yes | No |
| `/publish` | PublishPage | Yes | No |
| `/success` | SuccessPage | Yes | No |
| `/dashboard` | DashboardPage | Yes | Yes |
| `/campaigns/:id` | CampaignDetailPage | Yes | Yes |
| `/test/fb-auth` | FBAuthTest | Yes | No |
| `/test/image-editor` | ImageEditorTest | Yes | No |
| `*` | Redirect to `/` | -- | -- |

### Data guards

Pages with session data dependencies redirect to `/` if data is missing (e.g. `/adpack` without an adPack in context, `/dashboard` without auth).

### Session data

Session state lives in `AppContext` (`src/context/AppContext.tsx`). Transient data (adPack, result, selectedAd) uses localStorage with a 4-hour TTL. Form inputs (URL, businessType, generationMode) persist indefinitely.

## Architecture

```
src/
  context/AppContext.tsx   -- All shared session state + generation logic
  AppRoutes.tsx            -- Route definitions, AnimatePresence, global modals
  pages/                   -- Thin page wrappers (guards + navigation glue)
  components/              -- View components (unchanged, callback-based APIs)
  hooks/                   -- useAuth, useCampaigns, useFacebookAuth
```

Page wrappers read from context and pass props to existing view components. Zero business logic in pages -- all routing concerns only.

## Dev

```bash
npm install
npm run dev     # localhost:5173
npm run build   # tsc -b && vite build
```
