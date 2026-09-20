import math

import pytest

from backend.providers.embedding_provider import (
    BaseEmbeddingProvider,
    GeminiEmbeddingProvider,
    MockEmbeddingProvider,
)


@pytest.mark.asyncio
async def test_mock_embedding_provider_dimensions_and_normalization():
    provider = MockEmbeddingProvider(dimension=768)
    assert provider.dimension == 768
    assert isinstance(provider, BaseEmbeddingProvider)

    texts = ["First passage about science", "Second passage about history"]
    embeddings = await provider.embed_texts(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 768
    assert len(embeddings[1]) == 768

    # Verify unit-length normalization (L2 norm ≈ 1.0)
    norm = math.sqrt(sum(x * x for x in embeddings[0]))
    assert pytest.approx(norm, rel=1e-3) == 1.0


@pytest.mark.asyncio
async def test_mock_embedding_provider_deterministic_similarity():
    provider = MockEmbeddingProvider(dimension=768)

    # Identical texts should have cosine similarity 1.0
    vec1 = await provider.embed_query("quantum computing")
    vec2 = await provider.embed_query("quantum computing")
    vec3 = await provider.embed_query("gardening and flowers")

    dot_same = sum(a * b for a, b in zip(vec1, vec2, strict=False))
    dot_diff = sum(a * b for a, b in zip(vec1, vec3, strict=False))

    assert pytest.approx(dot_same, rel=1e-3) == 1.0
    assert dot_same > dot_diff


@pytest.mark.asyncio
async def test_gemini_embedding_provider_mocked(monkeypatch):
    provider = GeminiEmbeddingProvider(api_key="fake-test-key", model="text-embedding-004")
    assert provider.dimension == 768

    async def fake_aembedding(*args, **kwargs):
        class FakeResponse:
            data = [
                {"embedding": [0.1] * 768},
                {"embedding": [0.2] * 768},
            ]

        return FakeResponse()

    import litellm

    monkeypatch.setattr(litellm, "aembedding", fake_aembedding)

    embeddings = await provider.embed_texts(["hello", "world"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 768
