"""코어 스키마와 시리즈별 온톨로지 그래프를 읽고 쓰는 I/O 계층.

git에는 시리즈별 확장/인스턴스 데이터만 저장하고(코어 스키마와의 중복 없이),
로드할 때는 항상 코어 스키마를 합쳐서 완전한 그래프를 돌려준다.
"""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph

from anime_ontology.ontology.namespaces import CORE, series_namespace

_CORE_SCHEMA_PATH = Path(__file__).parent / "schema" / "core.ttl"


def load_core_schema() -> Graph:
    """코어 스키마만 담긴 그래프를 새로 로드한다."""
    graph = Graph()
    graph.bind("anime", CORE)
    graph.parse(_CORE_SCHEMA_PATH, format="turtle")
    return graph


def series_ontology_path(data_dir: Path, series: str) -> Path:
    return Path(data_dir) / series / "ontology" / f"{series}.ttl"


def load_series_graph(data_dir: Path, series: str) -> Graph:
    """코어 스키마 + 시리즈 확장/인스턴스 데이터를 합친 그래프를 로드한다.

    시리즈 ttl 파일이 아직 없으면 코어 스키마만 있는 그래프를 반환한다(신규 시리즈).
    """
    graph = load_core_schema()
    graph.bind(series, series_namespace(series))

    path = series_ontology_path(data_dir, series)
    if path.exists():
        graph.parse(path, format="turtle")
    return graph


def strip_core_schema(graph: Graph) -> Graph:
    """그래프에서 코어 스키마(클래스/속성 정의) 트리플을 뺀, 시리즈 고유 데이터만 남긴다.

    파일 저장(save_series_graph)과 Neo4j 내보내기 모두, 인스턴스 데이터만 다루고
    owl:Class/rdfs:domain 같은 스키마 정의 트리플은 제외해야 하므로 공통으로 쓴다.
    """
    core = load_core_schema()
    series_only = graph - core
    for prefix, namespace in graph.namespaces():
        series_only.bind(prefix, namespace)
    return series_only


def save_series_graph(graph: Graph, data_dir: Path, series: str) -> Path:
    """그래프에서 코어 스키마 트리플을 제외한 시리즈 고유 부분만 파일로 저장한다."""
    series_only = strip_core_schema(graph)

    path = series_ontology_path(data_dir, series)
    path.parent.mkdir(parents=True, exist_ok=True)
    series_only.serialize(destination=path, format="turtle")
    return path
