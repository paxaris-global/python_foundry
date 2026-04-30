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
