"""RDF(클래스/속성)를 Neo4j 프로퍼티 그래프(라벨/관계 타입)로 옮기는 규칙.

Neo4j로 내보낼 때(export/neo4j_export.py)와, 자연어 질문을 Cypher로 바꿀 때
LLM에게 스키마를 설명할 때(query/schema_context.py) 이 변환 규칙이 어긋나면
안 되므로 한 곳에 모아 공유한다.
"""

from __future__ import annotations

import re

from rdflib import RDF, RDFS, Graph, URIRef
from rdflib.namespace import OWL

from anime_ontology.ontology.namespaces import CORE

# RDF 데이터 속성 -> Neo4j 노드 프로퍼티 이름
DATATYPE_PROPERTY_FIELDS = {
    RDFS.label: "name",
    RDFS.comment: "description",
    CORE.aliasName: "aliases",
    CORE.episodeNumber: "episode_number",
}

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def local_name(uri: URIRef) -> str:
    text = str(uri)
    return text.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def sanitize_identifier(name: str) -> str:
    if not _IDENTIFIER.fullmatch(name):
        raise ValueError(f"Neo4j 라벨/관계 타입으로 쓸 수 없는 이름입니다: '{name}'")
    return name


def to_label(class_local_name: str) -> str:
    return sanitize_identifier(class_local_name)


def to_relationship_type(property_local_name: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", property_local_name).upper()
    return sanitize_identifier(snake)


def build_superclass_closure(schema_graph: Graph) -> dict[URIRef, set[URIRef]]:
    """클래스 -> 모든 상위 클래스(rdfs:subClassOf 전이 폐쇄) 매핑을 만든다.

    예: naruto:Jutsu가 core.ttl의 anime:Skill의 하위 클래스라면, Jutsu 인스턴스는
    OWL 의미상 Skill이기도 하고 Ability이기도 하다. rdflib는 asserted 트리플만
    갖고 있고 이 추론을 자동으로 하지 않으므로, Neo4j로 내보낼 때 라벨을 정할 때
    이 폐쇄 집합을 같이 붙여줘야 ":Ability" 같은 상위 개념으로도 조회할 수 있다.
    """
    closure: dict[URIRef, set[URIRef]] = {}
    for class_uri in schema_graph.subjects(RDF.type, OWL.Class):
        ancestors = set(schema_graph.transitive_objects(class_uri, RDFS.subClassOf))
        ancestors.discard(class_uri)
        closure[class_uri] = ancestors
    return closure
