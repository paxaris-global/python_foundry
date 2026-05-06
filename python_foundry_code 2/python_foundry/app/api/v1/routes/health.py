from fastapi import APIRouter
from redis import Redis

from app.core.config import get_settings
from app.db.session import engine
from app.services.rag.chroma_service import ChromaService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict:
    settings = get_settings()

    db_status = "up"
    redis_status = "up"
    chroma_status = "up"

    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception:
        db_status = "down"

    try:
        redis_client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        redis_client.ping()
    except Exception:
        redis_status = "down"

    try:
        _ = ChromaService().get_collection()
    except Exception:
        chroma_status = "down"

    overall = "ok" if db_status == "up" and redis_status == "up" else "degraded"

    return {
        "status": overall,
        "service": "ai-codegen-platform",
        "dependencies": {
            "db": db_status,
            "redis": redis_status,
            "chroma": chroma_status,
        },
    }
