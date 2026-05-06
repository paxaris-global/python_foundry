import json
from pathlib import Path

from app.core.config import get_settings


class BlueprintRegistry:
    def __init__(self) -> None:
        settings = get_settings()
        self.blueprints_dir = Path(settings.base_dir) / "templates" / "blueprints"

    def get_blueprint(self, domain: str) -> dict:
        target = self.blueprints_dir / f"{domain}.json"
        if not target.exists():
            target = self.blueprints_dir / "crm.json"
        return json.loads(target.read_text(encoding="utf-8"))

    def all_blueprints(self) -> list[str]:
        return sorted([item.stem for item in self.blueprints_dir.glob("*.json")])
