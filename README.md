# AppReviewr

Download app reviews from Google Play and the App Store in seconds.

Paste a store link → fetch public reviews → filter → preview → download CSV, Excel, or JSON. No signup in Phase 1.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js (App Router), TypeScript, Tailwind, shadcn/ui, TanStack Query |
| Backend | FastAPI, Python 3.12, SQLite cache |
| Data | Tier 1 free scrapers only (`google-play-scraper`, Apple iTunes lookup + RSS) |
| E2E | Playwright (`e2e/`) |

## Quick start (< 15 minutes)

### Prerequisites

- Node.js 20+
- Python 3.11+
- Optional: Docker Compose

### 1. Clone

```bash
git clone https://github.com/Bharath-OS/app-reviewr.git
cd app-reviewr
git checkout development
cp .env.example .env
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8741
```

Health: http://127.0.0.1:8741/api/health

### 3. Frontend (second terminal)

Prefer production start for a reliable client bundle:

```bash
cd frontend
npm install
cp ../.env.example ../.env   # or set NEXT_PUBLIC_API_URL
echo "NEXT_PUBLIC_API_URL=http://127.0.0.1:8741" > .env.local
npm run build
npm run start
```

Dev mode (Webpack — more reliable than Turbopack in some environments):

```bash
npm run dev
```

Open http://127.0.0.1:3741

### Docker (optional)

```bash
docker compose up --build
```

## Tests

```bash
# Backend unit/API
cd backend && source .venv/bin/activate
export PYTHONPATH=.
export APPREVIEW_DISABLE_RATE_LIMIT=1
pytest -q

# Frontend lint/build
cd frontend && npm run lint && npm run build

# Playwright e2e (frontend + backend must be running)
cd e2e && npm install && npx playwright install chromium && npm test
```

Scraper health probe:

```bash
cd backend && source .venv/bin/activate
python scripts/healthcheck.py --api http://127.0.0.1:8741/api/health --scrapers
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness |
| GET | `/api/app-info?url=` | App preview card |
| POST | `/api/jobs` | Start fetch job |
| GET | `/api/jobs/{id}` | Job status |
| GET | `/api/jobs/{id}/events` | SSE progress |
| POST | `/api/jobs/{id}/cancel` | Cancel |
| GET | `/api/jobs/{id}/reviews` | Paginated reviews |
| GET | `/api/jobs/{id}/export?format=csv\|xlsx\|json` | Download |

## Environment

See [`.env.example`](.env.example). Backend vars use the `APPREVIEW_` prefix.

## Branching

1. `main` — stable  
2. `development` — integration  
3. `feature/*` off `development` — merge only when tests pass  

## Caching

Reviews are cached **12 hours** per `(store, app_id, country, language, sort)`.

- First **Fetch reviews** scrapes the store and fills the cache.
- A later Fetch for the same app/country/sort uses the cache (**no Google/Apple review scrape**).
- **Refresh from store** forces a new scrape (`force_refresh: true`).
- Fresh scrapes: **10/hour per visitor IP**. Fully cached re-fetches skip that scrape quota (still 30 API calls/minute).

Set `NEXT_PUBLIC_SITE_URL` to your public domain for sitemap/robots/canonical SEO.

## Known limits (Phase 1)

- **Honesty:** AppReviewr never claims “all reviews.” UI shows returned counts.
- **App Store Tier 1:** Public iTunes RSS historically ~500 reviews/country. As of 2026-10 probes, RSS often returns an **empty feed** (HTTP 200, 0 entries) while lookup still works. Escalation documented; no silent paid tier.
- **Google Play:** Depth depends on `google-play-scraper` pagination; jobs capped at `APPREVIEW_MAX_REVIEWS_PER_JOB` (default 2000). Scrapes run from **your server IP**, not each visitor’s home IP (CDN only speeds the website).
- **Rate limits:** Per-IP SlowAPI limits (see Caching).
- **No auth / AI / payments** in Phase 1.

## Screenshots

See [`docs/screenshots/`](docs/screenshots/).

## Deploy notes

- Frontend: static/SSR Next.js app (Vercel-friendly). Set `NEXT_PUBLIC_API_URL` to the backend origin.
- Backend: long-lived process (Uvicorn/container/VPS). Not serverless — jobs + SSE need a sticky process.
- CORS: set `APPREVIEW_CORS_ORIGINS` to your frontend origin(s).

## License

Private / as configured by the repository owner.
