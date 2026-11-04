from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import create_app
from rag.corpus import Corpus
from rag.embeddings import HashingEmbedder
from rag.prompts import FIXED_SYSTEM_PROMPT
from rag.providers import FakeProvider
from rag.service import RagService


def _fixed_payload() -> str:
    return json.dumps(
        {
            "answerable": True,
            "answer": "The old key remains valid for 24 hours.",
            "claims": [
                {
                    "claim_id": "c1",
                    "text": "The old key remains valid for 24 hours.",
                    "citations": [
                        {
                            "ref": "helios-api-keys@v3#b4",
                            "quote": "Rotated keys remain valid for 24 hours after rotation.",
                        }
                    ],
                }
            ],
        }
    )


def _baseline_payload() -> str:
    return json.dumps(
        {
            "answerable": True,
            "answer": "Admins may opt out until April 2026.",
            "claims": [
                {
                    "claim_id": "c1",
                    "text": "Admins may opt out of SSO.",
                    "citations": [
                        {
                            "ref": "helios-sso-policy@v2#b1",
                            "quote": "Admins may opt out of SSO until 2026-04-01 by contacting support.",
                        }
                    ],
                }
            ],
        }
    )


def _build_app(corpus: Corpus, reports_dir: Path):
    def respond(system_prompt: str, user_prompt: str) -> str:
        return _fixed_payload() if system_prompt == FIXED_SYSTEM_PROMPT else _baseline_payload()

    provider = FakeProvider(respond)
    service = RagService(corpus, provider, embedder=HashingEmbedder())
    return create_app(service, reports_dir=reports_dir)


def test_health(corpus: Corpus, tmp_path: Path) -> None:
    client = TestClient(_build_app(corpus, tmp_path / "reports"))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "0.1.0",
        "qdrant": "ok",
        "model_provider": "fake",
    }


def test_query_contract_fixed(corpus: Corpus, tmp_path: Path) -> None:
    client = TestClient(_build_app(corpus, tmp_path / "reports"))

    response = client.post(
        "/api/query",
        json={
            "tenant_id": "northwind",
            "question": "How long do rotated keys stay valid?",
            "pipeline": "fixed",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {
        "answer",
        "abstained",
        "claims",
        "latency_ms",
        "model",
        "pipeline",
        "trace_id",
    }
    assert body["abstained"] is False
    assert body["pipeline"] == "fixed"
    assert body["model"] == "fake-model"
    assert len(body["trace_id"]) == 26
    citation = body["claims"][0]["citations"][0]
    assert set(citation) == {
        "doc_id",
        "title",
        "version",
        "page",
        "block_id",
        "anchor",
        "quote",
    }
    assert citation["version"] == "v3"
    assert citation["page"] == 2
    assert citation["block_id"] == "b4"


def test_query_baseline(corpus: Corpus, tmp_path: Path) -> None:
    client = TestClient(_build_app(corpus, tmp_path / "reports"))

    response = client.post(
        "/api/query",
        json={
            "tenant_id": "northwind",
            "question": "Can admins opt out of SSO?",
            "pipeline": "baseline",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pipeline"] == "baseline"
    assert body["abstained"] is False
    assert body["claims"][0]["citations"][0]["version"] == "v2"


def test_query_unknown_tenant_and_validation(corpus: Corpus, tmp_path: Path) -> None:
    client = TestClient(_build_app(corpus, tmp_path / "reports"))

    unknown = client.post(
        "/api/query",
        json={"tenant_id": "globex", "question": "Hello", "pipeline": "fixed"},
    )
    blank = client.post(
        "/api/query",
        json={"tenant_id": "northwind", "question": "", "pipeline": "fixed"},
    )
    bad_pipeline = client.post(
        "/api/query",
        json={"tenant_id": "northwind", "question": "Hello", "pipeline": "other"},
    )

    assert unknown.status_code == 400
    assert blank.status_code == 422
    assert bad_pipeline.status_code == 422


def test_demo_questions(corpus: Corpus, tmp_path: Path) -> None:
    client = TestClient(_build_app(corpus, tmp_path / "reports"))

    response = client.get("/api/demo/questions")

    assert response.status_code == 200
    questions = response.json()
    assert len(questions) >= 5
    assert {"id", "tenant_id", "question", "category"} <= set(questions[0])
    assert any(item["category"] == "version_specific" for item in questions)
    assert any(item["category"] == "unanswerable" for item in questions)


def test_eval_reports_empty_then_loaded(corpus: Corpus, tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    client = TestClient(_build_app(corpus, reports))

    empty = client.get("/api/eval/summary")
    empty_failures = client.get("/api/eval/failures")

    assert empty.status_code == 200
    assert empty.json() == {"generated_at": None, "rows": []}
    assert empty_failures.status_code == 200
    assert empty_failures.json() == []

    reports.mkdir(parents=True)
    (reports / "summary.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-11-03T00:00:00Z",
                "rows": [
                    {
                        "metric": "citation_page_accuracy",
                        "baseline": 0.61,
                        "fixed": 0.92,
                        "delta": 0.31,
                        "n": 80,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports / "failures.json").write_text(
        json.dumps(
            [
                {
                    "question_id": "q014",
                    "category": "conflicting",
                    "failure": "stale_citation",
                    "fixed_citations": [],
                    "extra_field": "preserved",
                }
            ]
        ),
        encoding="utf-8",
    )

    summary = client.get("/api/eval/summary").json()
    failures = client.get("/api/eval/failures").json()

    assert summary["rows"][0]["metric"] == "citation_page_accuracy"
    assert summary["rows"][0]["delta"] == 0.31
    assert failures[0]["failure"] == "stale_citation"
    assert failures[0]["extra_field"] == "preserved"


def test_eval_report_from_harness(corpus: Corpus, tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "eval-report.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-11-03T00:00:00Z",
                "n_questions": 3,
                "pipelines": ["baseline", "fixed"],
                "rows": [
                    {
                        "metric": "recall_at_5",
                        "pipeline": "baseline",
                        "category": "overall",
                        "label": "Recall@5",
                        "value": 0.25,
                        "n": 3,
                    },
                    {
                        "metric": "recall_at_5",
                        "pipeline": "fixed",
                        "category": "overall",
                        "label": "Recall@5",
                        "value": 0.5,
                        "n": 3,
                    },
                ],
                "failures": [
                    {
                        "question_id": "q001",
                        "category": "single_hop",
                        "pipeline": "baseline",
                        "failure": "missed_abstention",
                        "question": "How long do rotated keys stay valid?",
                        "answer": "The old key is valid forever.",
                        "citations": [],
                    },
                    {
                        "question_id": "q001",
                        "category": "single_hop",
                        "pipeline": "fixed",
                        "failure": "missed_abstention",
                        "question": "How long do rotated keys stay valid?",
                        "answer": "I could not find enough evidence.",
                        "citations": [],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(_build_app(corpus, reports))

    summary = client.get("/api/eval/summary").json()
    failures = client.get("/api/eval/failures").json()

    assert summary["rows"][0]["metric"] == "recall_at_5"
    assert summary["rows"][0]["baseline"] == 0.25
    assert summary["rows"][0]["fixed"] == 0.5
    assert summary["rows"][0]["delta"] == 0.25
    assert summary["n_questions"] == 3
    assert failures[0]["question_id"] == "q001"
    assert failures[0]["failure"] == "missed_abstention"
    assert failures[0]["baseline_answer"] == "The old key is valid forever."
    assert failures[0]["fixed_answer"] == "I could not find enough evidence."


def test_eval_malformed_reports_are_empty(corpus: Corpus, tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "summary.json").write_text("not json", encoding="utf-8")
    (reports / "failures.json").write_text("[]", encoding="utf-8")
    client = TestClient(_build_app(corpus, reports))

    assert client.get("/api/eval/summary").json() == {"generated_at": None, "rows": []}
    assert client.get("/api/eval/failures").json() == []


def test_document_block_viewer(corpus: Corpus, tmp_path: Path) -> None:
    client = TestClient(_build_app(corpus, tmp_path / "reports"))

    current = client.get(
        "/api/docs/helios-api-keys/blocks/b4",
        params={"tenant_id": "northwind"},
    )
    old = client.get(
        "/api/docs/helios-api-keys/blocks/b2",
        params={"tenant_id": "northwind", "version": "v2"},
    )
    cross_tenant = client.get(
        "/api/docs/helios-api-keys/blocks/b4",
        params={"tenant_id": "acme"},
    )
    missing = client.get(
        "/api/docs/helios-api-keys/blocks/missing",
        params={"tenant_id": "northwind"},
    )

    assert current.status_code == 200
    current_body = current.json()
    assert current_body["version"] == "v3"
    assert current_body["page"] == 2
    assert current_body["anchor"] == "#rotation-grace-period"
    assert current_body["heading"] == "Rotation grace period"
    assert old.status_code == 200
    assert old.json()["version"] == "v2"
    assert cross_tenant.status_code == 404
    assert missing.status_code == 404


def test_query_service_unavailable(monkeypatch, tmp_path: Path) -> None:
    from api import main as api_main

    def fail():
        raise RuntimeError("corpus exploded")

    monkeypatch.setattr(api_main, "build_service_from_env", fail)
    app = create_app(None, reports_dir=tmp_path / "reports")
    client = TestClient(app)

    health = client.get("/api/health")
    query = client.post(
        "/api/query",
        json={"tenant_id": "northwind", "question": "Hello", "pipeline": "fixed"},
    )

    assert health.status_code == 200
    assert health.json()["status"] == "degraded"
    assert query.status_code == 503
