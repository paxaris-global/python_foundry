from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    """Request body for creating a new code-generation job."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "project_name": "my-crm",
            "prompt": "Generate a CRM application with contact management and sales pipeline",
            "backend": "springboot",
            "frontend": "angular",
            "features": ["authentication", "dashboard", "contacts-crud"],
            "website_like": "https://www.hubspot.com",
            "mode_preference": "auto",
        }
    })

    project_name: str = Field(
        min_length=2, max_length=120,
        description="Short, URL-safe name for the generated project.",
    )
    prompt: Optional[str] = Field(
        default=None, min_length=10,
        description="Free-text description of the application to generate. When omitted, a default prompt is built from project_name and features.",
    )
    backend: Literal["springboot"] = Field(
        default="springboot",
        description="Backend technology stack.",
    )
    frontend: Literal["angular"] = Field(
        default="angular",
        description="Frontend technology stack.",
    )
    features: list[str] = Field(
        default_factory=list,
        description="Explicit list of features to include (e.g. 'authentication', 'dashboard').",
    )
    website_like: Optional[str] = Field(
        default=None, max_length=120,
        description="URL of a reference website whose UX/features should inspire the generated project.",
    )
    mode_preference: Literal["auto", "reuse", "adapt", "generate", "hybrid_scaffold"] = Field(
        default="auto",
        description="Execution strategy: 'auto' lets the platform decide, 'reuse' returns a cached project, 'generate' always creates fresh code.",
    )


class GenerateResponse(BaseModel):
    """Response returned after a generation job is accepted.

    Two scenarios:

    * **Cache miss** – ``status`` is ``pending``, ``cache_hit`` is ``false``.
      Poll ``GET /jobs/{job_id}`` until completion.
    * **Cache hit** – ``status`` is ``completed``, ``cache_hit`` is ``true``
      and ``cached_project_id`` points at the reused project. No polling needed.
    """

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "summary": "Cache miss – job enqueued",
                "value": {
                    "job_id": "b1e4a2f0-1234-5678-abcd-ef0123456789",
                    "status": "pending",
                    "fingerprint": "sha256:abc123def456",
                    "cache_hit": False,
                    "cached_project_id": None,
                    "mode_selected": None,
                },
            },
            {
                "summary": "Cache hit – project reused",
                "value": {
                    "job_id": "b1e4a2f0-1234-5678-abcd-ef0123456789",
                    "status": "completed",
                    "fingerprint": "sha256:abc123def456",
                    "cache_hit": True,
                    "cached_project_id": "c2f5b3e1-5678-1234-abcd-ef0123456789",
                    "mode_selected": "reuse",
                },
            },
        ]
    })

    job_id: str = Field(description="UUID of the created generation job. Use this to poll job status.")
    status: Literal["pending", "running", "completed", "failed"] = Field(
        description="Initial job status. 'pending' on cache miss, 'completed' on cache hit.",
    )
    fingerprint: str = Field(description="Content fingerprint (SHA-256) used for cache lookups.")
    cache_hit: bool = Field(default=False, description="True when an existing project was reused instead of generating fresh code.")
    cached_project_id: Optional[str] = Field(default=None, description="UUID of the reused project. Only set when cache_hit is true.")
    mode_selected: Optional[Literal["reuse", "adapt", "generate", "hybrid_scaffold"]] = Field(
        default=None,
        description="Execution mode chosen. Null when mode_preference was 'auto' and resolution is deferred to the worker.",
    )
    debug_prompt_url: Optional[str] = Field(default=None, description="URL to debug the prompt used for generation.")
