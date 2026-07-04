"""자연어 질문을 Cypher 쿼리로 바꾼다 (LLM Provider Proxy 사용, 벤더 중립)."""

from __future__ import annotations

import re

from anime_ontology.llm.base import LLMProvider

_CODE_FENCE = re.compile(r"^```(?:cypher)?|```$", re.MULTILINE)

_SYSTEM_TEMPLATE = """\
너는 Neo4j 그래프 데이터베이스에 대한 자연어 질문을 Cypher 쿼리로 바꾸는 변환기다.
아래 스키마에 있는 라벨/관계/프로퍼티만 사용해서 읽기 전용 Cypher 쿼리 하나만 출력한다.

규칙:
- MATCH, WHERE, WITH, RETURN, ORDER BY, LIMIT, OPTIONAL MATCH 등 읽기 전용 절만 쓴다.
- CREATE, MERGE, DELETE, SET, REMOVE, DROP 같은 쓰기/관리 절은 절대 쓰지 않는다.
- 결과를 그래프로 시각화할 것이므로, 개수/집계를 묻는 질문이 아니라면 관련된 노드와
  관계 자체를 RETURN한다 (예: RETURN n, r, m). 단순 개수/통계 질문이면 count(...)
  같은 스칼라 값만 반환해도 된다.
- 이름으로 노드를 찾을 때는 n.name = "..." 대신 CONTAINS나 정확한 값 비교를 상황에
  맞게 쓰고, 대소문자/공백 차이를 고려해 필요하면 toLower()를 쓴다.
- 반드시 LIMIT을 붙인다(없으면 50).
- Cypher 코드만 출력한다. 설명, 마크다운 코드블록을 붙이지 않는다.

스키마:
{schema}

예시:
질문: 나루토와 동료 관계인 캐릭터는 누구야?
Cypher:
MATCH (c:Character)
WHERE toLower(c.name) CONTAINS toLower("나루토") OR any(a IN coalesce(c.aliases, []) WHERE toLower(a) CONTAINS toLower("나루토"))
MATCH (c)-[r:ALLY_OF]->(other:Character)
RETURN c, r, other
LIMIT 50

질문: 몇 화까지 처리됐어?
Cypher:
MATCH (e:Episode)
RETURN count(e) AS episode_count
LIMIT 50
"""

_RETRY_USER_TEMPLATE = """\
질문: {question}

이전에 아래 Cypher를 생성했지만 실행에 실패했다.

이전 Cypher:
{previous_cypher}

오류:
{previous_error}

오류를 고쳐서 Cypher 쿼리 하나만 다시 출력하라.
"""


def _clean_cypher(raw: str) -> str:
    text = _CODE_FENCE.sub("", raw).strip()
    return text.rstrip(";").strip()


def generate_cypher(
    llm: LLMProvider,
    question: str,
    schema_description: str,
    *,
    previous_cypher: str | None = None,
    previous_error: str | None = None,
) -> str:
    system = _SYSTEM_TEMPLATE.format(schema=schema_description)
    if previous_cypher and previous_error:
        user = _RETRY_USER_TEMPLATE.format(
            question=question, previous_cypher=previous_cypher, previous_error=previous_error
        )
    else:
        user = f"질문: {question}"

    raw = llm.complete(system=system, user=user, temperature=0.0)
    return _clean_cypher(raw)
