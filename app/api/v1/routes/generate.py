from typing import Optional

from pathlib import Path
from urllib.parse import urlparse, urlunparse

from fastapi import APIRouter, status

from app.api.deps import DBSession
from app.core.constants import CODEGEN_TEMPLATE_VERSION
from app.core.exceptions import ServiceUnavailableException
from app.core.security import sanitize_project_name
from app.models.generation_cache import GenerationCache
from app.models.job import Job, JobStatus
from app.models.project import Project
from app.schemas.common import ErrorResponse
from app.schemas.generate import GenerateRequest, GenerateResponse
from app.services.caching.fingerprint import FingerprintService
from app.services.generation.prompt_parser import PromptParser
from app.services.generation.prompt_debugger import PromptDebugger
from app.services.generation.zip_packager import ZipPackager
from app.services.observability.tracing import new_trace_id
from app.services.web_discovery.search_client import SearchClient
from app.tasks.generation_tasks import generate_project_task
from app.utils.sanitizers import sanitize_feature_list
from app.utils.download_utils import copy_project_to_downloads
from app.core.logging import get_logger

router = APIRouter(prefix="/generate", tags=["Generate"])
logger = get_logger(__name__)


def _build_effective_prompt(project_name: str, prompt: Optional[str], features: list[str]) -> str:
    if prompt:
        return prompt

    if features:
        features_text = ", ".join(features)
        return (
            f"Generate a production-ready {project_name} application with Spring Boot backend and Angular frontend, "
            f"including the following features: {features_text}. "
            "Create a professional, modern UI with Angular Material components, beautiful color schemes, "
            "responsive design, and excellent user experience. Include authentication, role-based access, "
            "clean architecture, Docker support, tests, and comprehensive documentation. "
            "Use Material Design principles with attractive gradients, proper spacing, and intuitive navigation."
        )

    return (
        f"Generate a production-ready {project_name} application with Spring Boot backend and Angular frontend, "
        "featuring a professional, modern UI built with Angular Material. Include beautiful color schemes, "
        "responsive design, intuitive navigation, and excellent user experience. Implement authentication, "
        "role-based access control, clean architecture patterns, Docker containerization, comprehensive tests, "
        "and detailed documentation. Use Material Design components with attractive gradients, proper spacing, "
        "and modern styling throughout the application."
    )


def _normalize_website_like(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    parsed = urlparse(value.strip())
    if not parsed.scheme or not parsed.netloc:
        return value.strip()[:120]

    cleaned = urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))
    return cleaned[:120]


def _discover_website_like(project_name: str) -> Optional[str]:
    try:
        results = SearchClient().search(f"{project_name} official website", max_results=3)
    except Exception:
        return None

    for item in results:
        source_type = item.get("source_type")
        url = item.get("url")
        if source_type == "web" and url:
            return _normalize_website_like(url)
    return None


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=GenerateResponse,
    summary="Create a generation job",
    description="Accepts a project specification and enqueues an asynchronous code-generation job. "
                "Returns immediately with a job ID that can be polled via the Jobs endpoints. "
                "If a cached result matching the request fingerprint exists, it is returned instantly.",
    responses={
        202: {"description": "Job accepted and enqueued (or served from cache)."},
        422: {"description": "Invalid request payload.", "model": ErrorResponse},
        503: {"description": "Service unavailable.", "model": ErrorResponse},
    },
)
def create_generation_job(payload: GenerateRequest, db: DBSession) -> GenerateResponse:
    safe_name = sanitize_project_name(payload.project_name)
    safe_features = sanitize_feature_list(payload.features)
    effective_prompt = _build_effective_prompt(safe_name, payload.prompt, safe_features)
    effective_website_like = _normalize_website_like(payload.website_like)
    if not payload.prompt and not effective_website_like:
        effective_website_like = _discover_website_like(safe_name)

    parsed = PromptParser().parse_prompt(effective_prompt)
    fingerprint = FingerprintService().compute(
        prompt=effective_prompt,
        backend=payload.backend,
        frontend=payload.frontend,
        features=safe_features,
        domain="general",
        blueprint="scaffold",
        template_version=CODEGEN_TEMPLATE_VERSION,
    )
    trace_id = new_trace_id()

    cached = db.query(GenerationCache).filter(GenerationCache.fingerprint == fingerprint).first()
    if cached and cached.project_id and payload.mode_preference != "generate":
        # Verify the cached project actually has files on disk before reusing
        cached_project = db.query(Project).filter(Project.id == cached.project_id).first()
        if cached_project:
            project_root = Path(cached_project.project_path)
            if not project_root.exists() or not project_root.is_dir():
                # Cached project files don't exist, fall back to generation
                cached = None
            else:
                # Cached project exists, proceed with reuse
                cached_job = Job(
                    project_name=safe_name,
                    prompt=effective_prompt,
                    backend=payload.backend,
                    frontend=payload.frontend,
                    features=safe_features,
                    website_like=effective_website_like,
                    mode_preference=payload.mode_preference,
                    mode_selected="reuse",
                    fingerprint=fingerprint,
                    status=JobStatus.completed,
                    progress=100,
                    current_stage="finalize_job_status",
                    trace_id=trace_id,
                    cache_hit=True,
                    project_id=cached.project_id,
                    result_data={
                        "project_id": str(cached.project_id),
                        "cache": True,
                        "execution_mode": "reuse",
                        "mode_preference": payload.mode_preference,
                    },
                )
                db.add(cached_job)
                db.commit()
                db.refresh(cached_job)

                PromptDebugger(db).persist_prompt_artifact(
                    job_id=cached_job.id,
                    raw_user_prompt=effective_prompt,
                    parsed_prompt=parsed,
                    parsed_prompt_summary={
                        "summary": parsed.get("summary", ""),
                        "token_count": len(parsed.get("tokens", [])),
                        "entities": parsed.get("entities", []),
                        "feature_hints": parsed.get("feature_hints", []),
                    },
                    expanded_features=safe_features,
                    execution_mode="reuse",
                    rag_summary={"cache_hit": True},
                    rag_context_summary={},
                    web_discovery_summary={},
                    adaptation_context_summary={},
                    trusted_sources=[],
                    pre_final_prompt=None,
                    final_enriched_prompt=(
                        "CACHE_HIT\n"
                        f"Reused project_id={cached.project_id}\n"
                        f"fingerprint={fingerprint}\n"
                        f"mode_preference={payload.mode_preference}"
                    ),
                    system_prompt=None,
                )

                # Ensure cached project ZIP exists; if not, try to rebuild from the project folder
                try:
                    zip_path = Path(cached_project.zip_path) if cached_project.zip_path else None
                    if not zip_path or not zip_path.exists():
                        zip_path = project_root.with_suffix('.zip')
                        ZipPackager().package_to_zip(project_root, zip_path)
                        cached_project.zip_path = str(zip_path)
                        db.commit()
                    if zip_path and zip_path.exists():
                        download_path = copy_project_to_downloads(str(zip_path), safe_name)
                        logger.info(f"Cached project auto-downloaded to: {download_path}")
                except Exception as exc:
                    logger.error(f"Failed to auto-download cached project: {exc}")
                    # Don't fail the request if download fails

                return GenerateResponse(
                    job_id=str(cached_job.id),
                    status=cached_job.status.value,
                    fingerprint=fingerprint,
                    cache_hit=True,
                    cached_project_id=str(cached.project_id),
                    mode_selected="reuse",
                )

    job = Job(
        project_name=safe_name,
        prompt=effective_prompt,
        backend=payload.backend,
        frontend=payload.frontend,
        features=safe_features,
        website_like=effective_website_like,
        mode_preference=payload.mode_preference,
        fingerprint=fingerprint,
        status=JobStatus.pending,
        progress=0,
        current_stage="pending",
        trace_id=trace_id,
        cache_hit=False,
    )

    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception:
        logger.exception("Failed to persist generation job to database")
        raise ServiceUnavailableException("Failed to create generation job due to a database error")

    try:
        task = generate_project_task.apply_async(args=[str(job.id)], priority=5)
        job.celery_task_id = task.id
        db.commit()
    except Exception:
        logger.exception("Failed to enqueue generation task for job=%s", job.id)
        job.status = JobStatus.failed
        job.error = "Failed to enqueue generation task"
        job.current_stage = "failed"
        db.commit()
        raise ServiceUnavailableException("Failed to enqueue generation task. The task queue may be unavailable.")

    return GenerateResponse(
        job_id=str(job.id),
        status=job.status.value,
        fingerprint=fingerprint,
        cache_hit=False,
        mode_selected=payload.mode_preference if payload.mode_preference != "auto" else None,
    )
