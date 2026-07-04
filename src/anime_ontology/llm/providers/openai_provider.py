"""OpenAI Chat Completions API를 사용하는 LLM Provider."""

from __future__ import annotations

import httpx

from anime_ontology.llm.base import LLMProvider, LLMProviderError
from anime_ontology.config import env, require_env


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    @classmethod
    def from_env(cls) -> "OpenAIProvider":
        return cls(
            api_key=require_env("OPENAI_API_KEY"),
            model=env("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
            base_url=env("OPENAI_BASE_URL", "https://api.openai.com/v1") or "https://api.openai.com/v1",
        )

    def complete(self, *, system: str, user: str, temperature: float = 0.0) -> str:
        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "temperature": temperature,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            raise LLMProviderError(f"OpenAI 호출 실패: {exc}") from exc
