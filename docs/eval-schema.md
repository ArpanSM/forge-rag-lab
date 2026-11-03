# Evaluation Schema

## Question

```json
{
  "question_id": "q001",
  "tenant_id": "northwind",
  "question": "How do I rotate an API key in v3?",
  "category": "single_hop",
  "answerable": true,
  "gold_answer": "Open Settings → API keys and choose Rotate. The old key remains valid for 24 hours.",
  "gold_sources": [
    {
      "doc_id": "helios-api-keys",
      "version": "v3",
      "block_id": "b4",
      "page": 2
    }
  ],
  "notes": "Version-specific; v2 has no grace period."
}
```

Categories: `single_hop`, `multi_hop`, `version_specific`, `conflicting`, `unanswerable`.

## Result

```json
{
  "question_id": "q001",
  "pipeline": "fixed",
  "answer": "...",
  "abstained": false,
  "citations": [
    {
      "doc_id": "helios-api-keys",
      "version": "v3",
      "block_id": "b4",
      "page": 2
    }
  ],
  "latency_ms": 1234,
  "metrics": {
    "recall_at_5": 1.0,
    "citation_page_accuracy": 1.0,
    "stale_answer": 0.0,
    "abstention_correct": 1.0
  },
  "judge": {
    "answer_correctness": 0.9,
    "faithfulness": 1.0,
    "model": "judge-model-id"
  }
}
```

## Dataset quotas

- 24 single-hop
- 16 multi-hop
- 16 version-specific
- 8 conflicting-version
- 16 unanswerable
- Total: 80
- Split: 40 dev / 40 test
- Private shadow set: 20 questions, not committed

## Reporting

- Report per-category and overall metrics.
- Report n and confidence intervals.
- Report failures, not only averages.
- Do not claim statistical significance from small slices without a paired test.
