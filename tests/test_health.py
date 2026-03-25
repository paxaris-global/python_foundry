from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "ai-codegen-platform"
    assert payload["status"] in {"ok", "degraded"}
    assert "dependencies" in payload
    assert {"db", "redis", "chroma"}.issubset(set(payload["dependencies"].keys()))
