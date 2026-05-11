from app.core.config import get_settings
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.base import BaseLLMProvider
from app.services.llm.openai_provider import OpenAIProvider


def get_llm_provider() -> BaseLLMProvider:
    settings = get_settings()
    provider = (settings.llm_provider or "").strip().lower()

    if provider == "openai":
        return OpenAIProvider()
    if provider == "anthropic":
        return AnthropicProvider()

    if settings.anthropic_api_key:
        return AnthropicProvider()
    return OpenAIProvider()
