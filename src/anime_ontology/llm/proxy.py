"""여러 LLM provider를 하나의 LLMProvider처럼 보이게 감싸는 Proxy.

추출 모듈은 LLMProviderProxy만 의존하므로, .env의 LLM_PROVIDER 값만 바꾸면
Claude API에 종속되지 않고 OpenAI/Ollama/Anthropic 등을 자유롭게 교체할 수 있다.
primary provider 호출이 실패하면 LLM_FALLBACK_PROVIDERS에 지정된 순서로 재시도한다.
"""

from __future__ import annotations

from anime_ontology.llm.base import LLMProvider, LLMProviderError
from anime_ontology.llm.config import LLMSettings
from anime_ontology.llm.providers.registry import build_provider


class LLMProviderProxy(LLMProvider):
    name = "proxy"

    def __init__(self, primary: str, fallbacks: list[str] | None = None) -> None:
        self._provider_names = [primary, *(fallbacks or [])]
        self._provider_cache: dict[str, LLMProvider] = {}

    @classmethod
    def from_env(cls) -> "LLMProviderProxy":
        settings = LLMSettings.from_env()
        return cls(settings.default_provider, settings.fallback_providers)

    def _resolve(self, name: str) -> LLMProvider:
        if name not in self._provider_cache:
            self._provider_cache[name] = build_provider(name)
        return self._provider_cache[name]

    def complete(self, *, system: str, user: str, temperature: float = 0.0) -> str:
        errors: list[str] = []
        for name in self._provider_names:
            try:
                provider = self._resolve(name)
                return provider.complete(system=system, user=user, temperature=temperature)
            except LLMProviderError as exc:
                errors.append(f"{name}: {exc}")
            except Exception as exc:  # provider 생성 실패(예: API 키 누락) 등
                errors.append(f"{name}: 초기화 실패 - {exc}")

        raise LLMProviderError(
            "모든 LLM provider 호출이 실패했습니다.\n" + "\n".join(errors)
        )
