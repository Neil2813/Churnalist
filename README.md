# Churnalist

### Autonomous AI-Driven News Provenance & Claim Drift Intelligence

**Churnalist** is a multi-agent platform that continuously traces how a news story's factual claims move, change, and get corrected as they spread across outlets, languages, and time. It hunts down the original sources feeding a story, weaves together the underlying sequence of events, mines the atomic factual claims being made, investigates how those claims drift between publications, and lays down an evidence-backed truth trail—turning a scattered set of articles into a single, navigable lineage of fact.

The platform moves news analysis from static, single-article reading to a proactive, evidence-backed investigation workflow. Editors and readers interact through an investigation and provenance workspace while a coordinated agent pipeline handles source discovery, claim mining, drift detection, and correction tracking end-to-end across English, Hindi, Tamil, Telugu, Bengali, and Kannada.

---

## Table of Contents
- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [AWS Stack](#aws-stack)
- [System Architecture](#system-architecture)
- [Multi-Agent Orchestrator](#multi-agent-orchestrator)
- [Multi-Agent Intelligence Core](#multi-agent-intelligence-core)
- [Claim Drift & Provenance Analysis](#claim-drift--provenance-analysis)
- [LLM & Embeddings Layer](#llm--embeddings-layer)
- [Frontend Application](#frontend-application)
- [Backend API Engine](#backend-api-engine)
- [Data Model](#data-model)
- [Project Structure](#project-structure)
- [Environment Configuration](#environment-configuration)
- [Local Development](#local-development)
- [Testing](#testing)

---

## Problem Statement

A news claim rarely stays fixed once it is published. It gets picked up, translated, rewritten, paraphrased, exaggerated, or quietly corrected as it spreads outward from its original source. Readers see only the single version of the story in front of them, with no visibility into:

* **Where a claim originally came from**, and which outlets are simply relaying it
* **How the same fact is being reported differently** in wording, severity, certainty, or attribution across sources and languages
* **Whether a number, quote, or claim has mutated** as it moved downstream
* **Whether a correction or retraction was ever issued**, and whether the uncorrected version is still circulating

Traditional news aggregation treats every article as an independent, disconnected unit. **Churnalist** instead treats a story as a graph: sources, claims, and the edges connecting them so drift, churn, and silent corrections become visible rather than invisible.

---

## Solution Overview

| Capability | Description |
| :--- | :--- |
| **Multilingual Source Discovery** | The *Source Hunter Agent* searches outward from a seed article to find original sources, wire-service origins, and regional coverage across languages |
| **Event Clustering** | The *Event Weaver Agent* groups multilingual coverage of the same underlying story into a single tracked Event, combining entity overlap, dense semantic similarity, and LLM verification |
| **Atomic Claim Extraction** | The *Claim Miner Agent* extracts verifiable factual assertions, quotes, dates, and figures from article text, mapping each claim back to its exact source span |
| **Claim Drift Detection** | The *Drift Investigator Agent* classifies how claims evolve between articles (`IDENTICAL`, `PARAPHRASE`, `SPECIFICATION`, `GENERALIZATION`, `MUTATION`, `CONTRADICTION`, or `UNVERIFIED_ADDITION`) with a quantified severity score |
| **Churnalism Scoring** | Verbatim n-gram overlap and copy-paste proportion are computed between articles to flag uncredited republishing |
| **Correction Tracking** | Editorial retraction, correction, update, and clarification notices are detected and linked to the claims they affect, surfacing silent corrections |
| **Truth Trail Synthesis** | The *Truth Trail Agent* produces a chronological timeline, source credibility view, drift analysis, and an overall reporting-integrity rating for an event |
| **Provenance Graph** | A directed graph of article derivation (`CITED`, `SYNDICATED`, `CHURNED`, or `INFERRED`) reconstructs how a story's content spread |
| **Multilingual Coverage** | First-class support for English, Hindi, Tamil, Telugu, Bengali, and Kannada across claim extraction, drift comparison, and article translation |

---

## AWS Stack

Churnalist's agent pipeline and data plane are built to run on AWS, using managed services and AWS open-source frameworks for orchestration, retrieval, storage, and observability:

| AWS / Platform Service | Role |
| :--- | :--- |
| **AWS Step Functions / Strands Agents SDK** | Coordinates the multi-agent orchestrator, dispatches ingestion jobs, and sequences the Source Hunter, Event Weaver, Claim Miner, Drift Investigator, and Truth Trail agents |
| **Amazon OpenSearch Service** | Vector and lexical retrieval over ingested articles and claims, backing source discovery and claim matching |
| **AWS S3** | Stores raw artifacts and evidence backing every claim, source, and provenance trace |
| **AWS CloudWatch** | Metrics and logs across ingestion, orchestration, and the agent pipeline |
| **Groq / Amazon Bedrock** | LLM inference engine powering claim mining, drift classification, event alignment, and truth-trail synthesis |

---

## System Architecture

Churnalist uses a decoupled architecture: a React/Vite frontend that gives editors an investigation, provenance, and story-clustering workspace, and a Python FastAPI backend that ingests articles, dispatches multi-agent runs, and exposes claim, drift, and report data through a versioned REST API.

```text
Frontend Layer
  Home Dashboard · Investigation & Editorial Trace UI
  Provenance & Claim Lineage UI · Story Clustering & Narratives
  Axios Client + SSE Stream Handler
      │
      │  HTTP REST / SSE
      ▼
FastAPI API & Ingestion
  API Router · Ingestion Service & Scraper · Server-Sent Events
      │
      │  DISPATCH JOB
      ▼
Multi-Agent Orchestrator
  AWS Step Functions / Strands Agents SDK
      │
      ▼
Multi-Agent Intelligence Core
  Source Hunter → Event Weaver → Claim Miner → Drift Investigator → Truth Trail
      │
      ├───────────────┬────────────────────┬─────────────────────┐
      ▼               ▼                    ▼                     ▼
LLM Inference   Vector & Lexical      Artifact & Evidence    Telemetry &
Engine (Groq)   Retrieval             Store (AWS S3)         Observability
                (OpenSearch +                                (AWS CloudWatch)
                Embedding Model Engine)
```

---

## Multi-Agent Orchestrator

The orchestrator, built on **AWS Step Functions / Strands Agents SDK**, receives dispatched ingestion jobs from the API layer and sequences execution across the intelligence core:

1. **Source Hunting** — Ingest the seed article and discover related coverage across news providers and RSS feeds.
2. **Event Weaving** — Cluster articles covering the same underlying story using incident boundaries, location, entities, and timing.
3. **Claim Mining** — Extract atomic factual claims (Subject-Predicate-Object) from every article in the event.
4. **Drift Investigation** — Compare claims across articles, score drift severity, flag copy-paste overlap, and detect corrections.
5. **Truth Trail Synthesis** — Assemble the provenance graph and compile the final executive investigation report.

---

## Multi-Agent Intelligence Core

| Agent | Responsibility |
| :--- | :--- |
| **Source Hunter Agent** | Searches outward from a seed article or topic to discover original sources, wire-service origins, and regional coverage across languages |
| **Event Weaver Agent** | Clusters related multilingual articles covering the same story into a unified Event, using entity/keyword overlap, dense semantic similarity, and LLM verification for borderline pairs |
| **Claim Miner Agent** | Extracts verifiable factual assertions, quotes, dates, and figures from article content, mapping each claim to its exact source span and generating an English-normalized translation for non-English claims |
| **Drift Investigator Agent** | Compares claims chronologically across articles, classifies each pair (`IDENTICAL`, `PARAPHRASE`, `SPECIFICATION`, `GENERALIZATION`, `MUTATION`, `CONTRADICTION`, `UNVERIFIED_ADDITION`) with a severity score, computes churnalism overlap, and detects correction notices |
| **Truth Trail Agent** | Synthesizes every prior agent's output into a chronological timeline, source credibility view, drift analysis, corrections status, and an overall reporting-integrity rating |

---

## Claim Drift & Provenance Analysis

| Module | What It Measures |
| :--- | :--- |
| **Churnalism Scoring** | Verbatim n-gram overlap and copy-paste proportion between articles, flagging uncredited republishing |
| **Claim Evolution & Drift** | Classifies claim pairs into `IDENTICAL`, `PARAPHRASE`, `SPECIFICATION`, `GENERALIZATION`, `MUTATION`, `CONTRADICTION`, or `UNVERIFIED_ADDITION`, each with a 0.0–1.0 severity score |
| **Correction Detection** | Identifies retraction, correction, update, and clarification notices in article text and links them to the claims they affect, including silent (unflagged) corrections |
| **Provenance Graph** | Builds a directed graph of article derivation: `CITED`, `SYNDICATED`, `CHURNED`, `INFERRED` showing how content propagated from source to downstream coverage |

---

## LLM & Embeddings Layer

* **Groq (`llama-3.3-70b-versatile`) / Amazon Bedrock** drives reasoning across every agent: claim extraction, event alignment, drift classification, and truth-trail report synthesis.
* A dedicated embedding model engine (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) generates cross-lingual dense vectors feeding vector and lexical retrieval (Amazon OpenSearch), enabling source discovery and event clustering across English, Hindi, Tamil, Telugu, Bengali, and Kannada.

---

## Frontend Application

Built with **React**, **TypeScript**, and **Vite**.

### Pages
| Route | Page | Purpose |
| :--- | :--- | :--- |
| `/` | **Home** | Headline feed, URL input to trigger an investigation, language selector, breaking news and recent story list |
| `/investigate/:eventId` | **Investigation** | Split-screen original vs. downstream article view, claim drift badges, extracted entities, translation toggle |
| `/stories` | **Stories** | Index of clustered news events with source counts, mutation flags, and filtering |
| `/provenance/:eventId` | **Provenance** | Interactive graph of article derivation (`CITED` / `SYNDICATED` / `CHURNED`), timeline sequence, and copy-overlap percentages |

### Key Frontend Components
| Component | Role |
| :--- | :--- |
| `LanguageContext` | Provides the selected language and translation state across every page |
| `uiTranslations` | UI label dictionaries across English, Hindi, Tamil, Telugu, Bengali, and Kannada |
| `Axios Client + SSE Stream Handler` | Talks to the FastAPI backend over REST and consumes live Server-Sent Events progress streams |

---

## Backend API Engine

FastAPI backend, versioned under `/api/v1`.

### Ingestion & Articles
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/articles/ingest-url` | Fetches, parses, and extracts an article from a URL, runs language detection, and generates embeddings |
| `POST` | `/api/v1/articles/ingest-rss` | Parses an RSS/Atom feed and ingests all discovered entries |
| `GET` | `/api/v1/articles` | Paginated article list, filterable by language, domain, and event |
| `GET` | `/api/v1/articles/{article_id}` | Full article detail by ID |
| `GET` | `/api/v1/articles/{article_id}/translate` | Translates an article's title and body into a target language |

### News Discovery
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/news/top` | Live breaking headlines across multiple news providers, filterable by category and query |

### Events
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/events` | Creates a new news event cluster |
| `GET` | `/api/v1/events` | Paginated list of tracked events |
| `GET` | `/api/v1/events/{event_id}` | Event detail with associated articles |
| `POST` | `/api/v1/events/discover` | Discovers related articles and groups them under an event |

### Claims & Drift
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/claims` | Extracts and stores claims for an article |
| `GET` | `/api/v1/claims/event/{event_id}` | All claims extracted from an event's articles |
| `GET` | `/api/v1/claims/event/{event_id}/relations` | Claim-to-claim relationship pairs for an event |
| `GET` | `/api/v1/claims/event/{event_id}/drift` | Classified claim mutations, contradictions, and churnalism records |

### Multi-Agent Analysis Runs
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/analysis/run` | Triggers the end-to-end multi-agent analysis pipeline for an event or seed URL |
| `GET` | `/api/v1/analysis/runs/{run_id}` | Status, stage progress, and output of an analysis run |

### Provenance & Corrections
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/provenance/graph/{event_id}` | Directed graph of article derivation and content lineage |
| `GET` | `/api/v1/corrections/event/{event_id}` | Detected retraction and correction notices for an event |

### Reports & Sources
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/reports/event/{event_id}` | Executive truth trail report — timeline, consensus claims, drift findings |
| `POST` | `/api/v1/sources` | Registers a news source with credibility and bias metadata |
| `GET` | `/api/v1/sources` | Lists registered sources |

### Utility & Health
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Application health, including database and LLM provider connectivity |
| `GET` | `/health/live` | Liveness probe |
| `GET` | `/health/ready` | Readiness probe |

---

## Data Model

| Entity | Key Fields |
| :--- | :--- |
| **Article** | `url`, `canonical_url`, `title`, `byline`, `published_at`, `language`, `content_clean`, `word_count`, `embedding` |
| **ArticleTranslation** | `article_id`, `target_language`, `translated_title`, `translated_content` |
| **Claim** | `article_id`, `event_id`, `claim_text`, `claim_type`, `char_start`, `char_end`, `extracted_entities`, `confidence`, `original_language`, `original_text`, `english_translation`, `extracted_value` |
| **ClaimRelation** | `source_claim_id`, `target_claim_id`, `relation_type`, `severity_score`, `explanation`, `drift_category` |
| **Correction** | `article_id`, `correction_type`, `notice_text`, `claims_affected`, `is_silent` |
| **Event** | `title`, `description`, `primary_source_id`, `first_reported_at` |
| **ProvenanceEdge** | `event_id`, `parent_article_id`, `child_article_id`, `derivation_type`, `verbatim_overlap`, `confidence` |
| **Source** | `domain`, `name`, `bias_rating`, `factuality_rating`, `country`, `is_wire_service` |
| **AnalysisRun** | `event_id`, `status`, `current_stage`, `progress_percent`, `stages_data` |

---

## Project Structure

```text
Churnalist/
├── Backend/
│   ├── alembic/                       # Database migrations
│   ├── app/
│   │   ├── agents/                    # Source Hunter, Event Weaver, Claim Miner,
│   │   │                              # Drift Investigator, Truth Trail
│   │   ├── analysis/                  # Churnalism, drift classification,
│   │   │                              # correction detection, graph building
│   │   ├── api/v1/                    # FastAPI route controllers
│   │   ├── core/                      # Config, errors, logging
│   │   ├── db/models/                 # SQLAlchemy ORM models
│   │   ├── embeddings/                # Multilingual embedding encoder
│   │   ├── ingestion/
│   │   │   └── providers/             # News provider integrations
│   │   ├── llm/                       # LLM client abstraction
│   │   ├── orchestration/             # Analysis pipeline, stages, task manager
│   │   ├── prompts/                   # Agent prompt templates
│   │   ├── retrieval/                 # Hybrid lexical + semantic retrieval
│   │   ├── schemas/                   # Pydantic request/response models
│   │   ├── services/                  # Live news, translation services
│   │   ├── utils/                     # Text, time, URL helpers
│   │   └── main.py                    # API entry point
│   ├── scripts/                       # Operational and migration scripts
│   └── tests/
│       ├── integration/
│       └── unit/
│
└── Frontend/
    └── src/
        ├── context/                   # LanguageContext
        ├── pages/                     # Home, Investigation, Stories, Provenance
        ├── utils/                     # UI translation dictionaries
        ├── api.ts                     # Axios / fetch client
        └── App.tsx
```

---

## Environment Configuration

| Variable | Purpose |
| :--- | :--- |
| `LLM_PROVIDER` | Selects the LLM inference provider (`groq` / `bedrock`) |
| `GROQ_API_KEY` | API key for Groq inference |
| `GROQ_MODEL` | Model used for agent reasoning (`llama-3.3-70b-versatile`) |
| `EMBEDDING_MODEL_NAME` | Multilingual embedding model for semantic retrieval (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) |
| `GNEWS_API_KEY` / `NEWSDATA_API_KEY` / `GUARDIAN_API_KEY` | News provider credentials for source discovery and ingestion |
| `CORS_ORIGINS` | Allowed frontend origins |
| `LOG_LEVEL` | Backend log verbosity |
| `CHURNALISM_NGRAM_SIZE` / `CHURNALISM_THRESHOLD` | Copy-paste overlap detection tuning |
| `DRIFT_SEVERITY_THRESHOLD` | Threshold for flagging significant claim drift |

---

## Local Development

### Backend Setup
```bash
cd Backend
python -m venv .venv
# Activate venv:
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
python -m app.db.init_db

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
* Backend runs at `http://localhost:8000`
* Interactive API docs at `http://localhost:8000/docs`

### Frontend Setup
```bash
cd Frontend
npm install
npm run dev
```
* Frontend runs at `http://localhost:5173`

---

## Testing

```bash
cd Backend
pytest
```

| Test Suite | Coverage |
| :--- | :--- |
| `test_churnalism.py` | N-gram tokenization, Jaccard similarity, copy-paste overlap |
| `test_claim_miner.py` | Claim extraction, confidence, character span mapping |
| `test_corrections.py` | Correction and retraction language detection |
| `test_drift.py` | Claim relationship classification and severity scoring |
| `test_event_weaver.py` | Semantic clustering and threshold grouping |
| `test_language_detector.py` | Multilingual language identification |
| `test_multilingual.py` | Translation pipeline, multilingual claim mapping, and end-to-end analysis |
| `test_retrieval.py` | Lexical and semantic search ranking |
| `test_api.py` | FastAPI route responses and schemas |
| `test_pipeline.py` | Multi-agent orchestration, end to end |

---

**Churnalist** — *tracing every claim back to the truth.*  
Built by team CodeFather.