from datetime import datetime

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: str
    status: str
    progress: int
    current_stage: str
    error: str | None
    trace_id: str | None
    cache_hit: bool
    project_id: str | None
    stage_timings: dict
    result_data: dict
    created_at: datetime
    updated_at: datetime
