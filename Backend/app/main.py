"""
DRIFT FastAPI application entry point.
"""
from __future__ import annotations

import uuid
from http import HTTPStatus

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import DriftError
from app.core.lifecycle import lifespan

settings = get_settings()

app = FastAPI(
    title="DRIFT — News Provenance Intelligence",
    description=(
        "Reconstruct the lifecycle of information: original source → "
        "published article → multilingual rewrite → claim drift → correction."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request ID middleware ─────────────────────────────────────────────────────
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(DriftError)
async def drift_error_handler(request: Request, exc: DriftError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "request_id": structlog.contextvars.get_contextvars().get("request_id", ""),
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger = structlog.get_logger(__name__)
    logger.error("unhandled_exception", exc_info=exc)
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": structlog.contextvars.get_contextvars().get("request_id", ""),
                "details": {},
            }
        },
    )


# ── Health endpoints ──────────────────────────────────────────────────────────
@app.get("/health/live", tags=["Health"], summary="Liveness probe")
async def liveness():
    """Returns 200 if the process is alive."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"], summary="Readiness probe")
async def readiness(request: Request):
    """
    Returns 200 if all critical subsystems are ready:
    - Database connection
    - Embedding model loaded
    """
    checks: dict[str, str] = {}

    # DB check
    try:
        from app.db.session import get_engine
        from sqlalchemy import text
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Embedding check
    embedding_service = getattr(request.app.state, "embedding_service", None)
    checks["embedding_model"] = "ok" if embedding_service and embedding_service.is_loaded else "not_loaded"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )


# ── API v1 router (registered after routes are built in later phases) ─────────
from app.api.router import api_router  # noqa: E402
app.include_router(api_router, prefix="/api/v1")
