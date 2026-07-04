"""여러 STT provider를 하나의 TranscriptionProvider처럼 보이게 감싸는 Proxy.

LLMProviderProxy와 동일한 패턴이다: `.env`의 TRANSCRIPTION_PROVIDER/
TRANSCRIPTION_FALLBACK_PROVIDERS 설정만으로 local_whisper <-> openai를 교체할 수 있다.
"""

from __future__ import annotations

from pathlib import Path

from anime_ontology.subtitles.models import SubtitleCue
from anime_ontology.transcription.base import TranscriptionProvider, TranscriptionProviderError
from anime_ontology.transcription.config import TranscriptionSettings
from anime_ontology.transcription.providers.registry import build_provider


class TranscriptionProviderProxy(TranscriptionProvider):
    name = "proxy"

    def __init__(self, primary: str, fallbacks: list[str] | None = None) -> None:
        self._provider_names = [primary, *(fallbacks or [])]
        self._provider_cache: dict[str, TranscriptionProvider] = {}

    @classmethod
    def from_env(cls) -> "TranscriptionProviderProxy":
        settings = TranscriptionSettings.from_env()
        return cls(settings.default_provider, settings.fallback_providers)

    def _resolve(self, name: str) -> TranscriptionProvider:
        if name not in self._provider_cache:
            self._provider_cache[name] = build_provider(name)
        return self._provider_cache[name]

    def transcribe(self, audio_path: Path, *, language: str = "ko") -> list[SubtitleCue]:
        errors: list[str] = []
        for name in self._provider_names:
            try:
                provider = self._resolve(name)
                return provider.transcribe(audio_path, language=language)
            except TranscriptionProviderError as exc:
                errors.append(f"{name}: {exc}")
            except Exception as exc:  # provider 생성 실패(패키지 미설치 등)
                errors.append(f"{name}: 초기화 실패 - {exc}")

        raise TranscriptionProviderError("모든 STT provider 호출이 실패했습니다.\n" + "\n".join(errors))
