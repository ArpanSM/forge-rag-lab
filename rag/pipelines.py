"""Fixed and baseline answer pipelines."""

from __future__ import annotations

import re
import time
from collections.abc import Sequence

from rag.generation import AnswerGenerator
from rag.models import Answer
from rag.retrieval import (
    DEFAULT_CANDIDATE_K,
    DEFAULT_TOP_K,
    HybridRetriever,
    dedupe_evidence,
)

_VERSION_RE = re.compile(r"\bv(\d+)\b|\bversion\s+(\d+)\b", re.IGNORECASE)


class FixedPipeline:
    """Hybrid retrieval, current-version filtering, reranking and strict citations."""

    name = "fixed"

    def __init__(
        self,
        retriever: HybridRetriever,
        generator: AnswerGenerator,
        *,
        versions: Sequence[str] = (),
        top_k: int = DEFAULT_TOP_K,
        candidate_k: int = DEFAULT_CANDIDATE_K,
    ) -> None:
        self.retriever = retriever
        self.generator = generator
        self.versions = tuple(versions)
        self.top_k = top_k
        self.candidate_k = candidate_k

    def answer(self, question: str, *, tenant_id: str) -> Answer:
        started = time.perf_counter()
        versions, current_only = version_filter(question, self.versions)
        blocks = self.retriever.retrieve(
            question,
            tenant_id=tenant_id,
            top_k=self.top_k,
            candidate_k=self.candidate_k,
            current_only=current_only,
            use_bm25=True,
            use_reranker=True,
            versions=versions,
        )
        evidence = dedupe_evidence(blocks, self.top_k)
        answer = self.generator.generate(
            question,
            evidence,
            tenant_id=tenant_id,
            pipeline="fixed",
        )
        answer.retrieved = evidence
        answer.latency_ms = _elapsed_ms(started)
        return answer


class BaselinePipeline:
    """Naive fixed chunks, dense-only retrieval, no version filter, no abstention."""

    name = "baseline"

    def __init__(
        self,
        retriever: HybridRetriever,
        generator: AnswerGenerator,
        *,
        top_k: int = DEFAULT_TOP_K,
        candidate_k: int = DEFAULT_CANDIDATE_K,
    ) -> None:
        self.retriever = retriever
        self.generator = generator
        self.top_k = top_k
        self.candidate_k = candidate_k

    def answer(self, question: str, *, tenant_id: str) -> Answer:
        started = time.perf_counter()
        blocks = self.retriever.retrieve(
            question,
            tenant_id=tenant_id,
            top_k=self.top_k,
            candidate_k=self.candidate_k,
            current_only=False,
            use_bm25=False,
            use_reranker=False,
        )
        evidence = dedupe_evidence(blocks, self.top_k)
        answer = self.generator.generate(
            question,
            evidence,
            tenant_id=tenant_id,
            pipeline="baseline",
        )
        answer.retrieved = evidence
        answer.latency_ms = _elapsed_ms(started)
        return answer


def mentioned_versions(question: str, available: Sequence[str]) -> set[str]:
    """Extract explicitly mentioned versions that exist in the corpus."""
    known = set(available)
    found: set[str] = set()
    for match in _VERSION_RE.finditer(question):
        number = match.group(1) or match.group(2)
        candidate = f"v{number}"
        if candidate in known:
            found.add(candidate)
    return found


def version_filter(question: str, available: Sequence[str]) -> tuple[set[str] | None, bool]:
    """Choose the version filter for a question.

    A question naming one version asks about that version. A comparison naming
    several versions includes all of them. With no explicit version the fixed
    pipeline requires current documents, preventing stale pages from winning.
    """
    versions = mentioned_versions(question, available)
    if versions:
        return versions, False
    return None, True


def _elapsed_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1000))


__all__ = [
    "BaselinePipeline",
    "FixedPipeline",
    "mentioned_versions",
    "version_filter",
]
