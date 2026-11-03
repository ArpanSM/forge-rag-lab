"""Summarize an evaluation report by overall and category metrics.

Usage:
    python scripts/summarize_eval.py evals/reports/eval-report.json
    python scripts/summarize_eval.py --failures 8
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

OVERALL_METRICS = (
    "recall_at_5",
    "recall_at_10",
    "all_gold_at_10",
    "context_precision_at_10",
    "citation_coverage",
    "citation_page_accuracy",
    "abstention_correct",
    "stale_answer",
    "disambiguation",
    "p50_latency_ms",
    "p95_latency_ms",
)


def _row_lookup(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {(row["pipeline"], row["category"], row["metric"]): row for row in rows}


def _print_table(
    lookup: dict[tuple[str, str, str], dict[str, Any]],
    pipelines: list[str],
    categories: list[str],
    metrics: tuple[str, ...],
) -> None:
    header = f"{'category':16} {'pipeline':10} " + " ".join(f"{metric:>20}" for metric in metrics)
    print(header)
    print("-" * len(header))
    for category in categories:
        for pipeline in pipelines:
            values = []
            for metric in metrics:
                row = lookup.get((pipeline, category, metric))
                values.append(f"{row['value']:>20.3f}" if row else f"{'-':>20}")
            print(f"{category:16} {pipeline:10} " + " ".join(values))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "report",
        nargs="?",
        default="evals/reports/eval-report.json",
        help="path to eval-report.json",
    )
    parser.add_argument("--failures", type=int, default=5, help="number of failures to print")
    args = parser.parse_args()

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    rows = report.get("rows", [])
    failures = report.get("failures", [])
    pipelines = sorted(report.get("pipelines", []))
    categories = ["overall", *sorted(report.get("category_counts", {}))]
    lookup = _row_lookup(rows)

    print(f"report: {args.report}")
    print(f"generated: {report.get('generated_at')}  questions: {report.get('n_questions')}")
    print(f"pipelines: {', '.join(pipelines)}")
    metadata = report.get("metadata", {})
    for key in ("provider", "embedder", "reranker", "judge_enabled"):
        if key in metadata:
            print(f"{key}: {metadata[key]}")
    print()

    print("Overall metrics")
    _print_table(lookup, pipelines, ["overall"], OVERALL_METRICS)
    print("\nBy category")
    _print_table(lookup, pipelines, categories, OVERALL_METRICS)

    if failures:
        print("\nFailure summary")
        by_pipeline = Counter((item["pipeline"], item["failure"]) for item in failures)
        by_category = Counter((item["pipeline"], item["category"]) for item in failures)
        for (pipeline, failure), count in sorted(by_pipeline.items()):
            print(f"  {pipeline:10} {failure:24} {count}")
        print("\n  by category")
        for (pipeline, category), count in sorted(by_category.items()):
            print(f"  {pipeline:10} {category:24} {count}")

        print(f"\nFirst {min(args.failures, len(failures))} failures")
        for item in failures[: args.failures]:
            print(
                f"\n  [{item['pipeline']}] {item['question_id']} "
                f"{item['category']} -> {item['failure']} ({', '.join(item['reasons'])})"
            )
            print(f"  Q: {item['question']}")
            print(f"  A: {item['answer'][:280]}")
            print(f"  Citations: {len(item['citations'])}  Metrics: {item['metrics']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
