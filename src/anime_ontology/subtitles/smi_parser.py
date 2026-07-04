"""SAMI(.smi) 자막 파서.

한국 팬섭에서 흔히 쓰이는 SAMI는 EUC-KR/CP949로 저장된 경우가 많고, 표준 XML이
아니라 태그가 닫히지 않는 등 형식이 느슨하므로 정규식으로 파싱한다.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from anime_ontology.subtitles.encoding import decode_subtitle_bytes
from anime_ontology.subtitles.models import SubtitleCue

_SYNC_TAG = re.compile(r"<SYNC\s+Start\s*=\s*(\d+)[^>]*>", re.IGNORECASE)
_BR_TAG = re.compile(r"<br\s*/?>", re.IGNORECASE)
_ANY_TAG = re.compile(r"<[^>]+>")


def _clean_block_text(block: str) -> str:
    block = _BR_TAG.sub("\n", block)
    block = _ANY_TAG.sub("", block)
    block = html.unescape(block)
    lines = (line.strip() for line in block.splitlines())
    return "\n".join(line for line in lines if line)


def parse_smi(path: Path) -> list[SubtitleCue]:
    """SAMI(.smi) 자막 파일을 시간순 SubtitleCue 목록으로 변환한다."""

    text = decode_subtitle_bytes(Path(path).read_bytes())
    matches = list(_SYNC_TAG.finditer(text))

    cues: list[SubtitleCue] = []
    for index, match in enumerate(matches):
        block_start = match.end()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        cue_text = _clean_block_text(text[block_start:block_end])
        if not cue_text:
            continue

        start_ms = int(match.group(1))
        end_ms = int(matches[index + 1].group(1)) if index + 1 < len(matches) else None
        cues.append(SubtitleCue(start_ms=start_ms, end_ms=end_ms, text=cue_text))

    return cues
