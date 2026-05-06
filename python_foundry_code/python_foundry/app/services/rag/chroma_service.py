from chromadb import PersistentClient
from chromadb.api.models.Collection import Collection

from app.core.config import get_settings


class ChromaService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = PersistentClient(path=settings.chroma_persist_directory)

    def get_collection(self, name: str = "codegen_docs") -> Collection:
        return self.client.get_or_create_collection(name=name)

    def health(self) -> bool:
        try:
            _ = self.get_collection()
            return True
        except Exception:
            return False
