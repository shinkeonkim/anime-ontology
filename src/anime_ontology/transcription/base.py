"""음성 인식(STT) Provider가 지켜야 하는 공통 인터페이스.

자막이 없는 영상을 처리할 때, 결과를 SubtitleCue로 돌려주게 해서 자막 파싱
경로(subtitles 패키지)와 동일한 형태로 추출 파이프라인에 들어가게 한다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from anime_ontology.subtitles.models import SubtitleCue


class TranscriptionProviderError(RuntimeError):
    """음성 인식 호출이 실패했음을 나타내는 예외."""


class TranscriptionProvider(ABC):
    name: str

    @abstractmethod
    def transcribe(self, audio_path: Path, *, language: str = "ko") -> list[SubtitleCue]:
        """오디오 파일을 시간 정보가 있는 SubtitleCue 목록으로 변환한다."""
        raise NotImplementedError
