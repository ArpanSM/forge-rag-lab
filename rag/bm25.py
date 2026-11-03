"""Pure-Python BM25 index with tenant and version filters."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence

from rag.models import RetrievedBlock
from rag.text import tokenize


class BM25Index:
    """Okapi BM25 over :class:`RetrievedBlock` objects.

    Tenant filtering is mandatory on every search; version filtering is optional.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._blocks: list[RetrievedBlock] = []
        self._term_frequencies: list[Counter[str]] = []
        self._lengths: list[int] = []
        self._document_frequency: Counter[str] = Counter()
        self._postings: dict[str, list[tuple[int, int]]] = defaultdict(list)

    def __len__(self) -> int:
        return len(self._blocks)

    @property
    def blocks(self) -> Sequence[RetrievedBlock]:
        return tuple(self._blocks)

    def add(self, blocks: Iterable[RetrievedBlock]) -> None:
        for block in blocks:
            tokens = tokenize(block.search_text)
            frequencies = Counter(tokens)
            index = len(self._blocks)
            self._blocks.append(block)
            self._term_frequencies.append(frequencies)
            self._lengths.append(len(tokens))
            for term, count in frequencies.items():
                self._document_frequency[term] += 1
                self._postings[term].append((index, count))

    def search(
        self,
        query: str,
        *,
        tenant_id: str,
        top_k: int = 10,
        current_only: bool = False,
        versions: set[str] | None = None,
    ) -> list[RetrievedBlock]:
        query_terms = tokenize(query)
        if not query_terms or not self._blocks or not tenant_id or top_k <= 0:
            return []

        total = len(self._blocks)
        average_length = sum(self._lengths) / total or 1.0
        scores: dict[int, float] = defaultdict(float)
        for term in query_terms:
            postings = self._postings.get(term)
            if not postings:
                continue
            document_frequency = self._document_frequency[term]
            idf = math.log(1.0 + (total - document_frequency + 0.5) / (document_frequency + 0.5))
            for index, frequency in postings:
                block = self._blocks[index]
                if not _passes_filters(
                    block, tenant_id=tenant_id, current_only=current_only, versions=versions
                ):
                    continue
                length_ratio = self._lengths[index] / average_length
                denominator = frequency + self.k1 * (1.0 - self.b + self.b * length_ratio)
                scores[index] += idf * (frequency * (self.k1 + 1.0)) / denominator

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top_k]
        return [
            block.model_copy(
                update={
                    "score": score,
                    "bm25_score": score,
                    "retrieval_source": "bm25",
                }
            )
            for index, score in ranked
            for block in (self._blocks[index],)
        ]


def _passes_filters(
    block: RetrievedBlock,
    *,
    tenant_id: str,
    current_only: bool,
    versions: set[str] | None,
) -> bool:
    if block.tenant_id != tenant_id:
        return False
    if current_only and not block.is_current:
        return False
    if versions is not None:
        return block.version in versions
    return True


# Convenient alias for callers that prefer the shorter name.
BM25 = BM25Index
