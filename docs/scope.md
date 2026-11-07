# RAG Lab Scope

**For:** engineers and evaluators checking what is in and out of scope.

**Status:** locked 2026-11-03. Source of truth: [forge-roadmap#3](https://github.com/ArpanSM/forge-roadmap/issues/3).

## Product and corpus

- Synthetic **Helios**, a fictional project-management SaaS.
- About 60 pages across **v1, v2 and v3**; two tenants (`northwind`, `acme`) with overlapping docs and one private page each.
- Metadata: `doc_id`, `title`, `doc_type` (guide/API/release/policy), `version`, `effective_from`, `superseded_at`, `tenant_id`, `page`, `block_id`, `anchor`, `text`.
- Stable block IDs, page anchors, version metadata; Markdown source plus a JSON manifest.
- Failure fixtures: stale v1 page outranking v2; wrong-page citation; long page with a missed detail; unanswerable question; prompt injection in a document; conflicting versions; cross-tenant private page.
- Corpus generator committed; generated data reproducible; synthetic only.

## Architecture

- FastAPI backend; Next.js static export frontend; local Qdrant for development, Qdrant Cloud Free for hosted.
- Ingestion: parse → block split → structure-aware chunking → ONNX BGE-base dense via FastEmbed (BGE-M3 optional) plus sparse/BM25 → Qdrant with tenant, version and document metadata.
- Retrieval: tenant filter plus version filter → dense plus BM25 → RRF → `bge-reranker-v2-m3` top-k.
- Generation: Gemini 3.5 Flash-Lite (public docs only) with OpenRouter Gemma 4 31B free → Groq GPT-OSS 120B → Ollama Qwen 3.5 4B fallback. Structured claim JSON with citation IDs; abstain when evidence is insufficient; prompt-injection guard; no raw tool output in context.
- Baseline: naive fixed-size chunks plus dense-only retrieval, no version filter, no reranker, no abstention.
- Fixed: the pipeline above.
- Tenant isolation: `tenant_id` filter on every retrieval and citation read; one cross-tenant leak test.

## Evaluation

- 80 questions: 24 single-hop, 16 multi-hop, 16 version-specific, 8 conflicting-version, 16 unanswerable; 40/40 dev-test plus a 20-question private shadow set.
- Metrics: recall@5/10 and all-gold@10; context precision/recall; answer correctness, factual F1, faithfulness; citation page accuracy, span hit, ALCE precision/recall/coverage; stale-answer, stale-citation and disambiguation; abstention, false-abstention and selective accuracy; p50/p95 latency.
- Baseline vs fixed on the same set; report confidence intervals and paired tests; report failures.
- Tooling: Ragas 0.4.3 inside a thin runner; fallback DeepEval 4.3.2.

## Failure modes

Cover all seven:

1. Stale version outranks current.
2. Citation points to the wrong page or section.
3. Missed detail in a long page.
4. No abstention on unanswerable questions.
5. Prompt injection hidden in a document.
6. Conflicting versions across pages.
7. Cross-tenant leak.

The demo foregrounds 1–5. The 80-question eval covers stale versions, citations, missed details, abstention and conflicting versions; prompt injection and cross-tenant isolation are covered by unit/security tests.

## Demo

- Chat UI with answer and claim-level citations; clicking a citation opens the exact page/block with highlight.
- Baseline/fixed toggle shows the same question through both pipelines.
- Health report page: metric table, failure gallery, stale-version and abstention examples, latency.
- Live: Render Free API plus Cloudflare Pages frontend plus Qdrant Cloud free; cold-start banner; 60–90 second video fallback.
- Frontend: Next.js static export.
- Timebox: 2 weeks. Day-10 cut line drops the toggle and hosted deployment; keeps eval, citations and case study.

## Repo and proof

- `forge-rag-lab` structure: `api/`, `web/`, `rag/`, `evals/`, `data/`, `scripts/`, `docs/`, `tests/`.
- `GLOSSARY.md`: Document, Version, Block, Chunk, Citation, Claim, Answerability, Stale version, Baseline, Fixed pipeline, Tenant.
- Proof: README, architecture diagram, quickstart, eval table, limitations; one-page case study; 60–90 second video; Upwork portfolio item; proposal snippet.
- Case study angle: "I found and fixed five retrieval failures in a RAG assistant," with before/after numbers.

## Implementation status

**Last updated:** 2026-11-04.

**Shipped**

- Synthetic Helios corpus (62 document versions, 388 blocks), versioned and tenant-scoped.
- Structure-aware and baseline chunking; ONNX BGE-base embeddings; BM25; RRF; ONNX `bge-reranker-v2-m3-int8`; tenant/version filters.
- Fixed and baseline pipelines; claim-level citations; unsupported-claim dropping; abstention; prompt-injection sanitizer.
- FastAPI contract endpoints; Next.js chat, citation drawer, baseline/fixed toggle and health report.
- 80-question evaluation harness with 40/40 dev-test split; deterministic metrics; Wilson/bootstrap intervals; latency p50/p95; factual F1; paired bootstrap comparisons.
- Provider abstraction with Gemini, OpenRouter, Groq, OrcaRouter and Ollama; local LFM3-1.7B for iteration.
- Unit and integration tests covering retrieval, citations, abstention, injection handling, tenant isolation, the API and the eval adapter.

**Deferred or limited**

- LLM-judge metrics (answer correctness, faithfulness); ALCE precision/recall, span hit and selective accuracy; DeepEval fallback.
- A 20-question private shadow set.
- Prompt-injection and cross-tenant checks are covered by unit/security tests; they are not part of the 80-question score.
- Live deployment (Render/Cloudflare/Qdrant), walkthrough video, case study and Upwork portfolio item.
- Larger code-review refactors: pipeline dispatch, a `BlockRef` type, and splitting `rag/generation.py` into parsing, citation and generation modules.

**Implementation notes**

- ADR 0001 replaces BGE-M3 with ONNX BGE-base for the CPU-only $0 build. BGE-M3 remains an optional upgrade.
- ADR 0002 adds local LFM3 and OrcaRouter as evaluation providers; the hosted provider remains the public-demo and cross-check path.
- The health report's fixture data uses the measured 80-question local numbers, not invented values. The failure cards are representative corpus examples; the live API replaces them with the latest report.
