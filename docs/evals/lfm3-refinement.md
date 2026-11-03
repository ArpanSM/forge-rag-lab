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

## Remaining issues

- The 20-question slice covers single-hop and multi-hop only; the full 80 adds
  version-specific, conflicting and unanswerable questions.
- The question set is still heuristic and includes broad prompts. Coverage is
  unaffected, but citation precision is noisy.
- LFM3-1.7B is not a headline model; use OrcaRouter or a stronger model for the
  final cross-check and public claim.
- The local service is laptop-bound; do not expose it as a public endpoint.

## Next steps

1. Run the full 80-question local eval.
2. Review category-level results for version-specific, conflicting and
   unanswerable questions.
3. Cross-check a subset with OrcaRouter when the free tier allows.
4. Curate the broadest questions before the headline run.
5. Record the demo video and write the case study only after the curated run.
