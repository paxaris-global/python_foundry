from sqlalchemy.orm import Session

from app.models.rag_document import RAGDocument
from app.services.rag.chroma_service import ChromaService
from app.services.rag.embedding_service import EmbeddingService
from app.utils.hashing import sha256_text


class RAGSourceIngestor:
    def __init__(self, db: Session):
        self.db = db
        self.chroma = ChromaService()
        self.embedding = EmbeddingService()

    def ingest_documents(
        self,
        docs: list[dict],
        module_type: str,
        tags: list[str],
        source_type: str,
    ) -> dict:
        if not docs:
            return {"indexed_documents": 0}

        collection = self.chroma.get_collection()

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []

        for idx, doc in enumerate(docs):
            text = doc.get("content", "").strip()
            if not text:
                continue

            doc_id = sha256_text(f"{source_type}:{module_type}:{idx}:{text[:160]}")
            metadata = {
                "file_path": doc.get("source", doc.get("url", "web-discovery")),
                "language": doc.get("language", "text"),
                "module_type": module_type,
                "source_type": source_type,
                "source_url": doc.get("url"),
                "trust_score": doc.get("trust_score"),
                "tags": tags,
            }

            ids.append(doc_id)
            documents.append(text)
            metadatas.append(metadata)

            self.db.add(
                RAGDocument(
                    source_path=metadata["file_path"],
                    language=metadata["language"],
                    module_type=module_type,
                    source_type=source_type,
                    tags=tags,
                    content_hash=doc_id,
                    doc_metadata=metadata,
                )
            )

        if not documents:
            return {"indexed_documents": 0}

        embeddings = self.embedding.embed_texts(documents)
        collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        self.db.commit()

        return {"indexed_documents": len(documents)}
