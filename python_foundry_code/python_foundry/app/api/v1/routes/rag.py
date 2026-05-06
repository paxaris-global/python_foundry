from fastapi import APIRouter

from app.api.deps import DBSession
from app.core.exceptions import ServiceUnavailableException
from app.core.logging import get_logger
from app.schemas.common import ErrorResponse
from app.schemas.rag import RAGIndexRequest, RAGIndexResponse, RAGSearchRequest, RAGSearchResponse, RAGSearchResult
from app.services.rag.indexer import RAGIndexer
from app.services.rag.retriever import RAGRetriever

router = APIRouter(prefix="/rag", tags=["RAG"])
logger = get_logger(__name__)


@router.post(
    "/index",
    response_model=RAGIndexResponse,
    summary="Index content into RAG store",
    description="Reads files from the given paths, chunks them, and upserts embeddings into the ChromaDB vector store.",
    responses={
        422: {"description": "Invalid index request.", "model": ErrorResponse},
        503: {"description": "RAG service unavailable.", "model": ErrorResponse},
    },
)
def index_rag(payload: RAGIndexRequest, db: DBSession) -> RAGIndexResponse:
    try:
        indexer = RAGIndexer(db=db)
        result = indexer.index_paths(
            paths=payload.paths,
            module_type=payload.module_type,
            tags=payload.tags,
            source_type=payload.source_type,
        )
    except Exception:
        logger.exception("RAG indexing failed for paths=%s", payload.paths)
        raise ServiceUnavailableException("RAG indexing failed. The vector store or database may be unavailable.")
    return RAGIndexResponse(status="ok", **result)


@router.post(
    "/search",
    response_model=RAGSearchResponse,
    summary="Search the RAG store",
    description="Performs a semantic similarity search against indexed code and documents, returning the top-k most relevant fragments.",
    responses={
        422: {"description": "Invalid search request.", "model": ErrorResponse},
        503: {"description": "RAG service unavailable.", "model": ErrorResponse},
    },
)
def search_rag(payload: RAGSearchRequest) -> RAGSearchResponse:
    try:
        retriever = RAGRetriever()
        hits = retriever.search(query=payload.query, top_k=payload.top_k, min_similarity=payload.min_similarity)
    except Exception:
        logger.exception("RAG search failed for query=%s", payload.query[:100])
        raise ServiceUnavailableException("RAG search failed. The vector store may be unavailable.")
    return RAGSearchResponse(
        results=[
            RAGSearchResult(content=item["content"], score=item.get("score"), metadata=item.get("metadata", {}))
            for item in hits
        ]
    )
