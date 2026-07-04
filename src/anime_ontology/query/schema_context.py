"""코어 온톨로지로부터, LLM이 Cypher를 생성할 때 참고할 스키마 설명 텍스트를 만든다.

core.ttl이 바뀌면(클래스/관계 추가 등) 이 설명도 자동으로 갱신되므로, Neo4j로
내보내는 규칙(ontology/property_graph_mapping.py)과 항상 같은 스키마를 본다.
"""

from __future__ import annotations

from rdflib import RDF, RDFS
from rdflib.namespace import OWL

from anime_ontology.ontology.property_graph_mapping import (
    DATATYPE_PROPERTY_FIELDS,
    local_name,
    to_label,
    to_relationship_type,
)
from anime_ontology.ontology.store import load_core_schema


def build_schema_description() -> str:
    core = load_core_schema()
    lines: list[str] = []

    lines.append("모든 노드는 공통으로 :Entity 라벨과 uri 속성을 가진다. 그 외 라벨:")
    for class_uri in core.subjects(RDF.type, OWL.Class):
        label = core.value(class_uri, RDFS.label)
        comment = core.value(class_uri, RDFS.comment)
        lines.append(f"- :{to_label(local_name(class_uri))} ({label}) - {comment}")

    lines.append("")
    lines.append("관계 타입:")
    for prop_uri in core.subjects(RDF.type, OWL.ObjectProperty):
        label = core.value(prop_uri, RDFS.label)
        lines.append(f"- [:{to_relationship_type(local_name(prop_uri))}] ({label})")

    lines.append("")
    lines.append("노드 프로퍼티:")
    for field in dict.fromkeys(DATATYPE_PROPERTY_FIELDS.values()):
        lines.append(f"- {field}")
    lines.append("(name=이름, description=설명, aliases=별칭 목록, episode_number=화 번호(Episode 노드만))")

    return "\n".join(lines)
