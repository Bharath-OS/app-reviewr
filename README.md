# AppReviewr

Download app reviews from Google Play and the App Store in seconds.

Paste a store link → fetch public reviews → filter → preview → download CSV, Excel, or JSON. No signup in Phase 1.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js (App Router), TypeScript, Tailwind |
| Backend | FastAPI, Python 3.12, SQLite cache |
| Data | Tier 1 free scrapers only (`google-play-scraper`, Apple iTunes RSS) |

## Quick start (< 15 minutes)

### Prerequisites

- Node.js 20+
- Python 3.11+
- Optional: Docker + Docker Compose

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

Health check: [http://127.0.0.1:8741/api/health](http://127.0.0.1:8741/api/health)

### 3. Frontend (second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:3741](http://127.0.0.1:3741)

### Docker (optional)

```bash
docker compose up --build
```

- Frontend: http://127.0.0.1:3741  
- Backend: http://127.0.0.1:8741  

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Live store probes (skipped by default):

```bash
pytest -q -m live
```

API health script:

```bash
python scripts/healthcheck.py --api http://127.0.0.1:8741/api/health
```

## Environment

See [`.env.example`](.env.example). All backend vars use the `APPREVIEW_` prefix.

| Variable | Default | Purpose |
|---|---|---|
| `APPREVIEW_CORS_ORIGINS` | `http://localhost:3741,...` | Allowed frontend origins |
| `APPREVIEW_MAX_REVIEWS_PER_JOB` | `2000` | Hard cap per fetch job |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8741` | Frontend → API base URL |

## Branching

1. `main` — stable releases / docs  
2. `development` — integration  
3. `feature/*` off `development` — merge only when tests pass  

## Known limits (Phase 1)

- Tier 1 App Store RSS typically returns ~500 reviews per country.
- Google Play depth depends on the public scraper library; UI will state returned counts honestly.
- No auth, AI analysis, payments, or scheduled exports in Phase 1.

## License

Private / as configured by the repository owner.
