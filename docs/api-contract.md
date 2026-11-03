# API Contract

Base URL: `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000`).

## `GET /api/health`

```json
{
  "status": "ok",
  "version": "0.1.0",
  "qdrant": "ok",
  "model_provider": "gemini"
}
```

## `POST /api/query`

Request:

```json
{
  "tenant_id": "northwind",
  "question": "How do I rotate an API key in v3?",
  "pipeline": "fixed"
}
```

`pipeline` is `fixed` or `baseline`.

Response:

```json
{
  "answer": "In v3, open Settings → API keys and choose Rotate. The old key stays valid for 24 hours.",
  "abstained": false,
  "claims": [
    {
      "claim_id": "c1",
      "text": "The old key stays valid for 24 hours.",
      "citations": [
        {
          "doc_id": "helios-api-keys",
          "title": "API keys",
          "version": "v3",
          "page": 2,
          "block_id": "b4",
          "anchor": "#rotation-grace-period",
          "quote": "Rotated keys remain valid for 24 hours..."
        }
      ]
    }
  ],
  "latency_ms": 1234,
  "model": "gemini-3.5-flash-lite",
  "pipeline": "fixed",
  "trace_id": "01J..."
}
```

## `GET /api/demo/questions`

Returns sample questions for the chat UI:

```json
[
  {
    "id": "demo-1",
    "tenant_id": "northwind",
    "question": "How do I rotate an API key in v3?",
    "category": "version_specific"
  }
]
```

## `GET /api/eval/summary`

Returns the metric table used by the health report:

```json
{
  "generated_at": "2026-11-03T00:00:00Z",
  "rows": [
    {
      "metric": "citation_page_accuracy",
      "baseline": 0.61,
      "fixed": 0.92,
      "delta": 0.31,
      "n": 80
    }
  ]
}
```

## `GET /api/eval/failures`

Returns failure examples for the health report:

```json
[
  {
    "question_id": "q014",
    "category": "conflicting",
    "question": "...",
    "baseline_answer": "...",
    "fixed_answer": "...",
    "failure": "stale_citation",
    "fixed_citations": []
  }
]
```

## `GET /api/docs/{doc_id}/blocks/{block_id}?tenant_id=northwind`

Returns one block for the citation viewer:

```json
{
  "doc_id": "helios-api-keys",
  "tenant_id": "northwind",
  "title": "API keys",
  "version": "v3",
  "page": 2,
  "block_id": "b4",
  "anchor": "#rotation-grace-period",
  "heading": "Rotation grace period",
  "text": "Rotated keys remain valid for 24 hours..."
}
```
