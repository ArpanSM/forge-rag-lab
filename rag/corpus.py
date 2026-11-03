"""Load, validate and query the versioned corpus manifest."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from rag.models import Block, CorpusManifest, Document, RetrievedBlock


class CorpusError(RuntimeError):
    """Raised when the manifest is missing, malformed or fails validation."""


class Corpus:
    """Read-only view over a validated corpus manifest.

    Every lookup takes the tenant explicitly and cross-tenant reads return ``None``.
    """

    def __init__(self, manifest: CorpusManifest) -> None:
        self.manifest = manifest
        self._documents: dict[tuple[str, str, str], Document] = {
            (document.tenant_id, document.doc_id, document.version): document
            for document in manifest.documents
        }
        self._documents_by_id: dict[tuple[str, str], list[Document]] = {}
        for document in manifest.documents:
            self._documents_by_id.setdefault((document.tenant_id, document.doc_id), []).append(
                document
            )

    @classmethod
    def from_path(cls, path: str | Path) -> Corpus:
        manifest_path = Path(path)
        if not manifest_path.exists():
            raise CorpusError(f"corpus manifest not found: {manifest_path}")
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CorpusError(f"corpus manifest is not valid JSON: {exc}") from exc
        try:
            manifest = CorpusManifest.model_validate(raw)
        except ValidationError as exc:
            raise CorpusError(f"corpus manifest failed validation: {exc}") from exc
        return cls(manifest)

    @classmethod
    def empty(cls) -> Corpus:
        """An empty corpus so the API can boot before data is generated."""
        return cls(
            CorpusManifest(
                generated_at=datetime.now(UTC),
                product="Helios",
                tenants=["northwind", "acme"],
                versions=["v1", "v2", "v3"],
                documents=[],
                failure_fixtures={},
            )
        )

    @property
    def tenants(self) -> list[str]:
        return self.manifest.tenants

    @property
    def versions(self) -> list[str]:
        return self.manifest.versions

    @property
    def documents(self) -> list[Document]:
        return self.manifest.documents

    def has_tenant(self, tenant_id: str) -> bool:
        return tenant_id in self.manifest.tenants

    def get_document(
        self, tenant_id: str, doc_id: str, version: str | None = None
    ) -> Document | None:
        if version is not None:
            return self._documents.get((tenant_id, doc_id, version))
        candidates = self._documents_by_id.get((tenant_id, doc_id), [])
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda document: (document.is_current, document.effective_from),
        )

    def documents_for(self, tenant_id: str) -> list[Document]:
        return [document for document in self.documents if document.tenant_id == tenant_id]

    def iter_blocks(
        self, tenant_id: str | None = None, current_only: bool = False
    ) -> Iterator[tuple[Document, Block]]:
        for document in self.documents:
            if tenant_id is not None and document.tenant_id != tenant_id:
                continue
            if current_only and not document.is_current:
                continue
            for block in document.blocks:
                yield document, block

    def iter_retrieved(
        self, tenant_id: str | None = None, current_only: bool = False
    ) -> Iterator[RetrievedBlock]:
        for document, block in self.iter_blocks(tenant_id=tenant_id, current_only=current_only):
            yield self._to_retrieved(document, block)

    def get_block(
        self, tenant_id: str, doc_id: str, version: str, block_id: str
    ) -> RetrievedBlock | None:
        document = self._documents.get((tenant_id, doc_id, version))
        if document is None:
            return None
        for block in document.blocks:
            if block.block_id == block_id:
                return self._to_retrieved(document, block)
        return None

    def get_current_block(
        self, tenant_id: str, doc_id: str, block_id: str
    ) -> RetrievedBlock | None:
        """Resolve a block without a version, preferring the current version."""
        candidates = self._documents_by_id.get((tenant_id, doc_id), [])
        if not candidates:
            return None
        ordered = sorted(
            candidates,
            key=lambda document: (document.is_current, document.effective_from),
            reverse=True,
        )
        for document in ordered:
            for block in document.blocks:
                if block.block_id == block_id:
                    return self._to_retrieved(document, block)
        return None

    def version_history(self, blocks: Sequence[RetrievedBlock]) -> list[RetrievedBlock]:
        """Return superseded/current counterparts of the same block across versions.

        This gives the fixed pipeline a small, explicit version history for the
        retrieved evidence without globally surfacing every stale document.
        """
        history: list[RetrievedBlock] = []
        seen: set[tuple[str, str, str, str]] = set()
        for block in blocks:
            for document in self._documents_by_id.get((block.tenant_id, block.doc_id), []):
                if document.version == block.version:
                    continue
                for candidate in document.blocks:
                    if candidate.block_id != block.block_id:
                        continue
                    key = (
                        document.tenant_id,
                        document.doc_id,
                        document.version,
                        candidate.block_id,
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    history.append(self._to_retrieved(document, candidate))
        history.sort(key=lambda item: (item.doc_id, _version_key(item.version), item.block_id))
        return history

    @staticmethod
    def _to_retrieved(document: Document, block: Block) -> RetrievedBlock:
        return RetrievedBlock(
            doc_id=document.doc_id,
            tenant_id=document.tenant_id,
            title=document.title,
            doc_type=document.doc_type,
            version=document.version,
            page=block.page,
            block_id=block.block_id,
            anchor=block.anchor,
            heading=block.heading,
            text=block.text,
            is_current=document.is_current,
        )


def _version_key(version: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", version)
    return tuple(int(part) for part in parts) if parts else (0,)


def load_manifest(path: str | Path) -> CorpusManifest:
    """Load and validate a manifest without wrapping it in :class:`Corpus`."""
    return Corpus.from_path(path).manifest


def load_corpus(path: str | Path) -> Corpus:
    return Corpus.from_path(path)
