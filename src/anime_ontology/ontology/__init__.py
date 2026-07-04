"""RDF/OWL 기반 온톨로지 스키마 및 저장소."""

from anime_ontology.ontology.builder import OntologyBuilder
from anime_ontology.ontology.namespaces import CORE, series_namespace
from anime_ontology.ontology.store import load_series_graph, save_series_graph, series_ontology_path

__all__ = [
    "CORE",
    "OntologyBuilder",
    "series_namespace",
    "load_series_graph",
    "save_series_graph",
    "series_ontology_path",
]
