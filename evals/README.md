# Evaluation harness

A thin, Forge-owned harness for the Helios RAG lab. It scores retrieval,
citations, version safety, abstention and latency deterministically, then writes
JSON and Markdown reports. Ragas is optional and only used behind an env flag.

## Layout

| Path | Purpose |
|---|---|
| `schema.py` | Pydantic models for questions, sources, citations, results, metric rows, failures and reports. |
| `dataset.py` | Manifest loader and deterministic 80-question generator (24 single-hop, 16 multi-hop, 16 version-specific, 8 conflicting, 16 unanswerable). |
| `metrics.py` | Recall@5/10, all-gold@10, context precision/recall, citation page accuracy, stale-answer/citation, abstention, latency, Wilson/bootstrap intervals. |
| `runner.py` | Dependency-injected pipeline runner, command adapter, JSON-in/JSON-out CLI. |
| `report.py` | Overall/category tables, failure gallery, caveats, JSON + Markdown writers. |
| `judge.py` | Optional Ragas 0.4.x answer-correctness/faithfulness judge. |
| `data/questions.json` | The committed 80-question set generated from `data/manifests/corpus.json`. |
| `fixtures/` | Small self-contained manifest and question set used by unit tests. |

## Generate the dataset

```bash
python -m evals.dataset \
  --manifest data/manifests/corpus.json \
  --out evals/data/questions.json
```

The generator is deterministic for a fixed seed, uses real block IDs/pages from
the manifest, and fails loudly if the corpus cannot satisfy a quota. It assigns
40 dev / 40 test questions with category-stratified splits.

## Run an evaluation

Configure `evals/config.yaml`, then:

```bash
python -m evals.runner --config evals/config.yaml
```

The configured pipeline command receives one `Question` as JSON on stdin and
must print one `Result` as JSON on stdout. A minimal output is:

```json
{
  "question_id": "q001",
  "pipeline": "fixed",
  "answer": "Open Settings > API keys and choose Rotate.",
  "abstained": false,
  "citations": [
    {"doc_id": "helios-api-keys", "version": "v3", "block_id": "b3", "page": 2}
  ],
  "retrieved": [
    {"doc_id": "helios-api-keys", "version": "v3", "block_id": "b3", "page": 2, "text": "..."}
  ],
  "latency_ms": 812
}
```

Reports land in `evals/reports/` by default (`eval-report.json` and
`eval-report.md`). Use `--split dev|test`, `--limit`, or `--regenerate` for
smoke runs.

## Optional Ragas judge

Core tests and reports need no LLM or API key. To add answer correctness and
faithfulness:

```bash
pip install "ragas>=0.4.3"
export EVAL_ENABLE_LLM_JUDGE=1
# Configure the Ragas provider you want to use (local Ollama, free-tier key, etc.)
python -m evals.runner --config evals/config.yaml --judge
```

Judge failures are recorded as caveats, not crashes. The deterministic metrics
remain the primary evidence.

## Tests

```bash
pip install -r requirements-evals.txt
python -m pytest -q
```

The test suite uses `evals/fixtures/corpus_smoke.json` and
`evals/fixtures/questions_small.json`; it does not call an LLM.

## Metric notes

- Retrieval recall is macro over answerable questions; unanswerable questions
  are excluded instead of counted as zero.
- Context recall is the deterministic ID-based variant. It is not claim-level
  entailment; use the judge for semantic context recall.
- Citation page accuracy is undefined without citations. Citation coverage is
  reported separately.
- Stale-answer uses the first citation on version-specific questions.
- Abstention accuracy scores both sides: abstaining on unanswerable questions
  and answering answerable ones.
- Latency uses nearest-rank p50/p95 and excludes judge time.
- Wilson intervals are used for binary rates; seeded percentile bootstrap
  intervals are used for continuous metrics. Small slices are exploratory.
