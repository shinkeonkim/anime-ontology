"""로컬 Ollama 서버를 사용하는 LLM Provider. API 키가 필요 없다."""

from __future__ import annotations

import httpx

from anime_ontology.llm.base import LLMProvider, LLMProviderError
from anime_ontology.llm.config import env


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, model: str, base_url: str) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")

    @classmethod
    def from_env(cls) -> "OllamaProvider":
        return cls(
            model=env("OLLAMA_MODEL", "gemma4:latest") or "gemma4:latest",
            base_url=env("OLLAMA_BASE_URL", "http://localhost:11434") or "http://localhost:11434",
        )

    def complete(self, *, system: str, user: str, temperature: float = 0.0) -> str:
        try:
            response = httpx.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "stream": False,
                    "options": {"temperature": temperature},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=300,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except (httpx.HTTPError, KeyError) as exc:
            raise LLMProviderError(f"Ollama 호출 실패: {exc}") from exc
