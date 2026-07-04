"""장면 전환 감지 + 화면 텍스트 OCR을 묶은 "기본" 장면 분석."""

from __future__ import annotations

from pathlib import Path

from anime_ontology.vision.models import VisualCue
from anime_ontology.vision.ocr import detect_onscreen_text
from anime_ontology.vision.scene_detection import detect_scene_changes


def analyze_scenes(video_path: Path, *, max_scenes: int = 60, lang: str = "kor+eng") -> list[VisualCue]:
    """장면이 바뀌는 시점마다 화면 텍스트를 OCR로 읽어 VisualCue 목록으로 반환한다.

    OCR은 한 번에 프레임을 캡처하고 처리해야 해서 비용이 크므로, max_scenes로
    한 화당 OCR 호출 횟수를 제한한다.
    """

    timestamps_ms = detect_scene_changes(video_path, max_scenes=max_scenes)
    return detect_onscreen_text(video_path, timestamps_ms, lang=lang)
