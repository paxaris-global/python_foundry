from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path

from app.api.deps import DBSession
from app.core.exceptions import NotFoundException, ServiceUnavailableException, ValidationException
from app.core.logging import get_logger
from app.models.job import Job
from app.schemas.common import ErrorResponse
from app.schemas.job import JobResponse
from app.schemas.prompt_debug import FinalPromptResponse
from app.services.generation.prompt_debugger import PromptDebugger

router = APIRouter(prefix="/jobs", tags=["Jobs"])
logger = get_logger(__name__)
JOB_NOT_FOUND = "Job not found"

JobIdPath = Annotated[str, Path(
    description="UUID of the generation job (returned by POST /generate in the job_id field).",
    examples=["b1e4a2f0-1234-5678-abcd-ef0123456789"],
)]


def _parse_job_uuid(job_id: str) -> UUID:
    try:
        return UUID(job_id)
    except ValueError as exc:
        raise ValidationException(f"Invalid job ID format: {job_id}") from exc


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job status",
    description="Retrieve the current status, progress, and result data of a generation job by its UUID.",
    responses={
        404: {"description": "Job not found.", "model": ErrorResponse},
        422: {"description": "Invalid job ID format.", "model": ErrorResponse},
        503: {"description": "Service unavailable.", "model": ErrorResponse},
    },
)
def get_job(job_id: JobIdPath, db: DBSession) -> JobResponse:
    job_uuid = _parse_job_uuid(job_id)

    try:
        job = db.query(Job).filter(Job.id == job_uuid).first()
    except Exception:
        logger.exception("Database error fetching job=%s", job_id)
        raise ServiceUnavailableException("Failed to retrieve job due to a database error")

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


@router.get(
    "/{job_id}/final-prompt",
    response_model=FinalPromptResponse,
    summary="Get final prompt artifact",
    description="Returns the fully-assembled prompt artifact for a job, including parsed prompt, RAG context, web-discovery results, and the final enriched prompt sent to the LLM.",
    responses={
        404: {"description": "Job or prompt artifact not found.", "model": ErrorResponse},
        422: {"description": "Invalid job ID format.", "model": ErrorResponse},
        503: {"description": "Service unavailable.", "model": ErrorResponse},
    },
)
def get_final_prompt(job_id: JobIdPath, db: DBSession) -> FinalPromptResponse:
    job_uuid = _parse_job_uuid(job_id)

    try:
        job = db.query(Job).filter(Job.id == job_uuid).first()
    except Exception:
        logger.exception("Database error fetching job=%s", job_id)
        raise ServiceUnavailableException("Failed to retrieve job due to a database error")

    if not job:
        raise NotFoundException(JOB_NOT_FOUND)

    try:
        artifact = PromptDebugger(db).get_by_job_id(job_uuid)
    except Exception:
        logger.exception("Database error fetching prompt artifact for job=%s", job_id)
        raise ServiceUnavailableException("Failed to retrieve prompt artifact due to a database error")

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
