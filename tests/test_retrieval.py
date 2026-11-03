from __future__ import annotations

from collections.abc import Sequence

from rag.bm25 import BM25Index
from rag.chunking import structure_chunks
from rag.corpus import Corpus
from rag.embeddings import HashingEmbedder
from rag.models import RetrievedBlock
from rag.retrieval import (
    CrossEncoderReranker,
    HybridRetriever,
    NoopReranker,
    reciprocal_rank_fusion,
)
from rag.vector_store import InMemoryVectorStore


def _fixed_retriever(corpus: Corpus) -> HybridRetriever:
    retriever = HybridRetriever(
        HashingEmbedder(),
        InMemoryVectorStore(),
        bm25=BM25Index(),
        reranker=NoopReranker(),
    )
    retriever.index(structure_chunks(corpus))
    return retriever


def _baseline_retriever(corpus: Corpus) -> HybridRetriever:
    retriever = HybridRetriever(
        HashingEmbedder(),
        InMemoryVectorStore(),
        bm25=None,
        reranker=NoopReranker(),
    )
    retriever.index(structure_chunks(corpus))
    return retriever


def test_fixed_retrieval_excludes_stale_versions(corpus: Corpus) -> None:
    retriever = _fixed_retriever(corpus)

    results = retriever.retrieve(
        "How long do rotated keys stay valid?",
        tenant_id="northwind",
        top_k=5,
        current_only=True,
    )

    assert results
    assert results[0].ref == "helios-api-keys@v3#b4"
    assert all(block.version == "v3" for block in results)
    assert all(block.is_current for block in results)
    assert all(
        "bm25" in block.retrieval_source or "dense" in block.retrieval_source for block in results
    )


def test_fixed_retrieval_version_filter(corpus: Corpus) -> None:
    retriever = _fixed_retriever(corpus)

    results = retriever.retrieve(
        "How do I rotate an API key in v2?",
        tenant_id="northwind",
        top_k=5,
        current_only=False,
        versions={"v2"},
    )

    assert results
    assert all(block.version == "v2" for block in results)
    assert all(not block.is_current for block in results)


def test_fixed_retrieval_tenant_isolation(corpus: Corpus) -> None:
    retriever = _fixed_retriever(corpus)

    results = retriever.retrieve(
        "failover command",
        tenant_id="acme",
        top_k=10,
        current_only=True,
    )

    assert results
    assert all(block.tenant_id == "acme" for block in results)
    assert results[0].doc_id == "private-runbook"
    assert "acme-failover" in results[0].text


def test_baseline_dense_only_lets_stale_chunks_through(corpus: Corpus) -> None:
    retriever = _baseline_retriever(corpus)

    results = retriever.retrieve(
        "Can admins opt out of SSO?",
        tenant_id="northwind",
        top_k=5,
        current_only=False,
        use_bm25=False,
        use_reranker=False,
    )

    assert any(block.version == "v2" for block in results)
    assert results[0].retrieval_source == "dense"


def _block(
    block_id: str,
    *,
    score: float = 0.0,
    dense: float | None = None,
    bm25: float | None = None,
    source: str = "",
) -> RetrievedBlock:
    return RetrievedBlock(
        doc_id="doc",
        tenant_id="northwind",
        title="Title",
        doc_type="guide",
        version="v3",
        page=1,
        block_id=block_id,
        anchor=f"#{block_id}",
        heading="Heading",
        text=f"text {block_id}",
        is_current=True,
        score=score,
        dense_score=dense,
        bm25_score=bm25,
        retrieval_source=source,
    )


def test_rrf_fuses_and_deduplicates() -> None:
    first = _block("a", score=0.9, dense=0.9, source="dense")
    second = _block("b", score=0.8, dense=0.8, source="dense")
    second_bm25 = _block("b", score=2.0, bm25=2.0, source="bm25")
    third = _block("c", score=2.0, bm25=2.0, source="bm25")

    fused = reciprocal_rank_fusion([[first, second], [second_bm25, third]])

    assert [block.block_id for block in fused] == ["b", "a", "c"]
    assert fused[0].dense_score == 0.8
    assert fused[0].bm25_score == 2.0
    assert fused[0].retrieval_source == "bm25+dense"


def test_rrf_single_ranking_preserves_scores() -> None:
    first = _block("a", score=0.9, dense=0.9, source="dense")
    second = _block("b", score=0.8, dense=0.8, source="dense")

    assert reciprocal_rank_fusion([[first, second]]) == [first, second]
    assert reciprocal_rank_fusion([]) == []


def test_noop_reranker_limits_results() -> None:
    blocks = [_block("a", score=0.2), _block("b", score=0.9), _block("c", score=0.5)]

    results = NoopReranker().rerank("query", blocks, top_k=2)

    assert [block.block_id for block in results] == ["b", "c"]


def test_cross_encoder_falls_back_without_model(monkeypatch) -> None:
    reranker = CrossEncoderReranker()

    def unavailable():
        raise RuntimeError("sentence-transformers is not installed")

    monkeypatch.setattr(reranker, "_ensure_model", unavailable)
    blocks: Sequence[RetrievedBlock] = [_block("a", score=0.2), _block("b", score=0.9)]

    results = reranker.rerank("query", blocks, top_k=1)

    assert [block.block_id for block in results] == ["b"]
    assert reranker._failed is True
