"""
Orchestration Provider with AWS Strands / Step Functions Primary & Python Async Pipeline Fallback.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OrchestrationProvider(ABC):
    """Abstract Base Class for Multi-Agent Investigation Orchestration."""

    @abstractmethod
    async def run_investigation(self, story_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute investigation pipeline over story context."""
        pass


class StrandsAgentsPrimaryProvider(OrchestrationProvider):
    """Primary Cloud Provider: AWS Strands Agents SDK / Step Functions State Machine."""

    def __init__(self) -> None:
        logger.info("Initialized AWS Strands Agents / Step Functions Primary Provider")

    async def run_investigation(self, story_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            import boto3
            client = boto3.client("stepfunctions")
            # Example Step Functions state machine trigger
            response = client.start_execution(
                stateMachineArn="arn:aws:states:us-east-1:123456789012:stateMachine:ChurnalistPipeline",
                name=f"investigation-{story_id}",
                input=str(payload)
            )
            return {"status": "started", "execution_arn": response.get("executionArn")}
        except Exception as e:
            logger.error(f"Strands / Step Functions execution error: {e}")
            raise RuntimeError(f"Cloud Orchestration failed: {e}")


class LocalAsyncPipelineFallbackProvider(OrchestrationProvider):
    """Local Fallback Provider: Python `asyncio` Investigation Pipeline."""

    def __init__(self) -> None:
        logger.info("Initialized Local Async Pipeline Fallback Provider")

    async def run_investigation(self, story_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        from app.orchestration.investigation_pipeline import InvestigationPipeline
        
        logger.info(f"[LOCAL ORCHESTRATOR FALLBACK] Running local pipeline for story {story_id}")
        pipeline = InvestigationPipeline()
        query = payload.get("query", "")
        mode = payload.get("mode", "auto")
        
        result = await pipeline.run(query=query, mode=mode)
        return result


def get_orchestrator_provider() -> OrchestrationProvider:
    """
    Factory function for OrchestrationProvider.
    Checks config for `use_strands_agents`. Default is Local Async Pipeline Fallback.
    """
    settings = get_settings()
    if settings.use_strands_agents:
        try:
            return StrandsAgentsPrimaryProvider()
        except Exception as e:
            logger.warning(f"Strands Agents primary failed ({e}). Falling back to Local Async Pipeline Provider.")
            return LocalAsyncPipelineFallbackProvider()

    logger.info("AWS Strands / Step Functions is OFF. Running on Local Async Pipeline Fallback.")
    return LocalAsyncPipelineFallbackProvider()
