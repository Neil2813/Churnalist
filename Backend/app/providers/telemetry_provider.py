"""
Telemetry & Metrics Provider with AWS CloudWatch Primary & Local Logger Fallback.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TelemetryProvider(ABC):
    """Abstract Base Class for Metric Logging & Observability."""

    @abstractmethod
    def log_metric(self, metric_name: str, value: float, unit: str = "Count", dimensions: dict[str, str] | None = None) -> None:
        """Log metric measurement."""
        pass

    @abstractmethod
    def log_event(self, event_name: str, data: dict[str, Any]) -> None:
        """Log structured event telemetry."""
        pass


class CloudWatchPrimaryProvider(TelemetryProvider):
    """Primary Cloud Provider: AWS CloudWatch Logs & Metrics (PutMetricData)."""

    def __init__(self) -> None:
        try:
            import boto3
            self.cloudwatch = boto3.client("cloudwatch")
            logger.info("Initialized AWS CloudWatch Telemetry Primary Provider")
        except Exception as e:
            logger.warning(f"Failed to initialize CloudWatch client: {e}")
            self.cloudwatch = None

    def log_metric(self, metric_name: str, value: float, unit: str = "Count", dimensions: dict[str, str] | None = None) -> None:
        if not self.cloudwatch:
            return
        dims = [{"Name": k, "Value": v} for k, v in (dimensions or {}).items()]
        try:
            self.cloudwatch.put_metric_data(
                Namespace="DRIFT/Investigation",
                MetricData=[
                    {
                        "MetricName": metric_name,
                        "Value": value,
                        "Unit": unit,
                        "Dimensions": dims
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to push metric to CloudWatch: {e}")

    def log_event(self, event_name: str, data: dict[str, Any]) -> None:
        logger.info(f"[CLOUDWATCH EVENT] {event_name}: {data}")


class LocalTelemetryFallbackProvider(TelemetryProvider):
    """Local Fallback Provider: Local Structured Python Logging."""

    def __init__(self) -> None:
        logger.info("Initialized Local Telemetry Fallback Provider (Structured Console & Log File)")

    def log_metric(self, metric_name: str, value: float, unit: str = "Count", dimensions: dict[str, str] | None = None) -> None:
        logger.info(f"[METRIC FALLBACK] {metric_name}={value} ({unit}) | dims={dimensions or {}}")

    def log_event(self, event_name: str, data: dict[str, Any]) -> None:
        logger.info(f"[EVENT FALLBACK] {event_name} -> {data}")


def get_telemetry_provider() -> TelemetryProvider:
    """
    Factory function for TelemetryProvider.
    Checks config for `use_cloudwatch`. Default is Local Logger Fallback.
    """
    settings = get_settings()
    if settings.use_cloudwatch:
        try:
            return CloudWatchPrimaryProvider()
        except Exception as e:
            logger.warning(f"CloudWatch primary failed ({e}). Falling back to Local Telemetry Logger.")
            return LocalTelemetryFallbackProvider()

    return LocalTelemetryFallbackProvider()
