"""RDF(클래스/속성)를 Neo4j 프로퍼티 그래프(라벨/관계 타입)로 옮기는 규칙.

Neo4j로 내보낼 때(export/neo4j_export.py)와, 자연어 질문을 Cypher로 바꿀 때
LLM에게 스키마를 설명할 때(query/schema_context.py) 이 변환 규칙이 어긋나면
안 되므로 한 곳에 모아 공유한다.
"""

from __future__ import annotations

import re

from rdflib import RDFS, URIRef

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
