"""PGVector-backed vector store — replaces ChromaDB."""
from __future__ import annotations

import uuid
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Text, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Session

from app.models.rag_document import RAGDocument


class PGVectorService:
    """Thin wrapper around PostgreSQL + pgvector for upsert and similarity search."""

    COLLECTION_COLUMN = "collection_name"
    VECTOR_DIM = 1536  # text-embedding-3-small / ada-002

    # ------------------------------------------------------------------
    # Public API (mirrors the ChromaDB collection API used across the app)
    # ------------------------------------------------------------------

    def upsert(
        self,
        db: Session,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        collection: str = "codegen_docs",
    ) -> None:
        """Insert or update chunks in the rag_documents table."""
        for i, doc_id in enumerate(ids):
            existing = db.execute(
                select(RAGDocument).where(RAGDocument.content_hash == doc_id)
            ).scalar_one_or_none()

            meta = metadatas[i] if i < len(metadatas) else {}
            embedding = embeddings[i] if i < len(embeddings) else []

            if existing:
                existing.embedding = embedding
                existing.doc_metadata = {**meta, "collection": collection}
            else:
                db.add(
                    RAGDocument(
                        id=uuid.uuid4(),
                        source_path=meta.get("file_path", "unknown"),
                        language=meta.get("language", "text"),
                        module_type=meta.get("module_type"),
                        source_type=meta.get("source_type", "repo"),
                        tags=meta.get("tags", []),
                        content_hash=doc_id,
                        chunk_text=documents[i],
                        embedding=embedding,
                        doc_metadata={**meta, "collection": collection},
                    )
                )

    def search(
        self,
        db: Session,
        query_embedding: list[float],
        top_k: int = 5,
        collection: str = "codegen_docs",
    ) -> list[dict]:
        """Return top-k most similar chunks using cosine distance (<=>)."""
        rows = db.execute(
            select(
                RAGDocument,
                RAGDocument.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .where(RAGDocument.embedding.is_not(None))
            .order_by("distance")
            .limit(top_k)
        ).all()

        results = []
        for row, distance in rows:
            similarity = 1.0 - float(distance)
            results.append(
                {
                    "content": row.chunk_text or "",
                    "metadata": row.doc_metadata or {},
                    "score": round(similarity, 4),
                }
            )
        return results

    def health(self, db: Session) -> bool:
        try:
            db.execute(select(RAGDocument).limit(1))
            return True
        except Exception:
            return False
