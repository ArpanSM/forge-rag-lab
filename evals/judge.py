"""Optional Ragas 0.4.x judge metrics.

Core evaluation never imports Ragas. Set ``EVAL_ENABLE_LLM_JUDGE=1`` to opt in,
configure a Ragas-compatible judge/provider, and expect network/model cost.
No API key is needed for the deterministic harness or its tests.
"""

from __future__ import annotations

import math
import os
from collections.abc import Mapping, Sequence
from typing import Any

from evals.schema import JudgeScores, Question, Result

ENV_FLAG = "EVAL_ENABLE_LLM_JUDGE"


class JudgeUnavailable(RuntimeError):
    """Raised when the optional judge is requested but cannot run."""


def judge_enabled(flag: str = ENV_FLAG) -> bool:
    return os.getenv(flag, "").strip().lower() in {"1", "true", "yes", "on"}


def _finite_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def score_with_ragas(
    questions: Sequence[Question],
    results_by_pipeline: Mapping[str, Sequence[Result]],
    *,
    model: str | None = None,
    llm: Any | None = None,
) -> dict[str, dict[str, JudgeScores]]:
    """Score answer correctness and faithfulness with Ragas.

    Returns ``{pipeline: {question_id: JudgeScores}}``. Ragas is imported lazily
    so the deterministic harness and tests have no LLM dependency.
    """

    try:
        from ragas import EvaluationDataset, SingleTurnSample, evaluate
        from ragas.metrics import AnswerCorrectness, Faithfulness
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise JudgeUnavailable(
            "Ragas is not installed. Install the optional judge extras before "
            f"setting {ENV_FLAG}=1."
        ) from exc

    by_question = {question.question_id: question for question in questions}
    scores: dict[str, dict[str, JudgeScores]] = {}
    for pipeline in sorted(results_by_pipeline):
        samples = []
        ids: list[str] = []
        for result in results_by_pipeline[pipeline]:
            question = by_question.get(result.question_id)
            if question is None or not question.answerable or result.abstained:
                continue
            contexts = [chunk.text for chunk in result.retrieved if chunk.text]
            if not contexts:
                contexts = [citation.quote for citation in result.citations if citation.quote]
            if not contexts:
                continue
            samples.append(
                SingleTurnSample(
                    user_input=question.question,
                    retrieved_contexts=contexts,
                    response=result.answer,
                    reference=question.gold_answer,
                )
            )
            ids.append(result.question_id)
        if not samples:
            continue
        metrics = [AnswerCorrectness(weights=[1.0, 0.0]), Faithfulness()]
        dataset = EvaluationDataset(samples=samples)
        evaluation = evaluate(
            dataset,
            metrics=metrics,
            llm=llm,
            show_progress=False,
            raise_exceptions=False,
        )
        raw_scores = getattr(evaluation, "scores", []) or []
        pipeline_scores: dict[str, JudgeScores] = {}
        for question_id, row in zip(ids, raw_scores):
            if not isinstance(row, dict):
                continue
            pipeline_scores[question_id] = JudgeScores(
                answer_correctness=_finite_or_none(row.get("answer_correctness")),
                faithfulness=_finite_or_none(row.get("faithfulness")),
                model=model or "ragas-default",
            )
        scores[pipeline] = pipeline_scores
    return scores
