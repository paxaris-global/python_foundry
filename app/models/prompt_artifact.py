from typing import Optional

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PromptArtifact(Base, TimestampMixin):
    __tablename__ = "prompt_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))

    raw_user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_prompt: Mapped[dict] = mapped_column(JSONB, default=dict)
    parsed_prompt_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    expanded_features: Mapped[list[str]] = mapped_column(JSONB, default=list)
    execution_mode: Mapped[str] = mapped_column(String(30), default="generate", nullable=False)
    rag_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    rag_context_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    web_discovery_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    adaptation_context_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    trusted_sources: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    pre_final_prompt: Mapped[Optional[str]] = mapped_column(Text)
    final_enriched_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_text_path: Mapped[Optional[str]] = mapped_column(Text)
    artifact_json_path: Mapped[Optional[str]] = mapped_column(Text)
