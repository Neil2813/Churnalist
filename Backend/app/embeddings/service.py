"""
Multilingual embedding service using sentence-transformers.

Loads a single multilingual model once at startup and provides
synchronous batched embedding generation via a thread-pool executor
so it doesn't block the async event loop.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from app.core.logging import get_logger

logger = get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="embedding")


class EmbeddingService:
    """
    Singleton embedding service backed by a local sentence-transformers model.

    Model is loaded once during application startup.
    Embeddings are cached in-process by SHA-256(text + model_name).
    """

    def __init__(self, model_name: str, device: str = "cpu") -> None:
        self.model_name = model_name
        self.device = device
        self._model = None
        self._cache: dict[str, list[float]] = {}

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    async def load(self) -> None:
        """Load the model in a thread so startup doesn't block the event loop."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, self._load_sync)

    def _load_sync(self) -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore
        logger.info("embedding_model_loading", model=self.model_name, device=self.device)
        self._model = SentenceTransformer(self.model_name, device=self.device)
        logger.info("embedding_model_loaded", model=self.model_name)

    def _cache_key(self, text: str) -> str:
        raw = f"{text}||{self.model_name}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def embed_text(self, text: str) -> list[float]:
        """Return the embedding vector for a single text string."""
        key = self._cache_key(text)
        if key in self._cache:
            return self._cache[key]
        result = await self.embed_many([text])
        return result[0]

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a list of texts (batched)."""
        if not self._model:
            raise RuntimeError("EmbeddingService.load() was not called before embed_many()")

        # Separate cached from uncached
        keys = [self._cache_key(t) for t in texts]
        uncached_indices = [i for i, k in enumerate(keys) if k not in self._cache]
        uncached_texts = [texts[i] for i in uncached_indices]

        if uncached_texts:
            loop = asyncio.get_event_loop()
            vectors = await loop.run_in_executor(
                _executor,
                lambda: self._model.encode(uncached_texts, convert_to_numpy=True).tolist(),
            )
            for i, vec in zip(uncached_indices, vectors):
                self._cache[keys[i]] = vec

        return [self._cache[k] for k in keys]

    def embedding_to_json(self, vector: list[float]) -> str:
        """Serialise a vector to a JSON string for SQLite storage."""
        return json.dumps(vector)

    def json_to_embedding(self, json_str: str) -> list[float]:
        """Deserialise a vector from SQLite storage."""
        return json.loads(json_str)

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)
