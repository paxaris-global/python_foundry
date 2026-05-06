from typing import Optional

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class GenerationCache(Base, TimestampMixin):
    __tablename__ = "generation_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fingerprint: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    request_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    cache_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    hit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
