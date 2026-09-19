"""
Domain exception hierarchy for DRIFT.

All application errors map to these classes so that the global error handler
can produce consistent JSON responses without leaking stack traces.
"""
from __future__ import annotations

from http import HTTPStatus


class DriftError(Exception):
    """Base class for all domain errors."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ── 404 Not Found ─────────────────────────────────────────────────────────────

class NotFoundError(DriftError):
    status_code = HTTPStatus.NOT_FOUND

class EventNotFoundError(NotFoundError):
    error_code = "EVENT_NOT_FOUND"

class ArticleNotFoundError(NotFoundError):
    error_code = "ARTICLE_NOT_FOUND"

class ClaimNotFoundError(NotFoundError):
    error_code = "CLAIM_NOT_FOUND"

class AnalysisRunNotFoundError(NotFoundError):
    error_code = "ANALYSIS_RUN_NOT_FOUND"


# ── 400 Bad Request / Validation ──────────────────────────────────────────────

class ValidationError(DriftError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"

class InvalidURLError(DriftError):
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "INVALID_URL"

class UnsupportedURLSchemeError(DriftError):
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "UNSUPPORTED_URL_SCHEME"

class UnsupportedLanguageError(DriftError):
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "UNSUPPORTED_LANGUAGE"

class SSRFBlockedError(DriftError):
    status_code = HTTPStatus.FORBIDDEN
    error_code = "SSRF_BLOCKED"


# ── 413 Content Too Large ─────────────────────────────────────────────────────

class ArticleTooLargeError(DriftError):
    status_code = HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    error_code = "ARTICLE_TOO_LARGE"


# ── Ingestion & Extraction ────────────────────────────────────────────────────

class ArticleExtractionError(DriftError):
    error_code = "ARTICLE_EXTRACTION_FAILED"

class LanguageDetectionError(DriftError):
    error_code = "LANGUAGE_DETECTION_FAILED"

class NewsProviderError(DriftError):
    error_code = "NEWS_PROVIDER_ERROR"

class ExternalServiceError(DriftError):
    error_code = "EXTERNAL_SERVICE_ERROR"

class NewsProviderRateLimitError(NewsProviderError):
    error_code = "NEWS_PROVIDER_RATE_LIMITED"


class TranslationError(DriftError):
    status_code = HTTPStatus.BAD_GATEWAY
    error_code = "TRANSLATION_FAILED"



# ── LLM ──────────────────────────────────────────────────────────────────────

class LLMTimeoutError(DriftError):
    error_code = "LLM_TIMEOUT"

class LLMInvalidResponseError(DriftError):
    error_code = "LLM_INVALID_RESPONSE"

class LLMSchemaValidationError(DriftError):
    error_code = "LLM_SCHEMA_VALIDATION_FAILED"

class LLMQuotaExceededError(DriftError):
    error_code = "LLM_QUOTA_EXCEEDED"


# ── Embedding ─────────────────────────────────────────────────────────────────

class EmbeddingError(DriftError):
    error_code = "EMBEDDING_FAILED"


# ── Database ──────────────────────────────────────────────────────────────────

class DatabaseError(DriftError):
    error_code = "DATABASE_ERROR"


# ── Analysis ──────────────────────────────────────────────────────────────────

class AnalysisError(DriftError):
    error_code = "ANALYSIS_FAILED"

class AnalysisAlreadyRunningError(DriftError):
    status_code = HTTPStatus.CONFLICT
    error_code = "ANALYSIS_ALREADY_RUNNING"
