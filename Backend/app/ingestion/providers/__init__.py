"""Ingestion providers package."""
from __future__ import annotations

from app.ingestion.providers.currents import CurrentsProvider
from app.ingestion.providers.gnews import GNewsProvider
from app.ingestion.providers.guardian import GuardianProvider
from app.ingestion.providers.manual import ManualProvider
from app.ingestion.providers.mediastack import MediastackProvider
from app.ingestion.providers.newsdata import NewsDataProvider
from app.ingestion.providers.newsflash import NewsFlashProvider
from app.ingestion.providers.rss import RSSProvider
from app.ingestion.providers.spaceflight import SpaceflightProvider
from app.ingestion.providers.thenewsapi import TheNewsAPIProvider

__all__ = [
    "CurrentsProvider",
    "GNewsProvider",
    "GuardianProvider",
    "ManualProvider",
    "MediastackProvider",
    "NewsDataProvider",
    "NewsFlashProvider",
    "RSSProvider",
    "SpaceflightProvider",
    "TheNewsAPIProvider",
]
