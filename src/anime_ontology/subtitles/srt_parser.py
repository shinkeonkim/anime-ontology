"""SubRip(.srt) 자막 파서."""

from __future__ import annotations

import re
from pathlib import Path

from anime_ontology.subtitles.encoding import decode_subtitle_bytes
from anime_ontology.subtitles.models import SubtitleCue

_TIMESTAMP_LINE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
)
_ANY_TAG = re.compile(r"<[^>]+>")


def _to_ms(hours: str, minutes: str, seconds: str, millis: str) -> int:
    return ((int(hours) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(millis)


def _clean_text(text: str) -> str:
    lines = (_ANY_TAG.sub("", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def parse_srt(path: Path) -> list[SubtitleCue]:
    """SubRip(.srt) 자막 파일을 시간순 SubtitleCue 목록으로 변환한다."""

    text = decode_subtitle_bytes(Path(path).read_bytes())
    blocks = re.split(r"\r?\n\r?\n+", text.strip())

    cues: list[SubtitleCue] = []
    for block in blocks:
        lines = [line for line in block.splitlines() if line.strip()]
        timestamp_index = next((i for i, line in enumerate(lines) if _TIMESTAMP_LINE.search(line)), None)
        if timestamp_index is None:
            continue

        match = _TIMESTAMP_LINE.search(lines[timestamp_index])
        assert match is not None
        start_ms = _to_ms(*match.groups()[0:4])
        end_ms = _to_ms(*match.groups()[4:8])

        cue_text = _clean_text("\n".join(lines[timestamp_index + 1 :]))
        if not cue_text:
            continue

        cues.append(SubtitleCue(start_ms=start_ms, end_ms=end_ms, text=cue_text))

    return cues
