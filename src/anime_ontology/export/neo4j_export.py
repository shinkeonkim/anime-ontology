"""RDF 시리즈 그래프를 Neo4j로 내보낸다.

RDF(.ttl)가 정본이고 Neo4j는 시각화/탐색을 위한 파생 산출물이므로, 이 모듈은
언제 다시 실행해도 같은 노드/관계로 수렴하도록 URI를 유일 키로 MERGE만 사용한다.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from neo4j import GraphDatabase
from rdflib import RDF, RDFS, Graph, Literal, URIRef

from anime_ontology.config import env, require_env
from anime_ontology.ontology.namespaces import CORE

_DATATYPE_PROPERTY_FIELDS = {
    RDFS.label: "name",
    RDFS.comment: "description",
    CORE.aliasName: "aliases",
    CORE.episodeNumber: "episode_number",
}

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class Neo4jSettings:
    uri: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "Neo4jSettings":
        return cls(
            uri=env("NEO4J_URI", "bolt://localhost:7687") or "bolt://localhost:7687",
            user=env("NEO4J_USER", "neo4j") or "neo4j",
            password=require_env("NEO4J_PASSWORD"),
        )


def _local_name(uri: URIRef) -> str:
    text = str(uri)
    return text.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _sanitize_identifier(name: str) -> str:
    if not _IDENTIFIER.fullmatch(name):
        raise ValueError(f"Neo4j 라벨/관계 타입으로 쓸 수 없는 이름입니다: '{name}'")
    return name


def _to_label(local_name: str) -> str:
    return _sanitize_identifier(local_name)


def _to_relationship_type(local_name: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", local_name).upper()
    return _sanitize_identifier(snake)


def _collect_nodes(graph: Graph) -> dict[URIRef, dict]:
    nodes: dict[URIRef, dict] = defaultdict(lambda: {"labels": set(), "props": defaultdict(list)})

    for subject, predicate, obj in graph:
        if predicate == RDF.type and isinstance(obj, URIRef):
            nodes[subject]["labels"].add(_to_label(_local_name(obj)))
        elif predicate in _DATATYPE_PROPERTY_FIELDS and isinstance(obj, Literal):
            field = _DATATYPE_PROPERTY_FIELDS[predicate]
            nodes[subject]["props"][field].append(obj.toPython())

    return nodes


def _collect_relationships(graph: Graph) -> list[tuple[URIRef, str, URIRef]]:
    relationships = []
    for subject, predicate, obj in graph:
        if predicate == RDF.type or predicate in _DATATYPE_PROPERTY_FIELDS:
            continue
        if not isinstance(obj, URIRef):
            continue
        relationships.append((subject, _to_relationship_type(_local_name(predicate)), obj))
    return relationships


def _ensure_constraint(tx) -> None:
    tx.run("CREATE CONSTRAINT entity_uri IF NOT EXISTS FOR (n:Entity) REQUIRE n.uri IS UNIQUE")


def _merge_node(tx, uri: str, labels: list[str], props: dict[str, list]) -> None:
    flat_props = {key: (values if len(values) > 1 else values[0]) for key, values in props.items()}
    label_clause = "".join(f":{label}" for label in labels)
    set_labels = f" SET n{label_clause}" if label_clause else ""
    tx.run(f"MERGE (n:Entity {{uri: $uri}}){set_labels} SET n += $props", uri=uri, props=flat_props)


def _merge_relationship(tx, subject_uri: str, rel_type: str, object_uri: str) -> None:
    tx.run(
        f"""
        MERGE (a:Entity {{uri: $subject_uri}})
        MERGE (b:Entity {{uri: $object_uri}})
        MERGE (a)-[:{rel_type}]->(b)
        """,
        subject_uri=subject_uri,
        object_uri=object_uri,
    )


def export_graph_to_neo4j(graph: Graph, settings: Neo4jSettings | None = None) -> None:
    """RDF 그래프의 클래스/속성을 Neo4j 노드/관계로 MERGE한다."""

    settings = settings or Neo4jSettings.from_env()
    nodes = _collect_nodes(graph)
    relationships = _collect_relationships(graph)

    driver = GraphDatabase.driver(settings.uri, auth=(settings.user, settings.password))
    try:
        with driver.session() as session:
            session.execute_write(_ensure_constraint)
            for subject, data in nodes.items():
                session.execute_write(_merge_node, str(subject), sorted(data["labels"]), dict(data["props"]))
            for subject, rel_type, obj in relationships:
                session.execute_write(_merge_relationship, str(subject), rel_type, str(obj))
    finally:
        driver.close()
