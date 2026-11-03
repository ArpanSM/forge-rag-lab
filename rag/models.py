"""Domain models shared by ingestion, retrieval, generation and the API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PipelineName = Literal["fixed", "baseline"]


class Block(BaseModel):
    """A stable, citation-addressable unit of a document."""

    model_config = ConfigDict(extra="ignore")

    block_id: str = Field(min_length=1)
    page: int = Field(ge=1)
    heading: str | None = None
    anchor: str = Field(min_length=1)
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def _anchor_is_fragment(self) -> Block:
        if not self.anchor.startswith("#"):
            raise ValueError(f"block {self.block_id}: anchor must start with '#'")
        return self


class Document(BaseModel):
    """One version of one page belonging to exactly one tenant."""

    model_config = ConfigDict(extra="ignore")

    doc_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    doc_type: str = Field(min_length=1)
    version: str = Field(min_length=1)
    effective_from: date
    superseded_at: date | None = None
    url_path: str | None = None
    blocks: list[Block] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_document(self) -> Document:
        if self.superseded_at is not None and self.superseded_at < self.effective_from:
            raise ValueError(
                f"{self.tenant_id}/{self.doc_id}@{self.version}: "
                "superseded_at cannot be before effective_from"
            )
        seen: set[str] = set()
        anchors: set[str] = set()
        for block in self.blocks:
            if block.block_id in seen:
                raise ValueError(
                    f"{self.tenant_id}/{self.doc_id}@{self.version}: "
                    f"duplicate block_id {block.block_id!r}"
                )
            if block.anchor in anchors:
                raise ValueError(
                    f"{self.tenant_id}/{self.doc_id}@{self.version}: "
                    f"duplicate anchor {block.anchor!r}"
                )
            seen.add(block.block_id)
            anchors.add(block.anchor)
        return self

    @property
    def is_current(self) -> bool:
        return self.superseded_at is None

    @property
    def versioned_id(self) -> str:
        return f"{self.doc_id}@{self.version}"


class CorpusManifest(BaseModel):
    """Canonical corpus manifest described by ``docs/corpus-schema.md``."""

    model_config = ConfigDict(extra="ignore")

    generated_at: datetime
    product: str = Field(min_length=1)
    tenants: list[str] = Field(min_length=1)
    versions: list[str] = Field(min_length=1)
    documents: list[Document] = Field(default_factory=list)
    failure_fixtures: dict[str, list[str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_manifest(self) -> CorpusManifest:
        if len(set(self.tenants)) != len(self.tenants):
            raise ValueError("tenants must be unique")
        if len(set(self.versions)) != len(self.versions):
            raise ValueError("versions must be unique")

        seen: set[tuple[str, str, str]] = set()
        for document in self.documents:
            if document.tenant_id not in self.tenants:
                raise ValueError(
                    f"document {document.doc_id}@{document.version}: "
                    f"unknown tenant {document.tenant_id!r}"
                )
            if document.version not in self.versions:
                raise ValueError(
                    f"document {document.doc_id}: unknown version {document.version!r}"
                )
            key = (document.tenant_id, document.doc_id, document.version)
            if key in seen:
                raise ValueError(
                    "duplicate document version: "
                    f"{document.tenant_id}/{document.doc_id}@{document.version}"
                )
            seen.add(key)

        for fixture, references in self.failure_fixtures.items():
            for reference in references:
                if not self._fixture_exists(reference):
                    raise ValueError(
                        f"failure fixture {fixture!r} references missing {reference!r}"
                    )
        return self

    def _fixture_exists(self, reference: str) -> bool:
        """Accept ``doc@version``, ``tenant/doc`` and ``tenant/doc@version`` references."""
        tenant: str | None = None
        target = reference
        if "/" in target:
            tenant, target = target.split("/", 1)
        version: str | None = None
        if "@" in target:
            target, version = target.rsplit("@", 1)

        for document in self.documents:
            if document.doc_id != target:
                continue
            if tenant is not None and document.tenant_id != tenant:
                continue
            if version is not None and document.version != version:
                continue
            return True
        return False


class RetrievedBlock(BaseModel):
    """A block returned by retrieval, carrying enough metadata to build a citation."""

    model_config = ConfigDict(extra="ignore")

    doc_id: str
    tenant_id: str
    title: str
    doc_type: str
    version: str
    page: int = Field(ge=1)
    block_id: str
    anchor: str
    heading: str | None = None
    text: str
    is_current: bool
    chunk_id: str = ""
    score: float = 0.0
    dense_score: float | None = None
    bm25_score: float | None = None
    retrieval_source: str = ""

    @property
    def ref(self) -> str:
        """Stable reference used in prompts and parsed from model output."""
        return f"{self.doc_id}@{self.version}#{self.block_id}"

    @property
    def chunk_ref(self) -> str:
        """Unique identity inside a vector index (tenant-scoped, chunk-aware)."""
        return f"{self.tenant_id}/{self.doc_id}@{self.version}#{self.chunk_id or self.block_id}"

    @property
    def search_text(self) -> str:
        parts = [self.title]
        if self.heading:
            parts.append(self.heading)
        parts.append(self.text)
        return "\n".join(parts)


class Citation(BaseModel):
    """A resolved reference from a claim to one block in one document version."""

    doc_id: str
    title: str
    version: str
    page: int
    block_id: str
    anchor: str
    quote: str


class Claim(BaseModel):
    """A user-visible assertion plus the evidence that supports it."""

    claim_id: str
    text: str
    citations: list[Citation] = Field(default_factory=list)


class Answer(BaseModel):
    """Pipeline output matching ``docs/api-contract.md``."""

    answer: str
    abstained: bool
    claims: list[Claim] = Field(default_factory=list)
    latency_ms: int = 0
    model: str = "none"
    pipeline: PipelineName
    trace_id: str
    injection_detected: bool = False
