"""FastAPI endpoint for system health checks."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["Health"])


class HealthCheckResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    service: str = "DRIFT Backend"


@router.get("", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Return 200 OK health status."""
    return HealthCheckResponse()
