from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import deps
from app.api.v1.routes import generate as generate_route
from app.main import app
from app.models.generation_cache import GenerationCache
from app.models.job import Job
from app.tasks.generation_tasks import generate_project_task


class _Query:
    def __init__(self, result):
        self._result = result

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._result


class _FakeSession:
    def __init__(self, cached: GenerationCache | None = None):
        self.cached = cached
        self.created_jobs: list[Job] = []

    def query(self, model):
        if model is GenerationCache:
            return _Query(self.cached)
        return _Query(None)

    def add(self, obj):
        if isinstance(obj, Job):
            if not getattr(obj, "id", None):
                obj.id = uuid4()
            self.created_jobs.append(obj)

    def commit(self):
        return None

    def refresh(self, _obj):
        return None


def test_generate_creates_job(monkeypatch) -> None:
    fake_db = _FakeSession(cached=None)

    def _override_db():
        yield fake_db

    app.dependency_overrides.clear()
    app.dependency_overrides[deps.get_db] = _override_db

    monkeypatch.setattr(generate_project_task, "apply_async", lambda *_, **__: SimpleNamespace(id="task-123"))

    client = TestClient(app)
    response = client.post(
        "/api/v1/generate",
        json={
            "project_name": "my-crm",
            "prompt": "Build a CRM app with dashboard and reports",
            "backend": "springboot",
            "frontend": "angular",
            "features": ["dashboard", "reports"],
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert "job_id" in body
    assert body["cache_hit"] is False
    assert body["fingerprint"]

    app.dependency_overrides.clear()


def test_generate_uses_cache() -> None:
    cached = SimpleNamespace(fingerprint="abc", project_id=uuid4())
    fake_db = _FakeSession(cached=cached)

    def _override_db():
        yield fake_db

    app.dependency_overrides.clear()
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.post(
        "/api/v1/generate",
        json={
            "project_name": "my-crm",
            "prompt": "Build a CRM app with dashboard and reports",
            "backend": "springboot",
            "frontend": "angular",
            "features": ["dashboard", "reports"],
        },
    )

    assert response.status_code == 202
    assert response.json()["cache_hit"] is True
    assert response.json()["cached_project_id"] is not None

    app.dependency_overrides.clear()


def test_generate_validation_error() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/generate",
        json={
            "project_name": "x",
            "prompt": "short",
            "backend": "springboot",
            "frontend": "angular",
            "features": [],
        },
    )
    assert response.status_code == 422


def test_generate_minimal_payload_autobuilds_prompt(monkeypatch) -> None:
    fake_db = _FakeSession(cached=None)

    def _override_db():
        yield fake_db

    app.dependency_overrides.clear()
    app.dependency_overrides[deps.get_db] = _override_db

    monkeypatch.setattr(generate_project_task, "apply_async", lambda *_, **__: SimpleNamespace(id="task-456"))
    monkeypatch.setattr(generate_route, "_discover_website_like", lambda *_: "https://example.com")

    client = TestClient(app)
    response = client.post(
        "/api/v1/generate",
        json={
            "project_name": "hotel-management-system",
        },
    )

    assert response.status_code == 202
    assert fake_db.created_jobs
    created_job = fake_db.created_jobs[-1]
    assert "hotel-management-system" in created_job.prompt
    assert created_job.website_like == "https://example.com"

    app.dependency_overrides.clear()


def test_angular_package_json_does_not_use_invalid_http_dependency() -> None:
    from app.services.templates.jinja_renderer import JinjaRenderer

    renderer = JinjaRenderer()
    package_json = renderer.render("angular/package.json.j2", {"project_name": "my-angular-app"})

    assert "\"@angular/common/http\"" not in package_json
    assert "\"@angular/common\"" in package_json


def test_frontend_nginx_conf_is_required() -> None:
    from app.core.constants import ALLOWED_GENERATED_EXTENSIONS, MANDATORY_OUTPUT_FILES

    assert ".conf" in ALLOWED_GENERATED_EXTENSIONS
    assert "frontend/nginx.conf" in MANDATORY_OUTPUT_FILES

