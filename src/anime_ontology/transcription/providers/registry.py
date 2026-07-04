"""STT provider 이름 -> 생성 함수 레지스트리."""

from __future__ import annotations

from typing import Callable

from anime_ontology.transcription.base import TranscriptionProvider
from anime_ontology.transcription.providers.local_whisper_provider import LocalWhisperProvider
from anime_ontology.transcription.providers.openai_whisper_provider import OpenAIWhisperProvider

PROVIDER_BUILDERS: dict[str, Callable[[], TranscriptionProvider]] = {
    "local_whisper": LocalWhisperProvider.from_env,
    "openai": OpenAIWhisperProvider.from_env,
}


def build_provider(name: str) -> TranscriptionProvider:
    builder = PROVIDER_BUILDERS.get(name)
    if builder is None:
        supported = ", ".join(sorted(PROVIDER_BUILDERS))
        raise ValueError(f"지원하지 않는 STT provider입니다: '{name}' (지원: {supported})")
    return builder()
