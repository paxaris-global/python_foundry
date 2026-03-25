from fastapi import APIRouter

from app.api.deps import DBSession
from app.core.exceptions import NotFoundException
from app.models.generation_cache import GenerationCache

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/{fingerprint}")
def get_cache_entry(fingerprint: str, db: DBSession) -> dict:
    row = db.query(GenerationCache).filter(GenerationCache.fingerprint == fingerprint).first()
    if not row:
        raise NotFoundException("Cache entry not found")

    return {
        "fingerprint": row.fingerprint,
        "project_id": str(row.project_id) if row.project_id else None,
        "hit_count": row.hit_count,
        "request_payload": row.request_payload,
        "cache_metadata": row.cache_metadata,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }
