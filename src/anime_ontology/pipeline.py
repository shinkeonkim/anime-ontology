"""에피소드 단위로 전체 파이프라인(자막 파싱 -> 추출 -> 온톨로지 병합 -> 저장)을 오케스트레이션한다."""

from __future__ import annotations

from pathlib import Path

from anime_ontology.discovery import find_episode
from anime_ontology.extraction import extract_episode, load_cached_extraction, save_extraction_cache
from anime_ontology.llm import LLMProvider, LLMProviderProxy
from anime_ontology.ontology import OntologyBuilder, load_series_graph, save_series_graph
from anime_ontology.subtitles import parse_subtitle


def parse_episode_range(spec: str) -> list[int]:
    """"1" 또는 "1-5" 형식의 문자열을 화 번호 리스트로 변환한다."""
    spec = spec.strip()
    if "-" in spec:
        start_str, end_str = spec.split("-", 1)
        return list(range(int(start_str), int(end_str) + 1))
    return [int(spec)]


def run_episode(
    series_dir: Path,
    data_dir: Path,
    episode_no: int,
    *,
    llm: LLMProvider | None = None,
    force: bool = False,
) -> Path:
    """한 화를 처리해 시리즈 온톨로지에 병합하고, 저장된 ttl 경로를 반환한다.

    이미 캐시된 추출 결과가 있으면 LLM을 다시 호출하지 않는다(force=True면 무시하고 재호출).
    온톨로지 병합 자체도 이름 기반 중복 제거를 하므로 몇 번을 다시 실행해도 결과가 같다.
    """

    episode = find_episode(series_dir, episode_no)
    if episode is None:
        raise ValueError(f"{episode_no}화 원본을 찾을 수 없습니다: {series_dir}")
    if not episode.has_subtitle:
        raise ValueError(f"{episode_no}화에 자막이 없습니다: {episode.subtitle_path}")

    series = episode.series

    cached_result = None if force else load_cached_extraction(data_dir, series, episode_no)
    if cached_result is not None:
        result = cached_result
    else:
        cues = parse_subtitle(episode.subtitle_path)
        provider = llm or LLMProviderProxy.from_env()
        result = extract_episode(provider, series, episode_no, cues)
        save_extraction_cache(result, data_dir, series, episode_no)

    graph = load_series_graph(data_dir, series)
    OntologyBuilder(graph, series).merge_extraction(episode_no, result)
    return save_series_graph(graph, data_dir, series)


def run_episodes(
    series_dir: Path,
    data_dir: Path,
    episode_numbers: list[int],
    *,
    llm: LLMProvider | None = None,
    force: bool = False,
) -> Path:
    """여러 화를 순서대로 처리한다. 마지막으로 저장된 ttl 경로를 반환한다."""

    output_path: Path | None = None
    for episode_no in episode_numbers:
        output_path = run_episode(series_dir, data_dir, episode_no, llm=llm, force=force)
    if output_path is None:
        raise ValueError("처리할 화 번호가 비어 있습니다.")
    return output_path
