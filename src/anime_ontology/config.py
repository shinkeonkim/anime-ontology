"""프로젝트 전역에서 쓰는 .env 로딩 헬퍼. LLM/Neo4j 등 특정 기능에 종속되지 않는다."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"환경변수 '{name}'가 설정되지 않았습니다. .env를 확인하세요.")
    return value


def env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
