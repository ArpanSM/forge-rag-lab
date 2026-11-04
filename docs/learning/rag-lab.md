# RAG Lab — Learning Map

This is the reading path for everything the RAG lab uses. Read the concept, skim the
resource, then open the file where it lives. The goal is that you can explain any part of
the project without reading the whole codebase first.

If you only have one hour: read sections 1–3, then run the eval and read the report.

## 1. The mental model

A RAG system is three loops:

1. **Ingest** documents into small, addressable pieces.
2. **Retrieve** the right pieces for a question.
3. **Answer** using only those pieces, with citations, or say “I don’t know.”

Most failures happen in the middle loop. The model is often fine; the wrong page was
retrieved, the old version won, the citation pointed at a different section, or the system
answered a question the corpus could not support.

## 2. Reading path

### Stage 1 — What RAG is

- [RAG paper (Lewis et al., 2020)](https://arxiv.org/abs/2005.11401) — the original
  retrieval-augmented generation formulation.
- [RAG survey (Gao et al., 2023)](https://arxiv.org/abs/2312.10997) — broad map of
  retrieval, generation, augmentation and evaluation.
- Code: `docs/scope.md`, `README.md`.

### Stage 2 — Retrieval

- [Dense Passage Retrieval (Karpukhin et al., 2020)](https://arxiv.org/abs/2004.04906) —
  why dense embeddings beat sparse term matching for many questions.
- [BEIR benchmark (Thakur et al., 2021)](https://arxiv.org/abs/2104.08663) — retrieval
  evaluation across domains; read the metric definitions.
- [HNSW (Malkov & Yashunin, 2018)](https://arxiv.org/abs/1603.09320) — the approximate
  nearest-neighbour index behind most vector databases.
- [BM25 overview](https://en.wikipedia.org/wiki/Okapi_BM25) and the
  [Robertson & Zaragoza monograph](https://www.nowpublishers.com/article/Details/INR-019) —
  the lexical side of hybrid retrieval.
- [Reciprocal Rank Fusion (Cormack et al., 2009)](https://dl.acm.org/doi/10.1145/1571941.1572114) —
  how the two rankings are merged.
- [BGE-M3 (Chen et al., 2024)](https://arxiv.org/abs/2402.03216) — dense, sparse and
  multi-vector retrieval in one model; the project uses the BGE family through ONNX.
- Code: `rag/embeddings.py`, `rag/vector_store.py`, `rag/bm25.py`, `rag/retrieval.py`.

### Stage 3 — Chunking, citations and versioning

- [Chunking strategies (Pinecone)](https://www.pinecone.io/learn/chunking-strategies/) —
  fixed windows vs structure-aware chunks.
- [ALCE: Enabling Large Language Models to Generate Text with Citations (Gao et al., 2023)](https://arxiv.org/abs/2305.14627) —
  how citation quality is measured.
- [Lost in the Middle (Liu et al., 2023)](https://arxiv.org/abs/2307.03172) — why stuffing
  more context is not a fix.
- Code: `rag/chunking.py`, `rag/corpus.py`, `rag/generation.py`, `docs/eval-schema.md`.

### Stage 4 — Evaluation

- [RAGAS (Es et al., 2023)](https://arxiv.org/abs/2309.15217) and the
  [Ragas metric docs](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) —
  faithfulness, answer relevance, context precision/recall.
- [Wilson score interval](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval)
  and [bootstrap resampling](https://en.wikipedia.org/wiki/Bootstrapping_(statistics)) —
  why small eval slices need uncertainty bars.
- Code: `evals/metrics.py`, `evals/dataset.py`, `evals/runner.py`, `evals/report.py`.
- Read the actual report: `docs/evals/lfm3-refinement.md`.

### Stage 5 — Security and production concerns

- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) —
  prompt injection is LLM01.
- [Not what you’ve signed up for (Greshake et al., 2023)](https://arxiv.org/abs/2302.12173) —
  indirect prompt injection through retrieved documents.
- [JSON Schema](https://json-schema.org/) and
  [Pydantic](https://docs.pydantic.dev/) — the structured answer contract.
- Code: `rag/generation.py` (injection sanitizer, citation validation),
  `rag/pipelines.py` (tenant/version filters), `rag/providers.py` (fallback chain).

### Stage 6 — The engineering stack

- [FastAPI](https://fastapi.tiangolo.com/) — the API.
- [Next.js static export](https://nextjs.org/docs/app/building-your-application/deploying/static-exports) —
  the UI.
- [Qdrant docs](https://qdrant.tech/documentation/) — vector database and payload filters.
- [FastEmbed](https://github.com/qdrant/fastembed) and
  [ONNX Runtime](https://onnxruntime.ai/docs/) — CPU embeddings without PyTorch.
- [OrcaRouter docs](https://docs.orcarouter.ai/) — the hosted OpenAI-compatible gateway.
- [LFM3-1.7B](https://docs.liquid.ai/lfm/models/lfm3-1.7b) and
  [llama.cpp](https://github.com/ggml-org/llama.cpp) — the local chat model.
- [Render free tier](https://render.com/docs/free),
  [Cloudflare Pages](https://developers.cloudflare.com/pages/),
  [Qdrant Cloud](https://qdrant.tech/documentation/cloud/) — the planned $0 deployment.
- Code: `api/main.py`, `web/`, `docs/adr/0001-onnx-embeddings.md`,
  `docs/adr/0002-local-lfm3.md`.

## 3. Concept map

| Concept | Why it matters | Where it lives |
|---|---|---|
| Embeddings | Turn text into vectors that capture meaning | `rag/embeddings.py` |
| Vector search / HNSW | Find nearest neighbours without scanning everything | `rag/vector_store.py` |
| Chunking | The retrieval unit; bad chunks hide the answer | `rag/chunking.py` |
| BM25 | Exact terms, names and error codes that embeddings miss | `rag/bm25.py` |
| Hybrid retrieval / RRF | Combine semantic and lexical rankings | `rag/retrieval.py` |
| Cross-encoder reranking | Re-score the shortlist with the question and the passage together | `rag/retrieval.py` |
| Stable block IDs | Citations must point to a page and block, not a chunk number | `rag/corpus.py` |
| Version filters | Old docs must not outrank current ones | `rag/pipelines.py` |
| Tenant filters | One customer must never see another customer’s documents | `rag/corpus.py`, `rag/vector_store.py` |
| Claim-level citations | Every visible claim needs evidence | `rag/generation.py` |
| Abstention | Saying “I don’t know” is a feature | `rag/generation.py` |
| Prompt injection | Retrieved text is untrusted input | `rag/generation.py` |
| Recall@k / all-gold@k | Did the retriever find the evidence? | `evals/metrics.py` |
| Context precision/recall | Was the retrieved context relevant and complete? | `evals/metrics.py` |
| Citation coverage/accuracy | Did the answer cite the gold source, and how precise was it? | `evals/metrics.py` |
| Disambiguation | Did the answer name/cite every conflicting version? | `evals/metrics.py` |
| Wilson/bootstrap intervals | Small samples need error bars | `evals/metrics.py` |
| Structured outputs | The model must return a predictable JSON shape | `rag/prompts.py`, `rag/providers.py` |
| Provider fallback | Free tiers fail; the chain must degrade cleanly | `rag/providers.py` |
| ONNX vs PyTorch | The CPU-only, $0 constraint | `docs/adr/0001-onnx-embeddings.md` |
| Local vs hosted models | Iteration speed vs public reliability | `docs/adr/0002-local-lfm3.md` |

## 4. Code walkthrough

Read in this order:

1. `docs/scope.md` — what the project is supposed to do.
2. `GLOSSARY.md` — the words the code uses.
3. `rag/models.py` — the data shapes.
4. `rag/corpus.py` — versioned, tenant-scoped documents.
5. `rag/chunking.py` — how documents become retrieval units.
6. `rag/embeddings.py` + `rag/vector_store.py` — dense retrieval.
7. `rag/bm25.py` + `rag/retrieval.py` — hybrid retrieval and reranking.
8. `rag/prompts.py` + `rag/generation.py` — grounded answers and citations.
9. `rag/pipelines.py` — fixed vs baseline, version filter.
10. `api/main.py` — the HTTP contract.
11. `evals/` — how the claims are measured.
12. `web/` — what a user sees.

## 5. Exercises

1. Ask a question whose answer exists only in `v2`. Does the fixed pipeline answer with
   `v2` or `v3`? Why?
2. Add a new document to the synthetic corpus and regenerate it. What breaks in the
   manifest validation?
3. Swap `BAAI/bge-base-en-v1.5` for a smaller model and rerun the eval. Which metric moves
   first?
4. Disable the reranker (`RERANKER=noop`) and compare recall@5. Where does the reranker
   earn its keep?
5. Write a new prompt-injection fixture and confirm the sanitizer catches it.
6. Add one new question to each eval category and rerun. Does the quota validation catch
   the mismatch?
7. Change the conflicting-question template to a different wording and check whether
   `version_filter` still retrieves all versions.

## 6. What to read next

- [Qdrant hybrid search](https://qdrant.tech/documentation/concepts/hybrid-queries/)
- [Ragas evaluate tutorial](https://docs.ragas.io/en/stable/getstarted/rag_eval/)
- [OpenAI structured outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [Anthropic prompt engineering](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [Render free-tier limitations](https://render.com/docs/free)
- [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/)
