from fastapi import APIRouter

from app.api.deps import DBSession
from app.schemas.rag import RAGIndexRequest, RAGSearchRequest, RAGSearchResponse, RAGSearchResult
from app.services.rag.indexer import RAGIndexer
from app.services.rag.retriever import RAGRetriever

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/index")
def index_rag(payload: RAGIndexRequest, db: DBSession) -> dict:
    indexer = RAGIndexer(db=db)
    result = indexer.index_paths(
        paths=payload.paths,
        module_type=payload.module_type,
        tags=payload.tags,
        source_type=payload.source_type,
    )
    return {"status": "ok", **result}


@router.post("/search")
def search_rag(payload: RAGSearchRequest) -> RAGSearchResponse:
    retriever = RAGRetriever()
    hits = retriever.search(query=payload.query, top_k=payload.top_k, min_similarity=payload.min_similarity)
    return RAGSearchResponse(
        results=[
            RAGSearchResult(content=item["content"], score=item.get("score"), metadata=item.get("metadata", {}))
            for item in hits
        ]
    )
