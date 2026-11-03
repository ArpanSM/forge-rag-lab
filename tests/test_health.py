from pathlib import Path

from fastapi.testclient import TestClient

from api.main import create_app
from rag.corpus import Corpus
from rag.embeddings import HashingEmbedder
from rag.providers import FakeProvider
from rag.service import RagService

FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "corpus.json"


def _fake_service() -> RagService:
    corpus = Corpus.from_path(FIXTURE_CORPUS)
    provider = FakeProvider(
        '{"answerable": false, "answer": "no evidence", "claims": []}'
    )
    return RagService(corpus, provider, embedder=HashingEmbedder())


app = create_app(service=_fake_service())
client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_query_stub() -> None:
    response = client.post(
        "/api/query",
        json={"tenant_id": "northwind", "question": "test", "pipeline": "fixed"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["pipeline"] == "fixed"
    assert body["abstained"] is True
