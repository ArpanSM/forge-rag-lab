from fastapi.testclient import TestClient

from api.main import app

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
