# Churnalist Backend Engine

The **Churnalist Backend** ingests articles, dispatches multi-agent analysis jobs, and coordinates a five-agent intelligence core that hunts sources, weaves events, mines claims, investigates drift, and builds a truth trail—backed by an LLM inference engine, a vector/lexical retrieval layer, an evidence store, and pipeline telemetry.

---

## Table of Contents
- [System Architecture](#system-architecture)
- [FastAPI API & Ingestion](#fastapi-api--ingestion)
- [Multi-Agent Orchestrator](#multi-agent-orchestrator)
- [Multi-Agent Intelligence Core](#multi-agent-intelligence-core)
- [LLM Inference Engine](#llm-inference-engine)
- [Vector & Lexical Retrieval](#vector--lexical-retrieval)
- [Artifact & Evidence Store](#artifact--evidence-store)
- [Telemetry & Observability](#telemetry--observability)
- [Quick Start](#quick-start)

---

## System Architecture

```text
FastAPI API & Ingestion
      │
      │  DISPATCH JOB
      ▼
Multi-Agent Orchestrator
      │
      ▼
Multi-Agent Intelligence Core
 (Source Hunter → Event Weaver → Claim Miner → Drift Investigator → Truth Trail)
      │
      ├───────────────┬────────────────────┬─────────────────────┐
      ▼               ▼                    ▼                     ▼
LLM Inference   Vector & Lexical      Artifact & Evidence    Telemetry &
Engine (Groq)   Retrieval             Store                  Observability
```

---

## FastAPI API & Ingestion

| Component | Role | Path |
| :--- | :--- | :--- |
| **API Router** | Routes incoming REST requests from the frontend | `app/api/v1/` |
| **Ingestion Service & Scraper** | Pulls in and scrapes source articles for processing | `app/ingestion/orchestrator.py`, `app/ingestion/article_extractor.py` |
| **Server-Sent Events** | Streams ingestion and analysis progress back to the frontend | `app/main.py` |

---

## Multi-Agent Orchestrator

Coordinates dispatched ingestion jobs and sequences execution across the multi-agent intelligence core.

| Component | Path |
| :--- | :--- |
| **Orchestrator / Pipeline Runner** | `app/orchestration/analysis_pipeline.py` |
| **Pipeline Context & Progress** | `app/orchestration/pipeline_context.py`, `progress.py` |
| **Task Dispatch & State Management** | `app/orchestration/task_manager.py` |

---

## Multi-Agent Intelligence Core

| Agent | Role | Path |
| :--- | :--- | :--- |
| **Source Hunter Agent** | Locates and surfaces the sources behind a story | `app/agents/source_hunter.py` |
| **Event Weaver Agent** | Assembles the underlying sequence of events from those sources | `app/agents/event_weaver.py` |
| **Claim Miner Agent** | Extracts the atomic factual claims being made | `app/agents/claim_miner.py` |
| **Drift Investigator Agent** | Compares claims across sources and versions to detect drift | `app/agents/drift_investigator.py` |
| **Truth Trail Agent** | Builds the end-to-end provenance trail tying claims back to evidence | `app/agents/truth_trail.py` |

---

## LLM Inference Engine

Groq (`llama-3.3-70b-versatile`) and Amazon Bedrock power the reasoning layer for the multi-agent intelligence core.

| Component | Path |
| :--- | :--- |
| **LLM Client Wrapper** | `app/llm/client.py` |
| **Agent Prompt Templates** | `app/prompts/` |

---

## Vector & Lexical Retrieval

| Component | Role | Path |
| :--- | :--- | :--- |
| **Amazon OpenSearch Service / FTS Retrieval** | Vector and lexical search over ingested source material and claims | `app/retrieval/fts_retriever.py`, `app/retrieval/semantic_retriever.py`, `app/retrieval/candidate_retriever.py` |
| **Embedding Model Engine** | Generates the embeddings that power retrieval | `app/embeddings/service.py` |

---

## Artifact & Evidence Store

Persists raw artifacts, HTML snapshots, JSON claim matrices, and evidence that every claim, source, and lineage trace is backed by.

---

## Telemetry & Observability

Provides structured logging and pipeline execution metric tracking across the ingestion, orchestration, and agent layers.

| Component | Path |
| :--- | :--- |
| **Structured Logging** | `app/core/logging.py` |

---

## Quick Start

```bash
# 1. Activate environment
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # macOS/Linux

# 2. Run initial database setup
python -m app.db.init_db

# 3. Start Uvicorn development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Interactive API Documentation: `http://localhost:8000/docs`

---

**Churnalist Backend** — *tracing every claim back to the truth.*