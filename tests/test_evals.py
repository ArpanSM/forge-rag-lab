from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from evals.dataset import (
    generate_questions,
    load_manifest,
    load_questions,
    validate_quotas,
)
from evals.judge import judge_enabled
from evals.metrics import (
    all_gold_at_k,
    bootstrap_ci,
    citation_coverage,
    citation_page_accuracy,
    compute_question_metrics,
    context_precision_at_k,
    nearest_rank_percentile,
    recall_at_k,
    stale_answer,
    wilson_interval,
)
from evals.report import write_report
from evals.runner import CommandPipeline, load_config, run_evaluation
from evals.schema import Citation, GoldSource, Question, Report, Result, RetrievedChunk

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evals" / "fixtures"
SMALL_QUESTIONS = FIXTURES / "questions_small.json"
SMOKE_MANIFEST = FIXTURES / "corpus_smoke.json"
FULL_DATASET = ROOT / "evals" / "data" / "questions.json"


def _gold(doc_id: str = "helios-api-keys", version: str = "v3", block_id: str = "b1", page: int = 1) -> GoldSource:
    return GoldSource(
        doc_id=doc_id,
        version=version,
        block_id=block_id,
        page=page,
        anchor=f"#{block_id}",
        title="API keys",
        quote="A gold quote.",
    )


def _citation(doc_id: str = "helios-api-keys", version: str = "v3", block_id: str = "b1", page: int = 1) -> Citation:
    return Citation(
        doc_id=doc_id,
        version=version,
        block_id=block_id,
        page=page,
        anchor=f"#{block_id}",
        title="API keys",
        quote="A cited quote.",
    )


def _retrieved(source: GoldSource) -> RetrievedChunk:
    data = source.model_dump()
    data.update({"rank": 1, "text": f"Retrieved text for {source.block_id}", "score": 0.9})
    return RetrievedChunk.model_validate(data)


def _question(
    *,
    question_id: str = "q001",
    category: str = "single_hop",
    gold_sources: list[GoldSource] | None = None,
    answerable: bool = True,
    target_version: str | None = None,
    superseded_versions: list[str] | None = None,
) -> Question:
    sources = gold_sources if gold_sources is not None else [_gold()]
    return Question(
        question_id=question_id,
        tenant_id="northwind",
        question="How do I rotate an API key?",
        category=category,
        answerable=answerable,
        gold_answer="Gold answer.",
        gold_sources=sources,
        target_version=target_version,
        superseded_versions=superseded_versions or [],
    )


def _result(
    question_id: str = "q001",
    *,
    retrieved: list[RetrievedChunk] | None = None,
    citations: list[Citation] | None = None,
    abstained: bool = False,
    latency_ms: float = 100.0,
) -> Result:
    return Result(
        question_id=question_id,
        pipeline="fixed",
        answer="Answer.",
        abstained=abstained,
        retrieved=retrieved or [],
        citations=citations or [],
        latency_ms=latency_ms,
    )


# ---------------------------------------------------------------------------
# Dataset and schema
# ---------------------------------------------------------------------------


def test_committed_dataset_has_80_questions_and_quotas() -> None:
    questions = load_questions(FULL_DATASET)
    assert len(questions) == 80
    validate_quotas(questions)
    assert Counter(q.category for q in questions) == {
        "single_hop": 24,
        "multi_hop": 16,
        "version_specific": 16,
        "conflicting": 8,
        "unanswerable": 16,
    }
    assert Counter(q.split for q in questions) == {"dev": 40, "test": 40}
    assert len({q.question_id for q in questions}) == 80
    assert len({q.question for q in questions}) == 80


def test_generator_is_deterministic_and_hits_quotas() -> None:
    manifest = load_manifest(SMOKE_MANIFEST)
    first = generate_questions(manifest, seed=7)
    second = generate_questions(manifest, seed=7)
    validate_quotas(first)
    assert [q.model_dump() for q in first] == [q.model_dump() for q in second]
    assert Counter(q.split for q in first) == {"dev": 40, "test": 40}
    assert {q.tenant_id for q in first} == {"northwind", "acme"}
    cross_tenant = [
        q
        for q in first
        if q.category == "unanswerable" and "private" in q.question.lower()
    ]
    assert len(cross_tenant) >= 1


def test_small_fixture_loads() -> None:
    questions = load_questions(SMALL_QUESTIONS)
    assert len(questions) == 7
    assert {q.category for q in questions} == {
        "single_hop",
        "multi_hop",
        "version_specific",
        "conflicting",
        "unanswerable",
    }


def test_question_schema_rejects_unanswerable_with_gold() -> None:
    with pytest.raises(ValidationError):
        Question(
            question_id="bad",
            tenant_id="northwind",
            question="?",
            category="unanswerable",
            answerable=False,
            gold_answer="",
            gold_sources=[_gold()],
        )


# ---------------------------------------------------------------------------
# Deterministic metrics
# ---------------------------------------------------------------------------


def test_recall_all_gold_and_rank_weighted_context_precision() -> None:
    first = _gold("doc-a", "v3", "b1", 1)
    second = _gold("doc-b", "v3", "b2", 2)
    question = _question(gold_sources=[first, second])
    irrelevant = _citation("doc-c", "v3", "b9", 9)

    perfect = _result(
        retrieved=[
            _retrieved(first),
            RetrievedChunk.model_validate({**irrelevant.model_dump(), "rank": 2}),
            _retrieved(second),
        ]
    )
    assert recall_at_k(question, perfect, 5) == 1.0
    assert all_gold_at_k(question, perfect, 10) == 1.0
    assert context_precision_at_k(question, perfect, 10) == pytest.approx((1.0 + 2.0 / 3.0) / 2.0)

    partial = _result(
        retrieved=[
            _retrieved(first),
            RetrievedChunk.model_validate({**irrelevant.model_dump(), "rank": 2}),
        ]
    )
    assert recall_at_k(question, partial, 10) == 0.5
    assert all_gold_at_k(question, partial, 10) == 0.0
    assert context_precision_at_k(question, partial, 10) == 1.0
    assert recall_at_k(question, _result(retrieved=[_retrieved(first)]), 10) == 0.5


def test_citation_page_stale_and_abstention_metrics() -> None:
    gold = _gold("helios-api-keys", "v3", "b1", 2)
    question = _question(
        category="version_specific",
        gold_sources=[gold],
        target_version="v3",
        superseded_versions=["v1", "v2"],
    )
    stale = _result(retrieved=[_retrieved(gold)], citations=[_citation(version="v2", page=2)])
    assert citation_page_accuracy(question, stale) == 0.0
    assert citation_coverage(question, stale) == 1.0
    assert stale_answer(question, stale) == 1.0
    assert compute_question_metrics(question, stale)["stale_citation"] == 1.0

    fresh = _result(retrieved=[_retrieved(gold)], citations=[_citation(version="v3", page=2)])
    assert citation_page_accuracy(question, fresh) == 1.0
    assert stale_answer(question, fresh) == 0.0

    uncited = _result(retrieved=[_retrieved(gold)])
    assert citation_page_accuracy(question, uncited) is None
    assert citation_coverage(question, uncited) == 0.0
    assert stale_answer(question, uncited) is None

    unanswerable = _question(
        question_id="q099",
        category="unanswerable",
        gold_sources=[],
        answerable=False,
    )
    assert compute_question_metrics(unanswerable, _result())["abstention_correct"] == 0.0
    assert compute_question_metrics(unanswerable, _result(abstained=True))["missed_abstention"] == 0.0
    answerable = _question()
    assert compute_question_metrics(answerable, _result(abstained=True))["false_abstention"] == 1.0


def test_latency_percentiles_use_nearest_rank() -> None:
    assert nearest_rank_percentile([10, 20, 30, 40], 50) == 20
    assert nearest_rank_percentile([10, 20, 30, 40], 95) == 40
    assert nearest_rank_percentile([5], 95) == 5
    assert nearest_rank_percentile([], 95) is None


def test_wilson_and_bootstrap_intervals() -> None:
    low, high = wilson_interval(8, 10)
    assert low is not None and high is not None
    assert 0.49 < low < 0.52
    assert 0.92 < high < 0.96
    assert wilson_interval(0, 10)[0] == 0.0
    assert wilson_interval(10, 10)[1] == 1.0
    assert wilson_interval(0, 0) == (None, None)

    values = [0.0, 0.5, 1.0]
    first = bootstrap_ci(values, n_resamples=300, seed=11)
    second = bootstrap_ci(values, n_resamples=300, seed=11)
    assert first == second
    assert first[0] is not None and first[1] is not None
    assert first[0] <= 0.5 <= first[1]


# ---------------------------------------------------------------------------
# Runner and report
# ---------------------------------------------------------------------------


def _fake_pipeline(question: Question) -> Result:
    citations = [Citation.model_validate(source.model_dump()) for source in question.gold_sources]
    retrieved = [_retrieved(source) for source in question.gold_sources]
    if question.category == "unanswerable":
        return _result(question.question_id, abstained=question.question_id == "q007", latency_ms=40.0)
    if question.question_id == "q001":
        return _result(
            question.question_id,
            retrieved=retrieved,
            abstained=True,
            latency_ms=50.0,
        )
    if question.question_id == "q003":
        return _result(
            question.question_id,
            retrieved=retrieved[:1],
            citations=citations[:1],
            latency_ms=60.0,
        )
    if question.question_id == "q004":
        stale = Citation.model_validate(
            {**citations[0].model_dump(), "version": "v2"}
        )
        return _result(
            question.question_id,
            retrieved=retrieved,
            citations=[stale],
            latency_ms=70.0,
        )
    return _result(
        question.question_id,
        retrieved=retrieved,
        citations=citations,
        latency_ms=80.0,
    )


def test_runner_and_markdown_json_report(tmp_path: Path) -> None:
    questions = load_questions(SMALL_QUESTIONS)
    report = run_evaluation(
        questions,
        {"fixed": _fake_pipeline},
        dataset_path=str(SMALL_QUESTIONS),
        bootstrap_samples=200,
        seed=3,
    )
    assert isinstance(report, Report)
    assert report.n_questions == 7
    assert report.pipelines == ["fixed"]
    assert report.category_counts["single_hop"] == 2

    recall = next(
        row
        for row in report.rows
        if row.category == "overall" and row.metric == "recall_at_10"
    )
    assert recall.n == 5
    assert recall.value == pytest.approx(0.9)
    stale = next(
        row
        for row in report.rows
        if row.category == "overall" and row.metric == "stale_answer"
    )
    assert stale.n == 1
    assert stale.value == 1.0
    abstention = next(
        row
        for row in report.rows
        if row.category == "overall" and row.metric == "abstention_correct"
    )
    assert abstention.value == pytest.approx(5 / 7)

    failures = {failure.question_id for failure in report.failures}
    assert {"q001", "q003", "q004", "q006"} <= failures

    json_path, markdown_path = write_report(report, tmp_path)
    parsed = Report.model_validate(json.loads(json_path.read_text()))
    assert parsed.n_questions == 7
    markdown = markdown_path.read_text()
    assert "# Forge RAG Lab evaluation report" in markdown
    assert "## By category" in markdown
    assert "## Failure gallery" in markdown
    assert "## Caveats" in markdown
    assert "q004" in markdown
    assert "Stale-answer rate" in markdown


def test_config_and_judge_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    config = load_config(ROOT / "evals" / "config.yaml")
    assert config.dataset_path == Path("evals/data/questions.json")
    assert config.pipeline_command
    assert config.output_dir == Path("evals/reports")
    assert config.bootstrap_samples >= 1
    monkeypatch.delenv("EVAL_ENABLE_LLM_JUDGE", raising=False)
    assert judge_enabled() is False


def test_command_pipeline_json_adapter(tmp_path: Path) -> None:
    script = tmp_path / "pipeline.py"
    script.write_text(
        "import json, sys\n"
        "question = json.load(sys.stdin)\n"
        "print(json.dumps({\n"
        "  'question_id': question['question_id'],\n"
        "  'pipeline': 'fixed',\n"
        "  'answer': 'A stub answer',\n"
        "  'abstained': False,\n"
        "  'claims': [{\n"
        "    'claim_id': 'c1',\n"
        "    'text': 'A claim',\n"
        "    'citations': [{\n"
        "      'doc_id': 'helios-api-keys', 'version': 'v3',\n"
        "      'block_id': 'b1', 'page': 1\n"
        "    }],\n"
        "  }],\n"
        "  'retrieved': [],\n"
        "  'latency_ms': 12.5,\n"
        "}))\n"
    )
    pipeline = CommandPipeline("fixed", f"{sys.executable} {script}")
    result = pipeline(_question())
    assert result.question_id == "q001"
    assert result.pipeline == "fixed"
    assert result.answer == "A stub answer"
    assert result.latency_ms == 12.5
    assert len(result.citations) == 1
    assert result.citations[0].block_id == "b1"
