# Churnalist Frontend Workspace

The **Churnalist Frontend** is the editorial workspace where a news story's claims, sources, and drift are made visible through a home dashboard, an investigation/editorial trace view, a claim provenance/lineage view, and story clustering—all backed by live streaming from the backend.

---

## Table of Contents
- [System Architecture](#system-architecture)
- [Frontend Layer Components](#frontend-layer-components)
- [Quick Start](#quick-start)

---

## System Architecture

The frontend communicates with the FastAPI backend over HTTP REST and Server-Sent Events (SSE).

```text
Frontend Layer (React / Vite / Tailwind / CSS)
      │
      │  HTTP REST / SSE
      ▼
FastAPI API & Ingestion (Backend)
```

---

## Frontend Layer Components

| Component | Role | Path |
| :--- | :--- | :--- |
| **Home Dashboard** | Landing view, topic search input, category filters, breaking news feed | `src/pages/Home.tsx` |
| **Investigation & Editorial Trace UI** | Step through a story's editorial trace, claim mutation badges, and article comparisons | `src/pages/Investigation.tsx` |
| **Provenance & Claim Lineage UI** | Visualize where a claim came from and how it evolved over time | `src/pages/Provenance.tsx` |
| **Story Clustering & Narratives** | Groups related coverage into a unified narrative thread | `src/pages/Stories.tsx` |
| **Story Verification Report** | Interactive executive verification report UI | `src/components/StoryVerificationReport.tsx` |
| **Axios Client & SSE Stream Handler** | Talks to the backend over REST and consumes live Server-Sent Events progress streams | `src/api.ts` |

---

## Quick Start

```bash
# Install dependencies
npm install

# Run Vite development server
npm run dev
```
Frontend development server runs at `http://localhost:5173`

---

**Churnalist Frontend** — *tracing every claim back to the truth.*