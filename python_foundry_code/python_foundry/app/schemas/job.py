from typing import Any, Optional

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import JobStatusValue


class JobResponse(BaseModel):
    """Full status representation of a generation job.

    Poll this endpoint while ``status`` is ``pending`` or ``running``.
    When ``status`` becomes ``completed``, ``project_id`` is populated and the
    project can be fetched via ``GET /projects/{project_id}``.
    When ``status`` is ``failed``, ``error`` contains the failure reason.
    """

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "b1e4a2f0-1234-5678-abcd-ef0123456789",
            "status": "completed",
            "progress": 100,
            "current_stage": "finalize_job_status",
            "error": None,
            "trace_id": "trace-abc123",
            "cache_hit": False,
            "project_id": "c2f5b3e1-5678-1234-abcd-ef0123456789",
            "stage_timings": {"parse_prompt": 0.12, "generate_backend_code": 8.5, "package_to_zip": 0.4},
            "result_data": {"project_id": "c2f5b3e1-5678-1234-abcd-ef0123456789", "zip_path": "/data/projects/my-crm.zip", "execution_mode": "generate"},
            "created_at": "2025-06-01T12:00:00",
            "updated_at": "2025-06-01T12:01:00",
        }
    })

    id: str = Field(description="UUID of the job.")
    status: JobStatusValue = Field(description="Current lifecycle state.")
    progress: int = Field(ge=0, le=100, description="Completion percentage (0–100).")
    current_stage: str = Field(description="Name of the pipeline stage currently executing (e.g. 'parse_prompt', 'generate_backend_code').")
    error: Optional[str] = Field(default=None, description="Error message when status is 'failed'. Null otherwise.")
    trace_id: Optional[str] = Field(default=None, description="Distributed-tracing identifier for log correlation.")
    cache_hit: bool = Field(description="True when the result was served from the generation cache.")
    project_id: Optional[str] = Field(default=None, description="UUID of the generated project. Set once status reaches 'completed'.")
    stage_timings: Optional[dict[str, float]] = Field(
        default=None,
        description="Per-stage execution durations in seconds, keyed by stage name. Populated on completion.",
    )
    result_data: Optional[dict[str, Any]] = Field(
        default=None,
        description="Pipeline output payload (project_id, zip_path, manifest, validation_report, execution_mode, …). Populated on completion.",
    )
    created_at: datetime = Field(description="Timestamp when the job was created.")
    updated_at: datetime = Field(description="Timestamp of the last status update.")
