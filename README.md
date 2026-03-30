# AI Code Generation Platform (RAG + Async Jobs)

Production-ready platform to generate complete full-stack project ZIP bundles from natural language prompts.

Full process documentation:
- docs/FULL_PROCESS_GUIDE.md

## Tech Stack
- FastAPI + Python 3.11
- Celery + Redis for async processing
- PostgreSQL + SQLAlchemy + Alembic
- ChromaDB for vector persistence
- OpenAI integration with local embedding fallback
- Jinja2-based templated code generation
- Docker + Docker Compose

## API Endpoints
- GET /api/v1/health
- POST /api/v1/generate
- GET /api/v1/jobs/{job_id}
- GET /api/v1/jobs/{job_id}/final-prompt
- GET /api/v1/projects/{project_id}
- GET /api/v1/projects/{project_id}/download
- POST /api/v1/rag/index
- POST /api/v1/rag/search
- GET /api/v1/cache/{fingerprint}
- POST /api/v1/web-discovery/preview

## Pipeline Highlights
- Stage-based generation pipeline with explicit progress updates and stage timings
- Request fingerprinting + generation cache lookup
- Execution mode selection: auto/reuse/adapt/generate
- Optional trusted web discovery enrichment using website_like
- Domain classification and curated blueprint fallback strategy
- RAG retrieval from Chroma with similarity filtering
- Final enriched prompt persistence in DB + project _meta artifacts
- Validation + safe repair pass before packaging
- Post-generation indexing back into RAG for reuse
- Metrics endpoint at /metrics

## Quick Start
1. Copy environment file:
   cp .env.example .env

2. Build and run:
   docker compose up --build

3. Optional DB migrations:
   alembic upgrade head

4. Open API docs:
   http://localhost:8000/docs

## Sample Generate Request
POST /api/v1/generate

{
  "project_name": "my-crm",
  "prompt": "Build a CRM web app with authentication, customer management, dashboard, and reports",
  "backend": "springboot",
  "frontend": "angular",
   "features": ["auth", "dashboard", "crud", "reports"],
   "website_like": "https://angular.dev",
   "mode_preference": "auto"
}

## Generated Output
The worker creates:
- generated_projects/{project_id}/ (full project)
- generated_projects/{project_id}.zip (downloadable artifact)

Generated project includes:
- Spring Boot backend with layered architecture (controller, service, repository, DTO, entity, exception handling)
- Angular frontend with routing, feature modules, API service integration
- Dockerfiles for backend/frontend
- docker-compose.yml
- README.md
- API contract + manifest
- _meta/final_enriched_prompt.txt
- _meta/final_enriched_prompt.json

## Local Development Without Docker
1. Create virtual environment and install deps:
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt

2. Start API:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

3. Start worker:
   celery -A app.tasks.celery_app.celery_app worker --loglevel=INFOs

## Testing
Run:
pytest -q


echo "# python_foundry" >> README.md