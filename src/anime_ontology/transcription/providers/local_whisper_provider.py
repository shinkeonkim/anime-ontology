"""faster-whisper로 로컬에서 음성을 인식한다. API 키가 필요 없다.

`pip install -e ".[stt]"`로 faster-whisper를 설치해야 쓸 수 있다.
"""

from __future__ import annotations

from pathlib import Path

from anime_ontology.config import env
from anime_ontology.subtitles.models import SubtitleCue
from anime_ontology.transcription.base import TranscriptionProvider, TranscriptionProviderError


class LocalWhisperProvider(TranscriptionProvider):
    name = "local_whisper"

    def __init__(self, model_size: str, compute_type: str) -> None:
        self._model_size = model_size
        self._compute_type = compute_type
        self._model = None  # 모델 파일이 커서 실제로 쓸 때(transcribe 호출 시)만 로드한다.

    @classmethod
    def from_env(cls) -> "LocalWhisperProvider":
        return cls(
            model_size=env("WHISPER_MODEL_SIZE", "small") or "small",
            compute_type=env("WHISPER_COMPUTE_TYPE", "int8") or "int8",
        )

    def _get_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise TranscriptionProviderError(
                    "faster-whisper가 설치되어 있지 않습니다. `uv pip install -e \".[stt]\"`로 설치하세요."
                ) from exc
            self._model = WhisperModel(self._model_size, compute_type=self._compute_type)
        return self._model

    def transcribe(self, audio_path: Path, *, language: str = "ko") -> list[SubtitleCue]:
        try:
            model = self._get_model()
            segments, _info = model.transcribe(str(audio_path), language=language)
            return [
                SubtitleCue(start_ms=int(segment.start * 1000), end_ms=int(segment.end * 1000), text=text)
                for segment in segments
                if (text := segment.text.strip())
            ]
        except TranscriptionProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - whisper 내부 예외를 공통 에러로 변환
            raise TranscriptionProviderError(f"로컬 Whisper 인식 실패: {exc}") from exc
