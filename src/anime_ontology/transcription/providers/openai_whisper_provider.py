"""OpenAI Audio API(Whisper)로 음성을 인식한다."""

from __future__ import annotations

from pathlib import Path

import httpx

from anime_ontology.config import env, require_env
from anime_ontology.subtitles.models import SubtitleCue
from anime_ontology.transcription.base import TranscriptionProvider, TranscriptionProviderError


class OpenAIWhisperProvider(TranscriptionProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    @classmethod
    def from_env(cls) -> "OpenAIWhisperProvider":
        return cls(
            api_key=require_env("OPENAI_API_KEY"),
            model=env("OPENAI_WHISPER_MODEL", "whisper-1") or "whisper-1",
            base_url=env("OPENAI_BASE_URL", "https://api.openai.com/v1") or "https://api.openai.com/v1",
        )

    def transcribe(self, audio_path: Path, *, language: str = "ko") -> list[SubtitleCue]:
        try:
            with open(audio_path, "rb") as audio_file:
                response = httpx.post(
                    f"{self._base_url}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    data={"model": self._model, "language": language, "response_format": "verbose_json"},
                    files={"file": (audio_path.name, audio_file, "audio/wav")},
                    timeout=300,
                )
            response.raise_for_status()
            data = response.json()
            return [
                SubtitleCue(start_ms=int(segment["start"] * 1000), end_ms=int(segment["end"] * 1000), text=text)
                for segment in data.get("segments", [])
                if (text := segment.get("text", "").strip())
            ]
        except (httpx.HTTPError, KeyError) as exc:
            raise TranscriptionProviderError(f"OpenAI Whisper 호출 실패: {exc}") from exc
