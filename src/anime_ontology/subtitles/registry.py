"""자막 확장자에 맞는 파서를 선택하는 레지스트리.

새로운 자막 형식(.srt, .ass 등)을 지원하려면 파서 함수를 만들고
_PARSERS에 확장자만 추가하면 된다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from anime_ontology.subtitles.models import SubtitleCue
from anime_ontology.subtitles.smi_parser import parse_smi

_PARSERS: dict[str, Callable[[Path], list[SubtitleCue]]] = {
    ".smi": parse_smi,
}


def parse_subtitle(path: Path) -> list[SubtitleCue]:
    """확장자에 맞는 파서로 자막 파일을 파싱한다."""

    path = Path(path)
    ext = path.suffix.lower()
    parser = _PARSERS.get(ext)
    if parser is None:
        supported = ", ".join(sorted(_PARSERS))
        raise ValueError(f"지원하지 않는 자막 형식입니다: '{ext}' (지원 형식: {supported})")
    return parser(path)
