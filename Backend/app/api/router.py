"""
Top-level API router that aggregates all v1 routes.
Additional sub-routers will be registered as phases are completed.
"""
from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()

# Routes will be mounted here as each phase is implemented.
# Placeholder — prevents import errors in main.py during Phase 1.
