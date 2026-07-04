"""LLM Provider가 지켜야 하는 공통 인터페이스.

추출 모듈(extraction)은 이 인터페이스만 알고 있으며, 실제로 어떤 벤더가
호출되는지는 LLMProviderProxy가 감춘다(Proxy 패턴).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProviderError(RuntimeError):
    """LLM 호출이 실패했음을 나타내는 예외."""


class LLMProvider(ABC):
    """system/user 프롬프트를 받아 텍스트 응답을 반환하는 최소 인터페이스."""

    name: str

    @abstractmethod
    def complete(self, *, system: str, user: str, temperature: float = 0.0) -> str:
        """모델에 프롬프트를 보내고 텍스트 응답을 반환한다. 실패 시 LLMProviderError."""
        raise NotImplementedError
