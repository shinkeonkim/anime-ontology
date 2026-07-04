"""시리즈 디렉토리에서 영상/자막 파일을 화(episode) 단위로 페어링한다.

시리즈마다 파일명 규칙이 다를 수 있으므로, 아래 원칙만으로 동작하도록 만든다.

1. 영상 확장자와 자막 확장자를 재귀적으로 탐색한다.
2. 확장자를 뗀 파일명(stem)이 같은 영상/자막을 한 쌍으로 묶는다.
3. stem 끝의 숫자를 에피소드 번호로 쓰고, 숫자가 없으면 자연 정렬 순서를 번호로 쓴다.
4. stem 끝이 "221~222"처럼 두 숫자면 합본 화로 보고, 같은 파일을 두 화 번호 모두에 매핑한다.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi"}
SUBTITLE_EXTENSIONS = {".smi", ".srt", ".ass", ".vtt"}

_TRAILING_NUMBER = re.compile(r"(\d+)\s*$")
_COMBINED_TRAILING_NUMBERS = re.compile(r"(\d+)\s*~\s*(\d+)\s*$")
_NATURAL_SORT_CHUNK = re.compile(r"(\d+)")


@dataclass(frozen=True)
class EpisodeSource:
    """한 화(episode)에 대응하는 원본 파일 경로 묶음."""

    series: str
    episode_no: int
    stem: str
    video_path: Path | None
    subtitle_path: Path | None

    @property
    def has_subtitle(self) -> bool:
        return self.subtitle_path is not None


def _natural_sort_key(stem: str) -> tuple:
    chunks = _NATURAL_SORT_CHUNK.split(stem)
    return tuple(int(c) if c.isdigit() else c for c in chunks)


def _normalize_stem(stem: str) -> str:
    """유니코드 정규화 형식(NFC/NFD)을 통일한다.

    macOS(APFS/HFS+)는 한글 파일명을 NFD로 저장하는 반면, 대부분의 다운로드/복사
    도구는 NFC를 쓴다. 같은 이름의 영상/자막이 서로 다른 정규화 형식으로 존재하면
    바이트 단위로는 다른 문자열이 되어 페어링이 깨지므로, 비교 전에 NFC로 통일한다.
    """
    return unicodedata.normalize("NFC", stem)


def _infer_episode_numbers(stem: str, fallback_index: int) -> list[int]:
    """stem에서 화 번호를 추론한다. "221~222"처럼 합본 화면 두 번호를 모두 반환한다."""
    combined = _COMBINED_TRAILING_NUMBERS.search(stem)
    if combined:
        start, end = int(combined.group(1)), int(combined.group(2))
        return list(range(start, end + 1))

    match = _TRAILING_NUMBER.search(stem)
    if match:
        return [int(match.group(1))]
    return [fallback_index]


def discover_episodes(series_dir: Path, series: str | None = None) -> list[EpisodeSource]:
    """series_dir 하위를 재귀 탐색하여 화 단위로 정렬된 EpisodeSource 목록을 반환한다."""

    series_dir = Path(series_dir)
    series_name = series or series_dir.name

    videos_by_stem: dict[str, Path] = {}
    subtitles_by_stem: dict[str, Path] = {}

    for path in series_dir.rglob("*"):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        stem = _normalize_stem(path.stem)
        if ext in VIDEO_EXTENSIONS:
            videos_by_stem.setdefault(stem, path)
        elif ext in SUBTITLE_EXTENSIONS:
            subtitles_by_stem.setdefault(stem, path)

    all_stems = sorted(set(videos_by_stem) | set(subtitles_by_stem), key=_natural_sort_key)

    episodes: list[EpisodeSource] = []
    seen_episode_nos: dict[int, str] = {}
    for index, stem in enumerate(all_stems, start=1):
        # "221~222"처럼 두 화가 한 파일로 합본 발매된 경우, 같은 영상/자막을
        # 두 화 번호 모두에 매핑한다(내용을 나눌 기준이 없어 그대로 중복 처리).
        for episode_no in _infer_episode_numbers(stem, fallback_index=index):
            if episode_no in seen_episode_nos:
                raise ValueError(
                    f"에피소드 번호 {episode_no}가 중복되었습니다: "
                    f"'{seen_episode_nos[episode_no]}'와 '{stem}'"
                )
            seen_episode_nos[episode_no] = stem
            episodes.append(
                EpisodeSource(
                    series=series_name,
                    episode_no=episode_no,
                    stem=stem,
                    video_path=videos_by_stem.get(stem),
                    subtitle_path=subtitles_by_stem.get(stem),
                )
            )

    episodes.sort(key=lambda ep: ep.episode_no)
    return episodes


def find_episode(series_dir: Path, episode_no: int, series: str | None = None) -> EpisodeSource | None:
    """특정 화 번호에 해당하는 EpisodeSource를 찾는다. 없으면 None."""

    for episode in discover_episodes(series_dir, series=series):
        if episode.episode_no == episode_no:
            return episode
    return None
