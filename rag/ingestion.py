"""Corpus ingestion into an embedder + vector store pair."""

from __future__ import annotations

from collections.abc import Sequence

from rag.chunking import baseline_chunks, structure_chunks
from rag.corpus import Corpus
from rag.embeddings import Embedder
from rag.models import RetrievedBlock
from rag.vector_store import VectorStore

DEFAULT_BATCH_SIZE = 64


def ingest_blocks(
    blocks: Sequence[RetrievedBlock],
    embedder: Embedder,
    store: VectorStore,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> int:
    """Embed and upsert blocks in batches. Returns the number of indexed blocks."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for start in range(0, len(blocks), batch_size):
        batch = list(blocks[start : start + batch_size])
        vectors = embedder.embed_documents([block.search_text for block in batch])
        if len(vectors) != len(batch):
            raise RuntimeError(f"embedder returned {len(vectors)} vectors for {len(batch)} blocks")
        store.upsert(batch, vectors)
    return len(blocks)


def ingest_corpus(corpus: Corpus, embedder: Embedder, store: VectorStore) -> int:
    """Index the structure-aware blocks used by the fixed pipeline."""
    return ingest_blocks(structure_chunks(corpus), embedder, store)


def ingest_baseline(corpus: Corpus, embedder: Embedder, store: VectorStore) -> int:
    """Index naive fixed-size chunks used by the baseline pipeline."""
    return ingest_blocks(baseline_chunks(corpus), embedder, store)
