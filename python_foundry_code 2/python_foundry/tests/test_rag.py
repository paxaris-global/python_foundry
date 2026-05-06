from fastapi.testclient import TestClient

from app.api import deps
from app.main import app
from app.services.rag.indexer import RAGIndexer
from app.services.rag.retriever import RAGRetriever


def test_rag_search(monkeypatch) -> None:
    monkeypatch.setattr(
        RAGRetriever,
        "search",
        lambda self, query, top_k=5, min_similarity=0.0: [
            {"content": "example", "score": 0.92, "metadata": {"file_path": "demo.py"}}
        ],
    )

    client = TestClient(app)
    response = client.post("/api/v1/rag/search", json={"query": "auth flow", "top_k": 3, "min_similarity": 0.5})

    assert response.status_code == 200
    assert len(response.json()["results"]) == 1


def test_rag_index(monkeypatch) -> None:
    class _Session:
        pass

    def _override_db():
        yield _Session()

    app.dependency_overrides.clear()
    app.dependency_overrides[deps.get_db] = _override_db

    monkeypatch.setattr(
        RAGIndexer,
        "index_paths",
        lambda self, paths, module_type=None, tags=None, source_type="repo": {"indexed_files": 1, "indexed_chunks": 2},
    )

    client = TestClient(app)
    response = client.post("/api/v1/rag/index", json={"paths": ["."], "tags": ["demo"], "source_type": "repo"})

    assert response.status_code == 200
    assert response.json()["indexed_files"] == 1

    app.dependency_overrides.clear()
