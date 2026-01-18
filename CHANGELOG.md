# Changelog

## [Unreleased] - 2026-01-18

### Project Cleanup
- Removed old JSX frontend, replaced with TypeScript + Tailwind version
- Consolidated documentation into `docs/` folder
- Removed test artifacts and screenshots from root
- Cleaned up duplicate shell scripts
- Removed unused node_modules and cache directories

### Directory Structure
```
idea2ad/
├── app/                    # FastAPI backend
│   ├── services/          # Business logic (scraper, analyzer, creative, image_gen)
│   └── templates/         # Jinja2 ad templates
├── frontend/              # React + TypeScript + Tailwind frontend
├── tests/                 # Pytest unit/integration tests
├── testing/               # Playwright E2E tests
├── loadtests/             # Locust load tests
├── docs/                  # Documentation
├── prompts/               # AI prompt templates
└── prisma/                # Database schema
```

---

## [0.3.0] - 2026-01-18

### Added
- HTML template-based ad generation with Jinja2 + Playwright
- Three ad templates: product_focused, lifestyle, problem_solution
- Background removal (rembg) for product images
- Golden ratio sizing for visual elements
- Color utilities for brand-consistent image generation

### Fixed
- Duplicate CTA text appearing in subheadline
- GCP credentials loading from pydantic settings
- Product image scaling with CSS transform

---

## [0.2.0] - 2026-01-17

### Added
- New TypeScript + Tailwind landing page
- Pricing section (Single Campaign $29, Pro Monthly $129)
- Terminal component showing URL processing flow
- AdPreview component with tabs

### Infrastructure
- Vercel deployment for frontend (launchad.io)
- Railway deployment for backend
- GitHub Actions CI pipeline

---

## [0.1.0] - 2026-01-10

### Added
- Landing page scraper with SSRF protection
- AI analyzer using Google Gemini
- Creative generation for ad copy
- Meta Ads API integration
- OAuth flow for Meta authentication
- PostgreSQL database with Prisma ORM
- JWT authentication

### Security
- URL validation blocking internal IPs
- Parameterized queries via Prisma
- CORS configuration
- Rate limiting on API endpoints
