"""자막 파서가 공통으로 사용하는 데이터 모델."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SubtitleCue:
    """한 자막 구간(대사)."""

    start_ms: int
    end_ms: int | None
    text: str
