"""Run a pipeline adapter over the question set and persist reports.

Pipeline calls are dependency-injected: tests pass a Python callable, while the
CLI wraps ``pipeline_command`` in :class:`CommandPipeline`. The command receives
one question as JSON on stdin and must emit one result as JSON on stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import yaml
from pydantic import BaseModel, ConfigDict, Field

from evals.dataset import (
    DEFAULT_SEED,
    DatasetError,
    generate_questions,
    load_manifest,
    load_questions,
    save_questions,
    validate_quotas,
)
from evals.judge import ENV_FLAG, JudgeUnavailable, judge_enabled, score_with_ragas
from evals.metrics import compute_question_metrics
from evals.report import build_report, write_report
from evals.schema import Question, Report, Result

DEFAULT_CONFIG_PATH = Path("evals/config.yaml")


class PipelineError(RuntimeError):
    """Raised when a command pipeline fails or returns malformed output."""


@runtime_checkable
class Pipeline(Protocol):
    def __call__(self, question: Question) -> Result: ...


class JudgeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled_env: str = ENV_FLAG
    model: str | None = None


class EvalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_path: Path = Path("evals/data/questions.json")
    corpus_manifest: Path | None = Path("data/manifests/corpus.json")
    generate_if_missing: bool = True
    dataset_seed: int = DEFAULT_SEED
    split: str = "all"

    pipeline_name: str = "fixed"
    pipeline_command: str = ""
    pipeline_timeout_s: float = Field(default=120.0, gt=0)

    output_dir: Path = Path("evals/reports")
    output_json: str = "eval-report.json"
    output_markdown: str = "eval-report.md"

    bootstrap_samples: int = Field(default=2_000, ge=1)
    confidence: float = Field(default=0.95, gt=0.0, lt=1.0)
    judge: JudgeConfig = Field(default_factory=JudgeConfig)


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> EvalConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"evaluation config not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise TypeError(f"evaluation config must be a mapping: {config_path}")
    return EvalConfig.model_validate(data)


def _parse_json_output(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        raise PipelineError("pipeline produced no stdout")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None
        for line in reversed(text.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    if not isinstance(payload, dict):
        raise PipelineError("pipeline stdout is not a JSON object")
    return payload


class CommandPipeline:
    """Adapter for a JSON-in/JSON-out pipeline command."""

    def __init__(
        self,
        name: str,
        command: str,
        *,
        timeout_s: float = 120.0,
        env: Mapping[str, str] | None = None,
    ) -> None:
        if not name:
            raise ValueError("pipeline name is required")
        self.name = name
        self.command = command
        self.argv = shlex.split(command)
        if not self.argv:
            raise ValueError("pipeline command is empty")
        self.timeout_s = timeout_s
        self.env = None if env is None else {**os.environ, **env}

    def __call__(self, question: Question) -> Result:
        start = time.perf_counter()
        completed = subprocess.run(
            self.argv,
            input=json.dumps(question.model_dump(mode="json", exclude_none=True)),
            text=True,
            capture_output=True,
            timeout=self.timeout_s,
            env=self.env,
            check=False,
        )
        measured_ms = (time.perf_counter() - start) * 1000.0
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip().splitlines()
            tail = stderr[-1] if stderr else "no stderr"
            raise PipelineError(
                f"pipeline exited with {completed.returncode}: {tail[:300]}"
            )
        payload = _parse_json_output(completed.stdout)
        payload.setdefault("question_id", question.question_id)
        payload.setdefault("pipeline", self.name)
        if "citations" not in payload and payload.get("claims"):
            payload["citations"] = [
                citation
                for claim in payload.get("claims", [])
                for citation in claim.get("citations", [])
            ]
        # Result models citations directly; the API's claim envelope is an
        # adapter detail, not part of the eval schema.
        payload.pop("claims", None)
        if not payload.get("latency_ms"):
            payload["latency_ms"] = measured_ms
        return Result.model_validate(payload)


def _coerce_result(
    question: Question,
    pipeline_name: str,
    output: Result | Mapping[str, Any] | Any,
    measured_ms: float,
) -> Result:
    if isinstance(output, Result):
        result = output
    elif isinstance(output, Mapping):
        payload = dict(output)
        payload.setdefault("question_id", question.question_id)
        payload.setdefault("pipeline", pipeline_name)
        result = Result.model_validate(payload)
    else:
        raise TypeError(
            f"pipeline {pipeline_name!r} returned {type(output).__name__}, expected Result or mapping"
        )
    latency = result.latency_ms if result.latency_ms and result.latency_ms > 0 else measured_ms
    return result.model_copy(
        update={
            "question_id": question.question_id,
            "pipeline": pipeline_name,
            "latency_ms": latency,
        }
    )


def _apply_judge(
    questions: Sequence[Question],
    results_by_pipeline: dict[str, list[Result]],
    *,
    model: str | None,
) -> tuple[list[str], str | None]:
    try:
        judged = score_with_ragas(questions, results_by_pipeline, model=model)
    except JudgeUnavailable as exc:
        return [f"LLM judge was requested but is unavailable: {exc}"], str(exc)
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - provider/network dependent
        message = f"{type(exc).__name__}: {exc}"
        return [f"LLM judge failed and was skipped: {message}"], message

    for pipeline, scores_by_question in judged.items():
        for index, result in enumerate(results_by_pipeline.get(pipeline, [])):
            scores = scores_by_question.get(result.question_id)
            if scores is not None:
                results_by_pipeline[pipeline][index] = result.model_copy(update={"judge": scores})
    return [], None


def run_evaluation(
    questions: Sequence[Question],
    pipelines: Mapping[str, Pipeline],
    *,
    dataset_path: str = "",
    confidence: float = 0.95,
    bootstrap_samples: int = 2_000,
    seed: int = DEFAULT_SEED,
    judge: bool = False,
    judge_model: str | None = None,
    extra_caveats: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> Report:
    """Run every pipeline over every question and return a report.

    Exceptions raised by a pipeline become per-question errors, not a crashed
    evaluation, so one bad answer still produces an auditable report.
    """

    if not questions:
        raise ValueError("no questions to evaluate")
    if not pipelines:
        raise ValueError("at least one pipeline is required")

    results_by_pipeline: dict[str, list[Result]] = {}
    run_metadata: dict[str, Any] = dict(metadata or {})
    for pipeline_name in sorted(pipelines):
        pipeline = pipelines[pipeline_name]
        results: list[Result] = []
        for question in questions:
            start = time.perf_counter()
            try:
                output = pipeline(question)
            except Exception as exc:  # noqa: BLE001 - a bad answer must not stop the run
                measured_ms = (time.perf_counter() - start) * 1000.0
                result = Result(
                    question_id=question.question_id,
                    pipeline=pipeline_name,
                    answer="",
                    abstained=True,
                    latency_ms=measured_ms,
                    error=f"{type(exc).__name__}: {exc}",
                )
            else:
                measured_ms = (time.perf_counter() - start) * 1000.0
                result = _coerce_result(question, pipeline_name, output, measured_ms)
            result = result.model_copy(
                update={"metrics": compute_question_metrics(question, result)}
            )
            results.append(result)
        results_by_pipeline[pipeline_name] = results

    caveats = list(extra_caveats or [])
    if judge:
        judge_caveats, judge_error = _apply_judge(
            questions,
            results_by_pipeline,
            model=judge_model,
        )
        caveats.extend(judge_caveats)
        run_metadata["judge_error"] = judge_error

    return build_report(
        questions,
        results_by_pipeline,
        dataset_path=dataset_path,
        confidence=confidence,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
        extra_caveats=caveats,
        metadata=run_metadata,
    )


def _prepare_questions(args: argparse.Namespace, config: EvalConfig) -> tuple[list[Question], Path]:
    dataset_path = Path(args.dataset or config.dataset_path)
    corpus_path = Path(args.corpus_manifest or config.corpus_manifest) if (
        args.corpus_manifest or config.corpus_manifest
    ) else None
    regenerate = bool(args.regenerate)
    if regenerate or not dataset_path.exists():
        if corpus_path is None or not corpus_path.exists():
            raise FileNotFoundError(
                f"dataset {dataset_path} is missing and corpus manifest "
                f"{corpus_path or '(not configured)'} is unavailable; generate the corpus first "
                "or pass --dataset"
            )
        manifest = load_manifest(corpus_path)
        dataset_seed = args.seed if args.seed is not None else config.dataset_seed
        questions = generate_questions(manifest, seed=dataset_seed)
        validate_quotas(questions)
        save_questions(questions, dataset_path)
        print(f"generated {len(questions)} questions from {corpus_path} -> {dataset_path}")
    else:
        questions = load_questions(dataset_path)

    split = args.split or config.split
    if split != "all":
        questions = [question for question in questions if question.split == split]
    if args.limit is not None:
        questions = questions[: args.limit]
    if not questions:
        raise DatasetError(f"no questions selected from {dataset_path} (split={split})")
    return questions, dataset_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Forge RAG evaluation harness.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--corpus-manifest", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--pipeline-command", default=None)
    parser.add_argument("--pipeline-name", default=None)
    parser.add_argument("--split", choices=("all", "dev", "test", "shadow"), default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--regenerate", action="store_true")
    parser.add_argument("--judge", action="store_true", help="enable the optional Ragas judge")
    parser.add_argument("--no-judge", action="store_true", help="force the judge off")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    questions, dataset_path = _prepare_questions(args, config)

    pipeline_name = args.pipeline_name or config.pipeline_name
    command = args.pipeline_command or config.pipeline_command
    if not command:
        raise ValueError(
            "no pipeline command configured; set pipeline_command in evals/config.yaml "
            "or pass --pipeline-command"
        )
    pipeline = CommandPipeline(
        pipeline_name,
        command,
        timeout_s=config.pipeline_timeout_s,
    )

    use_judge = not args.no_judge and (args.judge or judge_enabled(config.judge.enabled_env))
    report = run_evaluation(
        questions,
        {pipeline_name: pipeline},
        dataset_path=str(dataset_path),
        confidence=config.confidence,
        bootstrap_samples=config.bootstrap_samples,
        seed=args.seed if args.seed is not None else config.dataset_seed,
        judge=use_judge,
        judge_model=config.judge.model,
        metadata={"config": args.config, "split": args.split or config.split},
    )

    output_dir = Path(args.output_dir or config.output_dir)
    json_path, markdown_path = write_report(
        report,
        output_dir,
        json_name=config.output_json,
        markdown_name=config.output_markdown,
    )
    print(
        f"evaluated {report.n_questions} questions with {', '.join(report.pipelines)} "
        f"({len(report.failures)} failures)"
    )
    print(f"wrote {json_path}")
    print(f"wrote {markdown_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
