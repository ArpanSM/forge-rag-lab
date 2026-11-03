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

## Docs

- [Scope](docs/scope.md)
- [API contract](docs/api-contract.md)
- [Corpus schema](docs/corpus-schema.md)
- [Evaluation schema](docs/eval-schema.md)
- [Glossary](GLOSSARY.md)

## Clean-room

Synthetic documents and data only. No employer code, names, metrics, screenshots or retail
support workflows.
