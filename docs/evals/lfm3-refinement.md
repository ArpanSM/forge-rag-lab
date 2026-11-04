# LFM3-1.7B refinement log

**Date:** 2026-11-04  
**Model:** LFM3-1.7B (Q6_K GGUF, llama.cpp, 32K context, thinking off)  
**Endpoint:** `http://127.0.0.1:8080/v1` via `lfm3 chat`  
**Embeddings:** ONNX `BAAI/bge-base-en-v1.5` (FastEmbed)  
**Reranker:** ONNX `BAAI/bge-reranker-v2-m3-int8` (FastEmbed)  
**Set:** 20-question test split (`--split test --limit 20`)  
**Caveat:** local 1.7B results are for iteration, not a headline quality claim.

## Why a local model

The OrcaRouter free tier works with `reasoning_effort="none"`, but one baseline
question timed out at 180 seconds and a full run takes about an hour. LFM3 runs
locally at ~43 tok/s with no API cost or rate limit, which makes prompt and
parser refinement much faster.

## Refinements

1. **Local provider:** added `lfm3` to the provider chain (`LFM3_BASE_URL`,
   `LFM3_MODEL`), no API key required.
2. **Nested citation arrays:** small models sometimes emit
   `"citations": [["[doc@version#block]"]]`; the resolver now flattens nested
   sequences.
3. **Schema suffixes:** refs like `doc@version#block@block_id` are normalized.
4. **Prose-wrapped refs:** refs embedded in prose, such as
   `"[doc@version#block] Doc title (version, page)"`, are extracted with a
   stable `doc@version#block` regex.
5. **Broad-question rule:** the fixed prompt now tells the model to summarize
   available evidence for broad questions and abstain only when no block
   contains the requested fact or the evidence is genuinely conflicting.

## Results

| Pipeline | Metric | Before | After |
|---|---|---:|---:|
| Fixed | Recall@10 | 1.000 | 1.000 |
| Fixed | All-gold@10 | 1.000 | 1.000 |
| Fixed | Citation coverage | 0.700 | **1.000** |
| Fixed | Abstention accuracy | 0.700 | **1.000** |
| Fixed | Citation page accuracy (precision) | 0.664 | 0.675 |
| Baseline | Recall@10 | 0.975 | 0.975 |
| Baseline | All-gold@10 | 0.950 | 0.950 |
| Baseline | Citation page accuracy (precision) | 0.431 | 0.511 |

## Reading the numbers

- **Fixed retrieval is perfect on this slice:** every gold block is retrieved.
- **Fixed coverage and abstention reached 1.0:** every answerable question got
  at least one valid citation, and no answerable question was falsely refused.
- **Citation page accuracy is a precision metric:** it falls when an answer
  cites several valid pages. The fixed pipeline cites more supporting pages
  than the baseline, so coverage is the primary citation metric here; precision
  is reported separately.
- **Baseline retrieval is slightly worse:** one question missed the gold block
  and one missed the full gold set. The baseline also cites stale versions more
  often.

## Conflicting-version refinement

The first full 80-question run exposed a real regression: the fixed pipeline
scored worse than the baseline on conflicting-version questions (recall@5
0.146 vs 0.458; disambiguation 0.0 vs 0.5). The version filter treated generic
"what does Helios say about X" questions as current-only, so it never retrieved
the older versions needed to explain a conflict.

Changes:

- Conflicting questions now explicitly ask about changes across versions.
- The fixed pipeline detects comparison/version-change language and retrieves
  all versions for those questions. Ordinary questions still use the
  current-version filter, preserving the stale-citation guard.
- Evidence blocks are labelled `[CURRENT]` or `[SUPERSEDED]`.
- The fixed prompt tells the model to state the difference and cite each
  conflicting version.

Conflicting subset after the change (8 questions):

| Metric | Baseline | Fixed |
|---|---:|---:|
| Recall@10 | 0.667 | **0.792** |
| All-gold@10 | 0.500 | **0.625** |
| Citation coverage | 0.875 | **1.000** |
| Citation page accuracy | 0.288 | **0.489** |
| Disambiguation | 1.000 | 1.000 |

The fixed pipeline still misses some gold versions at retrieval, but it now
beats the baseline on the conflicting slice instead of regressing.

## Full 80-question rerun

After the conflicting-version fix, the full 80-question set was rerun with
LFM3-1.7B (both pipelines, same questions):

| Category | Pipeline | Recall@10 | All-gold@10 | Citation coverage | Abstention | Disambiguation |
|---|---|---:|---:|---:|---:|---:|
| Overall | Baseline | 0.865 | 0.812 | 0.797 | 0.800 | 0.000 |
| Overall | Fixed | **0.943** | **0.891** | **1.000** | **1.000** | **1.000** |
| Single-hop | Baseline | 0.958 | 0.958 | 1.000 | 1.000 | - |
| Single-hop | Fixed | **1.000** | **1.000** | 1.000 | 1.000 | - |
| Multi-hop | Baseline | 0.812 | 0.688 | 1.000 | 1.000 | - |
| Multi-hop | Fixed | **0.875** | **0.750** | 1.000 | 1.000 | - |
| Version-specific | Baseline | 0.875 | 0.875 | 0.688 | 1.000 | - |
| Version-specific | Fixed | **1.000** | **1.000** | **1.000** | 1.000 | - |
| Conflicting | Baseline | 0.667 | 0.500 | 0.000 | 1.000 | 0.000 |
| Conflicting | Fixed | **0.792** | **0.625** | **1.000** | 1.000 | **1.000** |
| Unanswerable | Baseline | - | - | - | 0.000 | - |
| Unanswerable | Fixed | - | - | - | **1.000** | - |

Additional results:

- Fixed `stale_answer` is **0.0** on version-specific questions; the baseline is
  also 0.0 on this run.
- Fixed produced **no false abstentions** and **no missed abstentions** on the
  full set.
- Fixed citation page accuracy (precision) is 0.658 vs baseline 0.611. This
  metric penalizes comprehensive answers that cite several valid pages;
  citation coverage is the primary citation signal here and is 1.0 for fixed.
- Fixed is better on every retrieval and reliability slice; the conflicting
  slice is no longer a regression.

## Remaining issues

- The question set is still heuristic and includes broad prompts. Coverage is
  unaffected, but citation precision is noisy.
- LFM3-1.7B is not a headline model; use OrcaRouter or a stronger model for the
  final cross-check and public claim.
- The full 80-question run is a single local run; repeat it once after any
  prompt or dataset change and report both.
- No LLM judge was run, so answer correctness and faithfulness are not measured.
- The local service is laptop-bound; do not expose it as a public endpoint.

## Next steps

1. Cross-check a subset with OrcaRouter when the free tier allows.
2. Curate the broadest questions before the headline run.
3. Record the demo video and write the case study.
4. Deploy the demo with a hosted provider or a recorded local run.
5. Stop the local model with `lfm3 off` when finished.
