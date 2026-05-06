# Full Process Guide: AI Code Generation Platform

This document explains the complete runtime flow of the platform from incoming prompt to downloadable ZIP artifact, including cache, RAG, web discovery, and prompt artifact persistence.

## 1. High-Level Architecture

Core runtime services:
- API service: FastAPI app receiving generation and retrieval requests.
- Worker service: Celery worker executing long-running generation jobs.
- PostgreSQL: system-of-record for jobs, projects, cache, prompt artifacts, and web discovery metadata.
- Redis: Celery broker/result backend and async queue coordination.
- ChromaDB: vector store for RAG retrieval and post-generation indexing.

Primary modules:
- API routes in app/api/v1/routes
- Generation orchestration in app/services/generation/orchestrator.py
- Async task entry in app/tasks/generation_tasks.py
- Web discovery orchestration in app/services/web_discovery/web_discovery_orchestrator.py
- Prompt artifact persistence in app/services/generation/prompt_debugger.py

## 2. Full End-to-End Runtime Flow

### Step A: User submits generation request
Endpoint:
- POST /api/v1/generate

Important request fields:
- project_name
- prompt
- backend (currently springboot)
- frontend (currently angular)
- features
- website_like (optional, triggers web-discovery enrichment)
- mode_preference: auto | reuse | adapt | generate

What happens in route handler:
1. Input is sanitized (project name, features).
2. Prompt is parsed and domain-classified.
3. A deterministic fingerprint is computed.
4. Cache table is checked by fingerprint.

### Step B: Fast path cache reuse (route-level)
If cache hit with valid project_id:
1. A completed Job row is created immediately with cache_hit=true.
2. mode_selected is set to reuse.
3. A prompt artifact record is still persisted for auditability.
4. API returns 202 with job_id and cached_project_id.

### Step C: Async job creation
If cache miss in route:
1. A pending Job row is created.
2. Celery task generate_project_task is queued with job_id.
3. API returns 202 and caller tracks progress via job endpoint.

### Step D: Worker starts orchestration
Worker entrypoint:
- app/tasks/generation_tasks.py

Worker behavior:
1. Loads Job by UUID.
2. Marks job running.
3. Updates stage/progress via callback throughout pipeline.
4. Calls GenerationOrchestrator.run(...).

### Step E: Stage pipeline execution
Main stage map (progress-based) includes:
1. validate_request
2. compute_fingerprint
3. cache_lookup
4. parse_prompt
5. classify_domain
6. select_blueprint
7. expand_features
8. discover_existing_projects
9. select_execution_mode
10. run_web_discovery (if website_like provided)
11. build_project_spec
12. build_api_contract
13. build_manifest
14. retrieve_rag_context
15. resolve_fallback_strategy
16. build_adaptation_context
17. enrich_prompt
18. merge_contexts
19. persist_prompt_artifact
20. generate_backend_code
21. generate_frontend_code
22. generate_docker_files
23. generate_readme
24. assemble_project_files
25. write_prompt_files
26. validate_project_structure
27. repair_if_needed
28. revalidate_after_repair
29. package_to_zip
30. persist_project_metadata
31. index_generated_project_into_rag
32. finalize_job_status

### Step F: Execution mode logic
Mode is selected using similarity against existing projects plus user preference:
- reuse: return existing matching project if similarity/selection allows.
- adapt: generate using a base project diff context.
- generate: generate fully new project.
- auto: system decides based on candidates.

### Step G: Optional web discovery enrichment
Triggered when website_like is provided.

Pipeline summary:
1. Build web query from website_like + domain + top features.
2. Search provider retrieves candidates.
3. Trusted source filter applies allow/deny domain strategy and trust scoring.
4. Ranking orders results by trust + query overlap.
5. Fetch page/repo content and extract:
   - features
   - entities
   - routes
   - components
   - backend patterns
   - UI patterns
6. Persist web_discovery_runs and web_sources in DB.
7. Convert extracted docs into RAG ingestion payload and index to Chroma.

### Step H: Prompt enrichment and persistence
1. Base enriched prompt is created from:
   - user prompt
   - project spec
   - API contract
   - RAG snippets
   - fallback strategy
2. Additional contexts are merged:
   - adaptation context (if mode=adapt)
   - web discovery summary (if present)
3. Final prompt artifact is persisted to DB.
4. Project files include:
   - _meta/final_enriched_prompt.txt
   - _meta/final_enriched_prompt.json

### Step I: Code generation, validation, packaging
1. Generators produce backend, frontend, docker, and readme files.
2. Files assembled under generated_projects/{project_id}/
3. Structural/content/syntax validation runs.
4. Repair pass runs when needed, then revalidation.
5. ZIP created at generated_projects/{project_id}.zip

### Step J: Persistence and indexing
1. Project row is persisted with manifest, validation report, rag summary, mode, and prompt file paths.
2. Generation cache entry is stored by fingerprint for future reuse.
3. Generated project is indexed back into RAG for subsequent retrieval.

### Step K: Completion and retrieval
1. Worker marks job completed with project_id and stage timings.
2. Client retrieves:
   - GET /api/v1/jobs/{job_id}
   - GET /api/v1/projects/{project_id}
   - GET /api/v1/projects/{project_id}/download
   - GET /api/v1/jobs/{job_id}/final-prompt

## 3. API Reference for Process Tracking

Core endpoints:
- GET /api/v1/health
- POST /api/v1/generate
- GET /api/v1/jobs/{job_id}
- GET /api/v1/jobs/{job_id}/final-prompt
- GET /api/v1/projects/{project_id}
- GET /api/v1/projects/{project_id}/download
- GET /api/v1/cache/{fingerprint}
- POST /api/v1/rag/index
- POST /api/v1/rag/search
- POST /api/v1/web-discovery/preview
- GET /metrics

## 4. Setup and Run Process

### Docker (recommended)
1. Copy env:
   - cp .env.example .env
2. Start stack:
   - docker compose up --build
3. Optional migrations:
   - alembic upgrade head
4. Open docs:
   - http://localhost:8000/docs

### Local (without Docker)
Recommended Python:
- 3.10 or 3.11
- 3.14 may fail for some pinned dependencies in requirements.txt

Steps:
1. Install deps:
   - py -3.10 -m pip install -r requirements.txt
2. Start API:
   - py -3.10 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
3. Start worker:
   - py -3.10 -m celery -A app.tasks.celery_app.celery_app worker --loglevel=INFO
4. Run tests:
   - py -3.10 -m pytest -q

## 5. Data and Artifacts Produced

Database entities:
- jobs
- projects
- generation_cache
- prompt_artifacts
- web_discovery_runs
- web_sources
- rag_documents

Filesystem artifacts:
- generated_projects/{project_id}/
- generated_projects/{project_id}.zip
- generated_projects/{project_id}/_meta/final_enriched_prompt.txt
- generated_projects/{project_id}/_meta/final_enriched_prompt.json
- chroma_data/* (vector store persistence)

## 6. Operational Observability

Built-in visibility:
- Job status, stage, and progress via jobs endpoint.
- Per-stage timings via job result and stage_timings.
- Cache hit/miss and generation counters exposed via /metrics.
- Prompt artifacts retrievable via final-prompt endpoint.

## 7. Troubleshooting Checklist

If generation is stuck at pending:
- Ensure worker process is running and connected to Redis.

If jobs fail quickly:
- Check API and worker logs for DB/Redis/OpenAI connectivity.

If final prompt endpoint returns not found:
- Verify job reached artifact persistence stage.
- Check prompt_artifacts table and job_id mapping.

If web discovery returns poor results:
- Review ALLOWED_WEB_DOMAINS and DENIED_WEB_DOMAINS in env.
- Verify SEARCH_PROVIDER and optional SEARCH_API_KEY.

If ZIP missing:
- Confirm validation/repair stage did not fail.
- Check generated_projects folder permissions.

## 8. Suggested Production Run Order

1. Configure .env values for DB, Redis, OpenAI, and domain policies.
2. Start Postgres and Redis.
3. Run alembic upgrade head.
4. Start API and worker services.
5. Validate with /api/v1/health and /metrics.
6. Submit a generate request and poll job until completion.
7. Download artifact and inspect final prompt audit files in _meta.
