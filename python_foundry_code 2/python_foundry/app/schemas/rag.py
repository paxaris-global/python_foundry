from pydantic import BaseModel, Field


class RAGIndexRequest(BaseModel):
    paths: list[str] = Field(min_length=1)
    module_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_type: str = Field(default="repo")


class RAGSearchRequest(BaseModel):
    query: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)


class RAGSearchResult(BaseModel):
    content: str
    score: float | None = None
    metadata: dict


class RAGSearchResponse(BaseModel):
    results: list[RAGSearchResult]
