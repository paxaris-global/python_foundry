from typing import Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    project_name: str = Field(min_length=2, max_length=120)
    prompt: str | None = Field(default=None, min_length=10)
    backend: Literal["springboot"] = Field(default="springboot")
    frontend: Literal["angular"] = Field(default="angular")
    features: list[str] = Field(default_factory=list)
    website_like: str | None = Field(default=None, max_length=120)
    mode_preference: Literal["auto", "reuse", "adapt", "generate", "hybrid_scaffold"] = Field(default="auto")


class GenerateResponse(BaseModel):
    job_id: str
    status: str
    fingerprint: str
    cache_hit: bool = False
    cached_project_id: str | None = None
    mode_selected: str | None = None
