"""쿼리 결과(rows)를 근거로 질문에 대한 자연어 답변을 합성한다."""

from __future__ import annotations

import json

from anime_ontology.llm.base import LLMProvider
from anime_ontology.query.executor import QueryExecutionResult

_SYSTEM_PROMPT = """\
너는 그래프 데이터베이스 쿼리 결과를 보고 사용자 질문에 답하는 도우미다.
아래 JSON으로 주어지는 쿼리 결과(rows: 쿼리가 반환한 행, entities: 결과에 등장한
노드의 이름/설명)만 근거로 한국어로 간결하게 답하라. entities의 description을
적극 활용해라. 결과에 없는 내용은 추측해서 지어내지 마라. rows와 entities가 모두
비어 있으면 "결과가 없습니다"라고 답하라.
"""

_MAX_ITEMS_FOR_PROMPT = 30


def synthesize_answer(llm: LLMProvider, question: str, result: QueryExecutionResult) -> str:
    payload = {
        "rows": result.rows[:_MAX_ITEMS_FOR_PROMPT],
        "entities": [
            {"name": node.get("name"), "description": node.get("description")}
            for node in result.nodes[:_MAX_ITEMS_FOR_PROMPT]
            if node.get("description")
        ],
    }
    user = f"질문: {question}\n\n쿼리 결과:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    return llm.complete(system=_SYSTEM_PROMPT, user=user, temperature=0.0)
