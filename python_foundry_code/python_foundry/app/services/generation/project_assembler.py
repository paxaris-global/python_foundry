from pathlib import Path

from app.core.constants import ALLOWED_GENERATED_EXTENSIONS
from app.utils.file_utils import ensure_directory, safe_relative_path, write_text_file
from app.utils.path_utils import safe_join


class ProjectAssembler:
    def assemble_project_files(self, project_root: Path, files: dict[str, str]) -> list[str]:
        ensure_directory(project_root)
        written: list[str] = []

        for relative_path, content in files.items():
            target = safe_join(project_root, relative_path)
            suffix = target.suffix.lower()
            if suffix and suffix not in ALLOWED_GENERATED_EXTENSIONS:
                continue
            write_text_file(target, content)
            written.append(safe_relative_path(project_root, target))

        return sorted(written)
