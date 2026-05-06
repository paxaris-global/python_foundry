"""
Comprehensive test suite for the AI Code Generation Platform.

Covers:
  - All API endpoints (happy-path and error cases)
  - Core service logic (prompt parsing, domain classification, feature expansion,
    fingerprinting, caching, project similarity, discovery decider, merge engine,
    project differ, prompt enricher)
  - Database model field contracts
  - Background task execution flow
  - Edge cases (invalid input, missing resources, empty data, cache misses)
"""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.main import app
from app.models.generation_cache import GenerationCache
from app.models.job import Job, JobStatus
from app.models.project import Project
from app.models.prompt_artifact import PromptArtifact

from tests.conftest import (
    FakeQuery,
    FakeSession,
    make_cache_entry,
    make_job,
    make_project,
    make_prompt_artifact,
)


# ===================================================================
# 1. HEALTH ENDPOINT
# ===================================================================

class TestHealthEndpoint:
    def test_health_returns_service_name(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["service"] == "ai-codegen-platform"

    def test_health_reports_dependency_keys(self, client: TestClient):
        resp = client.get("/api/v1/health")
        deps_keys = set(resp.json()["dependencies"].keys())
        assert deps_keys == {"db", "redis", "chroma"}

    def test_health_status_is_ok_or_degraded(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert resp.json()["status"] in {"ok", "degraded"}


# ===================================================================
# 2. GENERATE ENDPOINT
# ===================================================================

class TestGenerateEndpoint:
    def test_create_generation_job_returns_202(self, client, override_db, monkeypatch):
        from app.tasks.generation_tasks import generate_project_task

        override_db(FakeSession())
        monkeypatch.setattr(
            generate_project_task, "apply_async",
            lambda *a, **kw: SimpleNamespace(id="task-001"),
        )

        resp = client.post("/api/v1/generate", json={
            "project_name": "my-crm",
            "prompt": "Build a CRM app with dashboard and reports",
            "backend": "springboot",
            "frontend": "angular",
            "features": ["dashboard", "reports"],
        })
        assert resp.status_code == 202
        body = resp.json()
        assert "job_id" in body
        assert body["status"] == "pending"
        assert body["cache_hit"] is False
        assert body["fingerprint"]  # non-empty string

    def test_cache_hit_returns_completed_immediately(self, client, override_db, tmp_path):
        project_id = uuid4()
        proj_dir = tmp_path / "cached-proj"
        proj_dir.mkdir()

        cached = SimpleNamespace(fingerprint="fp1", project_id=project_id)
        cached_project = SimpleNamespace(
            id=project_id,
            project_path=str(proj_dir),
            zip_path=None,
        )
        db = FakeSession({GenerationCache: cached, Project: cached_project})
        override_db(db)

        resp = client.post("/api/v1/generate", json={
            "project_name": "cached-crm",
            "prompt": "Build a CRM app with dashboard and reports",
        })
        assert resp.status_code == 202
        body = resp.json()
        assert body["cache_hit"] is True
        assert body["cached_project_id"] == str(project_id)
        assert body["mode_selected"] == "reuse"
        assert body["status"] == "completed"

    def test_project_name_too_short_returns_422(self, client):
        resp = client.post("/api/v1/generate", json={
            "project_name": "x",
            "prompt": "Build an app with auth",
        })
        assert resp.status_code == 422

    def test_prompt_too_short_returns_422(self, client):
        resp = client.post("/api/v1/generate", json={
            "project_name": "valid-name",
            "prompt": "short",
        })
        assert resp.status_code == 422

    def test_unsupported_backend_returns_422(self, client):
        resp = client.post("/api/v1/generate", json={
            "project_name": "valid-name",
            "prompt": "Build an app with dashboard",
            "backend": "django",
        })
        assert resp.status_code == 422

    def test_unsupported_frontend_returns_422(self, client):
        resp = client.post("/api/v1/generate", json={
            "project_name": "valid-name",
            "prompt": "Build an app with dashboard",
            "frontend": "react",
        })
        assert resp.status_code == 422

    def test_unsupported_mode_preference_returns_422(self, client):
        resp = client.post("/api/v1/generate", json={
            "project_name": "valid-name",
            "prompt": "Build an app with dashboard",
            "mode_preference": "invalid_mode",
        })
        assert resp.status_code == 422

    def test_missing_project_name_returns_422(self, client):
        resp = client.post("/api/v1/generate", json={
            "prompt": "Build an app with dashboard and reports",
        })
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client):
        resp = client.post("/api/v1/generate", json={})
        assert resp.status_code == 422

    def test_minimal_payload_auto_builds_prompt(self, client, override_db, monkeypatch):
        from app.api.v1.routes import generate as gen_mod
        from app.tasks.generation_tasks import generate_project_task

        override_db(FakeSession())
        monkeypatch.setattr(generate_project_task, "apply_async", lambda *a, **kw: SimpleNamespace(id="t1"))
        monkeypatch.setattr(gen_mod, "_discover_website_like", lambda *_: None)

        resp = client.post("/api/v1/generate", json={"project_name": "hotel-app"})
        assert resp.status_code == 202

    def test_generate_with_website_like(self, client, override_db, monkeypatch):
        from app.tasks.generation_tasks import generate_project_task

        db = FakeSession()
        override_db(db)
        monkeypatch.setattr(generate_project_task, "apply_async", lambda *a, **kw: SimpleNamespace(id="t2"))

        resp = client.post("/api/v1/generate", json={
            "project_name": "booking-app",
            "prompt": "Build a hotel booking system with reservations",
            "website_like": "https://booking.com",
        })
        assert resp.status_code == 202
        # The job should store the website_like
        added_jobs = [o for o in db.added if isinstance(o, Job)]
        assert len(added_jobs) == 1
        assert added_jobs[0].website_like == "https://booking.com"


# ===================================================================
# 3. JOBS ENDPOINT
# ===================================================================

class TestJobsEndpoint:
    def test_get_job_returns_full_response(self, client, override_db):
        job = make_job()
        override_db(FakeSession({Job: job}))

        resp = client.get(f"/api/v1/jobs/{uuid4()}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["progress"] == 100
        assert body["current_stage"] == "finalize_job_status"
        assert body["trace_id"] == "trace-xyz"
        assert "stage_timings" in body
        assert "created_at" in body

    def test_get_job_not_found(self, client, override_db):
        override_db(FakeSession())
        resp = client.get(f"/api/v1/jobs/{uuid4()}")
        assert resp.status_code == 404

    def test_get_job_invalid_uuid(self, client, override_db):
        override_db(FakeSession())
        resp = client.get("/api/v1/jobs/not-a-uuid")
        assert resp.status_code == 422

    def test_get_final_prompt(self, client, override_db):
        job_id = uuid4()
        job = make_job(id=job_id)
        artifact = make_prompt_artifact(job_id=job_id)
        override_db(FakeSession({Job: job, PromptArtifact: artifact}))

        resp = client.get(f"/api/v1/jobs/{job_id}/final-prompt")
        assert resp.status_code == 200
        body = resp.json()
        assert body["job_id"] == str(job_id)
        assert body["execution_mode"] == "generate"
        assert "final_enriched_prompt" in body
        assert "parsed_prompt_summary" in body
        assert "web_discovery_summary" in body
        assert "trusted_sources" in body

    def test_get_final_prompt_no_artifact(self, client, override_db):
        job = make_job()
        override_db(FakeSession({Job: job}))
        resp = client.get(f"/api/v1/jobs/{job.id}/final-prompt")
        assert resp.status_code == 404

    def test_get_final_prompt_no_job(self, client, override_db):
        override_db(FakeSession())
        resp = client.get(f"/api/v1/jobs/{uuid4()}/final-prompt")
        assert resp.status_code == 404


# ===================================================================
# 4. PROJECTS ENDPOINT
# ===================================================================

class TestProjectsEndpoint:
    def test_get_project_metadata(self, client, override_db, tmp_path):
        project = make_project(tmp_path)
        override_db(FakeSession({Project: project}))

        resp = client.get(f"/api/v1/projects/{uuid4()}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "test-project"
        assert body["backend_stack"] == "springboot"
        assert body["frontend_stack"] == "angular"
        assert body["domain"] == "crm"
        assert "manifest" in body
        assert "generated_files" in body
        assert "validation_report" in body

    def test_get_project_not_found(self, client, override_db):
        override_db(FakeSession())
        resp = client.get(f"/api/v1/projects/{uuid4()}")
        assert resp.status_code == 404

    def test_get_project_invalid_uuid(self, client, override_db):
        override_db(FakeSession())
        resp = client.get("/api/v1/projects/bad-id")
        assert resp.status_code == 422

    def test_download_project_zip(self, client, override_db, tmp_path):
        project = make_project(tmp_path)
        override_db(FakeSession({Project: project}))

        resp = client.get(f"/api/v1/projects/{uuid4()}/download")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        assert "test-project.zip" in resp.headers.get("content-disposition", "")

    def test_download_missing_zip_rebuilds(self, client, override_db, tmp_path, monkeypatch):
        from app.services.generation.zip_packager import ZipPackager

        project = make_project(tmp_path)
        # Remove zip so the endpoint tries to rebuild
        Path(project.zip_path).unlink()
        override_db(FakeSession({Project: project}))

        # Mock the packager to create the file
        def fake_package(self, src, dest):
            Path(dest).write_bytes(b"PK\x03\x04rebuilt")
            return str(dest)

        monkeypatch.setattr(ZipPackager, "package_to_zip", fake_package)

        resp = client.get(f"/api/v1/projects/{uuid4()}/download")
        assert resp.status_code == 200

    def test_download_missing_zip_and_dir_returns_404(self, client, override_db, tmp_path):
        project = make_project(tmp_path)
        Path(project.zip_path).unlink()
        # Remove project dir too
        import shutil
        shutil.rmtree(project.project_path)
        override_db(FakeSession({Project: project}))

        resp = client.get(f"/api/v1/projects/{uuid4()}/download")
        assert resp.status_code == 404


# ===================================================================
# 5. CACHE ENDPOINT
# ===================================================================

class TestCacheEndpoint:
    def test_get_cache_entry(self, client, override_db):
        entry = make_cache_entry(fingerprint="fp-abc")
        override_db(FakeSession({GenerationCache: entry}))

        resp = client.get("/api/v1/cache/fp-abc")
        assert resp.status_code == 200
        body = resp.json()
        assert body["fingerprint"] == "fp-abc"
        assert body["hit_count"] == 5
        assert "request_payload" in body
        assert "cache_metadata" in body

    def test_get_cache_entry_not_found(self, client, override_db):
        override_db(FakeSession())
        resp = client.get("/api/v1/cache/nonexistent")
        assert resp.status_code == 404


# ===================================================================
# 6. RAG ENDPOINTS
# ===================================================================

class TestRAGEndpoints:
    def test_rag_search(self, client, monkeypatch):
        from app.services.rag.retriever import RAGRetriever

        monkeypatch.setattr(
            RAGRetriever, "search",
            lambda self, query, top_k=5, min_similarity=0.0: [
                {"content": "auth code", "score": 0.85, "metadata": {"file_path": "auth.java"}},
            ],
        )

        resp = client.post("/api/v1/rag/search", json={
            "query": "Spring Boot auth",
            "top_k": 5,
            "min_similarity": 0.3,
        })
        assert resp.status_code == 200
        assert len(resp.json()["results"]) == 1
        assert resp.json()["results"][0]["score"] == 0.85

    def test_rag_search_empty_results(self, client, monkeypatch):
        from app.services.rag.retriever import RAGRetriever

        monkeypatch.setattr(RAGRetriever, "search", lambda self, **kw: [])

        resp = client.post("/api/v1/rag/search", json={"query": "obscure query xyz"})
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_rag_search_query_too_short(self, client):
        resp = client.post("/api/v1/rag/search", json={"query": "ab"})
        assert resp.status_code == 422

    def test_rag_search_top_k_bounds(self, client):
        resp = client.post("/api/v1/rag/search", json={"query": "valid query", "top_k": 0})
        assert resp.status_code == 422
        resp2 = client.post("/api/v1/rag/search", json={"query": "valid query", "top_k": 100})
        assert resp2.status_code == 422

    def test_rag_index(self, client, override_db, monkeypatch):
        from app.services.rag.indexer import RAGIndexer

        override_db(FakeSession())
        monkeypatch.setattr(
            RAGIndexer, "index_paths",
            lambda self, paths, module_type=None, tags=None, source_type="repo": {
                "indexed_files": 3, "indexed_chunks": 12,
            },
        )

        resp = client.post("/api/v1/rag/index", json={
            "paths": ["/some/path"],
            "module_type": "crm",
            "tags": ["auth", "dashboard"],
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["indexed_files"] == 3

    def test_rag_index_empty_paths_returns_422(self, client):
        resp = client.post("/api/v1/rag/index", json={"paths": []})
        assert resp.status_code == 422


# ===================================================================
# 7. WEB DISCOVERY ENDPOINT
# ===================================================================

class TestWebDiscoveryEndpoint:
    def test_preview(self, client, override_db, monkeypatch):
        from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator

        override_db(FakeSession())
        monkeypatch.setattr(
            WebDiscoveryOrchestrator, "discover",
            lambda self, query, job_id=None, module_type="general", tags=None: {
                "trusted_results": [{"url": "https://angular.dev", "title": "Angular"}],
                "extracted_features": ["routing"],
                "extracted_entities": ["user"],
                "extracted_routes": ["/api/users"],
                "extracted_components": ["NavBar"],
                "backend_patterns": ["rest_controller"],
                "suggested_architecture": ["modular"],
            },
        )

        resp = client.post("/api/v1/web-discovery/preview", json={
            "prompt": "Build a hospital management app with patient records",
            "website_like": "https://angular.dev",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["extracted_features"] == ["routing"]
        assert body["backend_patterns"] == ["rest_controller"]
        assert "draft_enriched_prompt" in body
        assert "query" in body

    def test_preview_prompt_too_short(self, client, override_db):
        override_db(FakeSession())
        resp = client.post("/api/v1/web-discovery/preview", json={"prompt": "hi"})
        assert resp.status_code == 422


# ===================================================================
# 8. PROMPT PARSER
# ===================================================================

class TestPromptParser:
    def test_extracts_feature_hints(self):
        from app.services.generation.prompt_parser import PromptParser

        result = PromptParser().parse_prompt(
            "Build a CRM with auth, dashboard, and reports"
        )
        assert "auth" in result["feature_hints"]
        assert "dashboard" in result["feature_hints"]
        assert "reports" in result["feature_hints"]

    def test_extracts_entities(self):
        from app.services.generation.prompt_parser import PromptParser

        result = PromptParser().parse_prompt(
            "Manage customer orders and invoices"
        )
        assert "customer" in result["entities"]
        assert "order" in result["entities"]
        assert "invoice" in result["entities"]

    def test_summary_is_trimmed_prompt(self):
        from app.services.generation.prompt_parser import PromptParser

        prompt = "  Build something  "
        result = PromptParser().parse_prompt(prompt)
        assert result["summary"] == "Build something"

    def test_tokens_are_limited(self):
        from app.services.generation.prompt_parser import PromptParser

        long_prompt = " ".join(f"word{i}" for i in range(200))
        result = PromptParser().parse_prompt(long_prompt)
        assert len(result["tokens"]) <= 120

    def test_no_features_found(self):
        from app.services.generation.prompt_parser import PromptParser

        result = PromptParser().parse_prompt("Build something generic without known keywords")
        assert result["feature_hints"] == []

    def test_no_entities_found(self):
        from app.services.generation.prompt_parser import PromptParser

        result = PromptParser().parse_prompt("Build a simple hello world app")
        assert result["entities"] == []

    def test_extracts_prompt_requirements(self):
        from app.services.generation.prompt_parser import PromptParser

        result = PromptParser().parse_prompt(
            "Build a modern ecommerce app with login, checkout, a hero section, pricing section, and charts"
        )
        assert "modern" in result["design_hints"]
        assert "login" in result["pages"]
        assert "hero" in result["sections"]
        assert "chart" in result["required_components"]


# ===================================================================
# 9. DOMAIN CLASSIFIER
# ===================================================================

class TestDomainClassifier:
    def test_classifies_hotel_management(self):
        from app.services.intelligence.domain_classifier import DomainClassifier

        assert DomainClassifier().classify({"summary": "Build a hotel booking system"}) == "hotel_management"

    def test_classifies_ecommerce(self):
        from app.services.intelligence.domain_classifier import DomainClassifier

        assert DomainClassifier().classify({"summary": "Build an ecommerce platform"}) == "ecommerce"

    def test_classifies_crm(self):
        from app.services.intelligence.domain_classifier import DomainClassifier

        assert DomainClassifier().classify({"summary": "Build a CRM for sales pipeline"}) == "crm"

    def test_classifies_hospital(self):
        from app.services.intelligence.domain_classifier import DomainClassifier

        assert DomainClassifier().classify({"summary": "Build a hospital patient management"}) == "hospital_management"

    def test_classifies_inventory(self):
        from app.services.intelligence.domain_classifier import DomainClassifier

        assert DomainClassifier().classify({"summary": "Build an inventory warehouse system"}) == "inventory_management"

    def test_defaults_to_general(self):
        from app.services.intelligence.domain_classifier import DomainClassifier

        assert DomainClassifier().classify({"summary": "Build something"}) == "general"

    def test_empty_summary_returns_general(self):
        from app.services.intelligence.domain_classifier import DomainClassifier

        assert DomainClassifier().classify({"summary": ""}) == "general"
        assert DomainClassifier().classify({}) == "general"


# ===================================================================
# 10. FEATURE EXPANDER
# ===================================================================

class TestFeatureExpander:
    def test_merges_user_hints_and_blueprint_features(self):
        from app.services.intelligence.feature_expander import FeatureExpander

        result = FeatureExpander().expand(
            parsed_prompt={"feature_hints": ["auth"]},
            features=["dashboard"],
            blueprint={"default_features": ["reports"]},
        )
        assert "auth" in result
        assert "dashboard" in result
        assert "reports" in result

    def test_deduplicates_and_sorts(self):
        from app.services.intelligence.feature_expander import FeatureExpander

        result = FeatureExpander().expand(
            parsed_prompt={"feature_hints": ["auth", "dashboard"]},
            features=["auth", "Dashboard"],
            blueprint={"default_features": ["auth"]},
        )
        assert result == sorted(set(result))

    def test_handles_empty_inputs(self):
        from app.services.intelligence.feature_expander import FeatureExpander

        result = FeatureExpander().expand(
            parsed_prompt={},
            features=[],
            blueprint={},
        )
        assert result == []


# ===================================================================
# 11. FINGERPRINT SERVICE
# ===================================================================

class TestFingerprintService:
    def test_deterministic(self):
        from app.services.caching.fingerprint import FingerprintService

        svc = FingerprintService()
        fp1 = svc.compute("Build CRM", "springboot", "angular", ["auth", "dashboard"])
        fp2 = svc.compute("Build CRM", "springboot", "angular", ["auth", "dashboard"])
        assert fp1 == fp2

    def test_feature_order_independent(self):
        from app.services.caching.fingerprint import FingerprintService

        svc = FingerprintService()
        fp1 = svc.compute("Build CRM", "springboot", "angular", ["auth", "dashboard"])
        fp2 = svc.compute("Build CRM", "springboot", "angular", ["dashboard", "auth"])
        assert fp1 == fp2

    def test_different_prompts_yield_different_fingerprints(self):
        from app.services.caching.fingerprint import FingerprintService

        svc = FingerprintService()
        fp1 = svc.compute("Build CRM app", "springboot", "angular", [])
        fp2 = svc.compute("Build hotel app", "springboot", "angular", [])
        assert fp1 != fp2

    def test_different_backends_yield_different_fingerprints(self):
        from app.services.caching.fingerprint import FingerprintService

        svc = FingerprintService()
        fp1 = svc.compute("Build app", "springboot", "angular", [])
        fp2 = svc.compute("Build app", "django", "angular", [])
        assert fp1 != fp2

    def test_case_insensitive(self):
        from app.services.caching.fingerprint import FingerprintService

        svc = FingerprintService()
        fp1 = svc.compute("Build CRM", "SpringBoot", "Angular", ["Auth"])
        fp2 = svc.compute("build crm", "springboot", "angular", ["auth"])
        assert fp1 == fp2

    def test_returns_hex_string(self):
        from app.services.caching.fingerprint import FingerprintService

        fp = FingerprintService().compute("test", "springboot", "angular", [])
        assert isinstance(fp, str)
        assert len(fp) == 64  # sha256 hex length
        int(fp, 16)  # must be valid hex


# ===================================================================
# 12. DISCOVERY DECIDER
# ===================================================================

class TestDiscoveryDecider:
    def test_runs_when_website_like_provided(self):
        from app.services.web_discovery.discovery_decider import DiscoveryDecider

        decision = DiscoveryDecider().decide(
            prompt="Build an app",
            domain="general",
            website_like="https://example.com",
            strong_reusable_project=True,
            rag_confidence=0.9,
            adaptation_score=0.9,
        )
        assert decision["should_run"] is True
        assert "website_like_provided" in decision["reasons"]

    def test_runs_when_low_rag_confidence(self):
        from app.services.web_discovery.discovery_decider import DiscoveryDecider

        decision = DiscoveryDecider().decide(
            prompt="Build an app",
            domain="general",
            website_like=None,
            strong_reusable_project=True,
            rag_confidence=0.1,
            adaptation_score=0.9,
        )
        assert decision["should_run"] is True
        assert "low_rag_confidence" in decision["reasons"]

    def test_runs_for_domain_keywords_in_prompt(self):
        from app.services.web_discovery.discovery_decider import DiscoveryDecider

        decision = DiscoveryDecider().decide(
            prompt="Build a hotel booking platform",
            domain="hotel_management",
            website_like=None,
            strong_reusable_project=True,
            rag_confidence=0.9,
            adaptation_score=0.9,
        )
        assert decision["should_run"] is True
        assert "domain_benefits_from_reference_discovery" in decision["reasons"]

    def test_runs_for_advanced_ui_keywords(self):
        from app.services.web_discovery.discovery_decider import DiscoveryDecider

        decision = DiscoveryDecider().decide(
            prompt="Build a production enterprise dashboard",
            domain="general",
            website_like=None,
            strong_reusable_project=True,
            rag_confidence=0.9,
            adaptation_score=0.9,
        )
        assert decision["should_run"] is True
        assert "advanced_ui_or_production_requested" in decision["reasons"]

    def test_no_reasons_means_no_run(self):
        from app.services.web_discovery.discovery_decider import DiscoveryDecider

        decision = DiscoveryDecider().decide(
            prompt="a very specific and long unique prompt that does not match any domain or ui keywords at all",
            domain="general",
            website_like=None,
            strong_reusable_project=True,
            rag_confidence=0.9,
            adaptation_score=0.0,
        )
        assert decision["should_run"] is False

    def test_weak_adaptation_candidate(self):
        from app.services.web_discovery.discovery_decider import DiscoveryDecider

        decision = DiscoveryDecider().decide(
            prompt="a very specific and long unique prompt that does not match any domain or ui keywords at all",
            domain="general",
            website_like=None,
            strong_reusable_project=True,
            rag_confidence=0.9,
            adaptation_score=0.5,
        )
        assert "weak_adaptation_candidate" in decision["reasons"]


# ===================================================================
# 13. MERGE ENGINE
# ===================================================================

class TestMergeEngine:
    def test_merges_all_contexts(self):
        from app.services.retrieval.merge_engine import MergeEngine

        result = MergeEngine().merge_contexts(
            base_enriched_prompt="base prompt",
            adaptation_context={"mode": "adapt"},
            web_discovery_summary={"used": True},
        )
        assert "base prompt" in result
        assert "AdaptationContext:" in result
        assert "WebDiscoverySummary:" in result

    def test_omits_empty_contexts(self):
        from app.services.retrieval.merge_engine import MergeEngine

        result = MergeEngine().merge_contexts(
            base_enriched_prompt="base only",
            adaptation_context=None,
            web_discovery_summary=None,
        )
        assert result == "base only"

    def test_omits_empty_dict_contexts(self):
        from app.services.retrieval.merge_engine import MergeEngine

        result = MergeEngine().merge_contexts(
            base_enriched_prompt="base",
            adaptation_context={},
            web_discovery_summary={},
        )
        # Empty dicts are falsy, so they should be omitted
        assert "AdaptationContext:" not in result


# ===================================================================
# 14. PROJECT DIFFER
# ===================================================================

class TestProjectDiffer:
    def test_diff_identifies_added_and_removed_features(self):
        from app.services.retrieval.project_differ import ProjectDiffer

        base = SimpleNamespace(
            manifest={"features": ["auth", "dashboard"]},
            description="old project",
        )
        result = ProjectDiffer().diff(
            base_project=base,
            prompt="Build new app",
            features=["dashboard", "reports"],
            website_like=None,
        )
        assert "reports" in result["add_features"]
        assert "auth" in result["remove_features"]
        assert "dashboard" in result["keep_features"]

    def test_diff_with_empty_base(self):
        from app.services.retrieval.project_differ import ProjectDiffer

        base = SimpleNamespace(manifest={}, description="")
        result = ProjectDiffer().diff(base, "Build app", ["auth"], None)
        assert "auth" in result["add_features"]
        assert result["remove_features"] == []


# ===================================================================
# 15. PROJECT SPEC BUILDER
# ===================================================================

class TestProjectSpecBuilder:
    def test_builds_correct_spec(self):
        from app.services.generation.project_spec_builder import ProjectSpecBuilder

        spec = ProjectSpecBuilder().build_project_spec(
            parsed_prompt={"summary": "CRM app", "feature_hints": ["auth"], "entities": ["customer"]},
            project_name="my-crm",
            backend="springboot",
            frontend="angular",
            features=["dashboard"],
        )
        assert spec["project_name"] == "my-crm"
        assert "auth" in spec["features"]
        assert "dashboard" in spec["features"]
        assert spec["backend"]["stack"] == "springboot"
        assert "Application" in spec["backend"]["application_class"]

    def test_entities_fallback(self):
        from app.services.generation.project_spec_builder import ProjectSpecBuilder

        spec = ProjectSpecBuilder().build_project_spec(
            parsed_prompt={"summary": "generic app"},
            project_name="app",
            backend="springboot",
            frontend="angular",
            features=[],
        )
        assert spec["entities"] == ["customer"]


# ===================================================================
# 16. API CONTRACT BUILDER
# ===================================================================

class TestAPIContractBuilder:
    def test_builds_openapi_contract(self):
        from app.services.generation.api_contract_builder import APIContractBuilder

        contract = APIContractBuilder().build_api_contract({"project_name": "demo"})
        assert contract["openapi"] == "3.0.3"
        assert "/api/v1/customers" in contract["paths"]


# ===================================================================
# 17. MANIFEST BUILDER
# ===================================================================

class TestManifestBuilder:
    def test_includes_mandatory_files(self):
        from app.services.generation.manifest_builder import ManifestBuilder

        manifest = ManifestBuilder().build_manifest(
            {"project_name": "demo", "domain": "crm", "backend": {"stack": "springboot"}, "frontend": {"stack": "angular"}, "features": ["auth"]},
            {"paths": {"/api/v1/customers": {}}},
        )
        assert "backend/pom.xml" in manifest["mandatory_files"]
        assert "frontend/package.json" in manifest["mandatory_files"]
        assert "_meta/final_enriched_prompt.txt" in manifest["mandatory_files"]


# ===================================================================
# 18. PROMPT ENRICHER
# ===================================================================

class TestPromptEnricher:
    def test_enriches_prompt_with_all_context(self):
        from app.services.intelligence.prompt_enricher import PromptEnricher

        result = PromptEnricher().enrich(
            original_prompt="Build CRM",
            project_spec={"project_name": "crm"},
            api_contract={"paths": {}},
            rag_context=[{"content": "code snippet", "score": 0.8, "metadata": {}}],
            fallback_context={"strategy": "scaffold"},
        )
        assert "Build CRM" in result
        assert "ProjectSpec:" in result
        assert "APIContract:" in result
        assert "RAGContext:" in result
        assert "FallbackContext:" in result


# ===================================================================
# 19. PROMPT DEBUGGER
# ===================================================================

class TestPromptDebugger:
    def test_writes_meta_files(self):
        from app.services.generation.prompt_debugger import PromptDebugger

        debugger = PromptDebugger(FakeSession())
        artifact = make_prompt_artifact(
            artifact_text_path=None,
            artifact_json_path=None,
            project_id=None,
        )

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            updated = debugger.write_project_prompt_files(project_root, artifact, uuid4())

            assert updated.artifact_text_path is not None
            assert updated.artifact_json_path is not None
            assert Path(updated.artifact_text_path).exists()
            assert Path(updated.artifact_json_path).exists()
            # Text file contains the final prompt
            assert Path(updated.artifact_text_path).read_text() == "final enriched prompt content"


# ===================================================================
# 20. GENERATION PIPELINE
# ===================================================================

class TestGenerationPipeline:
    def test_records_stage_timings(self):
        from app.services.generation.pipeline import GenerationPipeline

        pipeline = GenerationPipeline()
        result = pipeline.execute_stage("test_stage", lambda: 42, None, 50)
        assert result == 42
        assert "test_stage" in pipeline.stage_timings
        assert pipeline.stage_timings["test_stage"] >= 0

    def test_calls_progress_callback(self):
        from app.services.generation.pipeline import GenerationPipeline

        pipeline = GenerationPipeline()
        calls = []
        pipeline.execute_stage("s", lambda: None, lambda p, s: calls.append((p, s)), 75)
        assert calls == [(75, "s")]


# ===================================================================
# 21. VALIDATOR AND REPAIR ENGINE
# ===================================================================

class TestValidatorAndRepair:
    def test_build_report_all_ok(self):
        from app.services.generation.validator import ProjectValidator

        report = ProjectValidator().build_report(
            structure={"ok": True},
            required_files={"ok": True},
            non_empty_files={"ok": True},
            manifest_consistency={"ok": True},
            path_safety={"ok": True},
            prompt_requirements={"ok": True},
            syntax={"ok": True},
        )
        assert report["valid"] is True

    def test_build_report_detects_failure(self):
        from app.services.generation.validator import ProjectValidator

        report = ProjectValidator().build_report(
            structure={"ok": True},
            required_files={"ok": False, "missing_files": ["pom.xml"]},
            non_empty_files={"ok": True},
            manifest_consistency={"ok": True},
            path_safety={"ok": True},
            prompt_requirements={"ok": True},
            syntax={"ok": True},
        )
        assert report["valid"] is False

    def test_repair_restores_missing_files(self):
        from app.services.generation.repair_engine import RepairEngine

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            validation = {
                "required_files": {"missing_files": ["README.md"]},
                "manifest_consistency": {"missing_from_disk": []},
                "non_empty_files": {"empty_or_missing": []},
            }
            result = RepairEngine().repair_if_needed(
                root,
                {"README.md": "# Hello"},
                validation,
            )
            assert result["attempted"] is True
            assert (root / "README.md").exists()
            assert (root / "README.md").read_text() == "# Hello"

    def test_repair_does_nothing_when_valid(self):
        from app.services.generation.repair_engine import RepairEngine

        with TemporaryDirectory() as tmp:
            result = RepairEngine().repair_if_needed(
                Path(tmp),
                {},
                {"required_files": {}, "manifest_consistency": {}, "non_empty_files": {}},
            )
            assert result["attempted"] is False


# ===================================================================
# 22. PROJECT SIMILARITY AND BASE SELECTOR
# ===================================================================

class TestBaseProjectSelector:
    def test_determine_mode_generate_when_no_candidates(self):
        from app.services.retrieval.base_project_selector import BaseProjectSelector

        result = BaseProjectSelector().determine_mode([], mode_preference="auto")
        assert result["mode"] == "generate"
        assert result["selected"] is None
        assert result["score"] == 0.0

    def test_explicit_generate_mode_preference(self):
        from app.services.retrieval.base_project_selector import BaseProjectSelector

        candidate = {"project": SimpleNamespace(id=uuid4(), name="p"), "score": 0.95}
        result = BaseProjectSelector().determine_mode([candidate], mode_preference="generate")
        assert result["mode"] == "generate"
        assert result["selected"] is None

    def test_reuse_mode_for_high_score(self):
        from app.services.retrieval.base_project_selector import BaseProjectSelector

        project = SimpleNamespace(id=uuid4(), name="p")
        candidate = {"project": project, "score": 0.95}
        result = BaseProjectSelector().determine_mode([candidate], mode_preference="auto")
        assert result["mode"] == "reuse"
        assert result["selected"] is project

    def test_adapt_mode_for_medium_score(self):
        from app.services.retrieval.base_project_selector import BaseProjectSelector

        project = SimpleNamespace(id=uuid4(), name="p")
        candidate = {"project": project, "score": 0.70}
        result = BaseProjectSelector().determine_mode([candidate], mode_preference="auto")
        assert result["mode"] == "adapt"

    def test_hybrid_scaffold_for_low_score(self):
        from app.services.retrieval.base_project_selector import BaseProjectSelector

        project = SimpleNamespace(id=uuid4(), name="p")
        candidate = {"project": project, "score": 0.40}
        result = BaseProjectSelector().determine_mode([candidate], mode_preference="auto")
        assert result["mode"] == "hybrid_scaffold"

    def test_generate_mode_for_very_low_score(self):
        from app.services.retrieval.base_project_selector import BaseProjectSelector

        project = SimpleNamespace(id=uuid4(), name="p")
        candidate = {"project": project, "score": 0.10}
        result = BaseProjectSelector().determine_mode([candidate], mode_preference="auto")
        assert result["mode"] == "generate"


# ===================================================================
# 23. ORCHESTRATOR STAGES CONTRACT
# ===================================================================

class TestOrchestratorStages:
    def test_stage_list_is_complete(self):
        from app.services.generation.orchestrator import GenerationOrchestrator

        stages = GenerationOrchestrator.STAGES
        assert len(stages) >= 40
        assert stages[0] == "validate_request"
        assert stages[-1] == "finalize_job_status"

    def test_critical_stage_ordering(self):
        from app.services.generation.orchestrator import GenerationOrchestrator

        stages = GenerationOrchestrator.STAGES
        assert stages.index("validate_request") < stages.index("parse_prompt")
        assert stages.index("parse_prompt") < stages.index("classify_domain")
        assert stages.index("classify_domain") < stages.index("expand_features")
        assert stages.index("retrieve_rag_context") < stages.index("build_project_spec")
        assert stages.index("build_project_spec") < stages.index("generate_backend_code")
        assert stages.index("generate_backend_code") < stages.index("assemble_project_files")
        assert stages.index("assemble_project_files") < stages.index("validate_structure")
        assert stages.index("validate_structure") < stages.index("repair_if_needed")
        assert stages.index("package_to_zip") < stages.index("persist_project_metadata")
        assert stages.index("persist_generation_cache") < stages.index("finalize_job_status")

    def test_validate_request_rejects_unsupported_backend(self):
        from app.core.exceptions import ValidationException
        from app.services.generation.orchestrator import GenerationOrchestrator

        orchestrator = GenerationOrchestrator(db=FakeSession())
        with pytest.raises(ValidationException, match="Unsupported backend"):
            orchestrator.validate_request("django", "angular", "Build app", "auto")

    def test_validate_request_rejects_unsupported_frontend(self):
        from app.core.exceptions import ValidationException
        from app.services.generation.orchestrator import GenerationOrchestrator

        orchestrator = GenerationOrchestrator(db=FakeSession())
        with pytest.raises(ValidationException, match="Unsupported frontend"):
            orchestrator.validate_request("springboot", "react", "Build app", "auto")

    def test_validate_request_rejects_empty_prompt(self):
        from app.core.exceptions import ValidationException
        from app.services.generation.orchestrator import GenerationOrchestrator

        orchestrator = GenerationOrchestrator(db=FakeSession())
        with pytest.raises(ValidationException, match="empty"):
            orchestrator.validate_request("springboot", "angular", "   ", "auto")

    def test_validate_request_rejects_invalid_mode(self):
        from app.core.exceptions import ValidationException
        from app.services.generation.orchestrator import GenerationOrchestrator

        orchestrator = GenerationOrchestrator(db=FakeSession())
        with pytest.raises(ValidationException, match="Unsupported mode"):
            orchestrator.validate_request("springboot", "angular", "Build app", "invalid")

    def test_orchestrator_parse_and_classify(self):
        from app.services.generation.orchestrator import GenerationOrchestrator

        orchestrator = GenerationOrchestrator(db=FakeSession())
        parsed = orchestrator.parse_prompt("Build a hotel management app with booking")
        domain = orchestrator.classify_domain(parsed)
        assert domain == "hotel_management"
        assert "hotel" in parsed["summary"].lower()

    def test_default_scaffold_features(self):
        from app.services.generation.orchestrator import GenerationOrchestrator

        assert "booking" in GenerationOrchestrator.default_scaffold_features("hotel_management")
        assert "dashboard" in GenerationOrchestrator.default_scaffold_features("crm")
        assert GenerationOrchestrator.default_scaffold_features("general") == []

    def test_resolve_scaffold_strategy(self):
        from app.services.generation.orchestrator import GenerationOrchestrator

        orchestrator = GenerationOrchestrator(db=FakeSession())
        strategy = orchestrator.resolve_scaffold_strategy("crm", {"mode": "generate", "score": 0.0})
        assert strategy["strategy"] == "domain_scaffold"

        strategy = orchestrator.resolve_scaffold_strategy("general", {"mode": "generate", "score": 0.0})
        assert strategy["strategy"] == "clean_scaffold"

        strategy = orchestrator.resolve_scaffold_strategy("crm", {"mode": "reuse", "score": 0.95})
        assert strategy["strategy"] == "reuse_existing_project"

    def test_build_parsed_prompt_summary(self):
        from app.services.generation.orchestrator import GenerationOrchestrator

        summary = GenerationOrchestrator.build_parsed_prompt_summary({
            "summary": "test",
            "tokens": ["a", "b"],
            "entities": ["customer"],
            "feature_hints": ["auth"],
        })
        assert summary["token_count"] == 2
        assert summary["entities"] == ["customer"]

    def test_build_rag_context_summary(self):
        from app.services.generation.orchestrator import GenerationOrchestrator

        summary = GenerationOrchestrator.build_rag_context_summary([
            {"score": 0.8, "metadata": {"file": "a.java"}},
            {"score": 0.6, "metadata": {"file": "b.java"}},
        ])
        assert summary["retrieved_chunks"] == 2
        assert summary["top_score"] == 0.8

    def test_build_rag_context_summary_empty(self):
        from app.services.generation.orchestrator import GenerationOrchestrator

        summary = GenerationOrchestrator.build_rag_context_summary([])
        assert summary["retrieved_chunks"] == 0
        assert summary["top_score"] == 0.0


# ===================================================================
# 24. CELERY TASK FLOW
# ===================================================================

class TestCeleryTask:
    def test_task_sets_running_status(self, monkeypatch):
        from app.tasks import generation_tasks as task_mod
        from app.services.generation.orchestrator import GenerationOrchestrator

        job_id = uuid4()
        job = Job()
        job.id = job_id
        job.project_name = "test"
        job.prompt = "Build app with dashboard"
        job.backend = "springboot"
        job.frontend = "angular"
        job.features = ["dashboard"]
        job.fingerprint = "fp1"
        job.trace_id = "t1"
        job.website_like = None
        job.mode_preference = "auto"
        job.status = JobStatus.pending
        job.result_data = None
        job.progress = 0
        job.current_stage = "pending"
        job.error = None

        fake_db = FakeSession({Job: job})

        monkeypatch.setattr(task_mod, "SessionLocal", lambda: fake_db)
        monkeypatch.setattr(
            GenerationOrchestrator, "run",
            lambda self, **kw: {
                "project_id": str(uuid4()),
                "zip_path": "/tmp/test.zip",
                "execution_mode": "generate",
                "stage_timings": {},
            },
        )
        monkeypatch.setattr(task_mod, "copy_project_to_downloads", lambda *a, **kw: "/tmp/out.zip")

        # bind=True Celery tasks inject `self` automatically; call with job_id only
        result = task_mod.generate_project_task(str(job_id))

        assert result["project_id"]
        assert job.status == JobStatus.completed
        assert job.progress == 100

    def test_task_handles_failure(self, monkeypatch):
        from app.tasks import generation_tasks as task_mod
        from app.services.generation.orchestrator import GenerationOrchestrator

        job_id = uuid4()
        job = Job()
        job.id = job_id
        job.project_name = "fail-test"
        job.prompt = "Build app that will fail"
        job.backend = "springboot"
        job.frontend = "angular"
        job.features = []
        job.fingerprint = "fp-fail"
        job.trace_id = "t-fail"
        job.website_like = None
        job.mode_preference = "auto"
        job.status = JobStatus.pending
        job.result_data = None
        job.progress = 0
        job.current_stage = "pending"
        job.error = None

        fake_db = FakeSession({Job: job})
        monkeypatch.setattr(task_mod, "SessionLocal", lambda: fake_db)
        monkeypatch.setattr(
            GenerationOrchestrator, "run",
            lambda self, **kw: (_ for _ in ()).throw(RuntimeError("generation exploded")),
        )

        with pytest.raises(RuntimeError, match="generation exploded"):
            task_mod.generate_project_task(str(job_id))

        assert job.status == JobStatus.failed
        assert "generation exploded" in job.error

    def test_task_skips_already_completed_job(self, monkeypatch):
        from app.tasks import generation_tasks as task_mod

        job_id = uuid4()
        job = Job()
        job.id = job_id
        job.status = JobStatus.completed
        job.result_data = {"project_id": "already-done"}

        fake_db = FakeSession({Job: job})
        monkeypatch.setattr(task_mod, "SessionLocal", lambda: fake_db)

        result = task_mod.generate_project_task(str(job_id))

        assert result == {"project_id": "already-done"}


# ===================================================================
# 25. SANITIZERS AND UTILITIES
# ===================================================================

class TestSanitizers:
    def test_sanitize_project_name(self):
        from app.core.security import sanitize_project_name

        assert sanitize_project_name("My Project!") == "my-project"
        assert sanitize_project_name("valid-name") == "valid-name"
        assert sanitize_project_name("!!!") == "generated-app"

    def test_sanitize_text(self):
        from app.utils.sanitizers import sanitize_text

        assert sanitize_text("  hello   world  ") == "hello world"
        long_text = "a" * 20000
        assert len(sanitize_text(long_text)) == 10000

    def test_sanitize_feature_list(self):
        from app.utils.sanitizers import sanitize_feature_list

        result = sanitize_feature_list(["Auth!", "Dashboard", "auth", "  Reports  "])
        assert result == ["auth", "dashboard", "reports"]

    def test_sanitize_feature_list_empty(self):
        from app.utils.sanitizers import sanitize_feature_list

        assert sanitize_feature_list([]) == []

    def test_sha256_text(self):
        from app.utils.hashing import sha256_text

        h = sha256_text("hello")
        assert isinstance(h, str)
        assert len(h) == 64

    def test_sha256_deterministic(self):
        from app.utils.hashing import sha256_text

        assert sha256_text("test") == sha256_text("test")
        assert sha256_text("a") != sha256_text("b")


# ===================================================================
# 26. FILE UTILITIES
# ===================================================================

class TestFileUtils:
    def test_ensure_directory(self):
        from app.utils.file_utils import ensure_directory

        with TemporaryDirectory() as tmp:
            new_dir = Path(tmp) / "a" / "b" / "c"
            result = ensure_directory(new_dir)
            assert result.is_dir()

    def test_write_text_file(self):
        from app.utils.file_utils import write_text_file

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub" / "file.txt"
            write_text_file(path, "hello world")
            assert path.read_text() == "hello world"

    def test_list_files_recursive(self):
        from app.utils.file_utils import list_files_recursive

        with TemporaryDirectory() as tmp:
            (Path(tmp) / "a.txt").write_text("a")
            (Path(tmp) / "sub").mkdir()
            (Path(tmp) / "sub" / "b.txt").write_text("b")
            files = list_files_recursive(tmp)
            assert len(files) == 2

    def test_list_files_nonexistent(self):
        from app.utils.file_utils import list_files_recursive

        assert list_files_recursive("/nonexistent/path") == []


# ===================================================================
# 27. DOWNLOAD UTILS
# ===================================================================

class TestDownloadUtils:
    def test_copy_project_to_downloads(self):
        from app.utils.download_utils import copy_project_to_downloads

        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "source.zip"
            src.write_bytes(b"zipdata")
            dest_dir = Path(tmp) / "downloads"
            dest_dir.mkdir()

            result = copy_project_to_downloads(str(src), "myproject", str(dest_dir))
            assert Path(result).exists()
            assert "myproject.zip" in result

    def test_copy_handles_duplicate_names(self):
        from app.utils.download_utils import copy_project_to_downloads

        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "source.zip"
            src.write_bytes(b"zipdata")
            dest_dir = Path(tmp) / "downloads"
            dest_dir.mkdir()
            # Pre-create target to force counter increment
            (dest_dir / "myproject.zip").write_bytes(b"existing")

            result = copy_project_to_downloads(str(src), "myproject", str(dest_dir))
            assert "myproject-1.zip" in result

    def test_copy_raises_for_missing_source(self):
        from app.utils.download_utils import copy_project_to_downloads

        with pytest.raises(FileNotFoundError):
            copy_project_to_downloads("/nonexistent.zip", "proj", "/tmp")


# ===================================================================
# 28. SEARCH CLIENT
# ===================================================================

class TestSearchClient:
    def test_fallback_provider_on_primary_failure(self, monkeypatch):
        from app.services.web_discovery.search_client import SearchClient

        client = SearchClient()
        calls = []

        def _provider(provider, query, limit):
            calls.append(provider)
            if provider == "serpapi":
                raise RuntimeError("serpapi down")
            return [{"url": "https://fallback.dev", "title": "fb", "snippet": "ok"}]

        monkeypatch.setattr(client, "_search_via_provider", _provider)
        monkeypatch.setattr(client, "_search_github_repositories", lambda *a, **kw: [])
        client.settings.search_provider = "serpapi"
        client.settings.fallback_search_provider = "duckduckgo"

        results = client.search("test", max_results=3)
        assert "serpapi" in calls
        assert "duckduckgo" in calls
        assert len(results) == 1

    def test_deduplication(self):
        from app.services.web_discovery.search_client import SearchClient

        results = SearchClient._dedupe_results([
            {"url": "https://a.com", "title": "A"},
            {"url": "https://a.com", "title": "A duplicate"},
            {"url": "https://b.com", "title": "B"},
        ], limit=10)
        assert len(results) == 2

    def test_deduplication_respects_limit(self):
        from app.services.web_discovery.search_client import SearchClient

        results = SearchClient._dedupe_results([
            {"url": "https://a.com"}, {"url": "https://b.com"}, {"url": "https://c.com"},
        ], limit=2)
        assert len(results) == 2


# ===================================================================
# 29. CONSTANTS VERIFICATION
# ===================================================================

class TestConstants:
    def test_supported_backends(self):
        from app.core.constants import SUPPORTED_BACKENDS

        assert "springboot" in SUPPORTED_BACKENDS

    def test_supported_frontends(self):
        from app.core.constants import SUPPORTED_FRONTENDS

        assert "angular" in SUPPORTED_FRONTENDS

    def test_mandatory_output_files(self):
        from app.core.constants import MANDATORY_OUTPUT_FILES

        assert "backend/pom.xml" in MANDATORY_OUTPUT_FILES
        assert "frontend/package.json" in MANDATORY_OUTPUT_FILES
        assert "docker-compose.yml" in MANDATORY_OUTPUT_FILES
        assert "README.md" in MANDATORY_OUTPUT_FILES
        assert "_meta/final_enriched_prompt.txt" in MANDATORY_OUTPUT_FILES
        assert "_meta/final_enriched_prompt.json" in MANDATORY_OUTPUT_FILES
        assert "frontend/nginx.conf" in MANDATORY_OUTPUT_FILES

    def test_allowed_extensions(self):
        from app.core.constants import ALLOWED_GENERATED_EXTENSIONS

        assert ".java" in ALLOWED_GENERATED_EXTENSIONS
        assert ".ts" in ALLOWED_GENERATED_EXTENSIONS
        assert ".conf" in ALLOWED_GENERATED_EXTENSIONS
        assert ".xml" in ALLOWED_GENERATED_EXTENSIONS

    def test_api_prefix(self):
        from app.core.constants import API_PREFIX

        assert API_PREFIX == "/api/v1"


# ===================================================================
# 30. EXCEPTION HANDLING
# ===================================================================

class TestExceptions:
    def test_not_found_exception_status(self):
        from app.core.exceptions import NotFoundException

        exc = NotFoundException("missing item")
        assert exc.status_code == 404
        assert exc.detail == "missing item"

    def test_validation_exception_status(self):
        from app.core.exceptions import ValidationException

        exc = ValidationException("bad input")
        assert exc.status_code == 422

    def test_generation_exception_status(self):
        from app.core.exceptions import GenerationException

        exc = GenerationException("failed")
        assert exc.status_code == 500

    def test_default_detail(self):
        from app.core.exceptions import AppException

        exc = AppException()
        assert exc.detail == "Internal application error"


# ===================================================================
# 31. JOB STATUS ENUM
# ===================================================================

class TestJobStatus:
    def test_all_statuses(self):
        assert JobStatus.pending.value == "pending"
        assert JobStatus.running.value == "running"
        assert JobStatus.completed.value == "completed"
        assert JobStatus.failed.value == "failed"


# ===================================================================
# 32. CELERY APP CONFIG
# ===================================================================

class TestCeleryAppConfig:
    def test_celery_config(self):
        from app.tasks.celery_app import celery_app

        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.worker_prefetch_multiplier == 1
        assert celery_app.conf.task_time_limit == 1800
        assert celery_app.conf.task_soft_time_limit == 1700


# ===================================================================
# 33. WEB DISCOVERY ORCHESTRATOR UNIT TESTS
# ===================================================================

class TestWebDiscoveryOrchestrator:
    def test_search_web_sources_empty_queries(self):
        from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator

        orch = WebDiscoveryOrchestrator(db=FakeSession())
        assert orch.search_web_sources([]) == []

    def test_filter_trusted_empty(self):
        from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator

        orch = WebDiscoveryOrchestrator(db=FakeSession())
        assert orch.filter_trusted_sources([]) == []

    def test_rank_trusted_empty(self):
        from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator

        orch = WebDiscoveryOrchestrator(db=FakeSession())
        assert orch.rank_trusted_sources([], []) == []

    def test_fetch_shortlisted_skips_when_not_should_run(self):
        from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator

        orch = WebDiscoveryOrchestrator(db=FakeSession())
        result = orch.fetch_shortlisted_sources(
            [{"url": "https://example.com"}],
            {"should_run": False},
        )
        assert result == []

    def test_persist_metadata_skips_empty(self):
        from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator

        orch = WebDiscoveryOrchestrator(db=FakeSession())
        result = orch.persist_web_discovery_metadata(uuid4(), [], [], {})
        assert result["skipped"] is True

    def test_optionally_index_skips_when_not_should_run(self):
        from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator

        orch = WebDiscoveryOrchestrator(db=FakeSession())
        result = orch.optionally_index_web_knowledge_into_rag(
            {"should_run": False}, {}, "general", [],
        )
        assert result["attempted"] is False

    def test_summarize_web_discovery(self):
        from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator

        orch = WebDiscoveryOrchestrator(db=FakeSession())
        summary = orch.summarize_web_discovery(
            discovery_decision={"should_run": True, "reasons": ["test"]},
            discovery_queries=["q1"],
            ranked_sources=[{"url": "https://example.com"}],
            knowledge={"features": ["auth"], "entities": ["user"]},
            persisted_discovery={"run_id": "r1"},
            rag_ingestion={"attempted": True},
        )
        assert summary["used"] is True
        assert summary["discovered_count"] == 1
        assert summary["extracted_features"] == ["auth"]


# ===================================================================
# 34. METRICS MODULE
# ===================================================================

class TestMetrics:
    def test_track_stage_context_manager(self):
        from app.services.observability.metrics import track_stage

        with track_stage("test_metric_stage"):
            pass  # just ensure no error

    def test_counters_exist(self):
        from app.services.observability.metrics import CACHE_COUNTER, GENERATION_COUNTER

        assert CACHE_COUNTER is not None
        assert GENERATION_COUNTER is not None

    def test_trace_id_generation(self):
        from app.services.observability.tracing import new_trace_id

        t1 = new_trace_id()
        t2 = new_trace_id()
        assert isinstance(t1, str)
        assert len(t1) == 32  # uuid hex
        assert t1 != t2


# ===================================================================
# 35. GENERATION CACHE SERVICE
# ===================================================================

class TestGenerationCacheService:
    def test_lookup_returns_none_on_miss(self):
        from app.services.caching.generation_cache_service import GenerationCacheService

        svc = GenerationCacheService(db=FakeSession())
        assert svc.lookup("nonexistent-fp") is None

    def test_lookup_increments_hit_count(self):
        from app.services.caching.generation_cache_service import GenerationCacheService

        cache_obj = SimpleNamespace(fingerprint="fp1", hit_count=2)
        db = FakeSession({GenerationCache: cache_obj})
        svc = GenerationCacheService(db=db)
        result = svc.lookup("fp1")
        assert result is not None
        assert cache_obj.hit_count == 3
        assert db.committed >= 1


# ===================================================================
# 36. PROJECT SIMILARITY
# ===================================================================

class TestProjectSimilarity:
    def test_identical_tokens_yield_high_score(self):
        from app.services.retrieval.project_similarity import ProjectSimilarity

        project = SimpleNamespace(
            name="crm-app",
            description="Build CRM with auth and dashboard",
            domain="crm",
            manifest={"features": ["auth", "dashboard"]},
            validation_report={},
        )
        score = ProjectSimilarity().score("Build CRM with auth and dashboard", ["auth", "dashboard"], project)
        assert score > 0.5

    def test_unrelated_project_yields_low_score(self):
        from app.services.retrieval.project_similarity import ProjectSimilarity

        project = SimpleNamespace(
            name="weather-api",
            description="A weather forecast API",
            domain="general",
            manifest={"features": ["forecast"]},
            validation_report={},
        )
        score = ProjectSimilarity().score("Build CRM with auth", ["auth"], project)
        assert score < 0.3

    def test_domain_bonus(self):
        from app.services.retrieval.project_similarity import ProjectSimilarity

        project = SimpleNamespace(
            name="crm",
            description="customer management",
            domain="crm",
            manifest={"features": []},
            validation_report={},
        )
        score = ProjectSimilarity().score("Build a crm application", [], project)
        # Should get domain bonus
        assert score > 0.0
