from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from rag.corpus import Corpus, CorpusError, load_manifest

FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "corpus.json"


def test_loads_and_validates_manifest() -> None:
    corpus = Corpus.from_path(FIXTURE_CORPUS)

    assert len(corpus.documents) == 9
    assert sum(1 for _ in corpus.iter_blocks()) == 18
    assert corpus.tenants == ["northwind", "acme"]
    assert corpus.versions == ["v1", "v2", "v3"]
    assert load_manifest(FIXTURE_CORPUS).product == "Helios"


def test_iter_blocks_filters_tenant_and_version(corpus: Corpus) -> None:
    northwind = list(corpus.iter_blocks(tenant_id="northwind"))
    current = list(corpus.iter_blocks(tenant_id="northwind", current_only=True))

    assert northwind
    assert all(document.tenant_id == "northwind" for document, _ in northwind)
    assert all(document.is_current for document, _ in current)
    assert len(current) < len(northwind)
    assert all(document.version != "v2" for document, _ in current)


def test_get_block_by_tenant_doc_version_and_block(corpus: Corpus) -> None:
    block = corpus.get_block("northwind", "helios-api-keys", "v3", "b4")

    assert block is not None
    assert block.doc_id == "helios-api-keys"
    assert block.version == "v3"
    assert block.page == 2
    assert block.anchor == "#rotation-grace-period"
    assert block.is_current is True

    stale = corpus.get_block("northwind", "helios-api-keys", "v2", "b2")
    assert stale is not None
    assert stale.is_current is False


def test_version_history_returns_counterparts(corpus: Corpus) -> None:
    current = corpus.get_block("northwind", "helios-api-keys", "v3", "b2")
    assert current is not None
    history = corpus.version_history([current])

    assert {block.version for block in history} == {"v2"}
    assert all(block.is_current is False for block in history)
    assert all(block.block_id == "b2" for block in history)


def test_cross_tenant_reads_return_none(corpus: Corpus) -> None:
    assert corpus.get_block("acme", "helios-api-keys", "v3", "b4") is None
    assert corpus.get_block("northwind", "private-runbook", "v3", "b1") is not None
    assert corpus.get_block("acme", "private-runbook", "v3", "b1") is not None

    northwind = corpus.get_block("northwind", "private-runbook", "v3", "b1")
    acme = corpus.get_block("acme", "private-runbook", "v3", "b1")
    assert northwind is not None and acme is not None
    assert northwind.text != acme.text


def test_get_current_block_prefers_current_version(corpus: Corpus) -> None:
    block = corpus.get_current_block("northwind", "helios-api-keys", "b2")

    assert block is not None
    assert block.version == "v3"
    assert block.is_current is True


def test_unknown_tenant_or_block_is_none(corpus: Corpus) -> None:
    assert corpus.get_block("intruder", "helios-api-keys", "v3", "b1") is None
    assert corpus.get_block("northwind", "helios-api-keys", "v3", "missing") is None
    assert corpus.get_current_block("northwind", "missing", "b1") is None


def _write_manifest(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _fixture_payload() -> dict:
    return json.loads(FIXTURE_CORPUS.read_text(encoding="utf-8"))


def test_missing_manifest_raises() -> None:
    with pytest.raises(CorpusError, match="not found"):
        Corpus.from_path("/tmp/definitely-not-a-corpus.json")


def test_invalid_json_raises(tmp_path: Path) -> None:
    path = tmp_path / "corpus.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(CorpusError, match="not valid JSON"):
        Corpus.from_path(path)


def test_duplicate_block_ids_are_rejected(tmp_path: Path) -> None:
    payload = _fixture_payload()
    payload["documents"][0]["blocks"].append(copy.deepcopy(payload["documents"][0]["blocks"][0]))
    with pytest.raises(CorpusError, match="duplicate block_id"):
        Corpus.from_path(_write_manifest(tmp_path, payload))


def test_duplicate_anchors_are_rejected(tmp_path: Path) -> None:
    payload = _fixture_payload()
    payload["documents"][0]["blocks"][1]["anchor"] = payload["documents"][0]["blocks"][0]["anchor"]
    with pytest.raises(CorpusError, match="duplicate anchor"):
        Corpus.from_path(_write_manifest(tmp_path, payload))


def test_duplicate_document_versions_are_rejected(tmp_path: Path) -> None:
    payload = _fixture_payload()
    payload["documents"].append(copy.deepcopy(payload["documents"][0]))
    with pytest.raises(CorpusError, match="duplicate document version"):
        Corpus.from_path(_write_manifest(tmp_path, payload))


def test_bad_anchor_is_rejected(tmp_path: Path) -> None:
    payload = _fixture_payload()
    payload["documents"][0]["blocks"][0]["anchor"] = "overview"
    with pytest.raises(CorpusError, match="anchor must start"):
        Corpus.from_path(_write_manifest(tmp_path, payload))


def test_invalid_page_is_rejected(tmp_path: Path) -> None:
    payload = _fixture_payload()
    payload["documents"][0]["blocks"][0]["page"] = 0
    with pytest.raises(CorpusError):
        Corpus.from_path(_write_manifest(tmp_path, payload))


def test_bad_failure_fixture_reference_is_rejected(tmp_path: Path) -> None:
    payload = _fixture_payload()
    payload["failure_fixtures"]["stale_version"] = ["helios-api-keys@v99"]
    with pytest.raises(CorpusError, match="failure fixture"):
        Corpus.from_path(_write_manifest(tmp_path, payload))


def test_unknown_tenant_in_document_is_rejected(tmp_path: Path) -> None:
    payload = _fixture_payload()
    payload["documents"][0]["tenant_id"] = "globex"
    with pytest.raises(CorpusError, match="unknown tenant"):
        Corpus.from_path(_write_manifest(tmp_path, payload))


def test_empty_corpus_boots() -> None:
    corpus = Corpus.empty()
    assert corpus.documents == []
    assert "northwind" in corpus.tenants
