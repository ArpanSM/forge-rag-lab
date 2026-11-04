"""Pydantic schemas for Forge's evaluation harness.

The public shapes mirror ``docs/eval-schema.md`` and add the fields the
deterministic metrics need (retrieved chunks, target version, split).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Category = Literal[
    "single_hop",
    "multi_hop",
    "version_specific",
    "conflicting",
    "unanswerable",
]
Split = Literal["dev", "test", "shadow"]
FailureName = Literal[
    "pipeline_error",
    "false_abstention",
    "missed_abstention",
    "stale_answer",
    "no_disambiguation",
    "citation_page_miss",
    "retrieval_miss",
    "all_gold_miss",
]

CATEGORIES: tuple[Category, ...] = (
    "single_hop",
    "multi_hop",
    "version_specific",
    "conflicting",
    "unanswerable",
)


class _SourceBase(BaseModel):
    """A pointer to a stable block inside a versioned document."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    block_id: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    anchor: str | None = None
    title: str | None = None
    quote: str | None = None


class GoldSource(_SourceBase):
    """A block that must be retrieved/cited to answer a question."""


class Citation(_SourceBase):
    """A citation returned by a pipeline."""

    tenant_id: str | None = None


class RetrievedChunk(Citation):
    """A retrieved chunk, in rank order on ``Result.retrieved``."""

    rank: int | None = Field(default=None, ge=1)
    text: str | None = None
    score: float | None = None


class Question(BaseModel):
    """One evaluation question with gold evidence."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    category: Category
    answerable: bool
    gold_answer: str
    gold_sources: list[GoldSource] = Field(default_factory=list)
    notes: str = ""
    split: Split = "dev"
    target_version: str | None = None
    superseded_versions: list[str] = Field(default_factory=list)
    required_facts: list[str] = Field(default_factory=list)
    failure_mode: str | None = None

    @model_validator(mode="after")
    def _answerability_matches_category(self) -> Question:
        if self.category == "unanswerable":
            if self.answerable:
                raise ValueError("unanswerable questions must set answerable=false")
            if self.gold_sources:
                raise ValueError("unanswerable questions must not have gold sources")
        else:
            if not self.answerable:
                raise ValueError(f"{self.category} questions must be answerable")
            if not self.gold_sources:
                raise ValueError(f"{self.category} questions need at least one gold source")
        if self.category == "version_specific" and not self.target_version:
            raise ValueError("version_specific questions need target_version")
        return self


class JudgeScores(BaseModel):
    """Optional LLM-judge scores. ``None`` means the judge did not score it."""

    model_config = ConfigDict(extra="allow")

    answer_correctness: float | None = Field(default=None, ge=0.0, le=1.0)
    faithfulness: float | None = Field(default=None, ge=0.0, le=1.0)
    factual_f1: float | None = Field(default=None, ge=0.0, le=1.0)
    context_precision: float | None = Field(default=None, ge=0.0, le=1.0)
    context_recall: float | None = Field(default=None, ge=0.0, le=1.0)
    model: str | None = None


class Result(BaseModel):
    """One pipeline answer plus the evidence it returned."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    pipeline: str = Field(min_length=1)
    answer: str = ""
    abstained: bool = False
    citations: list[Citation] = Field(default_factory=list)
    retrieved: list[RetrievedChunk] = Field(default_factory=list)
    latency_ms: float = Field(default=0.0, ge=0.0)
    metrics: dict[str, float | None] = Field(default_factory=dict)
    judge: JudgeScores | None = None
    error: str | None = None
    model: str | None = None
    trace_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetricRow(BaseModel):
    """One aggregate metric for one pipeline, category and denominator."""

    model_config = ConfigDict(extra="forbid")

    pipeline: str
    category: str
    metric: str
    label: str
    value: float | None
    n: int = Field(ge=0)
    ci_low: float | None = None
    ci_high: float | None = None
    ci_method: Literal["wilson", "bootstrap", "none"] = "none"
    higher_is_better: bool = True
    unit: str | None = None


class PairedComparison(BaseModel):
    """Paired baseline-vs-fixed difference for one metric."""

    model_config = ConfigDict(extra="forbid")

    metric: str
    label: str
    baseline_mean: float | None = None
    fixed_mean: float | None = None
    delta: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    n: int = Field(ge=0)
    higher_is_better: bool = True


class FailureCase(BaseModel):
    """A concrete failing question kept for the report's failure gallery."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    category: Category
    pipeline: str
    failure: FailureName
    reasons: list[str] = Field(default_factory=list)
    question: str
    expected: str = ""
    answer: str = ""
    citations: list[Citation] = Field(default_factory=list)
    metrics: dict[str, float | None] = Field(default_factory=dict)
    notes: str = ""


class Report(BaseModel):
    """Machine-readable evaluation report, also rendered to Markdown."""

    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    dataset_path: str
    n_questions: int = Field(ge=0)
    pipelines: list[str] = Field(default_factory=list)
    category_counts: dict[str, int] = Field(default_factory=dict)
    split_counts: dict[str, int] = Field(default_factory=dict)
    rows: list[MetricRow] = Field(default_factory=list)
    paired_comparisons: list[PairedComparison] = Field(default_factory=list)
    failures: list[FailureCase] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
