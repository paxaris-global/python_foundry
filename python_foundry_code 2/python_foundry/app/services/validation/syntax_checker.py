import json
from pathlib import Path


class SyntaxChecker:
    def check(self, project_root: Path) -> dict:
        failed = []
        for path in project_root.rglob("*.json"):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                failed.append(str(path.relative_to(project_root)).replace("\\", "/"))
        return {"json_invalid": failed, "ok": not failed}
