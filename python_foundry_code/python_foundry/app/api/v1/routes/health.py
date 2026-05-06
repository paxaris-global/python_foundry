from fastapi import APIRouter
from redis import Redis

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import engine
from app.schemas.common import DependencyStatus, HealthCheckResponse
from app.services.rag.chroma_service import ChromaService

router = APIRouter(prefix="/health", tags=["Health"])
logger = get_logger(__name__)


@router.get(
    "",
    response_model=HealthCheckResponse,
    summary="Platform health check",
    description="Returns the aggregate health of the platform and each backing service (database, Redis, ChromaDB).",
)
def health_check() -> HealthCheckResponse:
    settings = get_settings()

    db_status = "up"
    redis_status = "up"
    chroma_status = "up"

    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception:
        logger.warning("Health check: database is down", exc_info=True)
        db_status = "down"

    try:
        redis_client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        redis_client.ping()
    except Exception:
        logger.warning("Health check: Redis is down", exc_info=True)
        redis_status = "down"

    try:
        _ = ChromaService().get_collection()
    except Exception:
        logger.warning("Health check: ChromaDB is down", exc_info=True)
        chroma_status = "down"

    overall = "ok" if db_status == "up" and redis_status == "up" else "degraded"

    return HealthCheckResponse(
        status=overall,
        service="ai-codegen-platform",
        dependencies=DependencyStatus(
            db=db_status,
            redis=redis_status,
            chroma=chroma_status,
        ),
    )
