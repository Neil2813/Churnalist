"""
Async SQLAlchemy engine and session factory for DRIFT.

Engine is created once at startup and reused for the lifetime of the application.
Sessions are created per-request via dependency injection.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _ensure_data_dir(database_url: str) -> None:
    """Create the data directory if using a file-based SQLite path."""
    if "sqlite" in database_url and "///" in database_url:
        path_part = database_url.split("///", 1)[-1]
        if path_part and path_part != ":memory:":
            db_path = Path(path_part)
            db_path.parent.mkdir(parents=True, exist_ok=True)


def create_engine() -> AsyncEngine:
    """Create and return the async SQLAlchemy engine."""
    settings = get_settings()
    _ensure_data_dir(settings.database_url)

    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        # SQLite-specific pragmas via connect_args
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    )
    logger.info("database_engine_created", url=settings.database_url.split("///")[-1])
    return engine


def get_engine() -> AsyncEngine:
    """Return the application-level engine singleton."""
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the application-level session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a new DB session per request.

    Usage:
        async def my_route(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Cleanly dispose the engine on application shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        logger.info("database_engine_disposed")
        _engine = None
