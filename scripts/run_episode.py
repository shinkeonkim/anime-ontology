#!/usr/bin/env python3
"""CLI: 시리즈 이름과 화 번호(또는 범위)를 받아 파이프라인을 실행한다.

사용 예:
    python scripts/run_episode.py naruto --episode 1
    python scripts/run_episode.py naruto --episodes 1-5
    python scripts/run_episode.py naruto --episodes 1-5 --force

실행 전 `uv pip install -e .`로 패키지를 설치해야 anime_ontology를 가져올 수 있다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from anime_ontology.pipeline import parse_episode_range, run_episode

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description="애니메이션 자막 -> 온톨로지 파이프라인 실행")
    parser.add_argument("series", help="시리즈 디렉토리 이름 (예: naruto)")
    parser.add_argument("--episode", type=int, help="처리할 화 번호 하나")
    parser.add_argument("--episodes", help="처리할 화 범위, 예: 1-5")
    parser.add_argument(
        "--series-dir", type=Path, default=None, help="원본 데이터 디렉토리 (기본: <repo>/<series>)"
    )
    parser.add_argument(
        "--data-dir", type=Path, default=REPO_ROOT / "data", help="온톨로지/캐시 출력 디렉토리"
    )
    parser.add_argument("--force", action="store_true", help="캐시를 무시하고 LLM을 다시 호출")
    args = parser.parse_args()

    if not args.episode and not args.episodes:
        parser.error("--episode 또는 --episodes 중 하나는 필요합니다.")

    series_dir = args.series_dir or (REPO_ROOT / args.series)
    episode_numbers = [args.episode] if args.episode else parse_episode_range(args.episodes)

    for episode_no in episode_numbers:
        print(f"[{args.series}] {episode_no}화 처리 중...")
        output_path = run_episode(series_dir, args.data_dir, episode_no, force=args.force)
        print(f"  -> {output_path}")


if __name__ == "__main__":
    main()
