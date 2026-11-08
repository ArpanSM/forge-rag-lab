# Case study: a RAG assistant that shows when it is wrong

> **In one paragraph:** A RAG assistant over versioned product documentation that cites the
> exact page and block, abstains when the evidence is missing, and shows the difference
> between a naive retrieval pipeline and a fixed one.
>
> **For:** clients whose support or docs assistant is sometimes confidently wrong, and
> engineers reviewing retrieval, citation and evaluation design.
>
> **Proof:** on 80 questions, the fixed pipeline raised retrieval recall@10 from 0.865 to
> 0.943, cited the gold source in every answerable answer, and abstained on all 16
> unanswerable questions. The corpus and questions are synthetic, so these are development
> numbers, not a production benchmark.

**Live demo:** https://arpansm.github.io/forge-rag-lab/  
**Proof film (45 s):** https://github.com/ArpanSM/forge-rag-lab/releases/download/v0.1.2-demo/forge-rag-lab-proof-45s.mp4  
**Walkthrough (75 s):** https://github.com/ArpanSM/forge-rag-lab/releases/download/v0.1.1-demo/forge-rag-lab-demo.mp4  
**Code:** https://github.com/ArpanSM/forge-rag-lab

## The problem

A RAG assistant can sound confident and still be wrong. It retrieves an old version of a policy, cites the wrong page, misses a detail buried in a long document, or answers a question the corpus cannot support. The worst part is that none of this looks broken in a normal demo. The answer is fluent, so everyone assumes it is grounded.

I built this project to make those failures visible, then fix them and measure the difference.

## What I built

A small RAG assistant over a synthetic, versioned SaaS documentation set. The corpus has 62 document versions and 388 blocks across three versions and two tenants. Documents are split into stable blocks, so a citation can point to a specific document version, page and block instead of a vague chunk.

The application has two pipelines:

- **Baseline:** fixed-size chunks, dense-only retrieval, no version filter, no reranker and no abstention. It is deliberately naive.
- **Fixed:** structure-aware chunks, ONNX BGE-base dense embeddings plus BM25, reciprocal-rank fusion, tenant and version filters, a cross-encoder reranker, claim-level citations, unsupported-claim dropping, abstention and a prompt-injection sanitizer.

The UI lets you ask the same question through both pipelines, open a citation drawer and inspect the exact source block. The health report shows the measured results and a failure gallery.

## What I measured

I wrote 80 questions: 24 single-hop, 16 multi-hop, 16 version-specific, 8 conflicting-version and 16 unanswerable. I ran both pipelines over the same set with a local LFM3-1.7B model.

| Metric | Baseline | Fixed |
|---|---:|---:|
| Retrieval recall@10 | 0.865 | **0.943** |
| Gold-source citation coverage | 0.797 | **1.000** |
| Correct abstention | 0.800 | **1.000** |
| Version disambiguation | 0.000 | **1.000** |
| Citation page accuracy (precision) | 0.611 | 0.658 |

The fixed pipeline found the right evidence more often, cited the gold source in every answerable answer, abstained on all 16 unanswerable questions, and handled conflicting versions instead of silently choosing one. The baseline answered all 16 unanswerable questions.

A 10-question hosted cross-check with OrcaRouter showed the same direction: recall@10 0.875 vs 0.833, all-gold@10 0.875 vs 0.750, and context precision 0.693 vs 0.367.

**Caveats:** synthetic corpus, heuristic questions, local 1.7B model, one run, no LLM judge. These are development numbers, not a production benchmark. The full breakdown is in [`docs/evals/lfm3-refinement.md`](evals/lfm3-refinement.md).

## What went wrong, and what I changed

I ran a two-axis code review after the first implementation. It caught three issues worth fixing before showing the project:

1. **The static health report was showing invented metrics.** The first fixture data looked plausible but was not measured. I replaced it with the real 80-question numbers, removed judge-only rows, and corrected the copy.
2. **The eval API did not match its documented contract.** The API returned the harness shape instead of the `{metric, baseline, fixed, delta, n}` shape the UI expected. I added a translation layer and tests.
3. **The fixed pipeline regressed on conflicting versions.** It was current-only, so it never retrieved the older versions needed to explain a conflict. I changed the version filter to detect comparison questions, retrieve all relevant versions, label evidence as current or superseded, and ask the model to state the difference.

I also added deterministic factual F1, paired bootstrap comparisons, and a test for the citation parsing bugs that small models expose. The review is part of the story: the first version looked good, and the checks found real problems.

## What this means for a client

If your RAG assistant is already live and “sometimes wrong,” the first step is not a rebuild. It is a short audit:

- reproduce the bad answers,
- measure retrieval and citation quality,
- separate stale-version failures from generation failures,
- rank the fixes by impact,
- and add a small regression set so the fixes stay fixed.

That is the offer: a **3–5 day RAG audit** with a written report and a prioritized fix list, followed by a fixed-scope implementation if you want the fixes delivered.

The same reliability approach applies to tool-using agents and voice agents: make the failure modes visible, measure them, and only then claim the system works.

## Limitations

- The hosted demo runs in fixture mode; the full API and model run locally. The video is a fixture-mode walkthrough.
- The corpus is synthetic. The next step is a client corpus and a human-reviewed eval set.
- Citation precision is still noisy: the fixed pipeline cites several valid pages, which lowers page precision even when coverage is perfect.
- The 20-question private shadow set, LLM-judge correctness/faithfulness and deployment of the live API are still pending.

## Try the audit checklist

I turned the failure modes into a short [RAG audit checklist](rag-audit-checklist.md). It is the same list I would use on a client corpus.

## Links

- [Live fixture-mode demo](https://arpansm.github.io/forge-rag-lab/)
- [45-second proof film](https://github.com/ArpanSM/forge-rag-lab/releases/download/v0.1.2-demo/forge-rag-lab-proof-45s.mp4)
- [75-second narrated walkthrough](https://github.com/ArpanSM/forge-rag-lab/releases/download/v0.1.1-demo/forge-rag-lab-demo.mp4)
- [Code and evaluation harness](https://github.com/ArpanSM/forge-rag-lab)
- [Learning map](learning/rag-lab.md)
- [Evaluation report](evals/lfm3-refinement.md)
