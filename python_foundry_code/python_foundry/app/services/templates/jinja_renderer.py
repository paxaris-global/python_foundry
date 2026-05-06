from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.core.config import get_settings


class JinjaRenderer:
    def __init__(self) -> None:
        settings = get_settings()
        templates_root = Path(settings.base_dir) / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(templates_root)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )

    def render(self, template_path: str, context: dict[str, Any]) -> str:
        template = self.env.get_template(template_path)
        return template.render(**context).strip() + "\n"
