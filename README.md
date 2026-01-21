# idea2ad

AI-powered landing page to Meta ad campaign generator. Paste a URL, get ready-to-launch ad creatives.

## Architecture

```
Frontend (Vercel)          Backend (Railway)
    │                           │
    ├─ POST /analyze/async ────►│ Create job, return job_id
    │                           │
    │◄─ { job_id } ─────────────┤
    │                           │
    ├─ GET /jobs/{id} ─────────►│ Poll status (pending/processing)
    │    (every 2s)             │
    │                           │ Background: scrape → analyze → generate
    │◄─ { status: complete } ───┤
```

## API Endpoints

### `POST /analyze/async`
Start async analysis job.

**Request:**
```json
{ "url": "https://example.com" }
```

**Response:**
```json
{ "job_id": "abc12345", "status": "pending", "url": "https://example.com" }
```

### `GET /jobs/{job_id}`
Poll job status.

**Response (processing):**
```json
{ "job_id": "abc12345", "status": "processing" }
```

**Response (complete):**
```json
{
  "job_id": "abc12345",
  "status": "complete",
  "result": { /* CampaignDraft */ }
}
```

**Response (failed):**
```json
{ "job_id": "abc12345", "status": "failed", "error": "Error message" }
```

### `GET /health`
Health check endpoint.

## Tech Stack

**Backend:**
- FastAPI + Python 3.13
- Playwright (web scraping)
- Google Gemini (AI analysis)
- Ideogram API (image generation)
- AWS S3 (image storage)
- Gunicorn + Uvicorn workers

**Frontend:**
- React + TypeScript + Vite
- TailwindCSS

**Infrastructure:**
- Railway (backend)
- Vercel (frontend)

## Environment Variables

### Backend
```
GEMINI_API_KEY=         # Google AI API key
IDEOGRAM_API_KEY=       # Ideogram image generation
AWS_ACCESS_KEY_ID=      # S3 access
AWS_SECRET_ACCESS_KEY=  # S3 secret
AWS_S3_BUCKET=          # S3 bucket name
DATABASE_URL=           # PostgreSQL connection string
```

### Frontend
```
VITE_API_URL=           # Backend API URL
```

## Local Development

### Backend
```bash
cd app
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Deployment

### Railway (Backend)
- Deploys from Dockerfile
- Auto-deploys on push to main
- Uses gunicorn with 180s timeout

### Vercel (Frontend)
- Deploys from frontend/ directory
- Auto-deploys on push to main

## Notes

- Async polling bypasses Railway's 60s proxy timeout
- Jobs stored in-memory with 2hr TTL
- Scraper uses tiered wait strategy for sites with endless trackers
