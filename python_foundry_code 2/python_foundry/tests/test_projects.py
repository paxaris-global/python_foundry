from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import deps
from app.main import app
from app.models.project import Project


class _FakeQuery:
    def __init__(self, value):
        self.value = value

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.value


class _FakeSession:
    def __init__(self, project):
        self.project = project

    def query(self, model):
        if model is Project:
            return _FakeQuery(self.project)
        return _FakeQuery(None)


def test_get_project_metadata() -> None:
    with TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "demo.zip"
        zip_path.write_bytes(b"zip")

        project = type("ProjectObj", (), {})()
        project.id = uuid4()
        project.name = "demo"
        project.description = "demo desc"
        project.backend_stack = "springboot"
        project.frontend_stack = "angular"
        project.domain = "crm"
        project.blueprint_used = "crm"
        project.project_path = str(Path(tmp) / "proj")
        project.zip_path = str(zip_path)
        project.manifest = {"k": "v"}
        project.rag_summary = {"retrieved_chunks": 0}
        project.cache_info = {"hit": False}
        project.generated_files = ["README.md"]
        project.validation_report = {"valid": True}
        project.created_at = datetime.now(timezone.utc)
        project.updated_at = datetime.now(timezone.utc)

        fake_db = _FakeSession(project)

        def _override_db():
            yield fake_db

        app.dependency_overrides.clear()
        app.dependency_overrides[deps.get_db] = _override_db

        client = TestClient(app)
        response = client.get(f"/api/v1/projects/{uuid4()}")

        assert response.status_code == 200
        assert response.json()["domain"] == "crm"

        app.dependency_overrides.clear()
