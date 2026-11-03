"""Embedding providers.

Heavy dependencies are imported lazily so the test suite only needs the
standard library plus Pydantic. The deterministic hashing embedder is intended
for tests and offline development; BGE-M3 is the production embedder.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from itertools import pairwise
from typing import Protocol, runtime_checkable

from rag.text import tokenize

BGE_M3_MODEL = "BAAI/bge-m3"
BGE_M3_DIMENSION = 1024


@runtime_checkable
class Embedder(Protocol):
    name: str
    dimension: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class HashingEmbedder:
    """Deterministic feature hashing with L2 normalisation.

    This is not a semantic model. It is stable across processes, needs no
    downloads and is good enough to exercise retrieval plumbing in tests.
    """

    def __init__(self, dimension: int = 256) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self.dimension = dimension
        self.name = f"hashing-{dimension}"

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = tokenize(text)
        for token in tokens:
            self._add(vector, token, 1.0)
        for left, right in pairwise(tokens):
            self._add(vector, f"{left}_{right}", 0.5)

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]

    def _add(self, vector: list[float], feature: str, weight: float) -> None:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % self.dimension
        vector[index] += weight


class BgeM3Embedder:
    """Lazy ``sentence-transformers`` wrapper around ``BAAI/bge-m3``."""

    def __init__(
        self,
        model_name: str = BGE_M3_MODEL,
        *,
        device: str | None = None,
        batch_size: int = 32,
    ) -> None:
        self.name = model_name
        self.batch_size = batch_size
        self.device = device
        self._model = None

    @property
    def dimension(self) -> int:
        if self._model is None:
            return BGE_M3_DIMENSION
        return int(self._model.get_sentence_embedding_dimension())

    def _ensure_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - depends on optional extra
                raise RuntimeError(
                    "sentence-transformers is not installed; install the retrieval extras "
                    "or set EMBEDDER=hashing"
                ) from exc
            self._model = SentenceTransformer(self.name, device=self.device)
        return self._model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._ensure_model()
        vectors = model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [[float(value) for value in vector] for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def build_embedder(name: str | None = None) -> Embedder:
    """Create the configured embedder without touching optional dependencies eagerly."""
    normalized = (name or "bge-m3").strip().lower()
    if normalized in {"hashing", "hash", "fake"}:
        return HashingEmbedder()
    if normalized in {"bge-m3", "bge", "bgem3"}:
        return BgeM3Embedder()
    raise ValueError(f"unknown embedder: {name!r}")
