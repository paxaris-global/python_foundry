from pathlib import Path
from typing import Optional

from app.core.constants import MANDATORY_OUTPUT_FILES
from app.utils.file_utils import write_text_file

# attempt lightweight regeneration for files that contain placeholders
from app.services.llm.provider_factory import get_llm_provider


def _is_placeholder(content: str) -> bool:
    if not content:
        return True
    lower = content.strip().lower()
    return "todo: llm failed" in lower or "llm failed" in lower or lower.startswith("todo:")


class RepairEngine:
    def __init__(self) -> None:
        self.provider = get_llm_provider()

    def _attempt_regenerate(self, file_path: str, final_prompt: Optional[str]) -> str:
        # build a concise regeneration prompt
        instruction = (
            f"Using the following project prompt, generate the full contents for the file '{file_path}'.\n"
            "Return only the raw file contents without any markdown fences or commentary."
        )
        if final_prompt:
            instruction = instruction + "\n\nProject prompt:\n" + final_prompt

        # choose a best-effort language label
        if file_path.endswith(".xml") or file_path.endswith("pom.xml"):
            language = "xml"
        elif file_path.endswith(".json") or file_path.endswith("package.json"):
            language = "json"
        elif file_path.endswith("Dockerfile") or file_path.endswith("dockerfile"):
            language = "dockerfile"
        elif file_path.endswith(".yml") or file_path.endswith(".yaml"):
            language = "yaml"
        elif file_path.endswith(".md"):
            language = "markdown"
        else:
            language = "text"

        try:
            result = self.provider.generate_code_block(prompt=instruction, language=language)
            if result and not _is_placeholder(result):
                return result
        except Exception:
            pass
        return ""

    def repair_if_needed(self, project_root: Path, existing_files: dict[str, str], validation_report: dict) -> dict:
        actions: list[str] = []

        required_missing = validation_report.get("required_files", {}).get("missing_files", [])
        manifest_missing = validation_report.get("manifest_consistency", {}).get("missing_from_disk", [])

        # try to restore missing/empty files from assembled payload; if placeholder, attempt LLM regen
        final_prompt = existing_files.get("_meta/final_enriched_prompt.txt") or existing_files.get(
            "_meta/final_enriched_prompt.json"
        )

        for missing in required_missing + manifest_missing:
            if missing in existing_files:
                content = existing_files[missing]
                if _is_placeholder(content):
                    regen = self._attempt_regenerate(missing, final_prompt)
                    if regen:
                        write_text_file(project_root / missing, regen)
                        existing_files[missing] = regen
                        actions.append(f"regenerated_via_llm:{missing}")
                        continue
                write_text_file(project_root / missing, content)
                actions.append(f"regenerated:{missing}")

        for empty_file in validation_report.get("non_empty_files", {}).get("empty_or_missing", []):
            if empty_file in existing_files:
                content = existing_files[empty_file]
                if _is_placeholder(content):
                    regen = self._attempt_regenerate(empty_file, final_prompt)
                    if regen:
                        write_text_file(project_root / empty_file, regen)
                        existing_files[empty_file] = regen
                        actions.append(f"repopulated_via_llm:{empty_file}")
                        continue
                write_text_file(project_root / empty_file, content)
                actions.append(f"repopulated:{empty_file}")

        for required in MANDATORY_OUTPUT_FILES:
            target = project_root / required
            if not target.exists() and required in existing_files:
                content = existing_files[required]
                if _is_placeholder(content):
                    regen = self._attempt_regenerate(required, final_prompt)
                    if regen:
                        write_text_file(target, regen)
                        existing_files[required] = regen
                        actions.append(f"restored_mandatory_via_llm:{required}")
                        continue
                write_text_file(target, content)
                actions.append(f"restored_mandatory:{required}")

        return {"actions": actions, "attempted": bool(actions)}
