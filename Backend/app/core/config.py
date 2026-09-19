from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ─────────────────────────────────────────────────────────
    app_name: str = "DRIFT"
    app_env: Literal["development", "production", "test", "demo"] = "development"
    debug: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./data/news.db"

    # ── Groq LLM ─────────────────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model: str = "groq/compound"
    groq_fast_model: str = "groq/compound-mini"



    # ── Timeouts (seconds) ────────────────────────────────────────────────────
    request_timeout_seconds: float = 15.0
    llm_timeout_seconds: float = 60.0

    # ── Content limits ────────────────────────────────────────────────────────
    max_article_bytes: int = 5_000_000
    max_article_chars: int = 100_000

    # ── Concurrency ──────────────────────────────────────────────────────────
    max_concurrent_fetches: int = 8
    max_concurrent_llm_calls: int = 4

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── Embeddings ────────────────────────────────────────────────────────────
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_device: str = "cpu"

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── Pipeline versions ────────────────────────────────────────────────────
    pipeline_version: str = "1.0"
    claim_extractor_version: int = 1
    drift_engine_version: int = 1
    report_version: int = 1

    # ── News API keys & Endpoints (optional – system degrades gracefully) ─────
    gnews_api_key: str = Field("", validation_alias=AliasChoices("gnews_api_key", "gnews"))
    newsdata_api_key: str = Field("", validation_alias=AliasChoices("newsdata_api_key", "newsdata"))
    mediastack_api_key: str = Field("", validation_alias=AliasChoices("mediastack_api_key", "mediastack"))
    currents_api_key: str = Field("", validation_alias=AliasChoices("currents_api_key", "currents"))
    thenewsapi_api_key: str = Field("", validation_alias=AliasChoices("thenewsapi_api_key", "thenewsapi", "the_news_api"))
    guardian_api_key: str = Field("", validation_alias=AliasChoices("guardian_api_key", "guardians", "guardian"))
    spaceflight_url: str = Field("https://api.spaceflightnewsapi.net/v4/articles/", validation_alias=AliasChoices("spaceflight_url", "spaceflight"))
    newsflash_api_key: str = Field("", validation_alias=AliasChoices("newsflash_api_key", "news_flash", "newsflash"))

    @field_validator(
        "groq_api_key",
        "gnews_api_key",
        "newsdata_api_key",
        "mediastack_api_key",
        "currents_api_key",
        "thenewsapi_api_key",
        "guardian_api_key",
        "newsflash_api_key",
        mode="before",
    )
    @classmethod
    def clean_api_keys(cls, v: Any) -> str:
        if not v or not isinstance(v, str):
            return ""
        # Strip inline comments and whitespace
        val = v.split("#")[0].strip()
        return val

    # ── Retrieval scoring weights ─────────────────────────────────────────────
    score_weight_embedding: float = 0.30
    score_weight_lexical: float = 0.20
    score_weight_entity: float = 0.20
    score_weight_temporal: float = 0.15
    score_weight_location: float = 0.10
    score_weight_source: float = 0.05

    # ── Derived helpers ───────────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def scoring_weights(self) -> dict[str, float]:
        return {
            "embedding": self.score_weight_embedding,
            "lexical": self.score_weight_lexical,
            "entity": self.score_weight_entity,
            "temporal": self.score_weight_temporal,
            "location": self.score_weight_location,
            "source": self.score_weight_source,
        }

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
