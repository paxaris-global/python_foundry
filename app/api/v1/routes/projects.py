from pathlib import Path
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.api.deps import DBSession
from app.core.exceptions import NotFoundException
from app.models.project import Project
from app.schemas.project import ProjectResponse
from app.services.generation.zip_packager import ZipPackager

router = APIRouter(prefix="/projects", tags=["projects"])
PROJECT_NOT_FOUND = "Project not found"


@router.get("/{project_id}")
def get_project(project_id: str, db: DBSession) -> ProjectResponse:
    try:
        project_uuid = UUID(project_id)
    except ValueError as exc:
        raise NotFoundException(PROJECT_NOT_FOUND) from exc

    project = db.query(Project).filter(Project.id == project_uuid).first()
    if not project:
        raise NotFoundException(PROJECT_NOT_FOUND)

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


@router.get("/{project_id}/download")
def download_project_zip(project_id: str, db: DBSession) -> FileResponse:
    try:
        project_uuid = UUID(project_id)
    except ValueError as exc:
        raise NotFoundException(PROJECT_NOT_FOUND) from exc

    project = db.query(Project).filter(Project.id == project_uuid).first()
    if not project:
        raise NotFoundException(PROJECT_NOT_FOUND)

    # if the ZIP path is stale / removed, try to recreate from project directory
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
            except Exception as exc:
                raise NotFoundException(f"ZIP artifact not found: {exc}") from exc
        else:
            raise NotFoundException("ZIP artifact not found")

    return FileResponse(
        path=str(zip_path),
        filename=f"{project.name}.zip",
        media_type="application/zip",
    )
