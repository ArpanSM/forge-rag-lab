from __future__ import annotations

from datetime import UTC, datetime

from rag.chunking import baseline_chunks, split_text, structure_chunks
from rag.corpus import Corpus
from rag.models import Block, CorpusManifest, Document
from rag.retrieval import dedupe_evidence


def _long_corpus() -> Corpus:
    text = " ".join(f"token{index}" for index in range(200))
    document = Document(
        doc_id="long-page",
        tenant_id="northwind",
        title="Long page",
        doc_type="guide",
        version="v3",
        effective_from=datetime(2026, 1, 1).date(),
        superseded_at=None,
        blocks=[Block(block_id="b7", page=4, heading="Detail", anchor="#detail", text=text)],
    )
    manifest = CorpusManifest(
        generated_at=datetime.now(UTC),
        product="Helios",
        tenants=["northwind"],
        versions=["v3"],
        documents=[document],
        failure_fixtures={},
    )
    return Corpus(manifest)


def test_split_text_uses_word_boundaries_and_overlap() -> None:
    text = " ".join(f"word{index}" for index in range(80))

    windows = split_text(text, max_chars=100, overlap=20)

    assert len(windows) > 1
    assert all(window for window in windows)
    assert all(len(window) <= 100 for window in windows)
    assert all(" " in window for window in windows)


def test_structure_chunks_preserve_blocks() -> None:
    corpus = _long_corpus()

    chunks = structure_chunks(corpus)

    assert len(chunks) == 1
    assert chunks[0].block_id == "b7"
    assert chunks[0].chunk_id == ""
    assert chunks[0].page == 4
    assert chunks[0].is_current is True


def test_baseline_chunks_are_fixed_size_and_addressable() -> None:
    corpus = _long_corpus()

    chunks = baseline_chunks(corpus, max_chars=120, overlap=24)

    assert len(chunks) > 1
    assert all(chunk.text for chunk in chunks)
    assert all(len(chunk.text) <= 120 for chunk in chunks)
    assert all(chunk.block_id == "b7" for chunk in chunks)
    assert all(chunk.chunk_id.startswith("b7-c") for chunk in chunks)
    assert all(chunk.ref == "long-page@v3#b7" for chunk in chunks)
    assert len({chunk.chunk_ref for chunk in chunks}) == len(chunks)


def test_dedupe_evidence_keeps_best_chunk_per_block() -> None:
    corpus = _long_corpus()
    chunks = baseline_chunks(corpus, max_chars=120, overlap=24)

    deduped = dedupe_evidence(chunks, limit=10)

    assert len(deduped) == 1
    assert deduped[0].ref == chunks[0].ref
