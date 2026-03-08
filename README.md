# Community Guardian
Mark Osei Kwabi

Community Safety and Digital Wellness

I worked on it for 8-10 hours

YOUTUBE LINK:https://youtu.be/x2_9Z9yxQmM

> AI-powered community safety alert system — calm, private, actionable.

Community Guardian transforms raw community reports into structured, actionable safety digests using RAG (Retrieval-Augmented Generation). It filters noise from signal, classifies threats by category and severity, generates step-by-step guidance, and provides an encrypted Safe Circle for trusted group communication.

---

## Features

| Feature | Description |
|---|---|
| **Noise-to-signal filtering** | Keyword-based filter discards irrelevant reports before any AI processing |
| **Threat classification** | Auto-categorizes alerts into cyber threat, scam, local crime, infrastructure, or general |
| **AI-powered digests** | RAG chain (ChromaDB + GPT-3.5) generates calm, specific 3-step action checklists |
| **Graceful fallback** | Pre-written checklists activate automatically when AI is unavailable — no downtime |
| **Privacy-first Safe Circle** | Fernet-encrypted group messaging; location data never stored in plain text |
| **RSS ingestion** | Pulls live alerts from CISA and The Hacker News feeds |
| **Stats dashboard** | Breakdowns by severity, category, and recent activity |
| **Rate limiting** | Per-IP rate limits on all endpoints via slowapi |
| **Schema migration** | Auto-migrates old database schemas on startup |
| **Docker support** | Single `docker compose up` deployment with persistent data volume |

---

## Architecture

```
community-guardian/
├── backend/
│   ├── main.py               # FastAPI app, lifespan startup, global error handler
│   ├── models.py             # Pydantic v2 input/output models
│   ├── core/
│   │   ├── config.py         # pydantic-settings env config (lru_cache)
│   │   └── security.py       # Fernet encrypt/decrypt helpers
│   ├── api/
│   │   ├── routes.py         # All API endpoints + rate limiting
│   │   └── dependencies.py   # Optional API key auth
│   ├── services/
│   │   ├── filter.py         # Signal/noise filter + threat classifier
│   │   ├── pipeline.py       # filter → classify → digest orchestration
│   │   ├── rag.py            # LangChain LCEL chain (ChromaDB + OpenAI)
│   │   ├── fallbacks.py      # Category-specific fallback checklists
│   │   └── rss_ingestor.py   # CISA + HackerNews RSS feed ingestion
│   └── db/
│       └── database.py       # SQLite persistence, encrypted location blobs
├── frontend/
│   └── index.html            # Dark UI — Submit Alert, Search, Dashboard, Safe Circle
├── data/
│   ├── security_docs.txt     # RAG knowledge base (6 safety categories)
│   └── sample_alerts.json    # Sample data for testing
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
└── .env                      # Secret keys (never commit this)
```

### Request flow

```
POST /api/v1/analyze
        │
        ▼
  filter_reports()       ← drops noise, keeps signal keywords
        │
        ▼
  location check         ← matches user_location or "national"
        │
        ▼
  classify_alert()       ← category + severity from keyword map
        │
        ▼
  generate_digest()      ← RAG chain (AI) or fallback checklist
        │
        ▼
  save_alert()           ← SQLite, location encrypted at rest
        │
        ▼
  AnalyzeResponse        ← alerts with digest steps returned to UI
```

---

## Quickstart (local)

### Prerequisites
- Python 3.11+
- An OpenAI API key with billing enabled

### 1. Clone and set up environment

```bash
git clone <repo-url>
cd community-guardian
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_KEY=your-fernet-key-here

# Your OpenAI API key (requires billing enabled)
OPENAI_API_KEY=sk-proj-...

# Optional: set a non-empty string to enable API key auth on all endpoints
API_KEY=
```

### 3. Run

```bash
uvicorn backend.main:app --reload
```

Open `http://localhost:8000` — the frontend loads automatically.
Interactive API docs: `http://localhost:8000/docs`

---

## Docker deployment

```bash
docker compose -f docker/docker-compose.yml up --build
```

The `data/` directory is mounted as a volume so the SQLite database and alert history persist across container restarts.

Health check: `http://localhost:8000/health`

---

## API Reference

### `POST /api/v1/analyze`
Submit community reports for analysis.

**Request:**
```json
{
  "reports": [
    { "text": "Phishing emails targeting Gmail users", "location": "Austin" }
  ],
  "user_location": "Austin"
}
```

**Response:**
```json
{
  "alerts": [{
    "alert": "Phishing emails targeting Gmail users",
    "location": "Austin",
    "category": "cyber_threat",
    "severity": "high",
    "digest": {
      "summary": "A phishing campaign is targeting local Gmail accounts.",
      "steps": [
        "Change your Gmail password immediately and enable 2FA.",
        "Do not click links in unexpected emails — verify senders directly.",
        "Check Google's security checkup at myaccount.google.com/security."
      ]
    },
    "method": "AI"
  }],
  "processed": 1,
  "filtered_out": 0
}
```

### `GET /api/v1/search?keyword=phishing`
Search stored alerts by keyword.

### `GET /api/v1/stats`
Returns total alerts, counts by severity, counts by category, and 5 most recent alerts.

### `POST /api/v1/ingest/rss`
Manually trigger RSS feed ingestion from CISA and The Hacker News.

### `POST /api/v1/safe-circle`
Send an encrypted message to a group circle.

```json
{ "message": "I'm safe. Sheltering at home.", "group_id": "my-family-2024" }
```

### `GET /api/v1/safe-circle/{group_id}`
Retrieve and decrypt all messages for a circle.

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `FERNET_KEY` | Yes | Base64 Fernet key for encrypting location data and messages |
| `OPENAI_API_KEY` | Yes | OpenAI API key — requires paid plan for embeddings and chat |
| `API_KEY` | No | If set, all endpoints require `X-API-Key: <value>` header. Leave empty to disable. |
| `SECURITY_DOCS_PATH` | No | Path to RAG knowledge base file (default: `data/security_docs.txt`) |
| `DB_PATH` | No | Path to SQLite database file (default: `data/alerts.db`) |

---

## Severity & category reference

| Category | Severity | Trigger keywords |
|---|---|---|
| `cyber_threat` | high | phishing, breach |
| `scam_alert` | medium | scam |
| `local_crime` | medium | theft |
| `infrastructure` | medium | outage |
| `general` | low | (catch-all) |

---

## Security design

- **Encryption at rest** — location data and Safe Circle messages are Fernet-encrypted before writing to SQLite. The raw location string is never stored.
- **No API key leakage** — the `X-API-Key` header auth is optional and disabled by default for local development.
- **No raw tracebacks** — a global exception handler returns `{"detail": "Internal server error"}` to clients; full stack traces go to server logs only.
- **Rate limiting** — all endpoints are rate-limited per IP (20–30 req/min for reads, 5–10 req/min for writes).
- **Input validation** — all inputs validated by Pydantic v2 with field length limits (reports max 2000 chars, max 50 per batch).

---

## Generating a Fernet key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the output as `FERNET_KEY` in your `.env`. Keep this secret — it's used to decrypt all stored location data and messages.

---

## Future work

### Near-term improvements
- **ML-based noise filter** — replace keyword matching with a fine-tuned classifier (e.g. DistilBERT) trained on labeled community reports to reduce false positives and catch threats that don't use exact keywords
- **Alert deduplication** — detect and merge near-duplicate reports (same event, multiple submissions) using embedding similarity before saving to the database
- **User accounts & alert subscriptions** — allow residents to register, set a home location, and receive email or push notifications only for alerts in their area
- **Severity confidence score** — expose a 0–1 confidence score alongside severity so the UI can communicate uncertainty to users
- **Persistent vector store** — replace in-memory ChromaDB with a persisted Chroma collection so the RAG knowledge base survives restarts without re-embedding on every boot

### Scalability
- **PostgreSQL backend** — swap SQLite for PostgreSQL with pgvector extension to support concurrent writes and vector search at scale
- **Async pipeline** — move the RAG digest generation to a background task queue (Celery + Redis) so `/analyze` returns immediately and digests are pushed when ready
- **Horizontal scaling** — containerize with a load balancer; the stateless FastAPI layer can scale independently of the database
- **Scheduled RSS ingestion** — replace the manual `/ingest/rss` endpoint with a cron job (APScheduler or external scheduler) that runs every 15 minutes automatically

### Features
- **Multi-language support** — detect report language and generate digests in the same language using GPT-4's multilingual capabilities
- **Verified source badge** — mark alerts that originated from official feeds (CISA, local government) vs. community-submitted reports so residents can weigh credibility
- **Alert expiry** — auto-archive alerts older than 30 days and expose an `/archive` endpoint so the dashboard stays relevant
- **Safe Circle read receipts** — track which group members have read each message using hashed member identifiers, without storing identities
- **Map view** — add a Leaflet.js map tab to the frontend that plots alert pins by location for spatial awareness
- **Export** — let users download their local alert history as a CSV or PDF report

### Security hardening
- **Key rotation** — add a `/admin/rotate-key` endpoint that re-encrypts all `location_enc` blobs with a new Fernet key without downtime
- **Audit logging** — write an append-only log of every alert submission and Safe Circle access with timestamps and hashed IPs for accountability
- **HTTPS enforcement** — add TLS termination via Nginx reverse proxy in the Docker Compose setup for production deployments
- **Content Security Policy** — add strict CSP headers to the frontend to prevent XSS on the served HTML

---

## Tech stack

- **FastAPI** — async web framework with automatic OpenAPI docs
- **LangChain LCEL** — modern chain pattern for RAG pipeline
- **ChromaDB** — in-memory vector store for semantic document retrieval
- **OpenAI** — `text-embedding-ada-002` for embeddings, `gpt-3.5-turbo` for digest generation
- **SQLite** — lightweight persistent storage, no external database required
- **Fernet (cryptography)** — symmetric authenticated encryption
- **pydantic-settings** — type-safe environment variable management
- **slowapi** — rate limiting middleware for FastAPI
- **feedparser** — RSS feed parsing for CISA and security news feeds
- **Docker** — containerized deployment with health checks
