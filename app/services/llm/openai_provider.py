import json
import re
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.llm.base import BaseLLMProvider

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self.settings = get_settings()
        self._enabled = bool(self.settings.openai_api_key)
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self._enabled else None
        self.last_usage: dict[str, int] = {}

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def _chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        trace_id: str | None = None,
    ) -> str:
        if self.settings.log_llm_prompts:
            safe_user_prompt = self._truncate_for_log(prompt)
            safe_system_prompt = self._truncate_for_log(system_prompt) if system_prompt else ""
            logger.info(
                "LLM_REQUEST trace_id=%s model=%s temperature=%s system_prompt=\"%s\" user_prompt=\"%s\"",
                trace_id,
                self.settings.openai_model,
                temperature,
                safe_system_prompt,
                safe_user_prompt,
            )

        if not self._enabled or self.client is None:
            return self._fallback_response(prompt)

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=messages,
            temperature=temperature,
            timeout=60,
            extra_headers={"x-trace-id": trace_id} if trace_id else None,
        )
        usage = response.usage
        if usage:
            self.last_usage = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
            logger.info("OpenAI usage=%s trace_id=%s", self.last_usage, trace_id)
        return response.choices[0].message.content or ""

    def generate_text(self, prompt: str, system_prompt: str | None = None, trace_id: str | None = None) -> str:
        return self._chat(prompt=prompt, system_prompt=system_prompt, trace_id=trace_id)

    def generate_structured_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        payload = self._chat(
            prompt=f"Return strict JSON only.\\n{prompt}",
            system_prompt=system_prompt,
            temperature=0.1,
            trace_id=trace_id,
        )
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", payload)
            if match:
                return json.loads(match.group(0))
            logger.warning("Failed to parse JSON from LLM output, returning empty payload")
            return {}

    def generate_code_block(
        self,
        prompt: str,
        language: str,
        system_prompt: str | None = None,
        trace_id: str | None = None,
    ) -> str:
        content = self._chat(
            prompt=f"Generate {language} code only, without markdown fences.\\n{prompt}",
            system_prompt=system_prompt,
            trace_id=trace_id,
        )
        return content.strip()

    def _fallback_response(self, prompt: str) -> str:
        compressed = " ".join(prompt.split())[:1200]
        return (
            '{"fallback": true, "reason": "OPENAI_API_KEY not configured", '
            f'"echo_prompt": {json.dumps(compressed)} }}'
        )

    def _truncate_for_log(self, value: str | None) -> str:
        if not value:
            return ""
        max_len = max(200, self.settings.llm_prompt_log_max_chars)
        if len(value) <= max_len:
            return value.replace("\n", "\\n")
        trimmed = value[:max_len]
        escaped = trimmed.replace("\n", "\\n")
        return f"{escaped}...[truncated:{len(value) - max_len} chars]"
