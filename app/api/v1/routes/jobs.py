from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DBSession
from app.core.exceptions import NotFoundException
from app.models.job import Job
from app.schemas.job import JobResponse
from app.schemas.prompt_debug import FinalPromptResponse
from app.services.generation.prompt_debugger import PromptDebugger

router = APIRouter(prefix="/jobs", tags=["jobs"])
JOB_NOT_FOUND = "Job not found"


@router.get("/{job_id}")
def get_job(job_id: str, db: DBSession) -> JobResponse:
    try:
        job_uuid = UUID(job_id)
    except ValueError as exc:
        raise NotFoundException(JOB_NOT_FOUND) from exc

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise NotFoundException(JOB_NOT_FOUND)

    return JobResponse(
        id=str(job.id),
        status=job.status.value,
        progress=job.progress,
        current_stage=job.current_stage,
        error=job.error,
        trace_id=job.trace_id,
        cache_hit=job.cache_hit,
        project_id=str(job.project_id) if job.project_id else None,
        stage_timings=job.stage_timings,
        result_data=job.result_data,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/{job_id}/final-prompt")
def get_final_prompt(job_id: str, db: DBSession) -> FinalPromptResponse:
    try:
        job_uuid = UUID(job_id)
    except ValueError as exc:
        raise NotFoundException(JOB_NOT_FOUND) from exc

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise NotFoundException(JOB_NOT_FOUND)

    artifact = PromptDebugger(db).get_by_job_id(job_uuid)
    if not artifact:
        raise NotFoundException("Final prompt artifact not found for job")

    return FinalPromptResponse(
        job_id=str(artifact.job_id),
        project_id=str(artifact.project_id) if artifact.project_id else None,
        raw_user_prompt=artifact.raw_user_prompt,
        parsed_prompt=artifact.parsed_prompt,
        parsed_prompt_summary=artifact.parsed_prompt_summary,
        expanded_features=artifact.expanded_features,
        execution_mode=artifact.execution_mode,
        rag_summary=artifact.rag_summary,
        rag_context_summary=artifact.rag_context_summary,
        web_discovery_summary=artifact.web_discovery_summary,
        adaptation_context_summary=artifact.adaptation_context_summary,
        trusted_sources=artifact.trusted_sources,
        pre_final_prompt=artifact.pre_final_prompt,
        final_enriched_prompt=artifact.final_enriched_prompt,
        artifact_text_path=artifact.artifact_text_path,
        artifact_json_path=artifact.artifact_json_path,
        created_at=artifact.created_at.isoformat(),
    )
