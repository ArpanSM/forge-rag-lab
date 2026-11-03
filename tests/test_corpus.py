"""Validate the generated Helios corpus and its failure fixtures."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pytest

from scripts.generate_corpus import (
    DOC_TYPES,
    PRODUCT,
    TENANTS,
    VERSIONS,
    build_corpus,
    build_outputs,
    write_corpus,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "manifests" / "corpus.json"
CORPUS_DIR = ROOT / "data" / "corpus"

DOCUMENT_KEYS = {
    "doc_id",
    "tenant_id",
    "title",
    "doc_type",
    "version",
    "effective_from",
    "superseded_at",
    "url_path",
    "blocks",
}
BLOCK_KEYS = {"block_id", "page", "heading", "anchor", "text"}
FIXTURE_KEYS = {
    "stale_version",
    "wrong_page_citation",
    "missed_detail",
    "unanswerable",
    "prompt_injection",
    "conflicting_versions",
    "cross_tenant",
}


@pytest.fixture(scope="module")
def manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def documents(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return manifest["documents"]


def find_documents(manifest: dict[str, Any], reference: str) -> list[dict[str, Any]]:
    """Resolve a fixture reference such as doc@v2 or tenant/doc."""
    if "/" in reference:
        tenant_id, doc_id = reference.split("/", 1)
        return [
            doc
            for doc in documents(manifest)
            if doc["tenant_id"] == tenant_id and doc["doc_id"] == doc_id
        ]
    doc_id, version = reference.rsplit("@", 1)
    return [
        doc
        for doc in documents(manifest)
        if doc["doc_id"] == doc_id and doc["version"] == version
    ]


def document_text(document: dict[str, Any]) -> str:
    return "\n".join(block["text"] for block in document["blocks"])


def test_manifest_top_level_shape(manifest: dict[str, Any]) -> None:
    assert set(manifest) == {
        "generated_at",
        "product",
        "tenants",
        "versions",
        "documents",
        "failure_fixtures",
    }
    assert manifest["product"] == PRODUCT
    assert manifest["tenants"] == list(TENANTS)
    assert manifest["versions"] == list(VERSIONS)
    assert manifest["generated_at"] == "2026-11-03T00:00:00Z"
    assert isinstance(manifest["documents"], list)
    assert set(manifest["failure_fixtures"]) == FIXTURE_KEYS


def test_document_metadata_shape(manifest: dict[str, Any]) -> None:
    for document in documents(manifest):
        assert set(document) == DOCUMENT_KEYS
        assert document["tenant_id"] in TENANTS
        assert document["version"] in VERSIONS
        assert document["doc_type"] in DOC_TYPES
        assert document["title"]
        assert document["url_path"].startswith("/")
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", document["effective_from"])
        if document["version"] == "v3":
            assert document["superseded_at"] is None
        else:
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", document["superseded_at"])
            assert document["superseded_at"] > document["effective_from"]


def test_corpus_size_and_version_coverage(manifest: dict[str, Any]) -> None:
    docs = documents(manifest)
    # "About 60 pages": 62 document versions are generated today.
    assert 55 <= len(docs) <= 65
    assert {doc["version"] for doc in docs} == set(VERSIONS)
    assert Counter(doc["version"] for doc in docs) == {
        "v1": 18,
        "v2": 20,
        "v3": 24,
    }
    assert Counter(doc["tenant_id"] for doc in docs) == {
        "northwind": 31,
        "acme": 31,
    }
    assert {doc["doc_type"] for doc in docs} == set(DOC_TYPES)

    per_tenant_versions = defaultdict(set)
    for document in docs:
        per_tenant_versions[document["tenant_id"]].add(document["version"])
    for tenant_id in TENANTS:
        assert per_tenant_versions[tenant_id] == set(VERSIONS)


def test_blocks_have_stable_unique_addresses(manifest: dict[str, Any]) -> None:
    for document in documents(manifest):
        blocks = document["blocks"]
        assert blocks
        block_ids = [block["block_id"] for block in blocks]
        anchors = [block["anchor"] for block in blocks]
        assert block_ids == [f"b{index}" for index in range(1, len(blocks) + 1)]
        assert len(set(block_ids)) == len(block_ids)
        assert len(set(anchors)) == len(anchors)
        for block in blocks:
            assert set(block) == BLOCK_KEYS
            assert isinstance(block["page"], int)
            assert block["page"] >= 1
            assert block["heading"]
            assert block["anchor"].startswith("#")
            assert " " not in block["anchor"]
            assert block["text"].strip()
        pages = sorted({block["page"] for block in blocks})
        assert pages == list(range(1, max(pages) + 1))


def test_markdown_files_match_manifest(manifest: dict[str, Any]) -> None:
    latest: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}
    for document in documents(manifest):
        tenant_id = document["tenant_id"]
        doc_id = document["doc_id"]
        version = document["version"]
        path = CORPUS_DIR / tenant_id / f"{doc_id}@{version}.md"
        assert path.is_file(), path
        content = path.read_text(encoding="utf-8")
        assert f"doc_id: {doc_id}" in content
        assert f"tenant_id: {tenant_id}" in content
        assert f"version: {version}" in content
        assert f"# {document['title']}" in content
        for block in document["blocks"]:
            assert block["text"] in content
            assert f'<a id="{block["anchor"].lstrip("#")}"></a>' in content
        for page in sorted({block["page"] for block in document["blocks"]}):
            assert f"<!-- page: {page} -->" in content
        current = latest.get((tenant_id, doc_id))
        if current is None or version > current[0]:
            latest[(tenant_id, doc_id)] = (version, document)

    # A stable <doc_id>.md alias points at the newest generated version.
    for (tenant_id, doc_id), (version, document) in latest.items():
        alias = CORPUS_DIR / tenant_id / f"{doc_id}.md"
        versioned = CORPUS_DIR / tenant_id / f"{doc_id}@{version}.md"
        assert alias.is_file(), alias
        assert alias.read_bytes() == versioned.read_bytes()


def test_shared_documents_overlap_and_private_pages_differ(manifest: dict[str, Any]) -> None:
    by_tenant_doc = defaultdict(list)
    for document in documents(manifest):
        by_tenant_doc[(document["tenant_id"], document["doc_id"])].append(document)

    shared_ids = {
        document["doc_id"]
        for document in documents(manifest)
        if document["doc_id"] != "private-runbook"
    }
    for doc_id in shared_ids:
        for version in VERSIONS:
            northwind = next(
                (
                    document
                    for document in by_tenant_doc[("northwind", doc_id)]
                    if document["version"] == version
                ),
                None,
            )
            acme = next(
                (
                    document
                    for document in by_tenant_doc[("acme", doc_id)]
                    if document["version"] == version
                ),
                None,
            )
            if northwind is None or acme is None:
                continue
            assert northwind["blocks"] == acme["blocks"]

    northwind_private = by_tenant_doc[("northwind", "private-runbook")]
    acme_private = by_tenant_doc[("acme", "private-runbook")]
    assert len(northwind_private) == 1
    assert len(acme_private) == 1
    assert northwind_private[0]["blocks"] != acme_private[0]["blocks"]


def test_committed_data_matches_a_fresh_build() -> None:
    assert json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) == build_corpus()


def test_generation_is_deterministic(tmp_path: Path) -> None:
    first_manifest, first_outputs = build_outputs(tmp_path)
    second_manifest, second_outputs = build_outputs(tmp_path)
    assert first_manifest == second_manifest
    assert first_outputs == second_outputs

    write_corpus(tmp_path)
    first_files = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in (tmp_path / "data").rglob("*")
        if path.is_file()
    }
    write_corpus(tmp_path)
    second_files = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in (tmp_path / "data").rglob("*")
        if path.is_file()
    }
    assert first_files == second_files


def test_all_failure_fixtures_resolve(manifest: dict[str, Any]) -> None:
    for fixture, references in manifest["failure_fixtures"].items():
        assert references, f"{fixture} has no references"
        for reference in references:
            matches = find_documents(manifest, reference)
            assert matches, f"{fixture} points at missing document {reference}"
            for document in matches:
                assert document["tenant_id"] in TENANTS


def test_stale_version_fixture(manifest: dict[str, Any]) -> None:
    for reference in manifest["failure_fixtures"]["stale_version"]:
        matches = find_documents(manifest, reference)
        assert matches
        for stale in matches:
            assert stale["superseded_at"] is not None
            current = [
                document
                for document in documents(manifest)
                if document["tenant_id"] == stale["tenant_id"]
                and document["doc_id"] == stale["doc_id"]
                and document["version"] > stale["version"]
                and document["superseded_at"] is None
            ]
            assert current
            assert "do not expire" in document_text(stale)
            assert "90 days" in document_text(current[-1])


def test_wrong_page_citation_fixture(manifest: dict[str, Any]) -> None:
    for reference in manifest["failure_fixtures"]["wrong_page_citation"]:
        matches = find_documents(manifest, reference)
        assert matches
        for document in matches:
            detail_blocks = [
                block
                for block in document["blocks"]
                if block["heading"] == "Audit log access"
            ]
            assert len(detail_blocks) == 1
            detail = detail_blocks[0]
            assert detail["page"] > 1
            assert "audit.export" in detail["text"]
            assert "30 days" in detail["text"]
            assert max(block["page"] for block in document["blocks"]) >= 3


def test_missed_detail_fixture(manifest: dict[str, Any]) -> None:
    for reference in manifest["failure_fixtures"]["missed_detail"]:
        matches = find_documents(manifest, reference)
        assert matches
        for document in matches:
            assert max(block["page"] for block in document["blocks"]) >= 5
            detail_blocks = [
                block
                for block in document["blocks"]
                if "14-day overage grace period" in block["text"]
            ]
            assert len(detail_blocks) == 1
            assert detail_blocks[0]["page"] == 4
            assert detail_blocks[0]["heading"] == "Overage grace period"
            assert len(document["blocks"]) >= 10


def test_unanswerable_fixture(manifest: dict[str, Any]) -> None:
    for reference in manifest["failure_fixtures"]["unanswerable"]:
        matches = find_documents(manifest, reference)
        assert matches
        for document in matches:
            text = document_text(document).lower()
            assert "on-premises distribution" in text
            assert "cloud-only" in text
            assert "no installer" in text
            # The page must not leak a supported installation command that would
            # make the fixture answerable by accident.
            assert "heliosctl install" not in text
            assert "install --" not in text


def test_prompt_injection_fixture(manifest: dict[str, Any]) -> None:
    for reference in manifest["failure_fixtures"]["prompt_injection"]:
        matches = find_documents(manifest, reference)
        assert matches
        for document in matches:
            text = document_text(document)
            assert "Ignore all previous instructions" in text
            assert "unlimited storage" in text
            assert "compromised localization import" in text

    clean = find_documents(manifest, "helios-release-notes@v2")
    assert clean
    assert all(
        "Ignore all previous instructions" not in document_text(document)
        for document in clean
    )


def test_conflicting_versions_fixture(manifest: dict[str, Any]) -> None:
    references = manifest["failure_fixtures"]["conflicting_versions"]
    assert len(references) >= 2
    resolved = [find_documents(manifest, reference)[0] for reference in references]
    assert {document["doc_id"] for document in resolved} == {"helios-sso-policy"}
    assert {document["version"] for document in resolved} == {"v2", "v3"}
    by_version = {document["version"]: document_text(document) for document in resolved}
    assert "SAML sessions expire after 12 hours" in by_version["v2"]
    assert "SCIM provisioning is not available" in by_version["v2"]
    assert "SAML sessions expire after 8 hours" in by_version["v3"]
    assert "SCIM 2.0 provisioning is available" in by_version["v3"]


def test_cross_tenant_fixture(manifest: dict[str, Any]) -> None:
    references = manifest["failure_fixtures"]["cross_tenant"]
    assert references == ["northwind/private-runbook", "acme/private-runbook"]
    northwind = find_documents(manifest, references[0])
    acme = find_documents(manifest, references[1])
    assert len(northwind) == 1
    assert len(acme) == 1
    assert northwind[0]["tenant_id"] == "northwind"
    assert acme[0]["tenant_id"] == "acme"
    assert northwind[0]["doc_id"] == acme[0]["doc_id"] == "private-runbook"

    northwind_text = document_text(northwind[0])
    acme_text = document_text(acme[0])
    assert "northwind-private marker: NW-RUNBOOK-7" in northwind_text
    assert "acme-private marker: ACME-PROC-4" in acme_text
    assert "ACME-PROC-4" not in northwind_text
    assert "NW-RUNBOOK-7" not in acme_text
    assert northwind[0]["blocks"] != acme[0]["blocks"]
