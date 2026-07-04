#!/usr/bin/env python3
"""CLI: 시리즈 온톨로지(.ttl)를 Neo4j로 내보낸다.

사용 예:
    python scripts/export_neo4j.py naruto

.env에 NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD가 설정되어 있어야 한다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from anime_ontology.export import export_graph_to_neo4j
from anime_ontology.ontology import load_series_graph, strip_core_schema

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description="시리즈 온톨로지를 Neo4j로 내보내기")
    parser.add_argument("series", help="시리즈 이름 (예: naruto)")
    parser.add_argument(
        "--data-dir", type=Path, default=REPO_ROOT / "data", help="온톨로지가 저장된 디렉토리"
    )
    args = parser.parse_args()

    graph = strip_core_schema(load_series_graph(args.data_dir, args.series))
    print(f"[{args.series}] 인스턴스 그래프 로드 완료: 트리플 {len(graph)}개. Neo4j로 내보내는 중...")
    export_graph_to_neo4j(graph)
    print("완료.")


if __name__ == "__main__":
    main()
