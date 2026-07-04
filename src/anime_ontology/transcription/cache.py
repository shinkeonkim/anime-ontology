"""화 단위 STT 결과 캐시. 재실행 시 오디오 추출/음성 인식을 다시 하지 않게 한다."""

from __future__ import annotations

import json
from pathlib import Path

from anime_ontology.subtitles.models import SubtitleCue


def cache_path(data_dir: Path, series: str, episode_no: int) -> Path:
    return Path(data_dir) / series / "transcript_cache" / f"{episode_no:03d}.json"


def load_cached_transcript(data_dir: Path, series: str, episode_no: int) -> list[SubtitleCue] | None:
    path = cache_path(data_dir, series, episode_no)
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [SubtitleCue(**item) for item in raw]


def save_transcript_cache(cues: list[SubtitleCue], data_dir: Path, series: str, episode_no: int) -> Path:
    path = cache_path(data_dir, series, episode_no)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [{"start_ms": cue.start_ms, "end_ms": cue.end_ms, "text": cue.text} for cue in cues]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
