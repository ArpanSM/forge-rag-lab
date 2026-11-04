"""Run the evaluation harness against the live RAG service in one process.

The default harness invokes ``python -m rag.pipeline`` once per question, which
reloads the corpus, embeddings and reranker every time. This script builds the
service once and runs both pipelines over the same question set, which is much
faster for a local evaluation run.

Usage:
    python scripts/run_eval_local.py --limit 10
    python scripts/run_eval_local.py --split test --pipeline both
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evals.dataset import load_questions
from evals.report import write_report
from evals.runner import run_evaluation
from rag.pipeline import run_question
from rag.service import build_service_from_env


class ProgressPipeline:
    def __init__(self, service, pipeline: str, total: int) -> None:
        self.service = service
        self.pipeline = pipeline
        self.total = total
        self.count = 0

    def __call__(self, question):
        self.count += 1
        print(
            f"[{self.count}/{self.total}] {self.pipeline} {question.question_id} "
            f"{question.category}",
            flush=True,
        )
        started = time.perf_counter()
        result = run_question(question.model_dump(mode="json"), self.service, self.pipeline)
        elapsed = time.perf_counter() - started
        print(
            f"  {elapsed:.1f}s abstained={result['abstained']} "
            f"citations={len(result['citations'])}",
            flush=True,
        )
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="evals/data/questions.json")
    parser.add_argument("--split", choices=("all", "dev", "test", "shadow"), default="all")
    parser.add_argument(
        "--category",
        choices=("single_hop", "multi_hop", "version_specific", "conflicting", "unanswerable"),
        default=None,
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--pipeline", choices=("both", "fixed", "baseline"), default="both")
    parser.add_argument("--output-dir", default="evals/reports")
    parser.add_argument("--json-name", default="eval-report.json")
    parser.add_argument("--markdown-name", default="eval-report.md")
    args = parser.parse_args()

    questions = load_questions(args.dataset)
    if args.split != "all":
        questions = [question for question in questions if question.split == args.split]
    if args.category:
        questions = [question for question in questions if question.category == args.category]
    if args.limit:
        questions = questions[: args.limit]
    if not questions:
        raise SystemExit("no questions selected")

    print(f"loading service for {len(questions)} questions...", flush=True)
    service = build_service_from_env()
    print(
        f"service ready: provider={service.provider_name} embedder={service.embedder.name} "
        f"blocks={service.indexed_blocks}",
        flush=True,
    )

    pipelines = {}
    if args.pipeline in {"both", "fixed"}:
        pipelines["fixed"] = ProgressPipeline(service, "fixed", len(questions))
    if args.pipeline in {"both", "baseline"}:
        pipelines["baseline"] = ProgressPipeline(service, "baseline", len(questions))

    report = run_evaluation(
        questions,
        pipelines,
        dataset_path=args.dataset,
        extra_caveats=[
            f"Live evaluation with provider={service.provider_name}; results are model- and date-specific.",
            f"Embedding model: {service.embedder.name}; reranker: {service.fixed_retriever.reranker.name}.",
        ],
        metadata={
            "provider": service.provider_name,
            "embedder": service.embedder.name,
            "reranker": service.fixed_retriever.reranker.name,
            "question_count": len(questions),
        },
    )
    json_path, markdown_path = write_report(
        report,
        args.output_dir,
        json_name=args.json_name,
        markdown_name=args.markdown_name,
    )
    print(f"wrote {json_path} and {markdown_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
