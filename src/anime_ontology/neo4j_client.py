"""Neo4j 연결 설정 및 드라이버 생성. export/query 등 여러 모듈이 공유한다."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from neo4j import Driver, GraphDatabase

from anime_ontology.config import env, require_env


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


@contextmanager
def open_driver(settings: Neo4jSettings | None = None):
    settings = settings or Neo4jSettings.from_env()
    driver: Driver = GraphDatabase.driver(settings.uri, auth=(settings.user, settings.password))
    try:
        yield driver
    finally:
        driver.close()
