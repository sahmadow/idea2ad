# LaunchAd (idea2ad)

AI-powered ad campaign generator. Paste a URL or describe your idea, get ready-to-launch Meta ad creatives.

## Quick Start

```bash
# 1. Setup (first time only)
cp .env.example .env
# Edit .env with your API keys

# 2. Generate SSL certs (required for Facebook OAuth)
./scripts/generate-certs.sh

# 3. Start both backend and frontend
./start_app.sh
```

Open https://localhost:5173 (accept the self-signed cert warning).

## Architecture

**Two generation modes:**

```
Quick Mode:
Frontend ── POST /quick/generate ──► Gemini (copy) → Imagen 3.0 (image) → S3 → response

Full Mode:
Frontend ── POST /analyze/async ───► Job created → scrape → Gemini (analysis)
         ── GET /jobs/{id} (poll) ──► → Gemini (copy) → Imagen 3.0 (images) → S3 → complete

Publishing:
Frontend ── Facebook OAuth ────────► /auth/facebook (popup flow)
         ── POST /facebook/campaign ► Create Meta ad campaign
```

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Meta Developer App (for Facebook OAuth)

### Setup

1. **Clone and install:**
```bash
git clone <repo>
cd idea2ad

# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Frontend
cd frontend && npm install && cd ..

# Database
npx prisma generate
npx prisma db push
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Generate SSL certificates** (required for Facebook OAuth):
```bash
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -nodes \
  -out certs/cert.pem -keyout certs/key.pem \
  -days 365 -subj '/CN=localhost'
```

4. **Start development servers:**
```bash
./start_app.sh
```

Or manually:
```bash
# Terminal 1: Backend
source venv/bin/activate
uvicorn app.main:app --reload --ssl-keyfile=./certs/key.pem --ssl-certfile=./certs/cert.pem

# Terminal 2: Frontend
cd frontend && npm run dev
```

### URLs
- Frontend: https://localhost:5173
- Backend: https://localhost:8000
- API Docs: https://localhost:8000/docs

## Environment Variables

### Required
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/idea2ad

# Google AI (content analysis)
GOOGLE_API_KEY=your_key
GOOGLE_CLOUD_PROJECT=your_project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Meta/Facebook
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_AD_ACCOUNT_ID=act_XXXXXXXXX

# AWS S3 (image storage)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your_bucket
```

### URLs (HTTPS required for OAuth)
```bash
api_url=https://localhost:8000
frontend_url=https://localhost:5173
```

See `.env.example` for all options.

## Facebook OAuth Setup

Facebook requires HTTPS for OAuth redirect URIs. See `docs/FACEBOOK_OAUTH_SETUP.md` for detailed instructions.

**Quick setup:**
1. Create Meta App at developers.facebook.com
2. Add Facebook Login product
3. Add redirect URI: `https://localhost:8000/auth/facebook/callback`
4. Copy App ID and Secret to `.env`

## API Endpoints

### Quick Mode
- `POST /quick/generate` - Generate ad from a text idea (Gemini copy + Imagen image)

### Full Mode (URL Analysis)
- `POST /analyze/async` - Start URL analysis job
- `GET /jobs/{job_id}` - Poll job status

### Facebook Integration
- `GET /auth/facebook` - Start OAuth flow
- `GET /auth/facebook/callback` - OAuth callback
- `GET /facebook/status` - Check connection status
- `POST /facebook/campaign` - Create ad campaign
- `POST /facebook/disconnect` - Disconnect account

### Health
- `GET /health` - Health check

## Tech Stack

**Backend:** FastAPI, Python 3.13, Prisma, Playwright, Google Gemini, Vertex AI Imagen 3.0

**Frontend:** React, TypeScript, Vite, TailwindCSS, Framer Motion

**Infrastructure:** PostgreSQL, AWS S3, Railway (prod), Vercel (frontend)

## Project Structure

```
.
├── app/                 # Backend FastAPI app
│   ├── routers/        # API routes
│   ├── services/       # Business logic
│   └── main.py         # App entry
├── frontend/           # React frontend
│   └── src/
│       ├── api/        # API client
│       ├── hooks/      # React hooks
│       ├── pages/      # Page components
│       └── types/      # TypeScript types
├── certs/              # SSL certificates (gitignored)
├── docs/               # Documentation
├── prisma/             # Database schema
├── scripts/            # Utility scripts
└── tests/              # Backend tests
```

## Deployment

### Production
**Backend (Railway):** Auto-deploys on push to `main`
- URL: `https://idea2ad-production.up.railway.app`
- Set all env vars in Railway dashboard

**Frontend (Vercel):** Auto-deploys on push to `main`
- URL: `https://launchad.io`
- Set `VITE_API_URL` to production backend URL

### Staging
**Backend (Railway):** Auto-deploys on push to `staging`
- URL: `https://idea2ad-staging-staging.up.railway.app`
- API Docs: `https://idea2ad-staging-staging.up.railway.app/docs`
- Health: `https://idea2ad-staging-staging.up.railway.app/health`

**Frontend (Vercel):** Auto-deploys on push to `staging`
- URL: `https://frontend-git-staging-salehs-projects-f9732e89.vercel.app`
- Set `VITE_API_URL` in Vercel env vars (Preview scope) to staging backend URL

### Deploying to Staging
```bash
git checkout staging
git merge <your-branch>
git push origin staging
# CI runs → Railway + Vercel auto-deploy
```

### Environment Setup
| Environment | Backend URL | Frontend URL | Vercel Env Scope |
|-------------|-------------|--------------|------------------|
| Production  | idea2ad-production.up.railway.app | launchad.io | Production |
| Staging     | idea2ad-staging-staging.up.railway.app | frontend-git-staging-*.vercel.app | Preview |

## License

MIT
