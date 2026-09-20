"""
Providers module exporting primary cloud vs local fallback interfaces.
"""
from app.providers.search_provider import SearchProvider, get_search_provider
from app.providers.storage_provider import StorageProvider, get_storage_provider
from app.providers.orchestration_provider import OrchestrationProvider, get_orchestrator_provider
from app.providers.telemetry_provider import TelemetryProvider, get_telemetry_provider

__all__ = [
    "SearchProvider",
    "get_search_provider",
    "StorageProvider",
    "get_storage_provider",
    "OrchestrationProvider",
    "get_orchestrator_provider",
    "TelemetryProvider",
    "get_telemetry_provider",
]
