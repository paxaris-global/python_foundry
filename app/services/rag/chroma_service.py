from chromadb import PersistentClient
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings


class ChromaService:
    def __init__(self) -> None:
        settings = get_settings()
        # Explicitly disable telemetry to avoid runtime capture() signature errors.
        telemetry_enabled = bool(settings.chroma_telemetry and settings.anonymized_telemetry)
        self.client = PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=telemetry_enabled,
                chroma_product_telemetry_impl="app.services.rag.noop_telemetry.NoOpProductTelemetryClient",
                chroma_telemetry_impl="app.services.rag.noop_telemetry.NoOpProductTelemetryClient",
            ),
        )

    def get_collection(self, name: str = "codegen_docs") -> Collection:
        return self.client.get_or_create_collection(name=name)

    def health(self) -> bool:
        try:
            _ = self.get_collection()
            return True
        except Exception:
            return False
