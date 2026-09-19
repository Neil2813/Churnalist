# Models package — import all models so Alembic autogenerate sees them
from app.db.models.event import Event
from app.db.models.source import Source
from app.db.models.article import Article, ArticleVersion, ArticleTranslation
from app.db.models.claim import Claim
from app.db.models.claim_relation import ClaimRelation
from app.db.models.correction import Correction
from app.db.models.provenance import ProvenanceEdge
from app.db.models.analysis_run import AnalysisRun
from app.db.models.ingestion_job import IngestionJob

__all__ = [
    "Event",
    "Source",
    "Article",
    "ArticleVersion",
    "ArticleTranslation",
    "Claim",
    "ClaimRelation",
    "Correction",
    "ProvenanceEdge",
    "AnalysisRun",
    "IngestionJob",
]
