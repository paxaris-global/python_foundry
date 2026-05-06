from app.services.generators.base import BaseGenerator
from app.services.templates.jinja_renderer import JinjaRenderer
from app.services.templates.template_registry import TemplateRegistry


class ComposeGenerator(BaseGenerator):
    def __init__(self) -> None:
        self.renderer = JinjaRenderer()

    def generate(self, project_spec: dict, api_contract: dict, rag_context: list[dict]) -> dict[str, str]:
        context = {
            "project_name": project_spec["project_name"],
        }
        return {
            "docker-compose.yml": self.renderer.render(TemplateRegistry.DOCKER_COMPOSE.path, context),
        }
