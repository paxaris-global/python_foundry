from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from uuid import uuid4

from app.core.exceptions import ValidationException
from app.services.generation.orchestrator import GenerationOrchestrator
from app.services.generation.prompt_debugger import PromptDebugger
from app.services.web_discovery.discovery_decider import DiscoveryDecider
from app.services.web_discovery.search_client import SearchClient


class _FakeQuery:
    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return None


class _FakeDB:
    def query(self, *_args, **_kwargs):
        return _FakeQuery()

    def add(self, *_args, **_kwargs):
        return None

    def commit(self):
        return None

    def refresh(self, *_args, **_kwargs):
        return None


def test_stage_order_contract() -> None:
    stages = GenerationOrchestrator.STAGES

    assert stages.index("retrieve_rag_context") < stages.index("build_project_spec")
    assert stages.index("create_project_skeleton") < stages.index("generate_backend_code")
    assert stages.index("validate_structure") < stages.index("repair_if_needed")
    assert stages.index("repair_if_needed") < stages.index("revalidate_after_repair")
    assert stages.index("revalidate_after_repair") < stages.index("package_to_zip")


def test_finalize_requires_critical_artifacts() -> None:
    orchestrator = GenerationOrchestrator(db=_FakeDB())

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        zip_path = root / "artifact.zip"
        zip_path.write_bytes(b"zip")

        try:
            orchestrator.finalize_job_status(
                result={"zip_path": str(zip_path)},
                project_root=root,
                artifact=None,
                cache_result={"stored": True},
                indexing_result={"attempted": True},
            )
            assert False, "Expected ValidationException for missing mandatory artifacts"
        except ValidationException as exc:
            assert "Missing critical artifact" in str(exc)


def test_discovery_decision_without_website_like() -> None:
    decision = DiscoveryDecider().decide(
        prompt="Build crm management system",
        domain="crm",
        website_like=None,
        strong_reusable_project=False,
        rag_confidence=0.2,
        adaptation_score=0.3,
    )

    assert decision["should_run"] is True
    assert "website_like_provided" not in decision["reasons"]
    assert "low_rag_confidence" in decision["reasons"]


def test_search_client_fallback_provider(monkeypatch) -> None:
    client = SearchClient()
    client.settings.search_provider = "serpapi"
    client.settings.fallback_search_provider = "duckduckgo"

    calls: list[str] = []

    def _provider(provider: str, query: str, limit: int) -> list[dict]:
        del query, limit
        calls.append(provider)
        if provider == "serpapi":
            raise RuntimeError("primary failed")
        return [{"url": "https://example.com", "title": "fallback", "snippet": "ok"}]

    monkeypatch.setattr(client, "_search_via_provider", _provider)
    monkeypatch.setattr(client, "_search_github_repositories", lambda *_args, **_kwargs: [])

    results = client.search("test query", max_results=3)

    assert calls == ["serpapi", "duckduckgo"]
    assert len(results) == 1


def test_search_client_primary_provider(monkeypatch) -> None:
    client = SearchClient()
    client.settings.search_provider = "serpapi"
    client.settings.fallback_search_provider = "duckduckgo"

    calls: list[str] = []

    def _provider(provider: str, query: str, limit: int) -> list[dict]:
        del query, limit
        calls.append(provider)
        if provider == "serpapi":
            return [{"url": "https://primary.dev", "title": "primary", "snippet": "ok"}]
        return [{"url": "https://fallback.dev", "title": "fallback", "snippet": "ok"}]

    monkeypatch.setattr(client, "_search_via_provider", _provider)
    monkeypatch.setattr(client, "_search_github_repositories", lambda *_args, **_kwargs: [])

    results = client.search("test query", max_results=3)

    assert calls == ["serpapi"]
    assert results[0]["url"] == "https://primary.dev"


def test_prompt_debugger_writes_meta_artifacts() -> None:
    debugger = PromptDebugger(_FakeDB())

    artifact = SimpleNamespace(
        job_id=uuid4(),
        project_id=None,
        raw_user_prompt="Build an app",
        parsed_prompt={"summary": "Build an app"},
        parsed_prompt_summary={"summary": "Build an app", "token_count": 3},
        expanded_features=["dashboard"],
        execution_mode="generate",
        rag_summary={"retrieved_chunks": 0},
        rag_context_summary={"retrieved_chunks": 0, "top_score": 0.0},
        web_discovery_summary={"used": False},
        adaptation_context_summary={},
        trusted_sources=[],
        pre_final_prompt="draft",
        final_enriched_prompt="final",
        system_prompt="system",
        artifact_text_path=None,
        artifact_json_path=None,
    )

    with TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        updated = debugger.write_project_prompt_files(project_root, artifact, uuid4())

        assert updated.artifact_text_path is not None
        assert updated.artifact_json_path is not None
        assert Path(updated.artifact_text_path).exists()
        assert Path(updated.artifact_json_path).exists()
