"""장면 분석 결과가 공통으로 쓰는 데이터 모델."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VisualCue:
    """특정 시점 화면에서 OCR로 읽어낸 텍스트(자막이 아니라 화면에 찍힌 글자)."""

    timestamp_ms: int
    text: str
