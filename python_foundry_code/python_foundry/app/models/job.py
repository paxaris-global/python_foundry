from typing import Optional

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name: Mapped[str] = mapped_column(String(150), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    backend: Mapped[str] = mapped_column(String(50), default="springboot", nullable=False)
    frontend: Mapped[str] = mapped_column(String(50), default="angular", nullable=False)
    features: Mapped[list[str]] = mapped_column(JSONB, default=list)
    website_like: Mapped[Optional[str]] = mapped_column(String(120))
    mode_preference: Mapped[str] = mapped_column(String(30), default="auto", nullable=False)
    mode_selected: Mapped[Optional[str]] = mapped_column(String(30))
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.pending, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_stage: Mapped[str] = mapped_column(String(120), default="pending", nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text)
    trace_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    cache_hit: Mapped[bool] = mapped_column(default=False, nullable=False)
    stage_timings: Mapped[dict] = mapped_column(JSONB, default=dict)
    result_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255))
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
