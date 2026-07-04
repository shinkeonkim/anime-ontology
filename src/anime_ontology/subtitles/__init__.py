"""자막 파일을 시간순 대사(cue) 목록으로 변환하는 패키지."""

from anime_ontology.subtitles.models import SubtitleCue
from anime_ontology.subtitles.registry import parse_subtitle

__all__ = ["SubtitleCue", "parse_subtitle"]
