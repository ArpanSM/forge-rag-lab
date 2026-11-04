"""Small timing helpers shared by the pipelines and generator."""

from __future__ import annotations

import time


def elapsed_ms(started: float) -> int:
    """Whole milliseconds since ``started`` (a ``time.perf_counter`` value)."""
    return max(0, round((time.perf_counter() - started) * 1000))
