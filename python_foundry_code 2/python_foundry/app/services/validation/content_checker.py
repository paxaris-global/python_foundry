from pathlib import Path

from app.core.constants import MANDATORY_OUTPUT_FILES
from app.core.constants import CRITICAL_NON_EMPTY_FILES


class ContentChecker:
    def check_required_files(self, project_root: Path, manifest: dict, generated_files: list[str]) -> dict:
        expected = set(MANDATORY_OUTPUT_FILES)
        expected.update(manifest.get("mandatory_files", []))

        generated_file_set = set(generated_files)
        missing_files = []
        missing_from_generated = []
        for file_name in sorted(expected):
            if file_name not in generated_file_set:
                missing_from_generated.append(file_name)
            if not (project_root / file_name).exists():
                missing_files.append(file_name)

        return {
            "missing_files": missing_files,
            "missing_from_generated": missing_from_generated,
            "ok": not missing_files,
        }

    def check_non_empty(self, project_root: Path) -> dict:
        empty_files = []
        for file_name in CRITICAL_NON_EMPTY_FILES:
            target = project_root / file_name
            if not target.exists() or target.stat().st_size == 0:
                empty_files.append(file_name)
        return {"empty_or_missing": empty_files, "ok": not empty_files}

    def check_manifest_consistency(self, project_root: Path, manifest: dict, generated_files: list[str]) -> dict:
        generated_file_set = set(generated_files)
        missing_from_disk = []
        missing_from_generated = []

        for file_name in manifest.get("mandatory_files", []):
            if not (project_root / file_name).exists():
                missing_from_disk.append(file_name)
            if file_name not in generated_file_set:
                missing_from_generated.append(file_name)

        return {
            "missing_from_disk": missing_from_disk,
            "missing_from_generated": missing_from_generated,
            "ok": not missing_from_disk,
        }

    def check_path_safety(self, generated_files: list[str]) -> dict:
        unsafe_paths = []
        for relative_path in generated_files:
            normalized = relative_path.replace("\\", "/")
            if normalized.startswith("/") or ".." in normalized.split("/"):
                unsafe_paths.append(relative_path)
        return {"unsafe_paths": unsafe_paths, "ok": not unsafe_paths}
