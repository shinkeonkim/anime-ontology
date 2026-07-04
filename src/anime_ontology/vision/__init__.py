"""자막이 없는 영상을 보완하는 기본 장면 분석(장면 전환 감지 + 화면 텍스트 OCR)."""

from anime_ontology.vision.models import VisualCue
from anime_ontology.vision.ocr import OcrError, detect_onscreen_text
from anime_ontology.vision.scene_analysis import analyze_scenes
from anime_ontology.vision.scene_detection import SceneDetectionError, detect_scene_changes

__all__ = [
    "VisualCue",
    "OcrError",
    "SceneDetectionError",
    "analyze_scenes",
    "detect_onscreen_text",
    "detect_scene_changes",
]
