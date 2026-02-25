# Email Collection Gate Before Generation

**Overall Progress:** `100%`

## TLDR
Gate the "Confirm & Generate Ads" button on ReviewPage behind email + ToS acceptance. Marketing consent is a **separate, optional, unticked checkbox** (GDPR Article 7(4) anti-bundling). Store email + consent proof (timestamp, IP, UA, form version) in new DB tables. Skip gate for authenticated users.

## Critical Decisions
- **Gate location**: ReviewPage, inline above the generate button — user has invested time (URL → upload → review), conversion highest here
- **GDPR bundling fix**: Email + ToS = required for service (Art. 6(1)(b) contract performance). Marketing checkbox = optional, unticked, clearly labeled "Optional". This avoids the **Critical** risk from legal review (bundled consent = invalid)
- **Consent proof storage**: New `Lead` + `ConsentLog` tables matching GDPR review's recommended schema — timestamp, IP, UA, form version stored
- **No double opt-in yet**: Phase 1 single opt-in. DOI deferred to email provider setup (Brevo/Mailjet). `consent_marketing` stored as-is for now
- **No field-level encryption yet**: MVP uses DB-level encryption (Prisma + PostgreSQL). App-level AES-256 is a follow-up
- **Email passed with generate request**: Added to `GenerateRequest` body so backend stores it atomically with generation
- **Skip for auth'd users**: If `isAuthenticated`, bypass gate — we have their email from registration
- **Company name**: Journeylauncher LLC (legal entity) in consent text
- **ToS/Privacy pages**: Real content, linked from checkboxes
- **Email provider**: Autosend (for future DOI flow)

## GDPR Compliance Status (per legal review)
- [x] Separate checkboxes for ToS and marketing
- [x] Marketing checkbox unticked by default, labeled "Optional"
- [x] Consent language names company, states purpose, mentions unsubscribe
- [x] Privacy Policy link visible
- [x] Consent proof stored (timestamp, IP, UA, form version)
- [x] Append-only consent_log audit trail
- [x] Soft delete support (deleted_at)
- [ ] Double opt-in flow (deferred — Phase 2 with Autosend)
- [ ] Tracking pixel consent (deferred — not sending emails yet)
- [ ] Field-level AES-256 encryption (follow-up)

## Tasks

- [x] 🟩 **Step 1: Prisma schema — add Lead + ConsentLog models**
  - [x] 🟩 Add `Lead` model with all GDPR fields
  - [x] 🟩 Add `ConsentLog` model (append-only audit trail)
  - [x] 🟩 Run `prisma db push` + `prisma generate`

- [x] 🟩 **Step 2: Backend — store lead with generate request**
  - [x] 🟩 Add `email`, `consent_marketing`, `consent_terms` to `GenerateRequest` (pydantic EmailStr)
  - [x] 🟩 Upsert Lead + append ConsentLog in `_store_lead()` (non-blocking async task)
  - [x] 🟩 Capture IP (X-Forwarded-For) + User-Agent from request headers
  - [x] 🟩 Rate limit: existing 10/min on /v2/generate via limiter

- [x] 🟩 **Step 3: Frontend — email + consent section on ReviewPage**
  - [x] 🟩 Email input + ToS checkbox (required) + marketing checkbox (optional)
  - [x] 🟩 GDPR-compliant consent language with Journeylauncher LLC
  - [x] 🟩 Button disabled until email valid + ToS checked
  - [x] 🟩 Section skipped for `ctx.auth.isAuthenticated`

- [x] 🟩 **Step 4: API client — pass email in generate call**
  - [x] 🟩 Added to `GenerateParams` in adpack.ts
  - [x] 🟩 Added to `startGeneration` overrides in AppContext.tsx
  - [x] 🟩 Email persisted to localStorage for back-nav pre-fill

- [x] 🟩 **Step 5: Legal pages**
  - [x] 🟩 `/terms` — TermsPage with GDPR-compliant content (Journeylauncher LLC)
  - [x] 🟩 `/privacy` — PrivacyPage with data collection, retention, rights
  - [x] 🟩 Registered lazy routes in AppRoutes.tsx

- [x] 🟩 **Step 6: Test & verify**
  - [x] 🟩 TypeScript compiles clean (tsc --noEmit)
  - [x] 🟩 Vite build succeeds
  - [x] 🟩 Backend GenerateRequest schema validates with EmailStr
  - [x] 🟩 Prisma Lead + ConsentLog tables queryable
  - [x] 🟩 Button disabled logic: `isAuthenticated || (validEmail && consentTerms)`

## Unresolved Questions
- None blocking.

## Complexity: MEDIUM
~6 files modified, 2 new models, 2 new placeholder pages, inline form on ReviewPage.
