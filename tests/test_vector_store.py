from __future__ import annotations

import pytest

from rag.chunking import structure_chunks
from rag.corpus import Corpus
from rag.embeddings import HashingEmbedder
from rag.vector_store import InMemoryVectorStore


def _store(corpus: Corpus) -> tuple[InMemoryVectorStore, HashingEmbedder]:
    embedder = HashingEmbedder(dimension=128)
    store = InMemoryVectorStore()
    chunks = structure_chunks(corpus)
    store.upsert(chunks, embedder.embed_documents([chunk.search_text for chunk in chunks]))
    return store, embedder


def test_store_round_trip_and_scores(corpus: Corpus) -> None:
    store, embedder = _store(corpus)

    results = store.search(
        embedder.embed_query("rotate API key v3"),
        tenant_id="northwind",
        top_k=5,
        current_only=True,
    )

    assert store.count() == sum(1 for _ in corpus.iter_blocks())
    assert results
    assert results[0].doc_id == "helios-api-keys"
    assert results[0].version == "v3"
    assert results[0].dense_score is not None
    assert results[0].score == results[0].dense_score
    assert results == sorted(results, key=lambda block: -block.score)


def test_store_tenant_filter(corpus: Corpus) -> None:
    store, embedder = _store(corpus)

    results = store.search(
        embedder.embed_query("failover command"),
        tenant_id="acme",
        top_k=10,
        current_only=True,
    )

    assert results
    assert all(block.tenant_id == "acme" for block in results)
    assert all("acme" in block.text for block in results)


def test_store_version_filters(corpus: Corpus) -> None:
    store, embedder = _store(corpus)
    query = embedder.embed_query("admins opt out of SSO")

    current = store.search(query, tenant_id="northwind", top_k=10, current_only=True)
    old = store.search(
        query,
        tenant_id="northwind",
        top_k=10,
        versions={"v2"},
    )

    assert current
    assert all(block.is_current for block in current)
    assert old
    assert all(block.version == "v2" for block in old)
    assert all(not block.is_current for block in old)


def test_store_validation_and_clear(corpus: Corpus) -> None:
    embedder = HashingEmbedder(dimension=8)
    store = InMemoryVectorStore(dimension=4)
    chunks = structure_chunks(corpus)[:1]

    with pytest.raises(ValueError, match="same length"):
        store.upsert(chunks, [])
    with pytest.raises(ValueError, match="dimension"):
        store.upsert(chunks, [embedder.embed_query("short")])

    store.clear()
    assert store.count() == 0
    assert store.status() == "ok"
