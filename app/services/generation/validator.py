from pathlib import Path

from app.services.validation.content_checker import ContentChecker
from app.services.validation.structure_checker import StructureChecker
from app.services.validation.syntax_checker import SyntaxChecker


class ProjectValidator:
    def __init__(self) -> None:
        self.structure_checker = StructureChecker()
        self.content_checker = ContentChecker()
        self.syntax_checker = SyntaxChecker()

    def validate_structure(self, project_root: Path) -> dict:
        return self.structure_checker.check(project_root)

    def validate_required_files(self, project_root: Path, manifest: dict, generated_files: list[str]) -> dict:
        return self.content_checker.check_required_files(project_root, manifest, generated_files)

    def validate_non_empty_files(self, project_root: Path) -> dict:
        return self.content_checker.check_non_empty(project_root)

    def validate_manifest_consistency(self, project_root: Path, manifest: dict, generated_files: list[str]) -> dict:
        return self.content_checker.check_manifest_consistency(project_root, manifest, generated_files)

    def validate_path_safety(self, generated_files: list[str]) -> dict:
        return self.content_checker.check_path_safety(generated_files)

    def optional_syntax_checks(self, project_root: Path) -> dict:
        return self.syntax_checker.check(project_root)

    def build_report(
        self,
        structure: dict,
        required_files: dict,
        non_empty_files: dict,
        manifest_consistency: dict,
        path_safety: dict,
        syntax: dict,
    ) -> dict:
        valid = all(
            [
                structure.get("ok", False),
                required_files.get("ok", False),
                non_empty_files.get("ok", False),
                manifest_consistency.get("ok", False),
                path_safety.get("ok", False),
                # syntax check is advisory — TypeScript/Angular errors are handled by ng build loop
            ]
        )
        return {
            "valid": valid,
            "structure": structure,
            "required_files": required_files,
            "non_empty_files": non_empty_files,
            "manifest_consistency": manifest_consistency,
            "path_safety": path_safety,
            "syntax": syntax,
        }
