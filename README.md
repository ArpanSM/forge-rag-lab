# Forge RAG Lab

An end-to-end RAG reliability lab: versioned SaaS documentation, hybrid retrieval,
page-level citations, stale-document handling, answerability checks and a baseline-vs-fixed
evaluation harness.

**Status:** building. Scope is locked in [docs/scope.md](docs/scope.md).

## Why this exists

Most RAG demos answer questions. This one shows what happens when retrieval goes wrong:
a stale version outranks the current one, a citation points to the wrong page, a detail is
missed, the system answers an unanswerable question, or a document tries to inject
instructions. The demo runs the same questions through a naive baseline and a fixed
pipeline, and reports the difference.

## What is inside

- **Corpus:** synthetic Helios project-management docs, ~60 pages across v1/v2/v3, two tenants.
- **Retrieval:** BGE-M3 dense + Qdrant BM25, RRF, `bge-reranker-v2-m3`, tenant/version filters.
- **Generation:** free-tier providers with a fallback chain, structured claim-level citations,
  abstention and a prompt-injection guard.
- **Evaluation:** 80 questions across five categories, baseline vs fixed, with a failure gallery.
- **UI:** Next.js static export with a chat view, citation viewer, pipeline toggle and health report.

## Quickstart

```bash
cp .env.example .env
make install
make dev          # API at http://localhost:8000
make web-dev      # UI at http://localhost:3000
make test
make eval
```

## Corpus

The committed corpus in `data/corpus/` and `data/manifests/corpus.json` is generated
from `scripts/generate_corpus.py` with no network access or paid APIs:

```bash
python scripts/generate_corpus.py
python scripts/generate_corpus.py --check   # verify committed output is current
python -m pytest tests/test_corpus.py -q
```

## Backend

The `rag/` package implements the fixed and baseline paths:

- `rag/corpus.py` loads and validates the manifest, with tenant-scoped block lookups.
- `rag/ingestion.py` builds structure-aware chunks or naive fixed-size chunks and indexes them.
- `rag/bm25.py` is a pure-Python BM25 index; `rag/retrieval.py` fuses dense and BM25 with RRF
  and applies an optional cross-encoder reranker.
- `rag/generation.py` parses claim JSON, resolves citations to blocks, drops unsupported claims,
  abstains when evidence is thin, and sanitizes prompt-injection attempts in documents.
- `api/main.py` exposes the endpoints in [docs/api-contract.md](docs/api-contract.md).
- `python -m rag.pipeline --json` is the JSON-in/JSON-out adapter consumed by the eval harness.

The API builds the service from `.env` on first use. Unit tests inject `HashingEmbedder`,
`InMemoryVectorStore`, `NoopReranker` and `FakeProvider`, so they need no network, model
downloads or API keys.

## Evaluation

The harness lives in [`evals/`](evals/README.md). It generates the 80-question set from the
corpus manifest, scores deterministic retrieval/citation/version/abstention metrics, and
writes JSON plus Markdown reports with confidence intervals and a failure gallery.

```bash
make eval-generate   # regenerate evals/data/questions.json from the manifest
make eval            # run the configured pipeline and write evals/reports/
python -m pytest -q  # fixture-based harness tests, no LLM or API key
```

## Docs

- [Scope](docs/scope.md)
- [API contract](docs/api-contract.md)
- [Corpus schema](docs/corpus-schema.md)
- [Evaluation schema](docs/eval-schema.md)
- [Glossary](GLOSSARY.md)

## Clean-room

Synthetic documents and data only. No employer code, names, metrics, screenshots or retail
support workflows.
