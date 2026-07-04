"""LLM이 생성한 Cypher를 실행하기 전에 거치는 안전장치.

LLM 생성 쿼리를 그대로 실행하는 건 위험하므로(쓰기/삭제 절 포함 가능, 무제한 결과 등)
실행 전에 최소한의 정적 검사를 한다. 이후 실행 단계(executor.py)에서도 읽기 전용
트랜잭션으로 실행해 서버 쪽에서도 한 번 더 강제한다(2중 방어).
"""

from __future__ import annotations

import re

_WRITE_KEYWORDS = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|CALL\s*\{)\b", re.IGNORECASE
)
_LIMIT_PATTERN = re.compile(r"\bLIMIT\s+\d+\b", re.IGNORECASE)


class QuerySafetyError(RuntimeError):
    """생성된 Cypher가 안전 검사를 통과하지 못했을 때 발생한다."""


def ensure_read_only(cypher: str) -> None:
    match = _WRITE_KEYWORDS.search(cypher)
    if match:
        raise QuerySafetyError(
            f"읽기 전용이 아닌 절('{match.group(0)}')이 포함되어 실행할 수 없습니다: {cypher}"
        )


def ensure_limit(cypher: str, default_limit: int = 50) -> str:
    if _LIMIT_PATTERN.search(cypher):
        return cypher
    return f"{cypher}\nLIMIT {default_limit}"
