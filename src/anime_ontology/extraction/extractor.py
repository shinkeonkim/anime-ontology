"""자막 큐를 청크로 나눠 LLM Provider(Proxy)로 개체/관계를 추출한다."""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from anime_ontology.extraction.prompts import SYSTEM_PROMPT, build_user_prompt
from anime_ontology.extraction.schema import ExtractionResult
from anime_ontology.llm.base import LLMProvider
from anime_ontology.subtitles.models import SubtitleCue

_CODE_FENCE = re.compile(r"^```(?:json)?|```$", re.MULTILINE)


class ExtractionError(RuntimeError):
    """LLM 응답을 유효한 추출 결과로 파싱하지 못했을 때 발생한다."""


def _format_timestamp(ms: int) -> str:
    total_seconds = ms // 1000
    return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"


def build_transcript(cues: list[SubtitleCue]) -> str:
    """자막 큐 목록을 '[mm:ss] 대사' 형태의 텍스트로 합친다."""
    lines = (f"[{_format_timestamp(cue.start_ms)}] {cue.text.replace(chr(10), ' / ')}" for cue in cues)
    return "\n".join(lines)


def chunk_cues(cues: list[SubtitleCue], max_chars: int = 3000) -> list[list[SubtitleCue]]:
    """자막 큐를 글자 수 기준으로 나눠, LLM 한 번 호출로 처리할 분량의 청크를 만든다."""
    chunks: list[list[SubtitleCue]] = []
    current: list[SubtitleCue] = []
    current_len = 0

    for cue in cues:
        cue_len = len(cue.text)
        if current and current_len + cue_len > max_chars:
            chunks.append(current)
            current = []
            current_len = 0
        current.append(cue)
        current_len += cue_len

    if current:
        chunks.append(current)
    return chunks


def _parse_json_object(raw: str) -> dict:
    text = _CODE_FENCE.sub("", raw).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("응답에서 JSON 객체를 찾을 수 없습니다.")
    return json.loads(text[start : end + 1])


def extract_chunk(
    llm: LLMProvider,
    series: str,
    episode_no: int,
    cues: list[SubtitleCue],
    *,
    max_retries: int = 1,
) -> ExtractionResult:
    """자막 청크 하나를 LLM에 보내 ExtractionResult로 검증까지 마친다."""

    user_prompt = build_user_prompt(series, episode_no, build_transcript(cues))

    last_error: Exception | None = None
    for _ in range(max_retries + 1):
        raw = llm.complete(system=SYSTEM_PROMPT, user=user_prompt)
        try:
            return ExtractionResult.model_validate(_parse_json_object(raw))
        except (ValueError, ValidationError) as exc:
            last_error = exc

    raise ExtractionError(f"LLM 응답을 추출 결과로 파싱하지 못했습니다: {last_error}")


def extract_episode(
    llm: LLMProvider,
    series: str,
    episode_no: int,
    cues: list[SubtitleCue],
    *,
    max_chars_per_chunk: int = 3000,
) -> ExtractionResult:
    """한 화 전체 자막을 청크 단위로 추출한 뒤 하나의 ExtractionResult로 합친다."""

    result = ExtractionResult()
    for chunk in chunk_cues(cues, max_chars=max_chars_per_chunk):
        result = result.merged_with(extract_chunk(llm, series, episode_no, chunk))
    return result
