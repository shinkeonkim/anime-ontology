"""생성된 Cypher를 Neo4j에서 실행하고, 표(rows)와 시각화용 서브그래프(nodes/edges)로 변환한다.

`RoutingControl.READ`로 실행해 Neo4j 서버 자신도 쓰기 절을 거부하게 만든다
(query/safety.py의 정적 검사와 이중으로 방어).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from neo4j import RoutingControl
from neo4j.graph import Node, Path, Relationship

from anime_ontology.neo4j_client import Neo4jSettings, open_driver


@dataclass
class QueryExecutionResult:
    columns: list[str]
    rows: list[dict]
    nodes: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)


def _node_to_dict(node: Node) -> dict:
    props = dict(node)
    return {
        "id": props.get("uri") or node.element_id,
        "labels": sorted(node.labels),
        "name": props.get("name"),
        "description": props.get("description"),
    }


def _edge_key_and_dict(rel: Relationship) -> tuple[str, dict]:
    source = dict(rel.start_node).get("uri") or rel.start_node.element_id
    target = dict(rel.end_node).get("uri") or rel.end_node.element_id
    return rel.element_id, {"type": rel.type, "source": source, "target": target}


def _scalar_value(value):
    if isinstance(value, Node):
        props = dict(value)
        return props.get("name") or props.get("uri")
    if isinstance(value, Relationship):
        return value.type
    if isinstance(value, list):
        return [_scalar_value(item) for item in value]
    return value


def _collect_graph_elements(value, nodes: dict[str, dict], edges: dict[str, dict]) -> None:
    if isinstance(value, Node):
        node_dict = _node_to_dict(value)
        nodes[node_dict["id"]] = node_dict
    elif isinstance(value, Relationship):
        edge_id, edge_dict = _edge_key_and_dict(value)
        edges[edge_id] = edge_dict
        _collect_graph_elements(value.start_node, nodes, edges)
        _collect_graph_elements(value.end_node, nodes, edges)
    elif isinstance(value, Path):
        for node in value.nodes:
            _collect_graph_elements(node, nodes, edges)
        for rel in value.relationships:
            _collect_graph_elements(rel, nodes, edges)
    elif isinstance(value, list):
        for item in value:
            _collect_graph_elements(item, nodes, edges)


def execute_cypher(cypher: str, settings: Neo4jSettings | None = None) -> QueryExecutionResult:
    """Cypher를 읽기 전용으로 실행하고 표/서브그래프 형태로 반환한다."""

    nodes: dict[str, dict] = {}
    edges: dict[str, dict] = {}
    rows: list[dict] = []

    with open_driver(settings) as driver:
        records, _summary, keys = driver.execute_query(cypher, routing_=RoutingControl.READ)
        for record in records:
            row = {}
            for key in keys:
                value = record[key]
                _collect_graph_elements(value, nodes, edges)
                row[key] = _scalar_value(value)
            rows.append(row)

    return QueryExecutionResult(columns=list(keys), rows=rows, nodes=list(nodes.values()), edges=list(edges.values()))
