"""JSON-in/JSON-out adapter used by the evaluation harness.

The harness (``evals/config.yaml``) runs ``python -m rag.pipeline --json`` once
per question. This module keeps the backend independent of ``evals`` while
emitting the result shape the harness expects.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from rag.models import Answer, RetrievedBlock
from rag.service import RagService, build_service_from_env


def answer_to_result(question: dict[str, Any], answer: Answer) -> dict[str, Any]:
    question_id = str(question.get("question_id") or "")
    tenant_id = question.get("tenant_id")
    citations: list[dict[str, Any]] = []
    for claim in answer.claims:
        for citation in claim.citations:
            citations.append(
                {
                    "doc_id": citation.doc_id,
                    "version": citation.version,
                    "block_id": citation.block_id,
                    "page": citation.page,
                    "anchor": citation.anchor,
                    "title": citation.title,
                    "quote": citation.quote,
                    "tenant_id": tenant_id,
                }
            )

    retrieved = [
        _retrieved_chunk(block, rank=index) for index, block in enumerate(answer.retrieved, start=1)
    ]
    return {
        "question_id": question_id,
        "pipeline": answer.pipeline,
        "answer": answer.answer,
        "abstained": answer.abstained,
        "citations": citations,
        "retrieved": retrieved,
        "latency_ms": float(answer.latency_ms),
        "metrics": {},
        "model": answer.model,
        "trace_id": answer.trace_id,
        "metadata": {
            "injection_detected": answer.injection_detected,
            "retrieved_count": len(retrieved),
        },
    }


def run_question(
    question: dict[str, Any], service: RagService, pipeline: str = "fixed"
) -> dict[str, Any]:
    tenant_id = str(question.get("tenant_id") or "")
    question_text = str(question.get("question") or "")
    selected = "baseline" if pipeline == "baseline" else "fixed"
    answer = service.query(tenant_id, question_text, selected)
    return answer_to_result(question, answer)


def error_result(question: dict[str, Any], pipeline: str, error: Exception | str) -> dict[str, Any]:
    return {
        "question_id": str(question.get("question_id") or ""),
        "pipeline": pipeline,
        "answer": "",
        "abstained": True,
        "citations": [],
        "retrieved": [],
        "latency_ms": 0.0,
        "metrics": {},
        "error": str(error),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one question through the RAG pipeline.")
    parser.add_argument(
        "--pipeline",
        choices=("fixed", "baseline"),
        default=os.environ.get("PIPELINE", "fixed"),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit one JSON result (the default; kept for eval config compatibility)",
    )
    args = parser.parse_args(argv)

    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        print(json.dumps(error_result({}, args.pipeline, exc)))
        return 1
    if not isinstance(payload, dict):
        print(json.dumps(error_result({}, args.pipeline, "question must be a JSON object")))
        return 1

    try:
        service = build_service_from_env()
        result = run_question(payload, service, args.pipeline)
    except Exception as exc:  # noqa: BLE001 - the harness reads the error field
        result = error_result(payload, args.pipeline, exc)
    print(json.dumps(result))
    return 0


def _retrieved_chunk(block: RetrievedBlock, *, rank: int) -> dict[str, Any]:
    return {
        "doc_id": block.doc_id,
        "version": block.version,
        "block_id": block.block_id,
        "page": block.page,
        "anchor": block.anchor,
        "title": block.title,
        "tenant_id": block.tenant_id,
        "rank": rank,
        "text": block.text,
        "score": block.score,
    }


if __name__ == "__main__":
    raise SystemExit(main())
