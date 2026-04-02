from typing import Annotated

from fastapi import APIRouter, Path

from app.api.deps import DBSession
from app.core.exceptions import NotFoundException, ServiceUnavailableException
from app.core.logging import get_logger
from app.models.generation_cache import GenerationCache
from app.schemas.common import CacheEntryResponse, ErrorResponse

router = APIRouter(prefix="/cache", tags=["Cache"])
logger = get_logger(__name__)

FingerprintPath = Annotated[str, Path(
    description="Content fingerprint (SHA-256 hash) identifying the cache entry. "
                "Returned by POST /generate in the fingerprint field.",
    examples=["sha256:abc123def456"],
)]


@router.get(
    "/{fingerprint}",
    response_model=CacheEntryResponse,
    summary="Look up a cache entry",
    description="Retrieve a generation-cache entry by its content fingerprint. "
                "Returns the linked project reference, original request payload, and hit statistics.",
    responses={
        404: {"description": "Cache entry not found.", "model": ErrorResponse},
        503: {"description": "Service unavailable.", "model": ErrorResponse},
    },
)
def get_cache_entry(fingerprint: FingerprintPath, db: DBSession) -> CacheEntryResponse:
    try:
        row = db.query(GenerationCache).filter(GenerationCache.fingerprint == fingerprint).first()
    except Exception:
        logger.exception("Database error looking up cache entry fingerprint=%s", fingerprint)
        raise ServiceUnavailableException("Cache lookup failed due to a database error")

    if not row:
        raise NotFoundException("Cache entry not found")

    return CacheEntryResponse(
        fingerprint=row.fingerprint,
        project_id=str(row.project_id) if row.project_id else None,
        hit_count=row.hit_count,
        request_payload=row.request_payload,
        cache_metadata=row.cache_metadata,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
