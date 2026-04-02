from typing import Optional

import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    backend_stack: Mapped[str] = mapped_column(String(50), nullable=False)
    frontend_stack: Mapped[str] = mapped_column(String(50), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(30), default="generate", nullable=False)
    domain: Mapped[str] = mapped_column(String(100), default="general", nullable=False)
    blueprint_used: Mapped[Optional[str]] = mapped_column(String(120))
    project_path: Mapped[str] = mapped_column(Text, nullable=False)
    zip_path: Mapped[str] = mapped_column(Text, nullable=False)
    manifest: Mapped[dict] = mapped_column(JSONB, default=dict)
    rag_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    cache_info: Mapped[dict] = mapped_column(JSONB, default=dict)
    final_prompt_text_path: Mapped[Optional[str]] = mapped_column(Text)
    final_prompt_json_path: Mapped[Optional[str]] = mapped_column(Text)
    generated_files: Mapped[list[str]] = mapped_column(JSONB, default=list)
    validation_report: Mapped[dict] = mapped_column(JSONB, default=dict)
