"""
Storage Provider with AWS S3 Primary & Local FileSystem Fallback.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class StorageProvider(ABC):
    """Abstract Base Class for Evidence & Report Storage Operations."""

    @abstractmethod
    async def save_artifact(self, category: str, filename: str, data: str | dict[str, Any]) -> str:
        """Save artifact content and return URI/Path."""
        pass

    @abstractmethod
    async def get_artifact(self, category: str, filename: str) -> str | None:
        """Retrieve artifact content by category and filename."""
        pass


class S3StoragePrimaryProvider(StorageProvider):
    """Primary Cloud Provider: AWS S3 / LocalStack S3 Bucket."""

    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name
        try:
            import boto3
            self.s3_client = boto3.client("s3")
            logger.info(f"Initialized AWS S3 Primary Storage Provider for bucket: {bucket_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize AWS S3 client: {e}")
            self.s3_client = None

    async def save_artifact(self, category: str, filename: str, data: str | dict[str, Any]) -> str:
        if not self.s3_client:
            raise RuntimeError("S3 client is unavailable")
        
        body = json.dumps(data) if isinstance(data, dict) else data
        key = f"{category}/{filename}"
        self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=body.encode("utf-8"))
        return f"s3://{self.bucket_name}/{key}"

    async def get_artifact(self, category: str, filename: str) -> str | None:
        if not self.s3_client:
            return None
        key = f"{category}/{filename}"
        try:
            res = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return res["Body"].read().decode("utf-8")
        except Exception as e:
            logger.error(f"Error fetching s3 object {key}: {e}")
            return None


class LocalStorageFallbackProvider(StorageProvider):
    """Local Fallback Provider: Local FileSystem Storage (`./data/raw/`, `./data/reports/`)."""

    def __init__(self, base_dir: str = "./data") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized Local Storage Fallback Provider at {self.base_dir.resolve()}")

    async def save_artifact(self, category: str, filename: str, data: str | dict[str, Any]) -> str:
        target_dir = self.base_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / filename
        
        content = json.dumps(data, indent=2) if isinstance(data, dict) else str(data)
        target_file.write_text(content, encoding="utf-8")
        logger.debug(f"[LOCAL STORAGE FALLBACK] Saved artifact: {target_file}")
        return str(target_file.resolve())

    async def get_artifact(self, category: str, filename: str) -> str | None:
        target_file = self.base_dir / category / filename
        if not target_file.exists():
            return None
        return target_file.read_text(encoding="utf-8")


def get_storage_provider() -> StorageProvider:
    """
    Factory function for StorageProvider.
    Checks config for `use_aws_s3`. Default is Local FileSystem Fallback.
    """
    settings = get_settings()
    if settings.use_aws_s3 and settings.aws_s3_bucket:
        try:
            return S3StoragePrimaryProvider(bucket_name=settings.aws_s3_bucket)
        except Exception as e:
            logger.warning(f"AWS S3 primary failed ({e}). Falling back to Local FileSystem Storage.")
            return LocalStorageFallbackProvider()

    logger.info("AWS S3 is OFF. Running on Local Storage Fallback Provider.")
    return LocalStorageFallbackProvider()
