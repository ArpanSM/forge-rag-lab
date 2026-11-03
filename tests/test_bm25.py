from __future__ import annotations

from rag.bm25 import BM25Index
from rag.corpus import Corpus
from rag.text import tokenize


def _index(corpus: Corpus) -> BM25Index:
    index = BM25Index()
    index.add(corpus.iter_retrieved())
    return index


def test_tokenize_drops_stopwords_and_punctuation() -> None:
    assert tokenize("How do I rotate an API key?") == ["rotate", "api", "key"]


def test_bm25_ranks_relevant_blocks(corpus: Corpus) -> None:
    index = _index(corpus)

    results = index.search(
        "rotate API key v3",
        tenant_id="northwind",
        top_k=5,
        current_only=True,
    )

    assert results
    assert results[0].doc_id == "helios-api-keys"
    assert results[0].version == "v3"
    assert results[0].bm25_score is not None
    assert results[0].bm25_score > 0
    assert results[0].retrieval_source == "bm25"


def test_bm25_current_version_filter(corpus: Corpus) -> None:
    index = _index(corpus)

    results = index.search(
        "admins opt out of SSO",
        tenant_id="northwind",
        top_k=10,
        current_only=True,
    )

    assert results
    assert all(block.is_current for block in results)
    assert all(block.version == "v3" for block in results)
    assert all(block.tenant_id == "northwind" for block in results)


def test_bm25_explicit_version_filter(corpus: Corpus) -> None:
    index = _index(corpus)

    results = index.search(
        "admins opt out of SSO",
        tenant_id="northwind",
        top_k=10,
        versions={"v2"},
    )

    assert results
    assert all(block.version == "v2" for block in results)
    assert all(not block.is_current for block in results)


def test_bm25_tenant_isolation(corpus: Corpus) -> None:
    index = _index(corpus)

    acme = index.search("failover command", tenant_id="acme", top_k=10)
    northwind = index.search("failover command", tenant_id="northwind", top_k=10)

    assert acme and northwind
    assert all(block.tenant_id == "acme" for block in acme)
    assert all(block.tenant_id == "northwind" for block in northwind)
    assert acme[0].text != northwind[0].text


def test_bm25_empty_and_limit(corpus: Corpus) -> None:
    index = _index(corpus)

    assert index.search("", tenant_id="northwind") == []
    assert index.search("rotate", tenant_id="") == []
    assert len(index.search("API keys", tenant_id="northwind", top_k=2)) == 2
