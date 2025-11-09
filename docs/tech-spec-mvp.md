<!--
  SEO Maximus MVP Technical Specification
  Author: Nemanja Tanaskovic
  Date: 2025-11-08
-->

# SEO Maximus – Performance Automation MVP

## 1. Executive Summary

SEO Maximus will ship an initial automation suite focused on the two highest-impact performance optimizations discussed with Chad Guzzi:

- **Critical CSS Load Optimizer** – automatically extracts and serves above-the-fold styles for key templates.
- **Above-the-Fold Image Optimizer** – converts hero imagery to modern formats (WebP/AVIF) using a third-party API and provides prefetch instructions.

The MVP delivers backend services only (no UI dashboard). It exposes authenticated APIs that the Angular frontend can integrate. The system is engineered for rapid delivery (target launch **December 1, 2025**) while providing a foundation for future expansion.

---

## 2. Goals & Non-Goals

### Goals
- Deliver production-ready FastAPI backend handling:
  - Critical CSS generation for specified URLs/templates.
  - Image optimization via a trusted third-party API (e.g., TinyPNG, ImageKit).
- Provide clear API contracts and reference client snippets for frontend integration.
- Ensure observability (logging, health checks) and safe deployment (Dockerized services).
- Support manual re-generation and retrieval of optimization artifacts.

### Non-Goals (Phase 2+)
- Full admin dashboard or UI controls (handled by frontend team later).
- Bulk backlog processing (existing media library, full-site CSS sweeps).
- Multi-tenant billing, rate limiting, advanced analytics.
- Vendor-independent image processing (local encoding) – optional future fallback.

---

## 3. High-Level Architecture
![Description of Image](diagram-2025-11-09-083010.png)

---

## 4. Detailed Components

### 4.1 API Gateway (FastAPI)
- **Endpoints**
  - `POST /v1/images/convert` – enqueue conversion job for a new image.
  - `GET /v1/images/{job_id}` – fetch job status and optimized asset metadata.
  - `POST /v1/critical-css/generate` – enqueue CSS extraction for a URL/template.
  - `GET /v1/critical-css/{job_id}` – retrieve critical CSS payload and guidance.
  - `GET /healthz` – health check for load balancers.
- **Security**
  - API key or JWT (per environment).
  - Request signing for webhook callbacks (optional).
  - Rate limiting via reverse proxy (NGINX/APIM) if needed.
- **Docs**
  - Auto-generated Swagger UI.
  - Markdown quick-start in `docs/api-guide.md`.

### 4.2 Task Execution Layer
- **Celery** with **Redis** broker for background processing.
- Provides retries, visibility into task progress, and concurrency control.
- Workers packaged as separate Docker service.

### 4.3 Image Optimization Worker
- Payload: image URL or binary upload, optional target formats.
- Steps:
  1. Download source asset.
  2. Upload to third-party API; request WebP (and AVIF if supported).
  3. Store optimized asset in configured bucket (S3/R2) or return vendor URL.
  4. Generate metadata: size reduction, format details, recommended `<img>` + `<link rel="prefetch">`.
  5. Persist results in Postgres.
- Resiliency:
  - Graceful fallback if vendor unavailable (retry/backoff).
  - Configurable timeouts and max payload size.

### 4.4 Critical CSS Worker
- Uses **Playwright (Chromium)** bundled with necessary system dependencies/fonts.
- Workflow:
  1. Launch headless browser with stealth headers.
  2. Iterate through configured viewports (desktop, tablet, mobile).
  3. For each viewport:
     - Navigate to URL, wait for network idle/event triggers.
     - Collect CSS coverage (`page.coverage.startCSSCoverage()`).
     - Capture DOM snapshot and above-the-fold height.
  4. Merge coverage data across viewports, preserving cascade order.
  5. Compose critical CSS block; optionally minify with `csscompressor`.
  6. Generate deferral snippet for remaining CSS/JS (e.g., `media="print"` switch).
  7. Persist results + debug artifacts (screenshots, logs).
- Configurability:
  - Viewport list per project.
  - Tolerance for lazy-loaded elements (scroll nudge, mutation observer wait).
  - Optional authentication headers/cookies.

### 4.5 Persistence
- **Postgres** schema (see Section 6).
- Stores job metadata, artifact references, and audit logs.
- Use SQLAlchemy ORM with Alembic migrations.
- Optionally store large artifacts (CSS, HTML snapshots) in object storage with signed URLs.

### 4.6 Observability & Ops
- Structured logging via `structlog`.
- Error tracking: Sentry (DSN configurable).
- Metrics: basic Prometheus endpoints (task success/failure, duration).
- Deployment: Docker images pushed to container registry, orchestrated on ECS Fargate or Cloud Run. Staging + production environments.

---

## 5. API Contracts (MVP)

### 5.1 `POST /v1/images/convert`
- **Headers**: `Authorization: Bearer <token>`
- **Body**
  ```json
  {
    "source_url": "https://cdn.example.com/hero.jpg",
    "asset_key": "home-hero",
    "prefetch": true,
    "formats": ["webp"]
  }
  ```
- **Responses**
  - `202 Accepted` with `{ "job_id": "img_123", "status": "queued" }`
  - Errors: `400` (validation), `401`, `429`, `500`.

### 5.2 `GET /v1/images/{job_id}`
```json
{
  "job_id": "img_123",
  "status": "completed",
  "source_url": "https://cdn.example.com/hero.jpg",
  "optimized_assets": [
    {
      "format": "webp",
      "url": "https://assets.seomaximus.com/home-hero.webp",
      "bytes": 45213,
      "savings_percent": 67.4
    }
  ],
  "prefetch_tag": "<link rel=\"prefetch\" href=\"https://assets.seomaximus.com/home-hero.webp\" as=\"image\">",
  "img_snippet": "<img src=\"https://assets.seomaximus.com/home-hero.webp\" type=\"image/webp\" alt=\"\" />"
}
```

### 5.3 `POST /v1/critical-css/generate`
```json
{
  "target_url": "https://demo-client.com/",
  "template": "home",
  "viewport_profiles": ["desktop", "mobile"],
  "auth_headers": null
}
```
- Response: `202 Accepted` with job ID.

### 5.4 `GET /v1/critical-css/{job_id}`
```json
{
  "job_id": "css_456",
  "status": "completed",
  "template": "home",
  "critical_css": "/* minified critical CSS */",
  "defer_instructions": {
    "description": "Swap stylesheet once page is interactive",
    "snippet": "<link rel=\"preload\" href=\"/static/app.css\" as=\"style\" onload=\"this.rel='stylesheet'\">"
  },
  "viewports": {
    "desktop": {"height": 900, "width": 1440},
    "mobile": {"height": 740, "width": 390}
  },
  "artifacts": {
    "screenshots": ["https://assets.seomaximus.com/css_456/mobile.png"]
  }
}
```

---

## 6. Data Model (Draft)

| Table | Key Fields | Notes |
|-------|------------|-------|
| `image_jobs` | `id`, `asset_key`, `source_url`, `status`, `created_at`, `completed_at`, `prefetch_tag`, `img_snippet`, `vendor_job_id` | Status enum: queued, processing, completed, failed. |
| `image_variants` | `id`, `job_id`, `format`, `url`, `bytes`, `savings_percent` | One-to-many with `image_jobs`. |
| `css_jobs` | `id`, `template`, `target_url`, `status`, `viewport_profiles`, `critical_css`, `defer_snippet`, `notes`, `created_at` | Store CSS in text column (compressed) or pointer to S3. |
| `job_logs` | `id`, `job_id`, `kind`, `message`, `timestamp` | For traceability/debugging. |
| `api_keys` (optional MVP) | `id`, `name`, `hashed_key`, `role`, `created_at`, `last_used_at`, `revoked` | Enables multiple integrations. |

Alembic migrations will initialize schema and provide upgrade path.

---

## 7. Third-Party Integration Details

### Image API (TinyPNG/TinyJPG)
- REST API with simple POST uploads.
- Supports WebP output; AVIF currently beta – confirm.
- Authentication via API key.
- Pricing: free tier 500 compressions/month then ~$0.002 per. Monitor via vendor dashboard.

Alternative: ImageKit or Cloudinary if CDN/transformation pipeline preferred. Abstraction layer allows swapping vendors later.

### Storage
- Expect existing AWS S3 bucket; configure IAM user with scoped permissions.
- Use pre-signed PUT for frontend uploads if needed later.

### Playwright Runtime
- Docker image based on `mcr.microsoft.com/playwright/python:v1.45.0-focal`.
- Include fonts, fallback CA certificates, and OS packages.
- Provide environment variables for stealth (User-Agent, Accept-Language).

---

## 8. Testing Strategy

- **Unit tests** (Pytest): validation schemas, vendor client wrappers, job orchestrators.
- **Integration tests**: 
  - Mock third-party API using `responses` or local stub to verify retry logic.
  - Playwright smoke test against controlled pages (hosted test fixtures).
- **Performance smoke**: ensure concurrent jobs under 1–2 min for typical pages.
- **QA staging**: deploy to staging environment with feature flag to run on sample URLs.

---

## 9. Deployment Plan

1. Build Docker images via GitHub Actions (lint, tests, image push).
2. Deploy to AWS ECS Fargate (or Cloud Run) using IaC (Terraform/CloudFormation). MVP can use manual provisioning + docker-compose on EC2 if faster.
3. Configure environment variables via Secrets Manager:
   - `TINYPING_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `SENTRY_DSN`, `JWT_SECRET`, etc.
4. Set up logging to CloudWatch/Stackdriver.
5. Provision CI/CD pipeline to run migrations automatically before deployment.

---

## 10. Timeline & Effort (reaffirmed)

| Week | Focus | Key Deliverables |
|------|-------|------------------|
| Nov 9 – Nov 15 | Foundations + Image Pipeline | Repo scaffold, Docker, FastAPI base, TinyPNG client, `POST /images/convert` |
| Nov 16 – Nov 22 | Critical CSS Engine | Playwright worker, CSS merge logic, `POST /critical-css/generate` |
| Nov 23 – Nov 29 | Hardening & Handoff | Observability, retries, docs, integration tests, staging deploy |
| Nov 30 | Buffer | Bug fixes, final review |

- Estimated effort: **75–85 hours**.
- Contingency buffer: 15%.
- Dependencies: API key provisioning, staging URLs, storage credentials by Nov 12 latest.

---

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Third-party API downtime | Image jobs fail | Implement retries + fallback queue, monitor vendor status. |
| Playwright blocked by target site | CSS job incomplete | Use stealth headers, optional proxy rotation, configurable wait hooks. |
| Changes in frontend structure | CSS becomes stale | Provide re-run endpoint + schedule nightly regeneration. |
| Large CSS bundles | Slow generation | Streamline coverage merging, enable per-template viewport throttling. |
| December 1 launch crunch | Miss deadline | Weekly demos, maintain burn chart, prioritize MVP endpoints first. |

---

## 12. Handoff Checklist

- ✅ FastAPI service with authentication and OpenAPI docs.
- ✅ Docker Compose for local dev + instructions.
- ✅ Celery worker + Redis configuration.
- ✅ Image optimization client with integration tests.
- ✅ Playwright critical CSS worker with sample outputs.
- ✅ Postgres migrations applied.
- ✅ README and runbook for frontend/ops teams.
- ✅ API key(s) rotated and documented.

---

## 13. Next Steps

1. Bootstrap repository with FastAPI, Celery, Redis, and Postgres config.
2. Implement TinyPNG client and mock tests.
3. Stand up Playwright worker with sample URL script.
4. Deliver MVP endpoints + documentation by end of November.

For questions or adjustments, reach out anytime. This spec will evolve as we iterate.


