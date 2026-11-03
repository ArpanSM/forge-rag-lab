"""Request and response models for the public API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=4000)
    pipeline: Literal["fixed", "baseline"] = "fixed"


class HealthResponse(BaseModel):
    status: str
    version: str
    qdrant: str
    model_provider: str


class DemoQuestion(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    tenant_id: str
    question: str
    category: str


class EvalSummaryRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    metric: str
    baseline: float | None = None
    fixed: float | None = None
    delta: float | None = None
    n: int | None = None


class EvalSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    generated_at: str | None = None
    rows: list[EvalSummaryRow] = Field(default_factory=list)


class EvalFailure(BaseModel):
    model_config = ConfigDict(extra="allow")

    question_id: str | None = None
    category: str | None = None
    question: str | None = None
    baseline_answer: str | None = None
    fixed_answer: str | None = None
    failure: str | None = None
    fixed_citations: list[Any] = Field(default_factory=list)


class BlockDetail(BaseModel):
    doc_id: str
    tenant_id: str
    title: str
    version: str
    page: int
    block_id: str
    anchor: str
    heading: str | None = None
    text: str
