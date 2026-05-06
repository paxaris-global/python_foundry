from app.services.caching.fingerprint import FingerprintService
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import deps
from app.main import app
from app.models.generation_cache import GenerationCache


def test_fingerprint_stable() -> None:
    svc = FingerprintService()
    fp1 = svc.compute("Build CRM app", "springboot", "angular", ["auth", "dashboard"])
    fp2 = svc.compute("Build CRM app", "springboot", "angular", ["dashboard", "auth"])

    assert fp1 == fp2


def test_cache_endpoint() -> None:
    cache_obj = SimpleNamespace(
        fingerprint="abc123",
        project_id=uuid4(),
        hit_count=3,
        request_payload={"prompt": "Build CRM"},
        cache_metadata={"domain": "crm"},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    class _Q:
        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return cache_obj

    class _DB:
        def query(self, model):
            if model is GenerationCache:
                return _Q()
            return _Q()

    def _override_db():
        yield _DB()

    app.dependency_overrides.clear()
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.get("/api/v1/cache/abc123")

    assert response.status_code == 200
    assert response.json()["fingerprint"] == "abc123"

    app.dependency_overrides.clear()
