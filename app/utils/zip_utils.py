from pathlib import Path

from app.utils.path_utils import ensure_within


def safe_arcname(project_root: Path, file_path: Path) -> str:
    safe_file = ensure_within(project_root, file_path)
    return str(safe_file.relative_to(project_root)).replace("\\", "/")
