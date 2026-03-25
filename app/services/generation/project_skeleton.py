from pathlib import Path
from uuid import UUID

from app.core.constants import REQUIRED_SKELETON_DIRS
from app.utils.file_utils import ensure_directory


class ProjectSkeletonBuilder:
    def create(self, project_root: Path, project_id: UUID) -> dict:
        created_dirs: list[str] = []
        for relative_dir in REQUIRED_SKELETON_DIRS:
            ensure_directory(project_root / relative_dir)
            created_dirs.append(relative_dir)

        return {
            "project_id": str(project_id),
            "project_root": str(project_root),
            "created_dirs": created_dirs,
        }
