from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.v1.routes.cache import router as cache_router
from app.api.v1.routes.generate import router as generate_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.jobs import router as jobs_router
from app.api.v1.routes.projects import router as projects_router
from app.api.v1.routes.rag import router as rag_router
from app.api.v1.routes.web_discovery import router as web_discovery_router
from app.api.v1.routes.debug import router as debug_router
from app.core.constants import API_PREFIX
from app.core.exceptions import register_exception_handlers
from app.schemas.common import ErrorResponse
from app.core.logging import get_logger, setup_logging
from app.db.init_db import init_db

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        init_db()
    except Exception as exc:
        logger.warning("Database not reachable during startup: %s", exc)
    yield


OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "Generate",
        "description": "Submit code-generation requests and receive job handles.",
    },
    {
        "name": "Jobs",
        "description": "Poll job status, progress, and retrieve prompt-debug artifacts.",
    },
    {
        "name": "Projects",
        "description": "Inspect and download generated project artefacts.",
    },
    {
        "name": "Cache",
        "description": "Look up generation-cache entries by fingerprint.",
    },
    {
        "name": "RAG",
        "description": "Index content into and search the retrieval-augmented generation vector store.",
    },
    {
        "name": "Web Discovery",
        "description": "Preview web-discovery results for a prompt before generation.",
    },
    {
        "name": "Health",
        "description": "Platform and dependency health checks.",
    },
]

def _simplify_operation_ids(application: FastAPI) -> None:
    """Strip the auto-generated path suffix from operation IDs so they read as
    clean function names (e.g. ``create_generation_job`` instead of
    ``create_generation_job_api_v1_generate_post``)."""
    for route in application.routes:
        if hasattr(route, "operation_id") and hasattr(route, "endpoint"):
            route.operation_id = route.endpoint.__name__


app = FastAPI(
    title="AI Code Generation Platform",
    description=(
        "Backend API for the AI-powered code generation platform.\n\n"
        "Accepts natural-language project descriptions, orchestrates LLM-based code generation "
        "with RAG retrieval and web discovery, and delivers downloadable project archives.\n\n"
        "## Key workflows\n\n"
        "1. **Generate** – submit a project spec and receive a job handle.\n"
        "2. **Poll** – watch job progress until completion.\n"
        "3. **Download** – retrieve the generated project as a ZIP archive.\n\n"
        "Cache look-ups, RAG indexing/search, and web-discovery preview are also exposed for "
        "advanced integrations."
    ),
    version="1.0.0",
    contact={
        "name": "AI CodeGen Platform Team",
        "url": "https://github.com/ai-codegen-platform",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
    responses={
        422: {"description": "Request validation failed.", "model": ErrorResponse},
        500: {"description": "Unexpected internal error.", "model": ErrorResponse},
        503: {"description": "A backing service (database, task queue, vector store) is unavailable.", "model": ErrorResponse},
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health_router, prefix=API_PREFIX)
app.include_router(generate_router, prefix=API_PREFIX)
app.include_router(jobs_router, prefix=API_PREFIX)
app.include_router(projects_router, prefix=API_PREFIX)
app.include_router(rag_router, prefix=API_PREFIX)
app.include_router(cache_router, prefix=API_PREFIX)
app.include_router(web_discovery_router, prefix=API_PREFIX)
app.include_router(debug_router, prefix=API_PREFIX)

_simplify_operation_ids(app)

app.mount("/metrics", make_asgi_app())
