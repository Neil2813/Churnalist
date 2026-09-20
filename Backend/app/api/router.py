"""
Top-level API router that aggregates all v1 routes.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.articles import router as articles_router
from app.api.v1.sources import router as sources_router
from app.api.v1.events import router as events_router
from app.api.v1.claims import router as claims_router
from app.api.v1.analysis import router as analysis_router, runs_router
from app.api.v1.provenance import router as provenance_router
from app.api.v1.health import router as health_router
from app.api.v1.corrections import router as corrections_router
from app.api.v1.reports import router as reports_router
from app.api.v1.news import router as news_router

api_router = APIRouter()

api_router.include_router(articles_router)
api_router.include_router(sources_router)
api_router.include_router(events_router)
api_router.include_router(claims_router)
api_router.include_router(analysis_router)
api_router.include_router(runs_router)
api_router.include_router(provenance_router)
api_router.include_router(health_router)
api_router.include_router(corrections_router)
api_router.include_router(reports_router)
api_router.include_router(news_router)

