"""Embedding providers.

Heavy dependencies are imported lazily so the test suite only needs the
standard library plus Pydantic. FastEmbed provides ONNX BGE embeddings without
PyTorch; the deterministic hashing embedder is for tests and offline development.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from itertools import pairwise
from typing import Protocol, runtime_checkable

from rag.text import tokenize

FASTEMBED_DEFAULT_MODEL = "BAAI/bge-base-en-v1.5"
FASTEMBED_DIMENSIONS = {
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
    "BAAI/bge-large-en-v1.5": 1024,
}


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


class FastEmbedEmbedder:
    """Lazy ONNX embedding wrapper around FastEmbed's BGE models.

    FastEmbed runs ONNX Runtime on CPU and does not require PyTorch. The default
    ``BAAI/bge-base-en-v1.5`` model is a practical CPU/quality tradeoff; BGE-M3
    can be supplied through a separate ONNX runtime if needed.
    """

    def __init__(
        self,
        model_name: str = FASTEMBED_DEFAULT_MODEL,
        *,
        cache_dir: str | None = None,
        threads: int | None = None,
    ) -> None:
        self.name = model_name
        self.cache_dir = cache_dir
        self.threads = threads
        self._model = None
        self._dimension = FASTEMBED_DIMENSIONS.get(model_name)

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            model = self._ensure_model()
            probe = next(iter(model.embed(["dimension probe"])))
            self._dimension = len(probe)
        return int(self._dimension)

    def _ensure_model(self):
        if self._model is None:
            try:
                from fastembed import TextEmbedding
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "fastembed is not installed; install fastembed or set EMBEDDER=hashing"
                ) from exc
            self._model = TextEmbedding(
                model_name=self.name,
                cache_dir=self.cache_dir,
                threads=self.threads,
            )
        return self._model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._ensure_model()
        return [[float(value) for value in vector] for vector in model.embed(list(texts))]

    def embed_query(self, text: str) -> list[float]:
        model = self._ensure_model()
        vector = next(iter(model.query_embed(text)))
        return [float(value) for value in vector]


def build_embedder(name: str | None = None, *, model_name: str | None = None) -> Embedder:
    """Create the configured embedder without touching optional dependencies eagerly."""
    normalized = (name or "fastembed").strip().lower()
    if normalized in {"hashing", "hash", "fake"}:
        return HashingEmbedder()
    if normalized in {"fastembed", "onnx", "bge", "bge-base"}:
        return FastEmbedEmbedder(model_name=model_name or FASTEMBED_DEFAULT_MODEL)
    if normalized in {"bge-m3", "bgem3"}:
        raise ValueError(
            "BGE-M3 ONNX is not bundled with FastEmbed; use fastembed/bge-base "
            "or wire an M3 ONNX runtime explicitly"
        )
    raise ValueError(f"unknown embedder: {name!r}")
