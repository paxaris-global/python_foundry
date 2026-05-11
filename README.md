# AI Code Generation Platform 

A production-ready platform that generates complete, downloadable full-stack web applications (Spring Boot + Angular) from natural language prompts. It uses an AI-enriched generation pipeline with RAG-based context retrieval, web discovery, intelligent caching, and async background processing to produce ready-to-run project bundles.

## Table of Contents

- [What Problem It Solves](#what-problem-it-solves)
- [How It Works (Overview)](#how-it-works-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Request and Response Formats](#request-and-response-formats)
- [Generation Pipeline (Detailed Flow)](#generation-pipeline-detailed-flow)
- [Background Processing (Celery)](#background-processing-celery)
- [Database Models](#database-models)
- [Main Services](#main-services)
- [Web Discovery](#web-discovery)
- [RAG (Retrieval-Augmented Generation)](#rag-retrieval-augmented-generation)
- [Caching and Fingerprinting](#caching-and-fingerprinting)
- [Generated Project Output](#generated-project-output)
- [Observability](#observability)
- [Local Development Without Docker](#local-development-without-docker)
- [Testing](#testing)
- [Additional Documentation](#additional-documentation)

---

## What Problem It Solves

Setting up a full-stack web project from scratch involves a lot of repetitive boilerplate: backend scaffolding, frontend module wiring, Docker configuration, API contracts, CI files, and more. This platform automates that entire process. You describe what you want in plain English (e.g., "Build a hotel management system with booking, dashboard, and reports"), and the platform generates a complete, working project with:

- A Spring Boot backend with layered architecture (controllers, services, repositories, DTOs, entities)
- An Angular frontend with routing, feature modules, and API integration
- Dockerfiles, docker-compose.yml, and environment configuration
- A README, API contract, and project manifest

The platform goes beyond simple templating by using AI (OpenAI GPT) to understand your prompt, retrieving relevant code patterns from previously generated projects via RAG, and optionally mining the web for architecture patterns from real-world reference sites.

## How It Works (Overview)

```
User sends POST /api/v1/generate
         |
         v
  API creates a Job record (status: pending)
  Dispatches a Celery background task
  Returns job_id immediately (HTTP 202)
         |
         v
  Celery worker picks up the task
  Runs the GenerationOrchestrator (40+ stages)
         |
         v
  Pipeline stages:
    1. Validate request & compute fingerprint
    2. Check cache for existing identical project
    3. Parse prompt, classify domain, expand features
    4. Search for similar existing projects in DB
    5. Decide execution mode (reuse / adapt / generate)
    6. Retrieve RAG context from ChromaDB
    7. Run web discovery (if needed) for architecture patterns
    8. Build project spec, API contract, and manifest
    9. Build enriched prompt with all gathered context
   10. Generate backend code (Spring Boot)
   11. Generate frontend code (Angular)
   12. Generate Docker and compose files
   13. Generate README
   14. Assemble, validate, repair if needed
   15. Package to ZIP
   16. Persist project metadata and cache entry
   17. Index generated project back into RAG
         |
         v
  Job status updated to "completed"
  ZIP auto-copied to Downloads folder
         |
         v
  User polls GET /api/v1/jobs/{job_id} for status
  Downloads via GET /api/v1/projects/{project_id}/download
```

## Tech Stack

| Component | Technology |
|---|---|
| API Framework | FastAPI (Python 3.12) |
| Background Tasks | Celery with Redis broker |
| Database | PostgreSQL 16 with SQLAlchemy 2.0 ORM |
| Migrations | Alembic |
| Vector Store | ChromaDB (for RAG embeddings) |
| LLM Provider | OpenAI API (GPT-4o-mini default) |
| Embeddings | OpenAI text-embedding-3-small |
| Templating | Jinja2 |
| Web Scraping | httpx, BeautifulSoup4, trafilatura, readability-lxml |
| Git Integration | GitPython |
| Metrics | Prometheus (prometheus-client) |
| Containerization | Docker + Docker Compose |

## Project Structure

```
app/
├── main.py                          # FastAPI app entry point, lifespan, middleware, routers
├── api/
│   ├── deps.py                      # Dependency injection (DB session)
│   └── v1/routes/
│       ├── generate.py              # POST /generate - start a generation job
│       ├── jobs.py                  # GET /jobs/{id} - poll job status
│       ├── projects.py             # GET /projects/{id} - project metadata & download
│       ├── rag.py                   # POST /rag/index, POST /rag/search
│       ├── cache.py                 # GET /cache/{fingerprint}
│       ├── web_discovery.py         # POST /web-discovery/preview
│       └── health.py               # GET /health - dependency health check
├── core/
│   ├── config.py                    # Settings loaded from .env via pydantic-settings
│   ├── constants.py                 # Supported stacks, required files, domain defaults
│   ├── exceptions.py                # Custom exception hierarchy + handlers
│   ├── logging.py                   # Structured logging setup
│   └── security.py                  # Input sanitization utilities
├── db/
│   ├── session.py                   # SQLAlchemy engine and session factory
│   ├── init_db.py                   # Database initialization on startup
│   └── base.py                      # Declarative base import aggregation
├── models/
│   ├── base.py                      # Base model with TimestampMixin
│   ├── job.py                       # Job model (generation request tracking)
│   ├── project.py                   # Project model (generated project metadata)
│   ├── generation_cache.py          # Cache model (fingerprint-based deduplication)
│   ├── prompt_artifact.py           # PromptArtifact (full prompt audit trail)
│   ├── rag_document.py              # RAGDocument (indexed code chunk metadata)
│   ├── web_discovery_run.py         # WebDiscoveryRun (web search session)
│   └── web_source.py               # WebSource (individual discovered URL)
├── schemas/
│   ├── generate.py                  # GenerateRequest / GenerateResponse
│   ├── job.py                       # JobResponse
│   ├── project.py                   # ProjectResponse
│   ├── rag.py                       # RAG index/search request/response
│   ├── web_discovery.py             # WebDiscoveryPreviewRequest/Response
│   ├── prompt_debug.py              # FinalPromptResponse
│   └── common.py, manifest.py      # Shared schemas
├── services/
│   ├── generation/
│   │   ├── orchestrator.py          # GenerationOrchestrator - the main 40-stage pipeline
│   │   ├── pipeline.py              # Stage execution with timing and progress tracking
│   │   ├── prompt_parser.py         # NLP-based prompt analysis
│   │   ├── prompt_debugger.py       # Prompt artifact persistence and file writing
│   │   ├── project_spec_builder.py  # Builds structured project specification
│   │   ├── api_contract_builder.py  # Generates REST API contract from spec
│   │   ├── manifest_builder.py      # Builds project file manifest
│   │   ├── project_skeleton.py      # Creates directory structure
│   │   ├── project_assembler.py     # Writes generated files to disk
│   │   ├── validator.py             # Multi-layer project validation
│   │   ├── repair_engine.py         # Auto-fixes validation failures
│   │   └── zip_packager.py          # ZIP packaging
│   ├── generators/
│   │   ├── springboot_generator.py  # Spring Boot code generation
│   │   ├── angular_generator.py     # Angular code generation
│   │   ├── docker_generator.py      # Dockerfile generation
│   │   ├── compose_generator.py     # docker-compose.yml generation
│   │   └── readme_generator.py      # README.md generation
│   ├── intelligence/
│   │   ├── domain_classifier.py     # Classifies project domain from prompt
│   │   ├── feature_expander.py      # Expands user features with domain defaults
│   │   ├── prompt_enricher.py       # Enriches prompt with RAG + web context
│   │   ├── blueprint_registry.py    # Domain-specific scaffold blueprints
│   │   └── post_generation_indexer.py # Indexes generated code back into RAG
│   ├── llm/
│   │   ├── base.py                  # Abstract LLM provider interface
│   │   ├── openai_provider.py       # OpenAI implementation with retry logic
│   │   └── prompt_library.py        # System prompts for different generation modes
│   ├── rag/
│   │   ├── indexer.py               # Indexes code files into ChromaDB
│   │   ├── retriever.py             # Searches ChromaDB for relevant code
│   │   └── chroma_service.py        # ChromaDB collection management
│   ├── retrieval/
│   │   ├── existing_project_search.py # Finds similar projects in the database
│   │   ├── base_project_selector.py   # Scores and selects base project for reuse
│   │   ├── project_differ.py          # Computes diff between base and new request
│   │   ├── project_adapter.py         # Builds adaptation context for adapt mode
│   │   └── merge_engine.py            # Merges multiple context sources
│   ├── web_discovery/
│   │   ├── web_discovery_orchestrator.py # Orchestrates the full web discovery flow
│   │   ├── search_client.py            # Web search API client (SerpAPI/DuckDuckGo)
│   │   ├── discovery_decider.py        # Decides if web discovery is needed
│   │   ├── trusted_source_filter.py    # Filters by allowed/denied domain lists
│   │   ├── result_ranker.py            # Ranks search results by relevance
│   │   ├── page_fetcher.py             # Fetches and extracts web page content
│   │   ├── feature_extractor.py        # Extracts features from web pages
│   │   ├── entity_extractor.py         # Extracts named entities
│   │   ├── route_extractor.py          # Extracts URL/API routes
│   │   ├── component_extractor.py      # Extracts UI component patterns
│   │   ├── ui_pattern_extractor.py     # Extracts UI design patterns
│   │   ├── backend_pattern_extractor.py # Extracts backend architecture patterns
│   │   ├── repo_fetcher.py             # Fetches GitHub repository content
│   │   ├── repo_analyzer.py            # Analyzes repository structure
│   │   └── web_knowledge_builder.py    # Builds structured knowledge from web data
│   ├── caching/
│   │   ├── fingerprint.py              # Computes request fingerprints
│   │   └── generation_cache_service.py # Cache lookup and storage
│   ├── observability/
│   │   ├── metrics.py                  # Prometheus counters, histograms
│   │   └── tracing.py                  # Trace ID generation
│   └── templates/                      # Jinja2 templates for code generation
├── tasks/
│   ├── celery_app.py                # Celery application configuration
│   └── generation_tasks.py          # Celery task: generate_project_task
├── utils/
│   ├── download_utils.py            # Copies ZIP to user's Downloads folder
│   ├── file_utils.py                # Directory and file helpers
│   ├── html_utils.py                # HTML parsing utilities
│   ├── json_utils.py                # JSON helpers
│   ├── zip_utils.py                 # ZIP utilities
│   ├── url_utils.py                 # URL validation and normalization
│   ├── hashing.py                   # Content hashing
│   ├── path_utils.py                # Path safety checks
│   └── sanitizers.py                # Input sanitization
├── alembic/                         # Database migration scripts
├── templates/                       # Jinja2 code generation templates
├── docker-compose.yml               # Full stack: API + worker + Postgres + Redis
├── Dockerfile                       # Python 3.12 container image
└── requirements.txt                 # Python dependencies
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- (Optional) An OpenAI API key for AI-powered generation

### Using Docker (Recommended)

```bash
# 1. Clone the repository and enter the directory
cd ai-code-generation-platform

# 2. Create your environment file
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY and adjust settings as needed

# 3. Build and start all services
docker compose up --build

# 4. Run database migrations
docker compose exec api alembic upgrade head

# 5. Open the API docs
# Visit http://localhost:8000/docs
```

This starts four containers:
- **api** (port 8000): FastAPI application
- **worker**: Celery worker processing generation tasks
- **postgres** (port 5432): PostgreSQL database
- **redis** (port 6379): Redis for Celery message broker

### Submit Your First Generation Request

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-crm",
    "prompt": "Build a CRM web app with authentication, customer management, dashboard, and reports",
    "backend": "springboot",
    "frontend": "angular",
    "features": ["auth", "dashboard", "crud", "reports"],
    "mode_preference": "auto"
  }'
```

Response (HTTP 202):
```json
{
  "job_id": "a1b2c3d4-...",
  "status": "pending",
  "fingerprint": "sha256:...",
  "cache_hit": false,
  "mode_selected": null
}
```

Then poll the job status:
```bash
curl http://localhost:8000/api/v1/jobs/{job_id}
```

When `status` is `"completed"`, download the project:
```bash
curl -O http://localhost:8000/api/v1/projects/{project_id}/download
```

## Configuration

All configuration is managed through environment variables (loaded from `.env`). Key settings:

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment name |
| `APP_HOST` | `0.0.0.0` | API bind host |
| `APP_PORT` | `8000` | API bind port |
| `SECRET_KEY` | `change_me` | Application secret key |
| `POSTGRES_USER` | `ai_codegen` | Database username |
| `POSTGRES_PASSWORD` | `ai_codegen_pass` | Database password |
| `POSTGRES_DB` | `ai_codegen_db` | Database name |
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Celery result backend URL |
| `OPENAI_API_KEY` | (none) | OpenAI API key. If not set, LLM calls return fallback responses |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model for RAG |
| `CHROMA_PERSIST_DIRECTORY` | `./chroma_data` | ChromaDB storage path |
| `SEARCH_PROVIDER` | `serpapi` | Web search provider (`serpapi`, `duckduckgo`, or `brave`) |
| `SEARCH_API_KEY` | (none) | API key for the search provider |
| `GITHUB_TOKEN` | (none) | GitHub token for repository fetching |
| `ALLOWED_WEB_DOMAINS` | `github.com,docs.github.com,spring.io,angular.dev` | Trusted domains for web discovery |
| `MAX_RAG_RESULTS` | `8` | Maximum RAG retrieval results |
| `MAX_WEB_RESULTS` | `10` | Maximum web search results |
| `MAX_GENERATED_FILE_COUNT` | `600` | Maximum files in a generated project |
| `MAX_ZIP_SIZE_MB` | `50` | Maximum ZIP file size |
| `DOWNLOADS_DIR` | `~/Downloads` | Auto-download destination path |
| `LOG_LLM_PROMPTS` | `false` | Whether to log full LLM prompts |

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Health Check

```
GET /api/v1/health
```

Returns the status of all dependencies (PostgreSQL, Redis, ChromaDB).

**Response:**
```json
{
  "status": "ok",
  "service": "ai-codegen-platform",
  "dependencies": {
    "db": "up",
    "redis": "up",
    "chroma": "up"
  }
}
```

---

### Generate a Project

```
POST /api/v1/generate
```

Starts an asynchronous project generation job. Returns immediately with a job ID.

**Request Body:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `project_name` | string (2-120 chars) | Yes | - | Name of the project to generate |
| `prompt` | string (min 10 chars) | No | Auto-generated from name + features | Natural language description |
| `backend` | `"springboot"` | No | `"springboot"` | Backend framework |
| `frontend` | `"angular"` | No | `"angular"` | Frontend framework |
| `features` | list of strings | No | `[]` | Feature tags (e.g., `["auth", "dashboard"]`) |
| `website_like` | string (max 120 chars) | No | Auto-discovered | Reference website URL for web discovery |
| `mode_preference` | `"auto"` / `"reuse"` / `"adapt"` / `"generate"` / `"hybrid_scaffold"` | No | `"auto"` | How to handle similar existing projects |

**Response (HTTP 202):**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "fingerprint": "sha256:...",
  "cache_hit": false,
  "cached_project_id": null,
  "mode_selected": null
}
```

If `cache_hit` is `true`, the response includes `cached_project_id` and the job is already `"completed"`.

---

### Poll Job Status

```
GET /api/v1/jobs/{job_id}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "pending | running | completed | failed",
  "progress": 0-100,
  "current_stage": "generate_backend_code",
  "error": null,
  "trace_id": "...",
  "cache_hit": false,
  "project_id": "uuid (when completed)",
  "stage_timings": { "parse_prompt": 0.012, "..." : "..." },
  "result_data": {},
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:01:00"
}
```

---

### Get Final Prompt Artifact

```
GET /api/v1/jobs/{job_id}/final-prompt
```

Returns the full prompt audit trail showing how the user's prompt was parsed, enriched with RAG context and web discovery data, and transformed into the final prompt sent to the LLM.

---

### Get Project Metadata

```
GET /api/v1/projects/{project_id}
```

Returns full metadata about a generated project including name, stacks, domain, manifest, generated files list, validation report, and file paths.

---

### Download Project ZIP

```
GET /api/v1/projects/{project_id}/download
```

Returns the generated project as a downloadable ZIP file. If the ZIP is missing but the project directory exists, it will attempt to rebuild the ZIP automatically.

---

### Index Code into RAG

```
POST /api/v1/rag/index
```

Manually index code files into the ChromaDB vector store for future retrieval.

**Request Body:**
```json
{
  "paths": ["/path/to/code/directory"],
  "module_type": "hotel_management",
  "tags": ["booking", "dashboard"],
  "source_type": "repo"
}
```

---

### Search RAG

```
POST /api/v1/rag/search
```

Search the vector store for relevant code snippets.

**Request Body:**
```json
{
  "query": "Spring Boot authentication with JWT",
  "top_k": 5,
  "min_similarity": 0.3
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "...",
      "score": 0.87,
      "metadata": { "source_path": "...", "language": "java" }
    }
  ]
}
```

---

### Cache Lookup

```
GET /api/v1/cache/{fingerprint}
```

Look up a cached generation result by its request fingerprint.

---

### Web Discovery Preview

```
POST /api/v1/web-discovery/preview
```

Preview what the web discovery system would extract for a given prompt, without triggering a full generation.

**Request Body:**
```json
{
  "prompt": "Build a hotel booking system",
  "domain_hint": "hotel_management",
  "website_like": "https://booking.com"
}
```

**Response** includes: trusted web results, extracted features, entities, routes, UI components, backend patterns, suggested architecture, and a draft enriched prompt.

---

### Prometheus Metrics

```
GET /metrics
```

Exposes Prometheus-compatible metrics including generation counters, cache hit/miss rates, RAG retrieval latency, and per-stage timing histograms.

## Request and Response Formats

All API communication uses JSON. Request validation is handled by Pydantic models. Errors return:

```json
{
  "detail": "Description of the error"
}
```

HTTP status codes:
- `200` - Successful retrieval
- `202` - Job accepted (generation started)
- `404` - Resource not found
- `422` - Validation error (bad input)
- `500` - Internal server error / generation failure

## Generation Pipeline (Detailed Flow)

The `GenerationOrchestrator` (`app/services/generation/orchestrator.py`) executes a pipeline of 40+ stages. Each stage is timed, reports progress back to the job record, and is tracked by Prometheus metrics.

### Stage Groups

**1. Request Validation and Cache Check (Stages 1-3)**
- Validates backend/frontend are supported (`springboot`/`angular`)
- Computes a SHA-256 fingerprint from the prompt + stack + features
- Checks if an identical project already exists in the cache

**2. Prompt Analysis (Stages 4-6)**
- Parses the prompt to extract entities, features, project name, and summary
- Classifies the domain (e.g., `crm`, `hotel_management`, `ecommerce`, `general`)
- Expands features using domain-specific defaults

**3. Project Reuse Decision (Stages 7-11)**
- Searches the database for previously generated projects in the same domain
- Scores candidates by similarity to the current request
- Selects an execution mode:
  - **reuse**: An existing project is close enough; return it directly
  - **adapt**: An existing project is used as a base with modifications
  - **generate**: Create everything from scratch
  - **hybrid_scaffold**: Mix existing structure with fresh generation

**4. RAG Context Retrieval (Stage 12)**
- Queries ChromaDB with the prompt + domain + features
- Returns relevant code snippets from previously generated or indexed projects
- Used to enrich the generation prompt with real code patterns

**5. Web Discovery (Stages 13-22)**
- The `DiscoveryDecider` evaluates if web discovery would add value
- Builds search queries from the prompt, domain, and `website_like` URL
- Searches the web via SerpAPI or DuckDuckGo
- Filters results to trusted domains only
- Ranks results by relevance
- Fetches top pages and extracts structured knowledge:
  - Features, entities, routes, UI components, backend patterns
- Persists discovery metadata to the database
- Optionally indexes extracted knowledge into RAG for future use

**6. Project Specification and Prompt Building (Stages 23-27)**
- Builds a structured project spec from all gathered context
- Generates an API contract (REST endpoints, DTOs, relationships)
- Builds a file manifest
- Enriches the original prompt with RAG context, web discovery data, and scaffold strategy
- Persists the full prompt artifact for debugging/audit

**7. Code Generation (Stages 28-32)**
- **Spring Boot generator**: Controllers, services, repositories, entities, DTOs, configuration, security, exception handling
- **Angular generator**: Modules, components, services, routing, models, guards
- **Docker generator**: Backend Dockerfile, frontend Dockerfile (with nginx)
- **Compose generator**: docker-compose.yml with all services
- **README generator**: Project documentation with setup instructions

**8. Assembly and Validation (Stages 33-40)**
- Writes all generated files to the project directory
- Runs multi-layer validation:
  - Directory structure check
  - Required files presence check
  - Non-empty file check
  - Manifest consistency check
  - Path safety check (no directory traversal)
  - Optional syntax checks
- Runs auto-repair if validation fails
- Re-validates after repair
- Packages the project into a ZIP file

**9. Persistence and Indexing (Stages 41-43)**
- Saves the `Project` record to PostgreSQL
- Stores a `GenerationCache` entry for future deduplication
- Indexes the generated project files into ChromaDB for RAG reuse

## Background Processing (Celery)

Generation is a long-running operation (can take 30+ seconds). It runs asynchronously via Celery.

**Celery Configuration** (`app/tasks/celery_app.py`):
- Broker: Redis
- Serialization: JSON
- Task time limit: 1800 seconds (30 minutes)
- Soft time limit: 1700 seconds
- Late acknowledgment (`task_acks_late=True`) for reliability
- Prefetch multiplier: 1 (one task at a time per worker)
- Auto-retry on `OperationalError`, `ConnectionError`, `TimeoutError` with exponential backoff (up to 3 retries)

**Task Flow** (`app/tasks/generation_tasks.py`):
1. Celery receives `generate_project_task(job_id)`
2. Opens a DB session and loads the `Job` record
3. Sets job status to `running`
4. Creates a progress callback that updates `job.progress` and `job.current_stage` in the DB on each pipeline stage
5. Calls `GenerationOrchestrator.run()`
6. On success: sets status to `completed`, stores result data, auto-downloads ZIP to the user's Downloads folder
7. On failure: sets status to `failed`, stores the error message

Start the worker:
```bash
celery -A app.tasks.celery_app.celery_app worker --loglevel=INFO --concurrency=2
```

## Database Models

All models use UUID primary keys and have `created_at` / `updated_at` timestamps.

| Model | Table | Purpose |
|---|---|---|
| `Job` | `jobs` | Tracks generation requests. Stores prompt, stack, features, status, progress, stage timings, and the final result data. Linked to a `Project` on completion. |
| `Project` | `projects` | Stores metadata about a generated project: file paths, manifest, validation report, RAG summary, cache info. |
| `GenerationCache` | `generation_cache` | Maps request fingerprints to project IDs. Enables instant cache hits for identical requests. Tracks hit count. |
| `PromptArtifact` | `prompt_artifacts` | Full audit trail of prompt processing: raw prompt, parsed result, expanded features, RAG summary, web discovery summary, and the final enriched prompt sent to the LLM. |
| `RAGDocument` | `rag_documents` | Metadata for code files indexed in ChromaDB: source path, language, module type, tags, content hash. |
| `WebDiscoveryRun` | `web_discovery_runs` | Records a web discovery session: query, status, discovered count, summary. Linked to a job. |
| `WebSource` | `web_sources` | Individual URLs discovered during web search: URL, title, source type, trust score. Linked to a discovery run. |

Database migrations are managed with Alembic:
```bash
alembic upgrade head     # Apply all migrations
alembic revision --autogenerate -m "description"  # Create a new migration
```

## Main Services

### GenerationOrchestrator (`app/services/generation/orchestrator.py`)
The core pipeline controller. Initializes all sub-services and runs each stage through the `GenerationPipeline` which handles timing, progress reporting, and metrics.

### GenerationPipeline (`app/services/generation/pipeline.py`)
Executes individual stages with timing measurement and Prometheus metric tracking. Each stage call records its elapsed time in `stage_timings`.

### Code Generators (`app/services/generators/`)
Each generator produces a `dict[str, str]` mapping relative file paths to their content:
- **SpringBootGenerator**: Java source files with layered architecture
- **AngularGenerator**: TypeScript/HTML/CSS files with module structure
- **DockerGenerator**: Dockerfiles for both backend and frontend
- **ComposeGenerator**: docker-compose.yml
- **ReadmeGenerator**: Project README.md

### ProjectValidator (`app/services/generation/validator.py`)
Validates generated projects across multiple dimensions: structure, required files, non-empty files, manifest consistency, and path safety.

### RepairEngine (`app/services/generation/repair_engine.py`)
Automatically attempts to fix validation failures (e.g., missing required files, empty files).

### OpenAIProvider (`app/services/llm/openai_provider.py`)
Wraps the OpenAI API with retry logic (exponential backoff, 3 attempts). Provides methods for text generation, structured JSON generation, and code block generation. Falls back to a stub response if `OPENAI_API_KEY` is not configured.

### PromptEnricher (`app/services/intelligence/prompt_enricher.py`)
Combines the user's original prompt with project spec, API contract, RAG context, scaffold strategy, and web discovery data into a final enriched prompt.

### DomainClassifier (`app/services/intelligence/domain_classifier.py`)
Analyzes the parsed prompt to classify the project domain (e.g., `crm`, `hotel_management`, `ecommerce`).

### FeatureExpander (`app/services/intelligence/feature_expander.py`)
Expands user-provided features with domain-specific defaults (e.g., a `hotel_management` domain automatically adds `booking`, `dashboard`, `reports`).

## Web Discovery

Web discovery enriches the generation process with patterns from real-world websites and repositories. The flow:

1. **Decision** (`DiscoveryDecider`): Evaluates whether web discovery would add value based on prompt complexity, domain, RAG confidence, and whether a `website_like` URL was provided
2. **Search** (`SearchClient`): Queries SerpAPI or DuckDuckGo for relevant pages
3. **Filter** (`TrustedSourceFilter`): Keeps only results from allowed domains, removes denied domains
4. **Rank** (`ResultRanker`): Scores results by relevance to the query
5. **Fetch** (`PageFetcher`): Downloads and extracts content from top-ranked pages
6. **Extract** (multiple extractors): Pulls structured data - features, entities, routes, components, UI patterns, backend patterns
7. **Persist**: Stores discovery metadata in `web_discovery_runs` and `web_sources` tables
8. **Index**: Optionally feeds extracted knowledge back into RAG

## RAG (Retrieval-Augmented Generation)

The RAG system uses ChromaDB as a vector store to provide relevant code context during generation.

**Indexing** (`RAGIndexer`):
- Reads code files from specified paths
- Splits them into chunks
- Generates embeddings (OpenAI text-embedding-3-small)
- Stores chunks in ChromaDB with metadata (language, module type, tags, source path)
- Records metadata in the `rag_documents` table

**Retrieval** (`RAGRetriever`):
- Accepts a query string, top_k, and minimum similarity threshold
- Searches ChromaDB for the most similar chunks
- Returns content, score, and metadata

**Post-Generation Indexing** (`PostGenerationIndexer`):
- After a project is successfully generated, its files are automatically indexed back into RAG
- This makes patterns from each generated project available for future generations, creating a self-improving feedback loop

## Caching and Fingerprinting

The platform avoids redundant generation through fingerprint-based caching:

1. **Fingerprint computation** (`FingerprintService`): Creates a deterministic SHA-256 hash from the prompt + backend + frontend + features + domain + blueprint
2. **Cache lookup**: Before starting generation, the system checks `generation_cache` for an existing entry with the same fingerprint
3. **Cache hit**: If found and the project files still exist on disk, the job completes instantly by reusing the cached project
4. **Cache storage**: After successful generation, a new cache entry is created linking the fingerprint to the project

## Generated Project Output

Each generated project is written to `generated_projects/{name}-{id_prefix}/` and includes:

```
my-crm-a1b2c3d4/
├── backend/
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/main/
│       ├── java/com/example/mycrm/
│       │   ├── controller/
│       │   ├── service/
│       │   ├── repository/
│       │   ├── entity/
│       │   ├── dto/
│       │   ├── config/
│       │   └── exception/
│       └── resources/
│           └── application.yml
├── frontend/
│   ├── package.json
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── main.ts
│       └── app/
│           ├── modules/
│           ├── services/
│           ├── guards/
│           └── models/
├── docker-compose.yml
├── .env.example
├── README.md
├── manifest.json
└── _meta/
    ├── final_enriched_prompt.txt
    └── final_enriched_prompt.json
```

The project is also packaged as a ZIP and automatically copied to the user's Downloads folder.

## Observability

- **Prometheus metrics** at `/metrics`: Generation counters (completed/failed/cached), cache hit/miss rates, RAG retrieval latency, per-stage timing
- **Structured logging**: All services use a centralized logger with context
- **Trace IDs**: Each generation job gets a unique trace ID for request correlation
- **Stage timings**: Every pipeline stage records its execution time, returned in the job result
- **Prompt artifacts**: Full audit trail of how the prompt was processed, stored in the database and as files in the project's `_meta/` directory

## Local Development Without Docker

If you prefer to run services directly:

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start PostgreSQL and Redis (must be running separately)

# 4. Create your .env file
cp .env.example .env

# 5. Run database migrations
alembic upgrade head

# 6. Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. Start the Celery worker (in a separate terminal)
celery -A app.tasks.celery_app.celery_app worker --loglevel=INFO
```

## Testing

```bash
pytest -q
```

## Additional Documentation

<<<<<<< HEAD
<<<<<<< HEAD
- `docs/FULL_PROCESS_GUIDE.md` - Detailed runtime flow documentation
- `docs/QUICK_REFERENCE.md` - Quick reference card
- `docs/RAG_CODE_GENERATION_GUIDE.md` - RAG system deep dive
- `docs/TEMPLATE_CATALOG.md` - Available code generation templates
- `docs/TEMPLATE_REFERENCE_GUIDE.md` - Template authoring guide
=======
echo "# python_foundry_dupli" >> README.md
>>>>>>> c2fee84e (Initial commit to new repo)
=======
echo "# python_foundry" >> README.md
>>>>>>> 54c87fc2 (upload latest code with template)



run backend 
cd "/Users/m5/paxarisglobal product/python_foundry_code/python_foundry"
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


run celery
cd "/Users/m5/paxarisglobal product/python_foundry_code/python_foundry"
source .venv/bin/activate
PYTHONPATH=. celery -A app.tasks.celery_app.celery_app worker --loglevel=INFO --pool=solo -n clean_worker@%h