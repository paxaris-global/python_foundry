import shutil
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Path as PathParam
from fastapi.responses import FileResponse

from app.api.deps import DBSession
from app.core.config import get_settings
from app.core.exceptions import AppException, NotFoundException, ServiceUnavailableException, ValidationException
from app.core.logging import get_logger
from app.models.project import Project
from app.schemas.common import ErrorResponse
from app.schemas.project import ProjectResponse
from app.services.generation.zip_packager import ZipPackager

router = APIRouter(prefix="/projects", tags=["Projects"])
logger = get_logger(__name__)
PROJECT_NOT_FOUND = "Project not found"

ProjectIdPath = Annotated[str, PathParam(
    description="UUID of the generated project (found in JobResponse.project_id once the job completes).",
    examples=["c2f5b3e1-5678-1234-abcd-ef0123456789"],
)]


def _parse_project_uuid(project_id: str) -> UUID:
    try:
        return UUID(project_id)
    except ValueError as exc:
        raise ValidationException(f"Invalid project ID format: {project_id}") from exc


def _get_project_or_404(project_id: str, db) -> Project:
    project_uuid = _parse_project_uuid(project_id)
    try:
        project = db.query(Project).filter(Project.id == project_uuid).first()
    except Exception:
        logger.exception("Database error fetching project=%s", project_id)
        raise ServiceUnavailableException("Failed to retrieve project due to a database error")
    if not project:
        raise NotFoundException(PROJECT_NOT_FOUND)
    return project


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
    description="Retrieve full metadata for a generated project including file manifest, validation report, and RAG summary.",
    responses={
        404: {"description": "Project not found.", "model": ErrorResponse},
        422: {"description": "Invalid project ID format.", "model": ErrorResponse},
        503: {"description": "Service unavailable.", "model": ErrorResponse},
    },
)
def get_project(project_id: ProjectIdPath, db: DBSession) -> ProjectResponse:
    project = _get_project_or_404(project_id, db)

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        backend_stack=project.backend_stack,
        frontend_stack=project.frontend_stack,
        domain=project.domain,
        blueprint_used=project.blueprint_used,
        project_path=project.project_path,
        zip_path=project.zip_path,
        manifest=project.manifest,
        rag_summary=project.rag_summary,
        cache_info=project.cache_info,
        generated_files=project.generated_files,
        validation_report=project.validation_report,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _cleanup_generated_artifacts(project_path: str, zip_path: str) -> None:
    try:
        Path(zip_path).unlink(missing_ok=True)
        if project_path:
            shutil.rmtree(Path(project_path), ignore_errors=True)
    except Exception:
        logger.warning("Failed to cleanup generated artifacts after download", exc_info=True)


@router.get(
    "/{project_id}/download",
    summary="Download project ZIP",
    description="Stream the generated project as a ZIP archive. If the archive was removed, it is rebuilt from the project directory.",
    response_class=FileResponse,
    responses={
        200: {"content": {"application/zip": {}}, "description": "ZIP archive of the generated project."},
        404: {"description": "Project or ZIP artifact not found.", "model": ErrorResponse},
        422: {"description": "Invalid project ID format.", "model": ErrorResponse},
        503: {"description": "Service unavailable.", "model": ErrorResponse},
    },
)
def download_project_zip(project_id: ProjectIdPath, db: DBSession, background_tasks: BackgroundTasks) -> FileResponse:
    project = _get_project_or_404(project_id, db)

    zip_path = Path(project.zip_path)
    if not zip_path.exists():
        project_root = Path(project.project_path)
        if project_root.exists() and project_root.is_dir():
            try:
                zip_path = project_root.with_suffix(".zip")
                ZipPackager().package_to_zip(project_root, zip_path)
                project.zip_path = str(zip_path)
                db.commit()
                db.refresh(project)
            except Exception:
                logger.exception("Failed to rebuild ZIP for project=%s", project_id)
                raise AppException("Failed to rebuild project archive")
        else:
            raise NotFoundException("ZIP artifact not found and project directory is missing")

    response = FileResponse(
        path=str(zip_path),
        filename=f"{project.name}.zip",
        media_type="application/zip",
    )
    # With STORE_FINAL_PROJECT=false we keep artifacts only until first download.
    if not get_settings().store_final_project:
        background_tasks.add_task(
            _cleanup_generated_artifacts,
            project.project_path,
            str(zip_path),
        )
    return response
