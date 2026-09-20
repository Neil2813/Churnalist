"""
Domain-level constants and enumerations for the DRIFT backend.

All enums used in SQLAlchemy models and Pydantic schemas are defined here
so they can be imported from a single location.
"""
from __future__ import annotations

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        pass


# ── Event status ─────────────────────────────────────────────────────────────

class EventStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    INGESTING = "INGESTING"
    READY = "READY"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class TimePrecision(StrEnum):
    EXACT = "EXACT"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    UNKNOWN = "UNKNOWN"


# ── Source types ──────────────────────────────────────────────────────────────

class SourceType(StrEnum):
    OFFICIAL = "OFFICIAL"
    WIRE = "WIRE"
    NEWSROOM = "NEWSROOM"
    BLOG = "BLOG"
    PRESS_RELEASE = "PRESS_RELEASE"
    AGENCY = "AGENCY"
    OTHER = "OTHER"


# ── Article extraction status ─────────────────────────────────────────────────

class ExtractionStatus(StrEnum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


# ── Claim types ───────────────────────────────────────────────────────────────

class ClaimType(StrEnum):
    FACT = "FACT"
    NUMBER = "NUMBER"
    DATE = "DATE"
    LOCATION = "LOCATION"
    CAUSE = "CAUSE"
    ATTRIBUTION = "ATTRIBUTION"
    SEVERITY = "SEVERITY"
    CERTAINTY = "CERTAINTY"
    QUOTE = "QUOTE"
    ACTION = "ACTION"
    CASUALTY = "CASUALTY"
    STATUS = "STATUS"
    OTHER = "OTHER"


# ── Claim relation types ──────────────────────────────────────────────────────

class RelationType(StrEnum):
    SAME = "SAME"
    MODIFIED = "MODIFIED"
    ADDED = "ADDED"
    DROPPED = "DROPPED"
    CONTRADICTS = "CONTRADICTS"
    NUMERICAL_DRIFT = "NUMERICAL_DRIFT"
    ATTRIBUTION_LOSS = "ATTRIBUTION_LOSS"
    SEVERITY_AMPLIFICATION = "SEVERITY_AMPLIFICATION"
    SEVERITY_SOFTENING = "SEVERITY_SOFTENING"
    CERTAINTY_CHANGE = "CERTAINTY_CHANGE"
    SOURCE_DERIVED = "SOURCE_DERIVED"
    SYNDICATED = "SYNDICATED"
    TRANSLATED = "TRANSLATED"


# ── Correction types ──────────────────────────────────────────────────────────

class CorrectionType(StrEnum):
    NUMBER_CHANGE = "NUMBER_CHANGE"
    DATE_CHANGE = "DATE_CHANGE"
    NAME_CHANGE = "NAME_CHANGE"
    LOCATION_CHANGE = "LOCATION_CHANGE"
    ATTRIBUTION_CHANGE = "ATTRIBUTION_CHANGE"
    STATUS_CHANGE = "STATUS_CHANGE"
    FACTUAL_CORRECTION = "FACTUAL_CORRECTION"
    RETRACTION = "RETRACTION"
    CLARIFICATION = "CLARIFICATION"
    OTHER = "OTHER"


# ── Provenance edge relation types ────────────────────────────────────────────

class ProvenanceRelation(StrEnum):
    SOURCE_OF = "SOURCE_OF"
    DERIVED_FROM = "DERIVED_FROM"
    REWRITTEN_TO = "REWRITTEN_TO"
    TRANSLATED_TO = "TRANSLATED_TO"
    SYNDICATED_TO = "SYNDICATED_TO"
    COPIED_BY = "COPIED_BY"
    CORRECTED_BY = "CORRECTED_BY"
    REFERENCES = "REFERENCES"


# ── Analysis run status ───────────────────────────────────────────────────────

class AnalysisStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ── Analysis pipeline stages ──────────────────────────────────────────────────

class PipelineStage(StrEnum):
    SOURCE_HUNTING = "SOURCE_HUNTING"
    CLAIM_MINING = "CLAIM_MINING"
    EVENT_WEAVING = "EVENT_WEAVING"
    DRIFT_INVESTIGATION = "DRIFT_INVESTIGATION"
    TRUTH_TRAIL = "TRUTH_TRAIL"
    COMPLETED = "COMPLETED"


# ── Ingestion job status ──────────────────────────────────────────────────────

class IngestionStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# ── News provider names ────────────────────────────────────────────────────────

class ProviderName(StrEnum):
    RSS = "RSS"
    GNEWS = "GNEWS"
    NEWSDATA = "NEWSDATA"
    MEDIASTACK = "MEDIASTACK"
    CURRENTS = "CURRENTS"
    THENEWSAPI = "THENEWSAPI"
    GUARDIAN = "GUARDIAN"
    SPACEFLIGHT = "SPACEFLIGHT"
    NEWSFLASH = "NEWSFLASH"
    MANUAL = "MANUAL"
    WEB_SCRAPER = "WEB_SCRAPER"


# ── Confidence levels ─────────────────────────────────────────────────────────

class ConfidenceLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ── Entity types (for NLP extraction) ────────────────────────────────────────

class EntityType(StrEnum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DATE = "DATE"
    NUMBER = "NUMBER"
    EVENT = "EVENT"
    OTHER = "OTHER"


# ── Supported languages ───────────────────────────────────────────────────────

SUPPORTED_LANGUAGES: frozenset[str] = frozenset({
    "en",  # English
    "hi",  # Hindi
    "ta",  # Tamil
    "te",  # Telugu
    "bn",  # Bengali
    "mr",  # Marathi
    "gu",  # Gujarati
    "ml",  # Malayalam
    "kn",  # Kannada
    "pa",  # Punjabi
    "ur",  # Urdu
    "es",  # Spanish
    "fr",  # French
    "de",  # German
})

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "ml": "Malayalam",
    "kn": "Kannada",
    "pa": "Punjabi",
    "ur": "Urdu",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}

# Tracking parameters to strip during URL normalization
TRACKING_PARAMS: frozenset[str] = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "ref", "source", "mc_eid", "mc_cid",
})

# Correction signal keywords (used for deterministic correction detection)
CORRECTION_KEYWORDS: tuple[str, ...] = (
    "correction", "corrected", "updated", "update", "clarification",
    "clarified", "editor's note", "editors note", "retraction", "retracted",
    "revised", "revision", "amendment", "amended",
)

# HTTP user-agent for responsible scraping
HTTP_USER_AGENT = (
    "DRIFT-NewsProvenance/1.0 "
    "(Academic Research; https://github.com/drift-news/drift; "
    "contact: drift@research.dev)"
)

# Maximum redirects to follow
MAX_REDIRECTS = 5

# FTS5 table name
FTS_TABLE = "articles_fts"

# Minimum cosine similarity to consider a candidate relevant
MIN_EMBEDDING_SIMILARITY = 0.50

# Retrieval candidate limits
MAX_FTS_CANDIDATES = 50
MAX_SEMANTIC_CANDIDATES = 20
MAX_LLM_VERIFICATION_CANDIDATES = 10

# Time window for event clustering (hours)
EVENT_CLUSTER_WINDOW_HOURS = 72
