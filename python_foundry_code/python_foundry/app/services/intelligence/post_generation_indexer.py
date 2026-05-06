from sqlalchemy.orm import Session

from app.services.rag.indexer import RAGIndexer


class PostGenerationIndexer:
    def __init__(self, db: Session):
        self.indexer = RAGIndexer(db=db)

    def index_generated_project(self, project_path: str, domain: str, tags: list[str]) -> dict:
        return self.indexer.index_paths(
            paths=[project_path],
            module_type=domain,
            tags=tags,
            source_type="generated_project",
        )
