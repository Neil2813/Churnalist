"""
Investigation Pipeline Orchestrator for Churnalist backend.

Executes the end-to-end 21-step "Trace a Story" investigation pipeline:
1. ingest_seed
2. extract_anchor_metadata
3. build_event_context
4. generate_search_queries
5. search_serpapi_duckduckgo
6. normalize_results
7. candidate_event_matching
8. deduplicate
9. fetch_articles
10. extract_article_content
11. chunk_documents
12. index_rag
13. extract_claims
14. retrieve_evidence
15. align_claims
16. detect_drift
17. detect_internal_inconsistency
18. detect_corrections
19. build_provenance
20. generate_report
21. persist_report
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.claim_miner import ClaimMinerAgent
from app.agents.drift_investigator import DriftInvestigatorAgent
from app.agents.event_weaver import EventWeaverAgent
from app.analysis.inconsistency import InconsistencyDetector
from app.core.constants import AnalysisStatus, PipelineStage
from app.core.logging import get_logger
from app.db.models.analysis_run import AnalysisRun
from app.db.models.article import Article
from app.db.models.claim import Claim
from app.db.models.claim_relation import ClaimRelation
from app.db.models.correction import Correction
from app.db.models.event import Event
from app.db.models.provenance import ProvenanceEdge
from app.db.models.search_result import SearchResult
from app.db.repositories.analysis_repository import AnalysisRepository
from app.db.repositories.claim_repository import ClaimRepository
from app.db.repositories.correction_repository import CorrectionRepository
from app.ingestion.article_extractor import ArticleExtractor, fetch_and_extract
from app.ingestion.async_fetcher import BoundedAsyncFetcher
from app.ingestion.deduplicator import DeduplicationAction, Deduplicator
from app.llm.groq_report_generator import GroqReportGenerator
from app.retrieval.candidate_retriever import CandidateRetriever
from app.retrieval.event_retriever import EventRetriever
from app.services.event_context_service import EventContextService
from app.services.search.serpapi_service import SerpAPIService
from app.utils.hashing import content_hash, hash_url

logger = get_logger(__name__)


class InvestigationPipeline:
    """Orchestrates the 21-step Trace a Story pipeline."""

    def __init__(self) -> None:
        self.extractor = ArticleExtractor()
        self.event_context_service = EventContextService()
        self.serpapi_service = SerpAPIService()
        self.candidate_retriever = CandidateRetriever()
        self.bounded_fetcher = BoundedAsyncFetcher()
        self.event_retriever = EventRetriever()
        self.claim_miner = ClaimMinerAgent()
        self.event_weaver = EventWeaverAgent()
        self.drift_investigator = DriftInvestigatorAgent()
        self.inconsistency_detector = InconsistencyDetector()
        self.report_generator = GroqReportGenerator()

    async def execute(
        self,
        db: AsyncSession,
        seed_url: str,
        run_id: str | None = None,
    ) -> tuple[Event, str]:
        """
        Execute full 21-step pipeline for a seed URL.
        Returns the created/updated Event record and run_id.
        """
        run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        logger.info("pipeline_start", run_id=run_id, url=seed_url)

        # ── Step 1: Ingest seed ───────────────────────────────────────────
        seed_raw = await fetch_and_extract(seed_url)

        # ── Step 2: Extract anchor metadata & Create Event ────────────────
        anchor_title = seed_raw.title or "Anchor News Article"
        anchor_content = seed_raw.content or ""
        anchor_pub = seed_raw.published_at or datetime.now(timezone.utc)
        anchor_source = seed_raw.source_name or "Seed Source"

        c_hash = content_hash(f"{anchor_title}:{anchor_pub.isoformat()[:10]}")
        stmt_evt = select(Event).where(Event.canonical_hash == c_hash)
        res_evt = await db.execute(stmt_evt)
        existing_evt = res_evt.scalar_one_or_none()

        if existing_evt:
            event = existing_evt
            event.status = "DISCOVERING"
        else:
            event = Event(
                id=f"evt_{uuid.uuid4().hex[:12]}",
                title=anchor_title,
                canonical_summary=anchor_content[:300],
                status="DISCOVERING",
                anchor_timestamp=anchor_pub,
                canonical_hash=c_hash,
            )
            db.add(event)
        await db.flush()

        # Create or fetch AnalysisRun
        run = AnalysisRun(
            id=run_id,
            event_id=event.id,
            status=AnalysisStatus.RUNNING,
            current_stage=PipelineStage.SOURCE_HUNTING,
            started_at=datetime.utcnow(),
            pipeline_version="1.0",
        )
        await AnalysisRepository.create_run(db, run)

        try:
            # Store Anchor Article in DB
            u_h = hash_url(seed_url)
            stmt_exist = select(Article).where(Article.url_hash == u_h)
            res_exist = await db.execute(stmt_exist)
            existing_anchor = res_exist.scalar_one_or_none()

            if existing_anchor:
                existing_anchor.event_id = event.id
                existing_anchor.title = anchor_title or existing_anchor.title
                existing_anchor.content = anchor_content or existing_anchor.content
                anchor_article = existing_anchor
            else:
                anchor_article = Article(
                    id=f"art_{uuid.uuid4().hex[:12]}",
                    event_id=event.id,
                    url=seed_url,
                    canonical_url=seed_raw.canonical_url or seed_url,
                    url_hash=u_h,
                    title=anchor_title,
                    content=anchor_content,
                    content_hash=seed_raw.content_hash or content_hash(anchor_content),
                    language=seed_raw.language or "en",
                    published_at=anchor_pub,
                    retrieved_at=datetime.now(timezone.utc),
                    extraction_status="FULL",
                )
                db.add(anchor_article)
            await db.flush()

            # ── Step 3: Build Event Context ───────────────────────────────────
            event_ctx = await self.event_context_service.build_event_context(
                title=anchor_title,
                content=anchor_content,
                published_at=anchor_pub,
                source_name=anchor_source,
            )
            event.incident_type = event_ctx.incident_type
            event.search_window_start = event_ctx.search_window_start
            event.search_window_end = event_ctx.search_window_end
            event.locations_json = json.dumps(event_ctx.locations)
            event.countries_json = json.dumps(event_ctx.countries)
            event.organizations_json = json.dumps(event_ctx.organizations)
            event.entities_json = json.dumps(event_ctx.important_entities)
            await db.flush()

            # ── Step 4 & 5: Generate queries & Search SerpAPI/DuckDuckGo ──────
            queries = self.event_context_service.generate_search_queries(event_ctx)
            raw_search_results: list[dict[str, Any]] = []

            for q in queries:
                res_items = await self.serpapi_service.search(
                    query=q,
                    start_date=event_ctx.search_window_start.strftime("%Y-%m-%d") if event_ctx.search_window_start else None,
                    end_date=event_ctx.search_window_end.strftime("%Y-%m-%d") if event_ctx.search_window_end else None,
                    limit=10,
                )
                raw_search_results.extend(res_items)

            # ── Step 6: Normalize search results & persist to DB ─────────────
            search_models: list[SearchResult] = []
            for item in raw_search_results:
                search_models.append(
                    SearchResult(
                        id=f"srch_{uuid.uuid4().hex[:12]}",
                        event_id=event.id,
                        run_id=run.id,
                        search_query=item.get("search_query", ""),
                        engine=item.get("engine", "duckduckgo"),
                        provider="serpapi",
                        title=item.get("title"),
                        url=item.get("url", ""),
                        snippet=item.get("snippet"),
                        source=item.get("source"),
                        published_at=None,
                        position=item.get("position", 1),
                        raw_response_json=item.get("raw_json"),
                    )
                )
            if search_models:
                db.add_all(search_models)
                await db.flush()

            # ── Step 7: Candidate event matching (casualty independent) ───────
            matched_candidates = self.candidate_retriever.filter_candidates(
                candidates=raw_search_results,
                context=event_ctx,
                min_threshold=0.20,
            )

            # ── Step 8: Deduplicate candidate URLs ────────────────────────────
            unique_candidates: list[dict[str, Any]] = []
            seen_urls = {hash_url(seed_url)}

            for cand in matched_candidates:
                cand_url = cand.get("url", "")
                u_h = hash_url(cand_url)
                if u_h not in seen_urls:
                    seen_urls.add(u_h)
                    unique_candidates.append(cand)

            unique_candidates = unique_candidates[:15]

            # ── Step 9 & 10: Fetch articles & Extract content ─────────────────
            run.current_stage = PipelineStage.CLAIM_MINING
            fetched_articles = await self.bounded_fetcher.fetch_all_candidates(unique_candidates)

            db_articles: list[Article] = [anchor_article]
            for f_art in fetched_articles:
                cand_hash = f_art.url_hash or hash_url(f_art.url)
                stmt_cand = select(Article).where(Article.url_hash == cand_hash)
                res_cand = await db.execute(stmt_cand)
                existing_cand = res_cand.scalar_one_or_none()

                if existing_cand:
                    existing_cand.event_id = event.id
                    db_articles.append(existing_cand)
                else:
                    art_model = Article(
                        id=f"art_{uuid.uuid4().hex[:12]}",
                        event_id=event.id,
                        url=f_art.url,
                        canonical_url=f_art.canonical_url,
                        url_hash=cand_hash,
                        title=f_art.title,
                        content=f_art.content,
                        content_hash=f_art.content_hash,
                        language=f_art.language or "en",
                        published_at=f_art.published_at or datetime.now(timezone.utc),
                        retrieved_at=f_art.retrieved_at or datetime.now(timezone.utc),
                        extraction_status=f_art.extraction_status,
                    )
                    db.add(art_model)
                    db_articles.append(art_model)
            await db.flush()

            # ── Step 11 & 12: Chunk documents & Index RAG corpus ──────────────
            all_chunks: list[dict[str, Any]] = []
            for art in db_articles:
                chunks = await self.event_retriever.index_article_chunks(
                    session=db,
                    article_id=art.id,
                    event_id=event.id,
                    content=art.content or "",
                    url=art.url,
                    source_name=art.source_type,
                    published_at=art.published_at,
                    language=art.language,
                )
                for chk in chunks:
                    all_chunks.append({
                        "chunk_id": chk.id,
                        "article_id": chk.article_id,
                        "event_id": chk.event_id,
                        "source_name": chk.source_name,
                        "url": chk.url,
                        "published_at": chk.published_at.isoformat() if chk.published_at else None,
                        "language": chk.language,
                        "content": chk.content,
                    })

            # ── Step 13: Extract atomic claims ────────────────────────────────
            all_claims: list[dict[str, Any]] = []
            for art in db_articles:
                claims = await self.claim_miner.mine_claims(
                    article_id=art.id,
                    event_id=event.id,
                    title=art.title or "",
                    content=art.content or "",
                    language=art.language or "en",
                )
                all_claims.extend(claims)
                claim_models = [
                    Claim(
                        id=f"clm_{uuid.uuid4().hex[:12]}",
                        article_id=c["article_id"],
                        event_id=c["event_id"],
                        claim_type=c["claim_type"],
                        subject=c.get("subject"),
                        predicate=c.get("predicate"),
                        object_value=c.get("object_value"),
                        object_unit=c.get("object_unit"),
                        raw_text=c.get("raw_text"),
                        original_language=c.get("original_language"),
                        original_text=c.get("original_text"),
                        english_translation=c.get("english_translation"),
                        extracted_value=str(c.get("extracted_value")) if c.get("extracted_value") else None,
                        source_start_offset=c.get("source_start_offset"),
                        source_end_offset=c.get("source_end_offset"),
                        attribution=c.get("attribution"),
                        certainty=c.get("certainty"),
                        severity=c.get("severity"),
                    )
                    for c in claims
                ]
                if claim_models:
                    await ClaimRepository.bulk_create(db, claim_models)

            # ── Step 14: Retrieve evidence ────────────────────────────────────
            evidence_chunks = await self.event_retriever.retrieve_evidence_chunks(
                session=db,
                event_id=event.id,
                query=anchor_title,
                top_k=12,
            )

            # ── Step 15 & 16: Align claims & Detect drift ─────────────────────
            run.current_stage = PipelineStage.DRIFT_INVESTIGATION
            relations: list[dict[str, Any]] = []
            if len(db_articles) >= 2:
                art_a_claims = [c for c in all_claims if c.get("article_id") == db_articles[0].id]
                art_b_claims = [c for c in all_claims if c.get("article_id") == db_articles[1].id]
                relations = await self.drift_investigator.investigate_claim_drift(
                    source_claims=art_a_claims,
                    target_claims=art_b_claims,
                    source_lang=db_articles[0].language or "en",
                    target_lang=db_articles[1].language or "en",
                )

            # Persist claim relations
            relation_models: list[ClaimRelation] = []
            for rel in relations:
                if rel.get("source_claim_id") and rel.get("target_claim_id"):
                    relation_models.append(
                        ClaimRelation(
                            id=f"rel_{uuid.uuid4().hex[:12]}",
                            source_claim_id=rel["source_claim_id"],
                            target_claim_id=rel["target_claim_id"],
                            relation_type=rel["relation_type"],
                            confidence=rel.get("confidence", 0.8),
                            reason=rel.get("reason"),
                        )
                    )
            if relation_models:
                await ClaimRepository.bulk_create_relations(db, relation_models)

            # ── Step 17: Detect internal article inconsistencies ─────────────
            inconsistencies: list[dict[str, Any]] = []
            for art in db_articles:
                inc_items = self.inconsistency_detector.check_article(
                    article_id=art.id,
                    event_id=event.id,
                    headline=art.title or "",
                    body=art.content or "",
                )
                inconsistencies.extend(inc_items)

            # ── Step 18: Detect corrections ───────────────────────────────────
            art_dicts = [
                {"id": a.id, "title": a.title, "content": a.content, "language": a.language}
                for a in db_articles
            ]
            corrections = self.drift_investigator.track_corrections(
                event_id=event.id,
                articles=art_dicts,
                claims=all_claims,
            )
            corr_models: list[Correction] = []
            for cor in corrections:
                corr_models.append(
                    Correction(
                        id=f"cor_{uuid.uuid4().hex[:12]}",
                        event_id=event.id,
                        article_id=cor.get("article_id"),
                        correction_text=cor.get("correction_text", "Correction identified."),
                        correction_type=cor.get("correction_type", "OTHER"),
                        original_claim_text=cor.get("original_claim_text"),
                        corrected_claim_text=cor.get("corrected_claim_text"),
                        confidence=cor.get("confidence", 0.7),
                    )
                )
            if corr_models:
                await CorrectionRepository.bulk_create(db, corr_models)

            # ── Step 19: Build provenance edges ───────────────────────────────
            prov_edges: list[ProvenanceEdge] = []
            for art_a, art_b in zip(db_articles[:-1], db_articles[1:]):
                prov_edges.append(
                    ProvenanceEdge(
                        id=f"prv_{uuid.uuid4().hex[:12]}",
                        from_entity_type="article",
                        from_entity_id=art_a.id,
                        to_entity_type="article",
                        to_entity_id=art_b.id,
                        relation_type="REPOSTED" if art_a.content_hash == art_b.content_hash else "DERIVED_FROM",
                        confidence=0.9,
                    )
                )
            if prov_edges:
                db.add_all(prov_edges)
                await db.flush()

            # ── Step 20 & 21: Generate & Persist Investigation Report ─────────
            run.current_stage = PipelineStage.TRUTH_TRAIL
            event_info = {
                "id": event.id,
                "title": event.title,
                "incident_type": event.incident_type,
                "location_name": event.location_name,
                "event_time": event.event_time.isoformat() if event.event_time else None,
            }
            report_dict = await self.report_generator.generate_investigation_report(
                event_info=event_info,
                articles=art_dicts,
                claims=all_claims,
                relations=relations,
                inconsistencies=inconsistencies,
                corrections=corrections,
                evidence_chunks=evidence_chunks,
            )

            event.status = "COMPLETED"
            run.status = AnalysisStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            run.result_summary_json = json.dumps(report_dict)
            await db.flush()

            logger.info("pipeline_completed", run_id=run.id, event_id=event.id, articles=len(db_articles))
            return event, run.id

        except Exception as exc:
            logger.error("pipeline_failed", run_id=run.id, error=str(exc), exc_info=exc)
            try:
                await db.rollback()
                stmt_r = select(AnalysisRun).where(AnalysisRun.id == run.id)
                res_r = await db.execute(stmt_r)
                r_obj = res_r.scalar_one_or_none()
                if r_obj:
                    r_obj.status = AnalysisStatus.FAILED
                    r_obj.error_message = str(exc)
                    await db.commit()
            except Exception as fail_err:
                logger.error("failed_to_mark_investigation_run_failed", exc_info=fail_err)
            raise exc
