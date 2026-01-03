# Idea2Ad - Production Checklist

## Completed

### Phase 1: Security & Database
- [x] `.gitignore` - secrets protection
- [x] `.env.example` - env var template
- [x] `app/config.py` - Pydantic settings
- [x] `prisma/schema.prisma` - PostgreSQL schema
- [x] `app/db.py` - DB connection manager
- [x] `app/auth/` - JWT auth (bcrypt, tokens)
- [x] `app/routers/auth.py` - `/auth/register`, `/auth/login`, `/auth/me`
- [x] URL validation + SSRF protection in scraper
- [x] Rate limiting (10/min analyze, 5/min publish)

### Phase 2: Image Pipeline
- [x] `app/services/image_gen.py` - Vertex AI Imagen 3.0
- [x] `app/services/s3.py` - AWS S3 upload
- [x] `app/routers/images.py` - `/images/generate`, `/images/generate-all`
- [x] `upload_image_from_url()` in meta_api.py
- [x] Image support in publish flow

### Phase 3: Production Readiness
- [x] `Dockerfile` - backend container
- [x] `frontend/Dockerfile` - frontend container
- [x] `docker-compose.yml` - full stack
- [x] `app/logging_config.py` - JSON logging
- [x] Sentry integration

### Phase 4: Testing
- [x] `pytest.ini` + `tests/conftest.py`
- [x] Unit tests (scraper, auth)
- [x] Integration tests (API endpoints)
- [x] Frontend tests (vitest + RTL)
- [x] `.github/workflows/ci.yml` - GitHub Actions

---

## Setup (Completed)

### 1. Install Dependencies
- [x] Backend: `pip install -r requirements.txt`
- [x] Playwright: `python -m playwright install chromium`
- [x] Frontend: `cd frontend && npm install`
- [x] Fixed bcrypt compatibility: `pip install 'bcrypt<5.0.0'`
- [x] Added Pillow: `pip install Pillow`
- [x] Added email-validator: `pip install email-validator`

### 2. Database Setup
- [x] Generated Prisma client: `prisma generate`
- [ ] Push schema to DB (requires DATABASE_URL in .env): `prisma db push`

### Test Results
- **Backend Tests:** 30 passed (no deprecation warnings)
- **Frontend Tests:** 8 passed
- **Total:** 38 tests passing

### 3. Environment Variables
Copy `.env.example` to `.env` and configure:

```env
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/idea2ad
JWT_SECRET_KEY=<generate 32+ char secret>
GOOGLE_API_KEY=<your key>
META_ACCESS_TOKEN=<your token>
META_APP_SECRET=<your secret>
META_APP_ID=<your app id>
META_AD_ACCOUNT_ID=act_<your account>

# For image generation
GOOGLE_CLOUD_PROJECT=<your gcp project>
AWS_ACCESS_KEY_ID=<your key>
AWS_SECRET_ACCESS_KEY=<your secret>
AWS_S3_BUCKET=idea2ad-images

# Optional
SENTRY_DSN=<your dsn>
```

### 4. AWS S3 Bucket
- Create bucket `idea2ad-images`
- Enable public read access (bucket policy)
- Configure CORS for frontend domain

### 5. GCP Vertex AI
- Enable Vertex AI API in GCP project
- Set up service account with Vertex AI permissions
- Set `GOOGLE_APPLICATION_CREDENTIALS` path

---

## Run Commands

```bash
# Development
./start_app.sh  # or manually:
uvicorn app.main:app --reload  # backend
cd frontend && npm run dev     # frontend

# Tests
pytest                          # backend tests
cd frontend && npm test         # frontend tests

# Docker
docker-compose up --build

# Database migrations
prisma db push
prisma migrate dev --name <migration_name>
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | No | Health check |
| GET | `/health` | No | Detailed health |
| POST | `/auth/register` | No | Create account |
| POST | `/auth/login` | No | Get JWT |
| GET | `/auth/me` | Yes | Current user |
| POST | `/analyze` | No* | Analyze URL |
| GET | `/campaigns` | Yes | List user campaigns |
| GET | `/campaigns/{id}` | Yes | Get campaign details |
| POST | `/campaigns` | Yes | Save campaign |
| PATCH | `/campaigns/{id}` | Yes | Update campaign |
| DELETE | `/campaigns/{id}` | Yes | Delete campaign |
| POST | `/campaigns/{id}/publish` | Yes | Publish to Meta |
| POST | `/images/generate` | Yes | Generate image from brief |
| POST | `/images/generate-all/{id}` | Yes | Generate all campaign images |
| POST | `/meta/publish` | No* | Publish to Meta |
| GET | `/meta/config` | No | Meta config status |
| GET | `/meta/test/*` | No | Meta API tests |

*Rate limited

---

## Production Deployment

### Railway
1. Connect GitHub repo
2. Add PostgreSQL service
3. Set environment variables
4. Deploy

### Vercel (Frontend)
1. Import frontend directory
2. Set build command: `npm run build`
3. Set output directory: `dist`
4. Configure API rewrites to backend

### Manual Docker
```bash
docker-compose -f docker-compose.yml up -d
```

---

## Technical Debt

- [x] Migrate `google.generativeai` → `google.genai` (deprecation warning in tests)

---

## Future Enhancements

### Data Persistence
- [x] Campaign history/persistence (save to DB) - `app/routers/campaigns.py`
- [x] User dashboard with past campaigns - `frontend/src/Dashboard.jsx`

### Campaign Features
- [x] Multiple ad creatives per campaign (already generates 2 headlines, 2 copy, 3 image briefs)
- [ ] A/B testing setup (COMPLEX - requires Meta Experiments API)
- [ ] Campaign performance analytics (COMPLEX - requires Meta Insights API integration)
- [ ] Webhook for campaign status updates (MEDIUM - add webhook endpoint + Meta webhook subscription)

### Platform Expansion
- [ ] Multi-platform (COMPLEX - Google Ads API + TikTok Marketing API integration)

### Collaboration
- [ ] Team/organization management (COMPLEX - requires org schema, RBAC, invites)
