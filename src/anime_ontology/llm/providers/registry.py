"""provider 이름(문자열) -> LLMProvider 생성 함수 레지스트리.

새 벤더를 추가하려면 provider 클래스를 만들고 이 딕셔너리에 한 줄만 추가하면 된다.
"""

from __future__ import annotations

from typing import Callable

from anime_ontology.llm.base import LLMProvider
from anime_ontology.llm.providers.anthropic_provider import AnthropicProvider
from anime_ontology.llm.providers.ollama_provider import OllamaProvider
from anime_ontology.llm.providers.openai_provider import OpenAIProvider

PROVIDER_BUILDERS: dict[str, Callable[[], LLMProvider]] = {
    "openai": OpenAIProvider.from_env,
    "ollama": OllamaProvider.from_env,
    "anthropic": AnthropicProvider.from_env,
}


def build_provider(name: str) -> LLMProvider:
    builder = PROVIDER_BUILDERS.get(name)
    if builder is None:
        supported = ", ".join(sorted(PROVIDER_BUILDERS))
        raise ValueError(f"지원하지 않는 LLM provider입니다: '{name}' (지원: {supported})")
    return builder()
