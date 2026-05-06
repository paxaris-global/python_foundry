from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class RAGIndexRequest(BaseModel):
    """Request to index one or more file paths into the RAG vector store."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "paths": ["/data/repos/my-crm/src"],
            "module_type": "backend",
            "tags": ["springboot", "java"],
            "source_type": "repo",
        }
    })

    paths: list[str] = Field(
        min_length=1,
        description="File or directory paths to index. Each path is walked recursively; supported file types are chunked and embedded.",
    )
    module_type: Optional[str] = Field(
        default=None,
        description="Module classification applied to every chunk (e.g. 'backend', 'frontend', 'crm').",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Freeform tags attached to every indexed document for later filtering.",
    )
    source_type: str = Field(
        default="repo",
        description="Origin type of the content being indexed (e.g. 'repo', 'web_discovery').",
    )


class RAGIndexResponse(BaseModel):
    """Result summary after indexing content into the RAG store."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "ok",
            "indexed_files": 42,
            "indexed_chunks": 318,
        }
    })

    status: Literal["ok"] = Field(description="Indexing outcome. Always 'ok' on success; failures return an error response.")
    indexed_files: int = Field(ge=0, description="Number of source files that were successfully chunked and embedded.")
    indexed_chunks: int = Field(ge=0, description="Total number of text chunks upserted into the vector store.")


class RAGSearchRequest(BaseModel):
    """Query the RAG vector store for relevant code/document fragments."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query": "Spring Boot authentication filter",
            "top_k": 5,
            "min_similarity": 0.3,
        }
    })

    query: str = Field(min_length=3, description="Natural-language or code-like search query.")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of results to return (1–20).")
    min_similarity: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Minimum cosine-similarity threshold (0.0–1.0). Results below this score are discarded.",
    )


class RAGSearchResult(BaseModel):
    """A single RAG search hit."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "content": "@Configuration public class SecurityConfig …",
            "score": 0.87,
            "metadata": {"file_path": "src/SecurityConfig.java", "module_type": "backend", "language": "java"},
        }
    })

    content: str = Field(description="The matched text chunk.")
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Cosine-similarity score (0.0–1.0). Higher is more relevant.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Chunk metadata: file_path, language, module_type, source_type, tags, chunk_index.",
    )


class RAGSearchResponse(BaseModel):
    """Ranked list of RAG search results."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "results": [
                {"content": "@Configuration public class SecurityConfig …", "score": 0.87, "metadata": {"file_path": "src/SecurityConfig.java", "module_type": "backend"}},
            ]
        }
    })

    results: list[RAGSearchResult] = Field(description="Matching chunks ordered by descending similarity score.")
