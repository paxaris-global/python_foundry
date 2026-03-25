from sqlalchemy.orm import Session

from app.models.generation_cache import GenerationCache
from app.models.project import Project


class GenerationCacheService:
    def __init__(self, db: Session):
        self.db = db

    def lookup(self, fingerprint: str) -> GenerationCache | None:
        cache = self.db.query(GenerationCache).filter(GenerationCache.fingerprint == fingerprint).first()
        if cache:
            cache.hit_count += 1
            self.db.commit()
            self.db.refresh(cache)
        return cache

    def store(
        self,
        fingerprint: str,
        project: Project,
        request_payload: dict,
        cache_metadata: dict,
    ) -> GenerationCache:
        existing = self.db.query(GenerationCache).filter(GenerationCache.fingerprint == fingerprint).first()
        if existing:
            existing.project_id = project.id
            existing.request_payload = request_payload
            existing.cache_metadata = cache_metadata
            self.db.commit()
            self.db.refresh(existing)
            return existing

        cache = GenerationCache(
            fingerprint=fingerprint,
            project_id=project.id,
            request_payload=request_payload,
            cache_metadata=cache_metadata,
        )
        self.db.add(cache)
        self.db.commit()
        self.db.refresh(cache)
        return cache
