from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import deps
from app.main import app
from app.models.job import Job
from app.models.prompt_artifact import PromptArtifact


class _FakeQuery:
    def __init__(self, model, row_map):
        self.model = model
        self.row_map = row_map

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.row_map.get(self.model)


class _FakeSession:
    def __init__(self, job_row, artifact_row):
        self.row_map = {Job: job_row, PromptArtifact: artifact_row}

    def query(self, model):
        return _FakeQuery(model, self.row_map)


def test_get_final_prompt() -> None:
    job_id = uuid4()
    project_id = uuid4()

    job_row = SimpleNamespace(id=job_id)
    artifact_row = SimpleNamespace(
        job_id=job_id,
        project_id=project_id,
        raw_user_prompt="Build an inventory system",
        parsed_prompt={"summary": "inventory system"},
        parsed_prompt_summary={"summary": "inventory system", "token_count": 2},
        expanded_features=["dashboard", "reports"],
        execution_mode="generate",
        rag_summary={"retrieved_chunks": 2},
        rag_context_summary={"retrieved_chunks": 2, "top_score": 0.64},
        web_discovery_summary={"features": ["catalog"]},
        adaptation_context_summary={},
        trusted_sources=[{"url": "https://example.com", "trust_score": 0.9}],
        pre_final_prompt="draft enriched prompt",
        final_enriched_prompt="final enriched prompt content",
        artifact_text_path="generated/_meta/final_enriched_prompt.txt",
        artifact_json_path="generated/_meta/final_enriched_prompt.json",
        created_at=datetime.now(timezone.utc),
    )

    fake_db = _FakeSession(job_row=job_row, artifact_row=artifact_row)

    def _override_db():
        yield fake_db

    app.dependency_overrides.clear()
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.get(f"/api/v1/jobs/{job_id}/final-prompt")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == str(job_id)
    assert body["project_id"] == str(project_id)
    assert body["execution_mode"] == "generate"
    assert body["parsed_prompt_summary"]["summary"] == "inventory system"
    assert body["rag_context_summary"]["retrieved_chunks"] == 2
    assert body["adaptation_context_summary"] == {}
    assert body["pre_final_prompt"] == "draft enriched prompt"
    assert "final_enriched_prompt" in body

    app.dependency_overrides.clear()
