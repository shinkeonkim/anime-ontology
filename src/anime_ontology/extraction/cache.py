"""에피소드별 LLM 추출 원본 결과 캐시.

같은 화를 다시 처리할 때 LLM을 다시 호출하지 않도록(비용/시간 절약, 재실행 안전성)
JSON으로 캐시한다. 캐시는 재생성 가능한 산출물이라 git에는 포함하지 않는다(.gitignore).
"""

from __future__ import annotations

from pathlib import Path

from anime_ontology.extraction.schema import ExtractionResult


def cache_path(data_dir: Path, series: str, episode_no: int) -> Path:
    return Path(data_dir) / series / "extraction_cache" / f"{episode_no:03d}.json"


def load_cached_extraction(data_dir: Path, series: str, episode_no: int) -> ExtractionResult | None:
    path = cache_path(data_dir, series, episode_no)
    if not path.exists():
        return None
    return ExtractionResult.model_validate_json(path.read_text(encoding="utf-8"))


def save_extraction_cache(
    result: ExtractionResult, data_dir: Path, series: str, episode_no: int
) -> Path:
    path = cache_path(data_dir, series, episode_no)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return path
