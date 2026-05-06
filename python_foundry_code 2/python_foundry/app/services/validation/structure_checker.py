from pathlib import Path

from app.core.constants import REQUIRED_SKELETON_DIRS


class StructureChecker:
    def check(self, project_root: Path) -> dict:
        missing_dirs = []
        for required_dir in REQUIRED_SKELETON_DIRS:
            if not (project_root / required_dir).exists():
                missing_dirs.append(required_dir)
        return {"missing_dirs": missing_dirs, "ok": not missing_dirs}
