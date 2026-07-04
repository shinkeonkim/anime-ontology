"""STT provider 선택(기본/대체) 설정."""

from __future__ import annotations

from dataclasses import dataclass, field

from anime_ontology.config import env


@dataclass(frozen=True)
class TranscriptionSettings:
    default_provider: str
    fallback_providers: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "TranscriptionSettings":
        default_provider = env("TRANSCRIPTION_PROVIDER", "local_whisper") or "local_whisper"
        raw_fallbacks = env("TRANSCRIPTION_FALLBACK_PROVIDERS", "") or ""
        fallback_providers = [name.strip() for name in raw_fallbacks.split(",") if name.strip()]
        return cls(default_provider=default_provider, fallback_providers=fallback_providers)
