import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class RAGDocument(Base, TimestampMixin):
    __tablename__ = "rag_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(30), nullable=False)
    module_type: Mapped[str | None] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50), default="repo", nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    doc_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
