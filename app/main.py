from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.api.v1.routes.cache import router as cache_router
from app.api.v1.routes.generate import router as generate_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.jobs import router as jobs_router
from app.api.v1.routes.projects import router as projects_router
from app.api.v1.routes.rag import router as rag_router
from app.api.v1.routes.web_discovery import router as web_discovery_router
from app.core.constants import API_PREFIX
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.db.init_db import init_db

setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="AI Code Generation Platform", version="1.0.0")

register_exception_handlers(app)

app.include_router(health_router, prefix=API_PREFIX)
app.include_router(generate_router, prefix=API_PREFIX)
app.include_router(jobs_router, prefix=API_PREFIX)
app.include_router(projects_router, prefix=API_PREFIX)
app.include_router(rag_router, prefix=API_PREFIX)
app.include_router(cache_router, prefix=API_PREFIX)
app.include_router(web_discovery_router, prefix=API_PREFIX)
app.mount("/metrics", make_asgi_app())


@app.on_event("startup")
def on_startup() -> None:
    try:
        init_db()
    except Exception as exc:
        logger.warning("Database not reachable during startup: %s", exc)
