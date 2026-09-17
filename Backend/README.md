# DRIFT Backend

**News Provenance & Multilingual Claim Drift Intelligence**

> Same event. Different versions. One traceable story.

---

## Quick Start

```bash
# 1. Create and activate the virtual environment (already done)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure environment variables
copy .env.example .env
# Edit .env — set GROQ_API_KEY at minimum

# 4. Run database migrations
alembic upgrade head

# 5. Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

---

## Architecture

Five logical AI agents orchestrated as a single pipeline:

| Agent | Role |
|---|---|
| **Source Hunter** | Discovers related articles from RSS, GNews, NewsData, and direct URLs |
| **Claim Miner** | Extracts atomic structured claims with source text spans |
| **Event Weaver** | Clusters articles describing the same real-world event |
| **Drift Investigator** | Detects numerical drift, attribution loss, severity changes, and churnalism |
| **Truth Trail** | Generates human-readable provenance reports from structured evidence |

---

## Project Structure

```
app/
├── core/          Settings, exceptions, logging, lifecycle
├── db/            SQLAlchemy models, session, FTS5 init
├── api/           FastAPI route handlers (v1)
├── agents/        The 5 AI agents
├── orchestration/ Analysis pipeline + task manager
├── services/      Application service layer
├── ingestion/     Web scraper + news API providers
├── retrieval/     FTS5 + semantic search + reranking
├── embeddings/    Local multilingual embedding service
├── llm/           Groq client wrapper
├── analysis/      Deterministic analysis modules
├── schemas/       Pydantic request/response schemas
├── prompts/       Versioned LLM prompt templates
└── utils/         URL, hashing, date, text helpers
```

---

## Environment Variables

See `.env.example` for all configuration options.

Required:
- `GROQ_API_KEY` — Groq API key for LLM inference

Optional (system degrades gracefully without them):
- `GNEWS_API_KEY` — GNews free tier key
- `NEWSDATA_API_KEY` — NewsData.io free tier key

---

## Running Tests

```bash
.venv\Scripts\pytest tests/ -v
```
