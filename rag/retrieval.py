"""Hybrid retrieval: dense + BM25, reciprocal-rank fusion and reranking."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from rag.bm25 import BM25Index
from rag.embeddings import Embedder
from rag.ingestion import ingest_blocks
from rag.models import RetrievedBlock
from rag.vector_store import VectorStore

DEFAULT_RRF_K = 60
DEFAULT_TOP_K = 8
DEFAULT_CANDIDATE_K = 30


@runtime_checkable
class Reranker(Protocol):
    name: str

    def rerank(
        self, query: str, blocks: Sequence[RetrievedBlock], top_k: int
    ) -> list[RetrievedBlock]: ...


class NoopReranker:
    """Stable score order; used offline, in tests, and as the reranker fallback."""

    name = "noop"

    def rerank(
        self, query: str, blocks: Sequence[RetrievedBlock], top_k: int
    ) -> list[RetrievedBlock]:
        ordered = sorted(blocks, key=lambda block: (-block.score, block.chunk_ref))
        return list(ordered[:top_k])


class CrossEncoderReranker:
    """Lazy ``sentence-transformers`` cross-encoder reranker (``bge-reranker-v2-m3``)."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        *,
        device: str | None = None,
        batch_size: int = 16,
    ) -> None:
        self.name = model_name
        self.device = device
        self.batch_size = batch_size
        self._model = None
        self._failed = False

    def _ensure_model(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "sentence-transformers is not installed; use NoopReranker"
                ) from exc
            self._model = CrossEncoder(self.name, device=self.device)
        return self._model

    def rerank(
        self, query: str, blocks: Sequence[RetrievedBlock], top_k: int
    ) -> list[RetrievedBlock]:
        if not blocks:
            return []
        if self._failed:
            return NoopReranker().rerank(query, blocks, top_k)
        try:
            model = self._ensure_model()
            pairs = [(query, block.search_text) for block in blocks]
            scores = model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False,
            )
        except Exception:  # noqa: BLE001  # pragma: no cover - model/load failure
            self._failed = True
            return NoopReranker().rerank(query, blocks, top_k)

        reranked = [
            block.model_copy(
                update={
                    "score": float(score),
                    "retrieval_source": _append_source(block.retrieval_source, "rerank"),
                }
            )
            for block, score in zip(blocks, scores, strict=True)
        ]
        reranked.sort(key=lambda block: (-block.score, block.chunk_ref))
        return reranked[:top_k]


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[RetrievedBlock]],
    *,
    k: int = DEFAULT_RRF_K,
    weights: Sequence[float] | None = None,
) -> list[RetrievedBlock]:
    """Fuse ranked lists by reciprocal rank.

    A single ranking is returned in its original order so the dense-only
    baseline keeps meaningful similarity scores.
    """
    non_empty = [ranking for ranking in rankings if ranking]
    if not non_empty:
        return []
    if len(non_empty) == 1:
        return list(non_empty[0])
    if k <= 0:
        raise ValueError("RRF k must be positive")

    applied_weights = list(weights) if weights is not None else [1.0] * len(non_empty)
    if len(applied_weights) != len(non_empty):
        raise ValueError("weights must match the number of non-empty rankings")

    fused: dict[str, RetrievedBlock] = {}
    scores: dict[str, float] = {}
    sources: dict[str, set[str]] = {}
    for weight, ranking in zip(applied_weights, non_empty, strict=True):
        for rank, block in enumerate(ranking, start=1):
            key = block.chunk_ref
            contribution = weight / (k + rank)
            scores[key] = scores.get(key, 0.0) + contribution
            if key not in fused:
                fused[key] = block.model_copy()
                sources[key] = set()
            if block.dense_score is not None:
                fused[key] = fused[key].model_copy(update={"dense_score": block.dense_score})
            if block.bm25_score is not None:
                fused[key] = fused[key].model_copy(update={"bm25_score": block.bm25_score})
            if block.retrieval_source:
                sources[key].update(block.retrieval_source.split("+"))

    results = [
        fused[key].model_copy(
            update={
                "score": round(score, 8),
                "retrieval_source": "+".join(sorted(sources[key])),
            }
        )
        for key, score in scores.items()
    ]
    results.sort(key=lambda block: (-block.score, block.chunk_ref))
    return results


class HybridRetriever:
    """Dense retrieval + BM25 + RRF + optional reranking, with payload filters."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        *,
        bm25: BM25Index | None = None,
        reranker: Reranker | None = None,
        rrf_k: int = DEFAULT_RRF_K,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.bm25 = bm25
        self.reranker = reranker or NoopReranker()
        self.rrf_k = rrf_k

    def index(self, blocks: Sequence[RetrievedBlock]) -> int:
        count = ingest_blocks(blocks, self.embedder, self.vector_store)
        if self.bm25 is not None:
            self.bm25.add(blocks)
        return count

    @property
    def indexed_count(self) -> int:
        return self.vector_store.count()

    def retrieve(
        self,
        query: str,
        *,
        tenant_id: str,
        top_k: int = DEFAULT_TOP_K,
        candidate_k: int = DEFAULT_CANDIDATE_K,
        current_only: bool = True,
        use_bm25: bool = True,
        use_reranker: bool = True,
        versions: set[str] | None = None,
    ) -> list[RetrievedBlock]:
        if not query.strip() or top_k <= 0 or not tenant_id:
            return []
        candidate_k = max(candidate_k, top_k)
        query_vector = self.embedder.embed_query(query)

        rankings: list[Sequence[RetrievedBlock]] = [
            self.vector_store.search(
                query_vector,
                tenant_id=tenant_id,
                top_k=candidate_k,
                current_only=current_only,
                versions=versions,
            )
        ]
        if use_bm25 and self.bm25 is not None:
            rankings.append(
                self.bm25.search(
                    query,
                    tenant_id=tenant_id,
                    top_k=candidate_k,
                    current_only=current_only,
                    versions=versions,
                )
            )

        fused = reciprocal_rank_fusion(rankings, k=self.rrf_k)
        if use_reranker:
            fused = self.reranker.rerank(query, fused, candidate_k)
        return list(fused[:top_k])


def dedupe_evidence(blocks: Sequence[RetrievedBlock], limit: int) -> list[RetrievedBlock]:
    """Keep the best chunk per block so citation references stay unambiguous."""
    seen: set[str] = set()
    result: list[RetrievedBlock] = []
    for block in blocks:
        if block.ref in seen:
            continue
        seen.add(block.ref)
        result.append(block)
        if len(result) >= limit:
            break
    return result


def _append_source(source: str, extra: str) -> str:
    parts = {part for part in source.split("+") if part}
    parts.add(extra)
    return "+".join(sorted(parts))
