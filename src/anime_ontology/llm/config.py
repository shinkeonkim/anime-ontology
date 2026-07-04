"""LLM provider 선택(기본/대체) 설정."""

from __future__ import annotations

from dataclasses import dataclass, field

from anime_ontology.config import env


@dataclass(frozen=True)
class LLMSettings:
    """어떤 provider를 기본/대체로 쓸지에 대한 설정."""

    default_provider: str
    fallback_providers: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "LLMSettings":
        default_provider = env("LLM_PROVIDER", "ollama") or "ollama"
        raw_fallbacks = env("LLM_FALLBACK_PROVIDERS", "") or ""
        fallback_providers = [name.strip() for name in raw_fallbacks.split(",") if name.strip()]
        return cls(default_provider=default_provider, fallback_providers=fallback_providers)
