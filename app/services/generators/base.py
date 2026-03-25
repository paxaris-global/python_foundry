from abc import ABC, abstractmethod


class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, project_spec: dict, api_contract: dict, rag_context: list[dict]) -> dict[str, str]:
        raise NotImplementedError
