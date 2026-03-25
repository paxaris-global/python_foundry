from pathlib import Path

from app.core.constants import MANDATORY_OUTPUT_FILES
from app.utils.file_utils import write_text_file


class RepairEngine:
    def repair_if_needed(self, project_root: Path, existing_files: dict[str, str], validation_report: dict) -> dict:
        actions: list[str] = []

        required_missing = validation_report.get("required_files", {}).get("missing_files", [])
        manifest_missing = validation_report.get("manifest_consistency", {}).get("missing_from_disk", [])

        for missing in required_missing + manifest_missing:
            if missing in existing_files:
                write_text_file(project_root / missing, existing_files[missing])
                actions.append(f"regenerated:{missing}")

        for empty_file in validation_report.get("non_empty_files", {}).get("empty_or_missing", []):
            if empty_file in existing_files:
                write_text_file(project_root / empty_file, existing_files[empty_file])
                actions.append(f"repopulated:{empty_file}")

        for required in MANDATORY_OUTPUT_FILES:
            target = project_root / required
            if not target.exists() and required in existing_files:
                write_text_file(target, existing_files[required])
                actions.append(f"restored_mandatory:{required}")

        return {"actions": actions, "attempted": bool(actions)}
