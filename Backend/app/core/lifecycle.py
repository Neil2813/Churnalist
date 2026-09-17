"""
FastAPI application lifespan — startup and shutdown logic.

Startup order:
  1. Configure structured logging
  2. Create HTTP client
  3. Verify database connection & run pending migrations
  4. Initialise FTS5 virtual table if missing
  5. Load embedding model (once, on the main process)
  6. Initialise Groq LLM client wrapper
  7. Create task manager for background analysis runs

Shutdown:
  - Close HTTP client
  - Dispose DB engine
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.constants import HTTP_USER_AGENT
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager — replaces deprecated on_event handlers."""
    settings = get_settings()

    # 1. Configure logging
    configure_logging(
        log_level=settings.log_level,
        as_json=settings.is_production,
    )
    logger.info("drift_startup", env=settings.app_env, debug=settings.debug)

    # 2. Create shared HTTP client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect=10.0,
            read=settings.request_timeout_seconds,
            write=settings.request_timeout_seconds,
            pool=10.0,
        ),
        limits=httpx.Limits(
            max_connections=settings.max_concurrent_fetches * 2,
            max_keepalive_connections=settings.max_concurrent_fetches,
        ),
        headers={"User-Agent": HTTP_USER_AGENT},
        follow_redirects=True,
        max_redirects=5,
    )
    app.state.http_client = http_client
    logger.info("http_client_ready")

    # 3. DB engine + migrations
    from app.db.session import get_engine, get_session_factory
    from app.db.init_db import init_database

    engine = get_engine()
    _ = get_session_factory()
    await init_database(engine)
    app.state.db_engine = engine
    logger.info("database_ready")

    # 4. Embedding service (loads model into memory once)
    from app.embeddings.service import EmbeddingService
    embedding_service = EmbeddingService(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
    )
    await embedding_service.load()
    app.state.embedding_service = embedding_service
    logger.info("embedding_model_ready", model=settings.embedding_model)

    # 5. Groq LLM client
    from app.llm.client import GroqClient
    llm_client = GroqClient(
        api_key=settings.groq_api_key,
        default_model=settings.groq_model,
        fast_model=settings.groq_fast_model,
        timeout=settings.llm_timeout_seconds,
        max_concurrent=settings.max_concurrent_llm_calls,
    )
    app.state.llm_client = llm_client
    logger.info("llm_client_ready", model=settings.groq_model)

    # 6. Task manager
    from app.orchestration.task_manager import TaskManager
    task_manager = TaskManager()
    app.state.task_manager = task_manager
    logger.info("task_manager_ready")

    logger.info("drift_startup_complete")

    yield  # ← application runs

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("drift_shutdown_starting")

    await task_manager.shutdown()
    await http_client.aclose()

    from app.db.session import dispose_engine
    await dispose_engine()

    logger.info("drift_shutdown_complete")
