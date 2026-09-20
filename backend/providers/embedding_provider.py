"""Pluggable embedding provider implementations for xBookLibrary RAG."""

import hashlib
import math
from abc import ABC, abstractmethod
from typing import Any

import litellm


class BaseEmbeddingProvider(ABC):
    """Abstract base class for vector embedding generation."""

    def __init__(self, dimension: int = 768):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate normalized vector embeddings for a list of text passages."""
        pass

    async def embed_query(self, query: str) -> list[float]:
        """Generate normalized vector embedding for a single search query."""
        results = await self.embed_texts([query])
        return results[0]


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic in-memory embedding provider for testing and offline environments."""

    def __init__(self, dimension: int = 768):
        super().__init__(dimension=dimension)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in texts:
            # Generate deterministic floats from text hash
            vec: list[float] = []
            for i in range(self.dimension):
                seed_str = f"{text}_{i}"
                h = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)
                # Map to range [-1.0, 1.0]
                val = (h / 0xFFFFFFFF) * 2.0 - 1.0
                vec.append(val)

            # Normalize vector to unit length (L2 norm)
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
        return embeddings


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Embedding provider using Google Gemini text-embedding-004 via litellm."""

    def __init__(self, api_key: str | None = None, model: str = "text-embedding-004"):
        super().__init__(dimension=768)
        self.api_key = api_key
        self.model = model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        model_name = self.model if self.model.startswith("gemini/") else f"gemini/{self.model}"
        kwargs: dict[str, Any] = {
            "model": model_name,
            "input": texts,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key

        response = await litellm.aembedding(**kwargs)
        embeddings: list[list[float]] = []
        for item in response.data:
            emb = item["embedding"] if isinstance(item, dict) else item.embedding
            # Ensure unit normalization
            norm = math.sqrt(sum(x * x for x in emb))
            if norm > 0:
                emb = [x / norm for x in emb]
            embeddings.append(emb)
        return embeddings
