"""자연어 질문 -> Cypher 생성 -> 실행 -> 답변 합성을 오케스트레이션한다."""

from __future__ import annotations

from dataclasses import dataclass, field

from anime_ontology.llm import LLMProvider, LLMProviderProxy
from anime_ontology.neo4j_client import Neo4jSettings
from anime_ontology.query.answer import synthesize_answer
from anime_ontology.query.cypher_generation import generate_cypher
from anime_ontology.query.executor import execute_cypher
from anime_ontology.query.safety import ensure_limit, ensure_read_only
from anime_ontology.query.schema_context import build_schema_description


@dataclass
class QueryAnswer:
    question: str
    cypher: str = ""
    columns: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    nodes: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)
    answer: str = ""
    error: str | None = None


class NLQueryEngine:
    """지식그래프에 자연어로 질문할 수 있게 해주는 엔진."""

    def __init__(
        self,
        llm: LLMProvider | None = None,
        neo4j_settings: Neo4jSettings | None = None,
        *,
        max_attempts: int = 2,
    ) -> None:
        self._llm = llm or LLMProviderProxy.from_env()
        self._neo4j_settings = neo4j_settings or Neo4jSettings.from_env()
        self._max_attempts = max_attempts
        self._schema_description = build_schema_description()

    def ask(self, question: str) -> QueryAnswer:
        cypher = generate_cypher(self._llm, question, self._schema_description)

        for attempt in range(self._max_attempts):
            try:
                ensure_read_only(cypher)
                runnable_cypher = ensure_limit(cypher)
                result = execute_cypher(runnable_cypher, self._neo4j_settings)
            except Exception as exc:  # noqa: BLE001 - 생성/실행 실패를 폭넓게 잡아 재시도하거나 에러로 응답
                error = str(exc)
                is_last_attempt = attempt + 1 == self._max_attempts
                if is_last_attempt:
                    return QueryAnswer(question=question, cypher=cypher, error=error)
                cypher = generate_cypher(
                    self._llm, question, self._schema_description, previous_cypher=cypher, previous_error=error
                )
                continue

            answer_text = synthesize_answer(self._llm, question, result)
            return QueryAnswer(
                question=question,
                cypher=runnable_cypher,
                columns=result.columns,
                rows=result.rows,
                nodes=result.nodes,
                edges=result.edges,
                answer=answer_text,
            )
