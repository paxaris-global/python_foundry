from app.services.generators.base import BaseGenerator


class DockerGenerator(BaseGenerator):
    def generate(self, project_spec: dict, api_contract: dict, rag_context: list[dict]) -> dict[str, str]:
        return {
            ".env.example": self._env_example(),
        }

    @staticmethod
    def _env_example() -> str:
        return """SPRING_PROFILES_ACTIVE=prod
BACKEND_HOST_PORT=18080
FRONTEND_HOST_PORT=14200
POSTGRES_HOST_PORT=15432
POSTGRES_DB=appdb
POSTGRES_USER=app
POSTGRES_PASSWORD=app_password
"""
