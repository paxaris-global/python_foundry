from fastapi.testclient import TestClient

from app.api import deps
from app.main import app
from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator


def test_web_discovery_preview(monkeypatch) -> None:
    class _Session:
        pass

    def _override_db():
        yield _Session()

    app.dependency_overrides.clear()
    app.dependency_overrides[deps.get_db] = _override_db

    monkeypatch.setattr(
        WebDiscoveryOrchestrator,
        "discover",
        lambda self, query, job_id=None, module_type="general", tags=None: {
            "query": query,
            "trusted_results": [{"url": "https://angular.dev", "title": "Angular", "trust_score": 0.95}],
            "extracted_features": ["dashboard"],
            "extracted_entities": ["user"],
            "extracted_routes": ["/dashboard"],
            "extracted_components": ["DataTable"],
            "backend_patterns": ["rest_api"],
            "suggested_architecture": ["dashboard_layout"],
        },
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/web-discovery/preview",
        json={
            "prompt": "Build a hospital management app",
            "website_like": "https://angular.dev",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["trusted_results"]
    assert body["extracted_features"] == ["dashboard"]
    assert body["backend_patterns"] == ["rest_api"]
    assert "draft_enriched_prompt" in body

    app.dependency_overrides.clear()
