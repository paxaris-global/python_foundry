from typing import Any, Optional

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectResponse(BaseModel):
    """Detailed metadata for a generated project."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "c2f5b3e1-5678-1234-abcd-ef0123456789",
            "name": "my-crm",
            "description": "CRM application with contact management",
            "backend_stack": "springboot",
            "frontend_stack": "angular",
            "domain": "crm",
            "blueprint_used": "scaffold",
            "project_path": "/data/projects/my-crm",
            "zip_path": "/data/projects/my-crm.zip",
            "manifest": {},
            "rag_summary": {},
            "cache_info": {},
            "generated_files": ["pom.xml", "src/main/java/App.java"],
            "validation_report": {"errors": 0},
            "created_at": "2025-06-01T12:00:00",
            "updated_at": "2025-06-01T12:01:00",
        }
    })

    id: str = Field(description="UUID of the project.")
    name: str = Field(description="Project name.")
    description: str = Field(description="Human-readable project description.")
    backend_stack: str = Field(description="Backend technology stack used.")
    frontend_stack: str = Field(description="Frontend technology stack used.")
    domain: str = Field(description="Classified business domain (e.g. 'crm', 'ecommerce').")
    blueprint_used: Optional[str] = Field(description="Blueprint template that was applied.")
    project_path: str = Field(description="Absolute path to the generated project directory.")
    zip_path: str = Field(description="Absolute path to the downloadable ZIP archive.")
    manifest: dict[str, Any] = Field(description="Generation manifest with structural metadata.")
    rag_summary: dict[str, Any] = Field(description="RAG retrieval summary used during generation.")
    cache_info: dict[str, Any] = Field(description="Cache metadata associated with this project.")
    generated_files: list[str] = Field(description="List of file paths created in the project.")
    validation_report: dict[str, Any] = Field(description="Post-generation validation results.")
    created_at: datetime = Field(description="Timestamp when the project was created.")
    updated_at: datetime = Field(description="Timestamp of the last update.")
