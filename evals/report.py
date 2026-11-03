"""Build, render and persist evaluation reports.

The JSON report is the source of truth; the Markdown report is the human view
with overall/category tables, a failure gallery and caveats.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evals.metrics import aggregate_metric_rows
from evals.schema import (
    CATEGORIES,
    FailureCase,
    FailureName,
    MetricRow,
    Question,
    Report,
    Result,
)

DEFAULT_CAVEATS: tuple[str, ...] = (
    "Small slices are exploratory: the conflicting-version slice is a failure audit, not a stable rate. Wilson/bootstrap intervals are reported with every row and are wide at this n.",
    "Deterministic context recall is block-ID based, not claim-level entailment. Enable the optional Ragas judge for semantic context precision/recall.",
    "Citation page accuracy is undefined for answers with no citations; citation coverage is reported separately so abstention cannot hide behind a precise denominator.",
    "Stale-answer and stale-citation are only computed on version-specific questions with a target version.",
    "Latency is local, single-process wall time excluding judge calls; it is not a production latency claim.",
    "No statistical significance is claimed from these numbers. A paired test on the same questions is required for baseline-vs-fixed claims.",
    "Questions are generated heuristically from the corpus manifest and need human review before they are treated as a headline benchmark.",
)

_FAILURE_PRIORITY: tuple[FailureName, ...] = (
    "pipeline_error",
    "false_abstention",
    "missed_abstention",
    "stale_answer",
    "no_disambiguation",
    "citation_page_miss",
    "all_gold_miss",
    "retrieval_miss",
)

_GALLERY_METRICS = (
    "recall_at_10",
    "all_gold_at_10",
    "context_precision_at_10",
    "citation_page_accuracy",
    "stale_answer",
    "disambiguation",
    "abstention_correct",
)


def _failure_reasons(question: Question, result: Result) -> list[FailureName]:
    reasons: list[FailureName] = []
    if result.error:
        reasons.append("pipeline_error")
        return reasons
    if question.answerable and result.abstained:
        reasons.append("false_abstention")
    if not question.answerable and not result.abstained:
        reasons.append("missed_abstention")
    if question.category == "version_specific" and result.metrics.get("stale_answer") == 1.0:
        reasons.append("stale_answer")
    if question.category == "conflicting" and result.metrics.get("disambiguation") == 0.0:
        reasons.append("no_disambiguation")
    if question.answerable and not result.abstained:
        page_accuracy = result.metrics.get("citation_page_accuracy")
        if page_accuracy is not None and page_accuracy < 1.0:
            reasons.append("citation_page_miss")
        if result.metrics.get("all_gold_at_10") == 0.0:
            reasons.append("all_gold_miss")
        recall = result.metrics.get("recall_at_10")
        if recall is not None and recall < 1.0:
            reasons.append("retrieval_miss")
    return reasons


def collect_failures(
    questions: Sequence[Question],
    results_by_pipeline: Mapping[str, Sequence[Result]],
) -> list[FailureCase]:
    by_question = {question.question_id: question for question in questions}
    failures: list[FailureCase] = []
    for pipeline in sorted(results_by_pipeline):
        for result in sorted(results_by_pipeline[pipeline], key=lambda item: item.question_id):
            question = by_question.get(result.question_id)
            if question is None:
                continue
            reasons = _failure_reasons(question, result)
            if not reasons:
                continue
            primary = next(reason for reason in _FAILURE_PRIORITY if reason in reasons)
            metrics = {
                key: result.metrics.get(key)
                for key in _GALLERY_METRICS
                if result.metrics.get(key) is not None
            }
            notes = question.notes
            if result.error:
                notes = f"{notes} Error: {result.error}".strip()
            failures.append(
                FailureCase(
                    question_id=question.question_id,
                    category=question.category,
                    pipeline=pipeline,
                    failure=primary,
                    reasons=reasons,
                    question=question.question,
                    expected=question.gold_answer,
                    answer=result.answer,
                    citations=result.citations,
                    metrics=metrics,
                    notes=notes,
                )
            )
    return failures


def build_report(
    questions: Sequence[Question],
    results_by_pipeline: Mapping[str, Sequence[Result]],
    *,
    dataset_path: str = "",
    confidence: float = 0.95,
    bootstrap_samples: int = 2_000,
    seed: int = 20261103,
    extra_caveats: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> Report:
    rows = aggregate_metric_rows(
        questions,
        results_by_pipeline,
        confidence=confidence,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )
    failures = collect_failures(questions, results_by_pipeline)
    category_counts = Counter(question.category for question in questions)
    split_counts = Counter(question.split for question in questions)

    caveats = list(DEFAULT_CAVEATS)
    judge_present = any(
        result.judge is not None
        for results in results_by_pipeline.values()
        for result in results
    )
    if not judge_present:
        caveats.append(
            "LLM judge metrics were not run. Set EVAL_ENABLE_LLM_JUDGE=1 with a configured "
            "Ragas judge (and any required provider key) to enable answer correctness and faithfulness."
        )
    if extra_caveats:
        caveats.extend(extra_caveats)

    digest = hashlib.sha256(
        json.dumps(
            [question.model_dump(mode="json") for question in questions],
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    report_metadata: dict[str, Any] = {
        "bootstrap_samples": bootstrap_samples,
        "confidence": confidence,
        "seed": seed,
        "dataset_sha256": digest,
        "failure_count": len(failures),
        "judge_enabled": judge_present,
    }
    if metadata:
        report_metadata.update(metadata)

    return Report(
        generated_at=datetime.now(UTC),
        dataset_path=dataset_path,
        n_questions=len(questions),
        pipelines=sorted(results_by_pipeline),
        category_counts={category: category_counts.get(category, 0) for category in CATEGORIES},
        split_counts={key: split_counts[key] for key in sorted(split_counts)},
        rows=rows,
        failures=failures,
        caveats=caveats,
        metadata=report_metadata,
    )


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _format_value(row: MetricRow) -> str:
    if row.value is None:
        return "—"
    if row.unit == "ms":
        return f"{row.value:.1f}"
    return f"{row.value:.3f}"


def _format_interval(row: MetricRow) -> str:
    if row.ci_low is None or row.ci_high is None:
        return "—"
    if row.unit == "ms":
        return f"[{row.ci_low:.1f}, {row.ci_high:.1f}]"
    return f"[{row.ci_low:.3f}, {row.ci_high:.3f}]"


def _table(rows: Sequence[MetricRow]) -> list[str]:
    if not rows:
        return ["_No metrics available for this slice._", ""]
    lines = [
        "| Pipeline | Metric | Value | 95% CI | n | Better |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        better = "higher" if row.higher_is_better else "lower"
        lines.append(
            f"| {_escape(row.pipeline)} | {_escape(row.label)} | {_format_value(row)} "
            f"| {_format_interval(row)} | {row.n} | {better} |"
        )
    lines.append("")
    return lines


def _comparison_table(rows: Sequence[MetricRow]) -> list[str]:
    overall = [row for row in rows if row.category == "overall"]
    pipelines = sorted({row.pipeline for row in overall})
    if len(pipelines) < 2:
        return []
    preferred = [name for name in ("baseline", "fixed") if name in pipelines]
    pipelines = preferred + [name for name in pipelines if name not in preferred]
    by_metric: dict[str, dict[str, MetricRow]] = {}
    labels: dict[str, str] = {}
    for row in overall:
        by_metric.setdefault(row.metric, {})[row.pipeline] = row
        labels[row.metric] = row.label
    lines = [
        "## Pipeline comparison",
        "",
        "| Metric | " + " | ".join(pipelines) + " | Delta (last - first) |",
        "|---|" + "---:|" * len(pipelines) + "---:|",
    ]
    for metric, per_pipeline in by_metric.items():
        cells = []
        values: list[float | None] = []
        for pipeline in pipelines:
            row = per_pipeline.get(pipeline)
            cells.append(_format_value(row) if row else "—")
            values.append(row.value if row else None)
        if values and values[0] is not None and values[-1] is not None:
            delta = values[-1] - values[0]
            delta_text = f"{delta:+.3f}"
        else:
            delta_text = "—"
        lines.append(f"| {_escape(labels[metric])} | " + " | ".join(cells) + f" | {delta_text} |")
    lines.append("")
    return lines


def _failure_gallery(report: Report, limit: int = 12) -> list[str]:
    if not report.failures:
        return ["## Failure gallery", "", "No failures recorded.", ""]
    lines = ["## Failure gallery", ""]
    for failure in report.failures[:limit]:
        lines.append(f"### {failure.question_id} · {failure.category} · {failure.pipeline}")
        lines.append("")
        lines.append(f"- **Failure:** `{failure.failure}`")
        if len(failure.reasons) > 1:
            lines.append(f"- **Reasons:** {', '.join(f'`{reason}`' for reason in failure.reasons)}")
        lines.append(f"- **Question:** {_escape(failure.question)}")
        lines.append(f"- **Gold answer:** {_escape(failure.expected)[:500]}")
        lines.append(f"- **Answer:** {_escape(failure.answer)[:500] or '(empty)'}")
        if failure.citations:
            citations = ", ".join(
                f"{citation.doc_id}@{citation.version}#{citation.block_id}"
                + (f" p{citation.page}" if citation.page is not None else "")
                for citation in failure.citations
            )
            lines.append(f"- **Citations:** {citations}")
        else:
            lines.append("- **Citations:** none")
        if failure.metrics:
            metrics = ", ".join(
                f"{key}={value:.3f}" if isinstance(value, float) else f"{key}={value}"
                for key, value in failure.metrics.items()
            )
            lines.append(f"- **Metrics:** {metrics}")
        if failure.notes:
            lines.append(f"- **Notes:** {_escape(failure.notes)}")
        lines.append("")
    if len(report.failures) > limit:
        lines.append(
            f"_{len(report.failures) - limit} more failures are in the JSON report._"
        )
        lines.append("")
    return lines


def render_markdown(report: Report) -> str:
    """Render a complete Markdown report."""

    overall = [row for row in report.rows if row.category == "overall"]
    lines = [
        "# Forge RAG Lab evaluation report",
        "",
        f"Generated: {report.generated_at.isoformat()}",
        f"Dataset: `{report.dataset_path}` ({report.n_questions} questions)",
        f"Pipelines: {', '.join(report.pipelines) or 'none'}",
        f"Splits: {report.split_counts}",
        "",
        "## Overall",
        "",
        *_table(overall),
        *_comparison_table(report.rows),
        "## By category",
        "",
    ]
    for category in CATEGORIES:
        category_rows = [row for row in report.rows if row.category == category]
        lines.extend([f"### {category} (n={report.category_counts.get(category, 0)})", ""])
        lines.extend(_table(category_rows))
    lines.extend(_failure_gallery(report))
    lines.extend(["## Caveats", ""])
    lines.extend(f"- {caveat}" for caveat in report.caveats)
    lines.extend(["", "---", "Generated by `evals/runner.py`; JSON is the machine-readable source."])
    return "\n".join(lines) + "\n"


def write_report(
    report: Report,
    output_dir: str | Path,
    *,
    json_name: str = "eval-report.json",
    markdown_name: str = "eval-report.md",
) -> tuple[Path, Path]:
    """Write JSON and Markdown reports, creating the output directory."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / json_name
    markdown_path = directory / markdown_name
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, markdown_path
