"""Read evaluation reports for the health-report endpoints.

The eval harness owns the report format. These readers accept the harness
``eval-report.json`` as well as the smaller contract-shaped ``summary.json`` /
``failures.json`` files, and always return the public API shape documented in
``docs/api-contract.md``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUMMARY_FILENAMES = ("summary.json", "eval-report.json")
FAILURE_FILENAMES = ("failures.json", "eval-report.json")


def read_eval_summary(reports_dir: Path) -> dict[str, Any]:
    payload = _read_first(reports_dir, SUMMARY_FILENAMES)
    if payload is None:
        return {"generated_at": None, "rows": []}
    if isinstance(payload, list):
        return {"generated_at": None, "rows": payload}
    if not isinstance(payload, dict):
        return {"generated_at": None, "rows": []}

    rows = payload.get("rows")
    if rows is None and isinstance(payload.get("summary"), list):
        rows = payload["summary"]
    if not isinstance(rows, list):
        rows = []

    result = dict(payload)
    result["generated_at"] = result.get("generated_at")
    result["rows"] = _pivot_summary(rows) if _looks_like_harness_rows(rows) else rows
    return result


def read_eval_failures(reports_dir: Path) -> list[dict[str, Any]]:
    payload = _read_first(reports_dir, FAILURE_FILENAMES)
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("failures", "items", "examples"):
        value = payload.get(key)
        if isinstance(value, list):
            items = [item for item in value if isinstance(item, dict)]
            return _pivot_failures(items) if _looks_like_harness_failures(items) else items
    return []


def _looks_like_harness_rows(rows: list[Any]) -> bool:
    return any(isinstance(row, dict) and "pipeline" in row and "value" in row for row in rows)


def _pivot_summary(rows: list[Any]) -> list[dict[str, Any]]:
    overall = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("category") in (None, "overall")
    ]
    if not overall:
        overall = [row for row in rows if isinstance(row, dict)]

    by_metric: dict[str, dict[str, Any]] = {}
    for row in overall:
        metric = str(row.get("metric") or "")
        pipeline = str(row.get("pipeline") or "")
        if not metric or not pipeline:
            continue
        entry = by_metric.setdefault(
            metric,
            {
                "metric": metric,
                "label": row.get("label"),
                "unit": row.get("unit"),
                "higher_is_better": row.get("higher_is_better", True),
                "baseline": None,
                "fixed": None,
                "delta": None,
                "n": 0,
            },
        )
        entry[pipeline] = row.get("value")
        entry["n"] = max(int(entry.get("n") or 0), int(row.get("n") or 0))
        if row.get("label"):
            entry["label"] = row["label"]
        if row.get("unit"):
            entry["unit"] = row["unit"]
        if row.get("higher_is_better") is not None:
            entry["higher_is_better"] = row["higher_is_better"]

    for entry in by_metric.values():
        baseline = entry.get("baseline")
        fixed = entry.get("fixed")
        if isinstance(baseline, (int, float)) and isinstance(fixed, (int, float)):
            entry["delta"] = fixed - baseline
    return list(by_metric.values())


def _looks_like_harness_failures(items: list[dict[str, Any]]) -> bool:
    return any("pipeline" in item for item in items)


def _pivot_failures(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        question_id = str(item.get("question_id") or "")
        if question_id:
            grouped.setdefault(question_id, []).append(item)

    pivoted: list[dict[str, Any]] = []
    for question_id, group in grouped.items():
        baseline = next((item for item in group if item.get("pipeline") == "baseline"), None)
        fixed = next((item for item in group if item.get("pipeline") == "fixed"), None)
        primary = fixed or baseline or group[0]
        reasons = sorted(
            {
                reason
                for item in group
                for reason in (item.get("reasons") or [item.get("failure")])
                if reason
            }
        )
        pivoted.append(
            {
                "question_id": question_id,
                "category": primary.get("category"),
                "question": primary.get("question"),
                "baseline_answer": (baseline or {}).get("answer", ""),
                "fixed_answer": (fixed or {}).get("answer", ""),
                "failure": (fixed or baseline or primary).get("failure"),
                "reasons": reasons,
                "baseline_citations": (baseline or {}).get("citations", []),
                "fixed_citations": (fixed or {}).get("citations", []),
                "expected": primary.get("expected", ""),
                "notes": primary.get("notes", ""),
            }
        )
    return pivoted


def _read_first(reports_dir: Path, names: tuple[str, ...]) -> Any | None:
    if not reports_dir.is_dir():
        return None
    for name in names:
        path = reports_dir / name
        if not path.is_file():
            continue
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
    return None
