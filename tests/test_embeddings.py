from __future__ import annotations

import math

import pytest

from rag.embeddings import BgeM3Embedder, HashingEmbedder, build_embedder


def test_hashing_embedder_is_deterministic_and_normalised() -> None:
    embedder = HashingEmbedder(dimension=64)

    first = embedder.embed_query("rotate the API key")
    second = HashingEmbedder(dimension=64).embed_query("rotate the API key")

    assert first == second
    assert len(first) == 64
    assert math.isclose(math.sqrt(sum(value * value for value in first)), 1.0)
    assert all(value == 0.0 for value in embedder.embed_query(""))


def test_hashing_embedder_prefers_related_text() -> None:
    embedder = HashingEmbedder()
    query = embedder.embed_query("rotate an API key")

    related = embedder.embed_query("Rotate an API key in the developer settings")
    unrelated = embedder.embed_query("Prepaid billing credits expire after 18 months")

    related_score = sum(left * right for left, right in zip(query, related, strict=True))
    unrelated_score = sum(left * right for left, right in zip(query, unrelated, strict=True))
    assert related_score > unrelated_score


def test_embed_documents_batch() -> None:
    embedder = HashingEmbedder(dimension=32)
    vectors = embedder.embed_documents(["one", "two", "one"])

    assert len(vectors) == 3
    assert vectors[0] == vectors[2]
    assert embedder.name == "hashing-32"


def test_bge_m3_does_not_import_until_used() -> None:
    embedder = BgeM3Embedder()

    assert embedder._model is None
    assert embedder.dimension == 1024
    assert embedder.name == "BAAI/bge-m3"


def test_build_embedder() -> None:
    assert isinstance(build_embedder("hashing"), HashingEmbedder)
    assert isinstance(build_embedder("bge-m3"), BgeM3Embedder)
    with pytest.raises(ValueError, match="unknown embedder"):
        build_embedder("word2vec")
