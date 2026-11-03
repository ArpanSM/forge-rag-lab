"""Chunking strategies for the fixed and baseline ingestion paths.

The manifest already gives structure-aware blocks, which the fixed pipeline
uses one-to-one. The baseline deliberately ignores that structure and cuts
fixed-size character windows, producing several chunks per block.
"""

from __future__ import annotations

from rag.corpus import Corpus
from rag.models import Block, Document, RetrievedBlock

BASELINE_MAX_CHARS = 320
BASELINE_OVERLAP = 64


def structure_chunks(corpus: Corpus) -> list[RetrievedBlock]:
    """Return one retrieval unit per manifest block, preserving structure."""
    return [_retrieved(document, block) for document, block in corpus.iter_blocks()]


def baseline_chunks(
    corpus: Corpus,
    max_chars: int = BASELINE_MAX_CHARS,
    overlap: int = BASELINE_OVERLAP,
) -> list[RetrievedBlock]:
    """Cut every block into overlapping fixed-size windows."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must satisfy 0 <= overlap < max_chars")

    chunks: list[RetrievedBlock] = []
    for document, block in corpus.iter_blocks():
        windows = split_text(block.text, max_chars=max_chars, overlap=overlap)
        for index, window in enumerate(windows):
            chunks.append(_retrieved(document, block, window, f"{block.block_id}-c{index:02d}"))
    return chunks


def split_text(text: str, max_chars: int, overlap: int) -> list[str]:
    """Split on word boundaries into overlapping windows."""
    stripped = " ".join(text.split())
    if not stripped:
        return []
    if len(stripped) <= max_chars:
        return [stripped]

    windows: list[str] = []
    start = 0
    length = len(stripped)
    while start < length:
        end = min(start + max_chars, length)
        if end < length:
            boundary = stripped.rfind(" ", start + max_chars // 2, end)
            if boundary > start:
                end = boundary
        window = stripped[start:end].strip()
        if window:
            windows.append(window)
        if end >= length:
            break
        next_start = max(end - overlap, start + 1)
        if next_start <= start:
            next_start = end
        start = next_start
    return windows


def _retrieved(
    document: Document,
    block: Block,
    text: str | None = None,
    chunk_id: str = "",
) -> RetrievedBlock:
    return RetrievedBlock(
        doc_id=document.doc_id,
        tenant_id=document.tenant_id,
        title=document.title,
        doc_type=document.doc_type,
        version=document.version,
        page=block.page,
        block_id=block.block_id,
        anchor=block.anchor,
        heading=block.heading,
        text=text if text is not None else block.text,
        is_current=document.is_current,
        chunk_id=chunk_id,
    )
