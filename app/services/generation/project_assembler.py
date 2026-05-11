from pathlib import Path

from app.core.constants import ALLOWED_GENERATED_EXTENSIONS
from app.services.generation.post_generation_sanitizer import PostGenerationSanitizer
from app.utils.file_utils import ensure_directory, safe_relative_path, write_text_file
from app.utils.path_utils import safe_join


class ProjectAssembler:
    def __init__(self) -> None:
        self.sanitizer = PostGenerationSanitizer()

    def assemble_project_files(self, project_root: Path, files: dict[str, str]) -> list[str]:
        ensure_directory(project_root)
        written: list[str] = []

        for relative_path, content in files.items():
            target = safe_join(project_root, relative_path)
            suffix = target.suffix.lower()
            if suffix and suffix not in ALLOWED_GENERATED_EXTENSIONS:
                continue
            sanitized_content = self.sanitizer.sanitize_file_content(relative_path, content)
            write_text_file(target, sanitized_content)
            written.append(safe_relative_path(project_root, target))

        return sorted(written)
