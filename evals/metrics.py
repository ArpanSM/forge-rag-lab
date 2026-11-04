"""Deterministic retrieval, citation, version and abstention metrics.

No LLM, network or API key is used here. The definitions follow
``research/rag-eval-tooling.md`` and ``docs/eval-schema.md``:

* retrieval recall is macro over answerable questions and uses block IDs;
* context precision is rank-weighted (Ragas-style);
* context recall is the deterministic ID-based variant;
* citation page accuracy compares document, version and page;
* stale-answer uses the first citation on version-specific questions;
* abstention is scored on both answerable and unanswerable questions;
* latency uses nearest-rank p50/p95.

Confidence intervals are Wilson for binary rates and seeded bootstrap
percentiles for continuous metrics, so reports are reproducible.
"""

from __future__ import annotations

import math
import random
import re
import statistics
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from evals.schema import (
    CATEGORIES,
    Citation,
    GoldSource,
    MetricRow,
    PairedComparison,
    Question,
    Result,
)

MetricKind = Literal["continuous", "rate"]


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    kind: MetricKind
    higher_is_better: bool = True


METRIC_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec("recall_at_5", "Recall@5", "continuous"),
    MetricSpec("recall_at_10", "Recall@10", "continuous"),
    MetricSpec("all_gold_at_10", "All-gold@10", "rate"),
    MetricSpec("context_precision_at_10", "Context precision@10", "continuous"),
    MetricSpec("context_recall_at_10", "Context recall@10", "continuous"),
    MetricSpec("factual_f1", "Factual F1", "continuous"),
    MetricSpec("citation_page_accuracy", "Citation page accuracy", "continuous"),
    MetricSpec("citation_coverage", "Citation coverage", "continuous"),
    MetricSpec("stale_answer", "Stale-answer rate", "rate", higher_is_better=False),
    MetricSpec("stale_citation", "Stale-citation rate", "continuous", higher_is_better=False),
    MetricSpec("disambiguation", "Version disambiguation", "rate"),
    MetricSpec("abstention_correct", "Abstention accuracy", "rate"),
    MetricSpec("false_abstention", "False-abstention rate", "rate", higher_is_better=False),
    MetricSpec("missed_abstention", "Missed-abstention rate", "rate", higher_is_better=False),
)

JUDGE_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec("answer_correctness", "Answer correctness (judge)", "continuous"),
    MetricSpec("faithfulness", "Faithfulness (judge)", "continuous"),
    MetricSpec("context_precision", "Context precision (judge)", "continuous"),
    MetricSpec("context_recall", "Context recall (judge)", "continuous"),
)


# ---------------------------------------------------------------------------
# Small statistics helpers
# ---------------------------------------------------------------------------


def wilson_interval(
    successes: int,
    n: int,
    confidence: float = 0.95,
) -> tuple[float | None, float | None]:
    """Wilson score interval for a binomial rate ``successes / n``."""

    if n < 0 or successes < 0 or successes > n:
        raise ValueError("require 0 <= successes <= n")
    if n == 0:
        return None, None
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    z = statistics.NormalDist().inv_cdf(1.0 - (1.0 - confidence) / 2.0)
    p = successes / n
    denominator = 1.0 + (z * z) / n
    centre = (p + (z * z) / (2.0 * n)) / denominator
    margin = (
        z
        * math.sqrt((p * (1.0 - p) / n) + (z * z) / (4.0 * n * n))
        / denominator
    )
    low = max(0.0, centre - margin)
    high = min(1.0, centre + margin)
    if successes == 0:
        low = 0.0
    if successes == n:
        high = 1.0
    return low, high


def _quantile(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("quantile of empty sequence")
    if probability <= 0.0:
        return sorted_values[0]
    if probability >= 1.0:
        return sorted_values[-1]
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    fraction = position - lower
    return sorted_values[lower] * (1.0 - fraction) + sorted_values[upper] * fraction


def bootstrap_ci(
    values: Iterable[float | None],
    *,
    statistic: Callable[[Sequence[float]], float] = statistics.fmean,
    confidence: float = 0.95,
    n_resamples: int = 2_000,
    seed: int = 20261103,
) -> tuple[float | None, float | None]:
    """Seeded percentile bootstrap interval over per-question values."""

    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not clean:
        return None, None
    if len(clean) == 1:
        return clean[0], clean[0]
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if n_resamples < 1:
        raise ValueError("n_resamples must be positive")
    rng = random.Random(seed)
    size = len(clean)
    samples: list[float] = []
    for _ in range(n_resamples):
        resample = [clean[rng.randrange(size)] for _ in range(size)]
        samples.append(float(statistic(resample)))
    samples.sort()
    alpha = (1.0 - confidence) / 2.0
    return _quantile(samples, alpha), _quantile(samples, 1.0 - alpha)


def paired_bootstrap_diff_ci(
    pairs: Iterable[tuple[float | None, float | None]],
    *,
    confidence: float = 0.95,
    n_resamples: int = 2_000,
    seed: int = 20261103,
) -> tuple[float | None, float | None]:
    """Bootstrap the mean per-question difference of paired results.

    The first value in each pair is treated as the comparison/baseline score.
    """

    clean = [
        (float(first), float(second))
        for first, second in pairs
        if first is not None
        and second is not None
        and math.isfinite(float(first))
        and math.isfinite(float(second))
    ]
    if not clean:
        return None, None
    differences = [second - first for first, second in clean]
    return bootstrap_ci(
        differences,
        statistic=statistics.fmean,
        confidence=confidence,
        n_resamples=n_resamples,
        seed=seed,
    )


def nearest_rank_percentile(values: Iterable[float | None], percentile: float) -> float | None:
    """Nearest-rank percentile (the definition used for p50/p95 latency)."""

    clean = sorted(
        float(value) for value in values if value is not None and math.isfinite(float(value))
    )
    if not clean:
        return None
    if not 0.0 <= percentile <= 100.0:
        raise ValueError("percentile must be between 0 and 100")
    if percentile <= 0.0:
        return clean[0]
    if percentile >= 100.0:
        return clean[-1]
    rank = max(1, math.ceil((percentile / 100.0) * len(clean)))
    return clean[rank - 1]


# ---------------------------------------------------------------------------
# Per-question metrics
# ---------------------------------------------------------------------------


def source_key(source: GoldSource | Citation) -> tuple[str, str, str]:
    """Stable retrieval key: document + version + block."""

    return (source.doc_id, source.version, source.block_id)


def _unique_keys(sources: Iterable[GoldSource | Citation]) -> list[tuple[str, str, str]]:
    seen: set[tuple[str, str, str]] = set()
    keys: list[tuple[str, str, str]] = []
    for source in sources:
        key = source_key(source)
        if key not in seen:
            seen.add(key)
            keys.append(key)
    return keys


def _gold_keys(question: Question) -> set[tuple[str, str, str]]:
    return {source_key(source) for source in question.gold_sources}


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def token_f1(prediction: str, reference: str) -> float:
    """Lexical token F1 between an answer and the gold answer.

    This is a deterministic, judge-free signal. It is not a semantic
    correctness metric; the optional Ragas judge remains the semantic check.
    """
    pred_tokens = _TOKEN_RE.findall(prediction.lower())
    ref_tokens = _TOKEN_RE.findall(reference.lower())
    if not pred_tokens or not ref_tokens:
        return 0.0
    overlap = sum((Counter(pred_tokens) & Counter(ref_tokens)).values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(pred_tokens)
    recall = overlap / len(ref_tokens)
    return 2.0 * precision * recall / (precision + recall)


def page_matches(citation: Citation, gold: GoldSource) -> bool:
    """True when a citation points at a gold document/version/page.

    When either side has no page (for example HTML docs), fall back to the
    stable block ID instead of guessing a page.
    """

    if citation.doc_id != gold.doc_id or citation.version != gold.version:
        return False
    if citation.page is None or gold.page is None:
        return citation.block_id == gold.block_id
    return citation.page == gold.page


def recall_at_k(question: Question, result: Result, k: int) -> float | None:
    """Macro-style per-question retrieval recall over gold blocks."""

    gold = _gold_keys(question)
    if not gold:
        return None
    retrieved = set(_unique_keys(result.retrieved)[:k])
    return len(gold & retrieved) / len(gold)


def all_gold_at_k(question: Question, result: Result, k: int) -> float | None:
    gold = _gold_keys(question)
    if not gold:
        return None
    retrieved = set(_unique_keys(result.retrieved)[:k])
    return 1.0 if gold <= retrieved else 0.0


def context_precision_at_k(question: Question, result: Result, k: int = 10) -> float | None:
    """Rank-weighted context precision over the retrieved block IDs.

    ``CP@K = sum(P@k * v_k) / sum(v_k)`` where ``v_k`` marks a relevant chunk.
    No relevant retrieved chunk scores 0.0; an unanswerable question is None.
    """

    gold = _gold_keys(question)
    if not gold:
        return None
    retrieved = _unique_keys(result.retrieved)[:k]
    relevant = [1 if key in gold else 0 for key in retrieved]
    if not any(relevant):
        return 0.0
    hits = 0
    weighted_sum = 0.0
    for rank, is_relevant in enumerate(relevant, start=1):
        hits += is_relevant
        if is_relevant:
            weighted_sum += hits / rank
    return weighted_sum / hits


def context_recall_at_k(question: Question, result: Result, k: int = 10) -> float | None:
    """ID-based context recall (deterministic Ragas-compatible variant).

    This is intentionally not claim-level entailment. The optional Ragas judge
    adds semantic context recall when explicitly enabled.
    """

    return recall_at_k(question, result, k)


def citation_page_accuracy(question: Question, result: Result) -> float | None:
    """Fraction of returned citations that resolve to a gold page.

    ``None`` for unanswerable questions and for answers with no citations.
    Citation coverage is reported separately so abstention cannot hide here.
    """

    if not question.answerable:
        return None
    if result.abstained or not result.citations:
        return None
    hits = sum(
        1
        for citation in result.citations
        if any(page_matches(citation, gold) for gold in question.gold_sources)
    )
    return hits / len(result.citations)


def citation_coverage(question: Question, result: Result) -> float | None:
    if not question.answerable:
        return None
    return 0.0 if result.abstained or not result.citations else 1.0


def stale_answer(question: Question, result: Result) -> float | None:
    """1.0 when the primary citation is not the question's target version.

    Only meaningful for ``version_specific`` questions. Abstentions and
    citation-less answers are excluded (``None``), not silently counted as
    fresh.
    """

    if question.category != "version_specific" or not question.target_version:
        return None
    if result.abstained or not result.citations:
        return None
    return 1.0 if result.citations[0].version != question.target_version else 0.0


def stale_citation(question: Question, result: Result) -> float | None:
    if question.category != "version_specific" or not question.target_version:
        return None
    if result.abstained or not result.citations:
        return None
    stale = sum(1 for citation in result.citations if citation.version != question.target_version)
    return stale / len(result.citations)


def disambiguation(question: Question, result: Result) -> float | None:
    """1.0 when a conflicting-version answer names/cites every gold version."""

    if question.category != "conflicting":
        return None
    if result.abstained:
        return 0.0
    expected_versions = {source.version for source in question.gold_sources}
    cited_versions = {citation.version for citation in result.citations}
    if expected_versions <= cited_versions:
        return 1.0
    answer = result.answer.lower()
    if expected_versions and all(version.lower() in answer for version in expected_versions):
        return 1.0
    return 0.0


def abstention_correct(question: Question, result: Result) -> float:
    """One balanced decision per question: abstain iff unanswerable."""

    if question.answerable:
        return 0.0 if result.abstained else 1.0
    return 1.0 if result.abstained else 0.0


def false_abstention(question: Question, result: Result) -> float | None:
    if not question.answerable:
        return None
    return 1.0 if result.abstained else 0.0


def missed_abstention(question: Question, result: Result) -> float | None:
    if question.answerable:
        return None
    return 0.0 if result.abstained else 1.0


def compute_question_metrics(question: Question, result: Result) -> dict[str, float | None]:
    """All deterministic per-question metrics. Undefined metrics are ``None``."""

    if result.error:
        return {spec.key: None for spec in METRIC_SPECS}
    return {
        "recall_at_5": recall_at_k(question, result, 5),
        "recall_at_10": recall_at_k(question, result, 10),
        "all_gold_at_10": all_gold_at_k(question, result, 10),
        "context_precision_at_10": context_precision_at_k(question, result, 10),
        "context_recall_at_10": context_recall_at_k(question, result, 10),
        "factual_f1": (
            None
            if not question.answerable
            else (0.0 if result.abstained else token_f1(result.answer, question.gold_answer))
        ),
        "citation_page_accuracy": citation_page_accuracy(question, result),
        "citation_coverage": citation_coverage(question, result),
        "stale_answer": stale_answer(question, result),
        "stale_citation": stale_citation(question, result),
        "disambiguation": disambiguation(question, result),
        "abstention_correct": abstention_correct(question, result),
        "false_abstention": false_abstention(question, result),
        "missed_abstention": missed_abstention(question, result),
    }


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _clean_values(values: Iterable[float | None]) -> list[float]:
    return [
        float(value)
        for value in values
        if value is not None and math.isfinite(float(value))
    ]


def _row(
    *,
    pipeline: str,
    category: str,
    spec: MetricSpec,
    values: Sequence[float],
    confidence: float,
    bootstrap_samples: int,
    seed: int,
    unit: str | None = None,
    statistic: Callable[[Sequence[float]], float] = statistics.fmean,
) -> MetricRow:
    value = float(statistic(values))
    if spec.kind == "rate":
        successes = round(sum(values))
        low, high = wilson_interval(successes, len(values), confidence)
        method = "wilson"
    else:
        low, high = bootstrap_ci(
            values,
            statistic=statistic,
            confidence=confidence,
            n_resamples=bootstrap_samples,
            seed=seed,
        )
        method = "bootstrap"
    if unit != "ms":
        low = None if low is None else max(0.0, min(1.0, low))
        high = None if high is None else max(0.0, min(1.0, high))
    return MetricRow(
        pipeline=pipeline,
        category=category,
        metric=spec.key,
        label=spec.label,
        value=value,
        n=len(values),
        ci_low=low,
        ci_high=high,
        ci_method=method,
        higher_is_better=spec.higher_is_better,
        unit=unit,
    )


def aggregate_metric_rows(
    questions: Sequence[Question],
    results_by_pipeline: Mapping[str, Sequence[Result]],
    *,
    confidence: float = 0.95,
    bootstrap_samples: int = 2_000,
    seed: int = 20261103,
) -> list[MetricRow]:
    """Build overall and per-category rows for every pipeline."""

    by_question = {question.question_id: question for question in questions}
    rows: list[MetricRow] = []
    categories: list[str] = ["overall", *CATEGORIES]

    for pipeline in sorted(results_by_pipeline):
        results = {result.question_id: result for result in results_by_pipeline[pipeline]}
        for category in categories:
            pairs = [
                (by_question[question_id], result)
                for question_id, result in results.items()
                if question_id in by_question
                and (category == "overall" or by_question[question_id].category == category)
            ]
            pairs.sort(key=lambda pair: pair[0].question_id)
            if not pairs:
                continue

            for spec in METRIC_SPECS:
                values = _clean_values(result.metrics.get(spec.key) for _question, result in pairs)
                if not values:
                    continue
                rows.append(
                    _row(
                        pipeline=pipeline,
                        category=category,
                        spec=spec,
                        values=values,
                        confidence=confidence,
                        bootstrap_samples=bootstrap_samples,
                        seed=seed,
                    )
                )

            for spec in JUDGE_SPECS:
                judge_values = _clean_values(
                    getattr(result.judge, spec.key, None) if result.judge else None
                    for _question, result in pairs
                )
                if judge_values:
                    rows.append(
                        _row(
                            pipeline=pipeline,
                            category=category,
                            spec=spec,
                            values=judge_values,
                            confidence=confidence,
                            bootstrap_samples=bootstrap_samples,
                            seed=seed,
                        )
                    )

            latencies = _clean_values(
                result.latency_ms for _question, result in pairs if not result.error
            )
            if latencies:
                for percentile, label in ((50, "Latency p50"), (95, "Latency p95")):
                    spec = MetricSpec(
                        key=f"latency_p{percentile}",
                        label=f"{label} (ms)",
                        kind="continuous",
                        higher_is_better=False,
                    )
                    low, high = bootstrap_ci(
                        latencies,
                        statistic=lambda sample, p=percentile: nearest_rank_percentile(sample, p)
                        or 0.0,
                        confidence=confidence,
                        n_resamples=bootstrap_samples,
                        seed=seed,
                    )
                    rows.append(
                        MetricRow(
                            pipeline=pipeline,
                            category=category,
                            metric=spec.key,
                            label=spec.label,
                            value=nearest_rank_percentile(latencies, percentile),
                            n=len(latencies),
                            ci_low=low,
                            ci_high=high,
                            ci_method="bootstrap",
                            higher_is_better=False,
                            unit="ms",
                        )
                    )
    return rows


def paired_metric_comparisons(
    questions: Sequence[Question],
    results_by_pipeline: Mapping[str, Sequence[Result]],
    *,
    confidence: float = 0.95,
    bootstrap_samples: int = 2_000,
    seed: int = 20261103,
) -> list[PairedComparison]:
    """Paired baseline-vs-fixed deltas with bootstrap confidence intervals."""
    if "baseline" not in results_by_pipeline or "fixed" not in results_by_pipeline:
        return []
    baseline = {result.question_id: result for result in results_by_pipeline["baseline"]}
    fixed = {result.question_id: result for result in results_by_pipeline["fixed"]}

    comparisons: list[PairedComparison] = []
    for spec in METRIC_SPECS:
        pairs: list[tuple[float, float]] = []
        for question in questions:
            base_result = baseline.get(question.question_id)
            fixed_result = fixed.get(question.question_id)
            if base_result is None or fixed_result is None:
                continue
            base_value = base_result.metrics.get(spec.key)
            fixed_value = fixed_result.metrics.get(spec.key)
            if base_value is None or fixed_value is None:
                continue
            pairs.append((float(base_value), float(fixed_value)))
        if not pairs:
            continue
        low, high = paired_bootstrap_diff_ci(
            pairs,
            confidence=confidence,
            n_resamples=bootstrap_samples,
            seed=seed,
        )
        deltas = [fixed_value - base_value for base_value, fixed_value in pairs]
        comparisons.append(
            PairedComparison(
                metric=spec.key,
                label=spec.label,
                baseline_mean=statistics.fmean(base for base, _fixed in pairs),
                fixed_mean=statistics.fmean(fixed for _base, fixed in pairs),
                delta=statistics.fmean(deltas),
                ci_low=low,
                ci_high=high,
                n=len(pairs),
                higher_is_better=spec.higher_is_better,
            )
        )
    return comparisons


def rows_by_pipeline(rows: Sequence[MetricRow]) -> dict[str, list[MetricRow]]:
    grouped: dict[str, list[MetricRow]] = {}
    for row in rows:
        grouped.setdefault(row.pipeline, []).append(row)
    return grouped
