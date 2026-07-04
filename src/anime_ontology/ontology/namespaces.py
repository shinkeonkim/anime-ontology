"""온톨로지에서 사용하는 RDF 네임스페이스."""

from __future__ import annotations

from rdflib import Namespace

CORE = Namespace("https://anime-ontology.local/core#")


def series_namespace(series: str) -> Namespace:
    """시리즈별 확장 클래스/인스턴스가 사용하는 네임스페이스."""
    return Namespace(f"https://anime-ontology.local/series/{series}#")
