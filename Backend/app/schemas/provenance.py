"""Pydantic schemas for Provenance Graph Nodes and Edges."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ProvenanceRelation


class ProvenanceEdgeResponse(BaseModel):
    """Schema representing an edge in the provenance graph."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    from_type: str
    from_id: str
    to_type: str
    to_id: str
    relation: ProvenanceRelation
    confidence: float = 1.0
    created_at: datetime


class ProvenanceGraphNode(BaseModel):
    """Node in the visual provenance graph."""
    id: str
    label: str
    node_type: str  # "SOURCE", "ARTICLE", "CLAIM", "CORRECTION"
    language: str | None = None
    source_name: str | None = None
    url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProvenanceGraphResponse(BaseModel):
    """Graph response representing full event provenance network."""
    event_id: str
    nodes: list[ProvenanceGraphNode] = Field(default_factory=list)
    edges: list[ProvenanceEdgeResponse] = Field(default_factory=list)
