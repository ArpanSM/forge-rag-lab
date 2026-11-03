"""Read evaluation reports for the health-report endpoints.

The eval harness owns the report format. These readers accept the common
``summary.json`` / ``failures.json`` shape and degrade to empty results when a
report is missing or malformed, so the API never depends on eval state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUMMARY_FILENAMES = ("summary.json", "eval_summary.json", "eval-summary.json")
FAILURE_FILENAMES = ("failures.json", "eval_failures.json", "eval-failures.json")


def read_eval_summary(reports_dir: Path) -> dict[str, Any]:
    payload = _read_first(reports_dir, SUMMARY_FILENAMES, "*summary*.json")
    if payload is None:
        return {"generated_at": None, "rows": []}
    if isinstance(payload, list):
        return {"generated_at": None, "rows": payload}
    if isinstance(payload, dict):
        rows = payload.get("rows")
        if rows is None and isinstance(payload.get("summary"), list):
            rows = payload["summary"]
        result = dict(payload)
        result["generated_at"] = result.get("generated_at")
        result["rows"] = rows if isinstance(rows, list) else []
        return result
    return {"generated_at": None, "rows": []}


def read_eval_failures(reports_dir: Path) -> list[dict[str, Any]]:
    payload = _read_first(reports_dir, FAILURE_FILENAMES, "*failure*.json")
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("failures", "items", "examples"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _read_first(reports_dir: Path, names: tuple[str, ...], fallback_glob: str) -> Any | None:
    if not reports_dir.is_dir():
        return None
    candidates = [reports_dir / name for name in names if (reports_dir / name).is_file()]
    if not candidates:
        candidates = sorted(reports_dir.glob(fallback_glob))
    for path in candidates:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
    return None
