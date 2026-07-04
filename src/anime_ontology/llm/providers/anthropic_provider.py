"""Anthropic Messages API를 사용하는 LLM Provider."""

from __future__ import annotations

import httpx

from anime_ontology.llm.base import LLMProvider, LLMProviderError
from anime_ontology.llm.config import env, require_env

_ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    @classmethod
    def from_env(cls) -> "AnthropicProvider":
        return cls(
            api_key=require_env("ANTHROPIC_API_KEY"),
            model=env("ANTHROPIC_MODEL", "claude-sonnet-5") or "claude-sonnet-5",
            base_url=env("ANTHROPIC_BASE_URL", "https://api.anthropic.com") or "https://api.anthropic.com",
        )

    def complete(self, *, system: str, user: str, temperature: float = 0.0) -> str:
        try:
            response = httpx.post(
                f"{self._base_url}/v1/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": _ANTHROPIC_VERSION,
                },
                json={
                    "model": self._model,
                    "max_tokens": 4096,
                    "temperature": temperature,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            return "".join(block["text"] for block in data["content"] if block.get("type") == "text")
        except (httpx.HTTPError, KeyError) as exc:
            raise LLMProviderError(f"Anthropic 호출 실패: {exc}") from exc
