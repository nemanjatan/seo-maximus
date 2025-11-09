# SEO Maximus Backend (MVP)

Backend services supporting the SEO Maximus performance automation MVP, focused on:

- Automated conversion of above-the-fold images to modern formats (WebP/AVIF) using a third-party API.
- Critical CSS extraction for key templates using Playwright-powered headless rendering.

## Project Layout

```
.
├── app/                # FastAPI application code
│   ├── api/            # Route handlers and dependencies
│   ├── core/           # Configuration, logging, security helpers
│   ├── db/             # Database models and sessions
│   ├── services/       # Domain logic for optimizers
│   └── worker/         # Celery worker bootstrap
├── docs/               # Technical specification and supplementary docs
├── tests/              # Unit and integration tests
├── docker/             # Container build assets
└── pyproject.toml
```

## Quick Start

1. Ensure Python 3.11+, Docker, and `make` are available.
2. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -e .
   pip install -e ".[dev]"
   playwright install chromium
   ```
3. Copy `env.example` to `.env` and configure secrets for your environment (set `TINYPNG_API_KEY` to your real key).
4. Run services locally:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

Docker Compose definitions and detailed runbooks will follow as the MVP evolves.

