"""환경변수(.env) 로딩 및 provider 선택 설정."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"환경변수 '{name}'가 설정되지 않았습니다. .env를 확인하세요.")
    return value


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
