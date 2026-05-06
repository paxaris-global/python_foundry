import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class WebDiscoveryRun(Base, TimestampMixin):
    __tablename__ = "web_discovery_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), index=True)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="completed", nullable=False)
    discovered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[dict] = mapped_column(JSONB, default=dict)
