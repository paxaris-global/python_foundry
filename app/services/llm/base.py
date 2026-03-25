from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_structured_json(self, prompt: str, system_prompt: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def generate_code_block(self, prompt: str, language: str, system_prompt: str | None = None) -> str:
        raise NotImplementedError
