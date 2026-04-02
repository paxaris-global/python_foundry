"""Shared test fixtures used across the test suite."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.main import app
from app.models.generation_cache import GenerationCache
from app.models.job import Job, JobStatus
from app.models.project import Project
from app.models.prompt_artifact import PromptArtifact


# ---------------------------------------------------------------------------
# Reusable fake DB primitives
# ---------------------------------------------------------------------------

class FakeQuery:
    """A chainable query stub that always returns *result* from .first()."""

    def __init__(self, result=None):
        self._result = result

    def filter(self, *_a, **_kw):
        return self

    def order_by(self, *_a, **_kw):
        return self

    def limit(self, *_a, **_kw):
        return self

    def all(self):
        if self._result is None:
            return []
        return self._result if isinstance(self._result, list) else [self._result]

    def first(self):
        if isinstance(self._result, list):
            return self._result[0] if self._result else None
        return self._result


class FakeSession:
    """In-memory session double.

    Pass *row_map* as ``{ModelClass: row_or_list}`` so that
    ``db.query(ModelClass)`` returns the right stub.
    """

    def __init__(self, row_map: dict | None = None):
        self._row_map = row_map or {}
        self.added: list = []
        self.committed = 0

    def query(self, model):
        return FakeQuery(self._row_map.get(model))

    def add(self, obj):
        if isinstance(obj, Job) and not getattr(obj, "id", None):
            obj.id = uuid4()
        self.added.append(obj)

    def commit(self):
        self.committed += 1

    def refresh(self, _obj):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_job(**overrides) -> SimpleNamespace:
    defaults = dict(
        id=uuid4(),
        project_name="test-project",
        prompt="Build a test app with dashboard and reports",
        backend="springboot",
        frontend="angular",
        features=["dashboard", "reports"],
        website_like=None,
        mode_preference="auto",
        mode_selected=None,
        fingerprint="abc123",
        status=SimpleNamespace(value="completed"),
        progress=100,
        current_stage="finalize_job_status",
        error=None,
        trace_id="trace-xyz",
        cache_hit=False,
        stage_timings={"parse_prompt": 0.01},
        result_data={"project_id": str(uuid4())},
        celery_task_id="celery-task-1",
        project_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_project(tmp_path: Path, **overrides) -> SimpleNamespace:
    zip_path = tmp_path / "project.zip"
    zip_path.write_bytes(b"PK\x03\x04fake-zip")
    proj_dir = tmp_path / "project"
    proj_dir.mkdir(exist_ok=True)

    defaults = dict(
        id=uuid4(),
        name="test-project",
        description="A test project",
        backend_stack="springboot",
        frontend_stack="angular",
        execution_mode="generate",
        domain="crm",
        blueprint_used="clean_scaffold",
        project_path=str(proj_dir),
        zip_path=str(zip_path),
        manifest={"project_name": "test-project", "features": ["dashboard"]},
        rag_summary={"retrieved_chunks": 0, "top_score": 0.0},
        cache_info={"hit": False, "fingerprint": "abc123"},
        final_prompt_text_path=None,
        final_prompt_json_path=None,
        generated_files=["README.md", "backend/pom.xml"],
        validation_report={"valid": True},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_prompt_artifact(**overrides) -> SimpleNamespace:
    defaults = dict(
        id=uuid4(),
        job_id=uuid4(),
        project_id=uuid4(),
        raw_user_prompt="Build a CRM app",
        parsed_prompt={"summary": "CRM app", "tokens": ["crm", "app"], "entities": ["customer"], "feature_hints": ["dashboard"]},
        parsed_prompt_summary={"summary": "CRM app", "token_count": 2, "entities": ["customer"], "feature_hints": ["dashboard"]},
        expanded_features=["dashboard", "reports"],
        execution_mode="generate",
        rag_summary={"retrieved_chunks": 3, "top_score": 0.72},
        rag_context_summary={"retrieved_chunks": 3, "top_score": 0.72, "sources": []},
        web_discovery_summary={"used": True, "reasons": ["low_rag_confidence"]},
        adaptation_context_summary={},
        trusted_sources=[{"url": "https://example.com", "trust_score": 0.9}],
        system_prompt="You are a senior software architect.",
        pre_final_prompt="draft prompt",
        final_enriched_prompt="final enriched prompt content",
        artifact_text_path="/tmp/meta/final_enriched_prompt.txt",
        artifact_json_path="/tmp/meta/final_enriched_prompt.json",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_cache_entry(**overrides) -> SimpleNamespace:
    defaults = dict(
        id=uuid4(),
        fingerprint="sha256abc",
        project_id=uuid4(),
        hit_count=5,
        request_payload={"prompt": "Build CRM", "backend": "springboot"},
        cache_metadata={"domain": "crm", "execution_mode": "generate"},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """Return a fresh TestClient and clear overrides after use."""
    app.dependency_overrides.clear()
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def override_db():
    """Return a callable that installs a FakeSession as the DB dependency."""
    def _install(fake_db):
        def _gen():
            yield fake_db
        app.dependency_overrides[deps.get_db] = _gen
    return _install
