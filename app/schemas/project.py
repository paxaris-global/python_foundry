from datetime import datetime

from pydantic import BaseModel


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    backend_stack: str
    frontend_stack: str
    domain: str
    blueprint_used: str | None
    project_path: str
    zip_path: str
    manifest: dict
    rag_summary: dict
    cache_info: dict
    generated_files: list[str]
    validation_report: dict
    created_at: datetime
    updated_at: datetime
