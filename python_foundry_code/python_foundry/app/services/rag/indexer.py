from typing import Optional

from pathlib import Path

from sqlalchemy.orm import Session

from app.models.rag_document import RAGDocument
from app.services.rag.chroma_service import ChromaService
from app.services.rag.chunker import CodeChunker
from app.services.rag.embedding_service import EmbeddingService
from app.utils.file_utils import is_text_file
from app.utils.hashing import sha256_text

SUPPORTED_EXTENSIONS = {
    ".py",
    ".java",
    ".ts",
    ".js",
    ".html",
    ".css",
    ".json",
    ".yml",
    ".yaml",
    ".xml",
    ".md",
}


class RAGIndexer:
    def __init__(self, db: Session):
        self.db = db
        self.chroma = ChromaService()
        self.embedding = EmbeddingService()
        self.chunker = CodeChunker(chunk_size=1200, chunk_overlap=120)

    def index_paths(
        self,
        paths: list[str],
        module_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        source_type: str = "repo",
    ) -> dict:
        tags = tags or []
        collection = self.chroma.get_collection()

        indexed_chunks = 0
        indexed_files = 0

        for raw_path in paths:
            base = Path(raw_path)
            if not base.exists():
                continue

            for file_path in base.rglob("*"):
                prepared = self._prepare_file_chunks(file_path)
                if not prepared:
                    continue

                chunks, embeddings = prepared
                ids, metadatas = self._build_chunk_metadata(
                    file_path=file_path,
                    chunks=chunks,
                    module_type=module_type,
                    tags=tags,
                    source_type=source_type,
                )

                collection.add(ids=ids, documents=chunks, metadatas=metadatas, embeddings=embeddings)
                indexed_chunks += len(chunks)
                indexed_files += 1

        self.db.commit()
        return {
            "indexed_files": indexed_files,
            "indexed_chunks": indexed_chunks,
        }

    @staticmethod
    def _is_supported(file_path: Path) -> bool:
        return file_path.suffix.lower() in SUPPORTED_EXTENSIONS or file_path.name == "Dockerfile"

    @staticmethod
    def _language_for(file_path: Path) -> str:
        if file_path.name == "Dockerfile":
            return "docker"
        suffix = file_path.suffix.lower().lstrip(".")
        return suffix or "text"

    def _prepare_file_chunks(self, file_path: Path) -> Optional[tuple[list[str], list[list[float]]]]:
        if not file_path.is_file() or not self._is_supported(file_path) or not is_text_file(file_path):
            return None

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            return None

        chunks = self.chunker.chunk(content)
        if not chunks:
            return None

        embeddings = self.embedding.embed_texts(chunks)
        return chunks, embeddings

    def _build_chunk_metadata(
        self,
        file_path: Path,
        chunks: list[str],
        module_type: Optional[str],
        tags: list[str],
        source_type: str,
    ) -> tuple[list[str], list[dict]]:
        ids: list[str] = []
        metadatas: list[dict] = []
        language = self._language_for(file_path)

        for idx, chunk in enumerate(chunks):
            content_hash = sha256_text(f"{file_path}:{idx}:{chunk[:100]}")
            metadata = {
                "file_path": str(file_path),
                "language": language,
                "module_type": module_type or "general",
                "source_type": source_type,
                "tags": ",".join(tags) if tags else "",
                "chunk_index": idx,
            }
            ids.append(content_hash)
            metadatas.append(metadata)

            self.db.add(
                RAGDocument(
                    source_path=str(file_path),
                    language=language,
                    module_type=module_type,
                    source_type=source_type,
                    tags=tags,
                    content_hash=content_hash,
                    doc_metadata=metadata,
                )
            )

        return ids, metadatas
