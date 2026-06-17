# APCTT Technology Gateway

A federated search engine for technology transfer across Asia-Pacific databases. Built as a prototype for APCTT (Asian and Pacific Centre for Transfer of Technology), a body under UN ESCAP.

Instead of visiting each national database separately, researchers and institutions can search once and get consolidated results from multiple sources — with metadata displayed inline, no redirects.

---

## What it does

- Searches across registered Asia-Pacific technology databases in parallel
- Returns normalized metadata: title, summary, sector, keywords, organisation, transfer type, development status
- Inline translation from Korean to English via the MyMemory free translation API
- Results are cached for 24 hours to avoid hammering external APIs on repeated queries
- Frontend is a static HTML/CSS/JS site — no build step required

---

## Architecture

```
frontend/           Static site (HTML + CSS + JS) — talks to the backend API
backend/
  main.py           FastAPI application entry point
  config.py         Environment variable loading (pydantic-settings)
  routers/
    search.py       GET /api/v1/search — fan-out query across all sources
    sources.py      GET /api/v1/sources — list registered databases
  sources/
    base.py         Abstract base class every source adapter must implement
    registry.py     List of active source instances
    korea_ntb.py    Korea National Technology Bank (live metadata, XML API)
    wipo_patentscope.py  WIPO PATENTSCOPE international patents (REST JSON)
    india_tifac.py  India TIFAC TechMonitor (redirect — no public API)
  models/
    technology.py   Normalized data models (Technology, Source)
    response.py     SearchResponse envelope
  cache/
    ttl_cache.py    Thread-safe in-memory cache with configurable TTL
```

The backend exposes two endpoints. The frontend calls them directly from the browser.

---

## Data sources

| Source | Country | Type | API |
|---|---|---|---|
| Korea National Technology Bank (NTB) | Republic of Korea | Live metadata | data.go.kr public API (key required) |
| WIPO PATENTSCOPE | International | Live metadata | WIPO REST API (no key) |
| India TIFAC TechMonitor | India | Redirect | No public API |

**Note on Korea NTB:** The NTB portal (`ntb.kr`) blocks all external deep-links via session verification. All metadata is fetched and displayed inline — the link in each card points to the NTB homepage rather than a specific record page. This is a platform restriction on their end, not a limitation of this system.

---

## Running locally

**Requirements:** Python 3.11+

```bash
cd apctt-gateway

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r backend/requirements.txt
```

Create a `.env` file in the project root (never commit this):

```
KOREA_NTB_API_KEY=your_api_key_here
KOREA_NTB_BASE_URL=https://apis.data.go.kr/B552536/tech_4/techall
CACHE_TTL_SECONDS=86400
```

Start the backend:

```bash
uvicorn backend.main:app --reload
```

Open `frontend/index.html` in a browser, or serve it with any static file server.

---

## Deploying to Render

The `render.yaml` in the project root configures the backend as a Render Web Service.

1. Push this repository to GitHub
2. Create a new Web Service on Render, connect the GitHub repo
3. Add `KOREA_NTB_API_KEY` as a secret environment variable in the Render dashboard (do not put it in `render.yaml`)
4. After the backend deploys, update `API_BASE` in `frontend/app.js` to the Render service URL
5. Deploy the frontend as a Render Static Site or GitHub Pages (root directory: `frontend/`)

The free tier on Render spins down after 15 minutes of inactivity. The first request after inactivity takes around 30 seconds to wake the service.

---

## Adding a new data source

1. Create `backend/sources/<source_id>.py` — extend `BaseSource`, implement `search()` and `is_healthy()`
2. Add the instance to the `SOURCES` list in `backend/sources/registry.py`

The search router, caching, and frontend all pick up the new source automatically.

---

## API reference

### GET /api/v1/search

Query parameters:

| Parameter | Description |
|---|---|
| `q` | Search keyword |
| `country` | Filter by country |
| `sector` | Filter by technology sector |
| `source` | Filter by source ID (e.g. `korea_ntb`) |
| `language` | Filter by language of the record |

Returns a `SearchResponse` with `total`, `sources_hit`, `cached`, and a `results` array of `Technology` objects.

### GET /api/v1/sources

Returns the list of registered source databases with their status and metadata.

### GET /health

Returns `{"status": "ok"}`. Used by Render for health checks.

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `KOREA_NTB_API_KEY` | Yes | API key from data.go.kr for the NTB dataset |
| `KOREA_NTB_BASE_URL` | Yes | NTB API endpoint URL |
| `CACHE_TTL_SECONDS` | No | Cache lifetime in seconds (default: 86400) |

---

## Korea NTB API key

Register at [data.go.kr](https://www.data.go.kr) and apply for the dataset **15158994** (Korea NTB Technology Information). The key is issued within 1-2 business days. Keep it out of version control — use the `.env` file locally and Render's secret env vars in production.
