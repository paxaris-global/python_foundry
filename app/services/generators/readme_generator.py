from app.services.generators.base import BaseGenerator
from app.services.templates.jinja_renderer import JinjaRenderer
from app.services.templates.template_registry import TemplateRegistry


class ReadmeGenerator(BaseGenerator):
    def __init__(self) -> None:
        self.renderer = JinjaRenderer()

    def generate(self, project_spec: dict, api_contract: dict, rag_context: list[dict]) -> dict[str, str]:
        context = {
            "project_name": project_spec["project_name"],
            "description": project_spec["description"],
            "backend": project_spec["backend"]["stack"],
            "frontend": project_spec["frontend"]["stack"],
            "features": project_spec["features"],
        }
        return {
            "README.md": self.renderer.render(TemplateRegistry.README.path, context),
            "api-contract.json": self._api_contract_json(api_contract),
            "manifest.json": self._manifest_stub(project_spec),
        }

    @staticmethod
    def _api_contract_json(api_contract: dict) -> str:
        import json

        return json.dumps(api_contract, indent=2)

    @staticmethod
    def _manifest_stub(project_spec: dict) -> str:
        import json

        return json.dumps(
            {
                "project_name": project_spec["project_name"],
                "backend": project_spec["backend"]["stack"],
                "frontend": project_spec["frontend"]["stack"],
                "features": project_spec["features"],
            },
            indent=2,
        )
