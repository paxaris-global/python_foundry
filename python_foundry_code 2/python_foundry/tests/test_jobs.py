from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import deps
from app.main import app
from app.models.job import Job


class _FakeJob:
    def __init__(self) -> None:
        self.id = uuid4()
        self.status = SimpleNamespace(value="completed")
        self.progress = 100
        self.current_stage = "finalize_job_status"
        self.error = None
        self.trace_id = "trace123"
        self.cache_hit = False
        self.project_id = uuid4()
        self.stage_timings = {"parse_prompt": 0.1}
        self.result_data = {"zip_path": "generated.zip"}
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class _FakeQuery:
    def __init__(self, job: _FakeJob):
        self.job = job

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.job


class _FakeSession:
    def __init__(self):
        self.job = _FakeJob()

    def query(self, model):
        if model is Job:
            return _FakeQuery(self.job)
        return _FakeQuery(None)


def test_get_job() -> None:
    fake_db = _FakeSession()

    def _override_db():
        yield fake_db

    app.dependency_overrides.clear()
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.get(f"/api/v1/jobs/{uuid4()}")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["current_stage"] == "finalize_job_status"

    app.dependency_overrides.clear()
