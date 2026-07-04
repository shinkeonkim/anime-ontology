"""자연어 질의 웹 뷰를 제공하는 FastAPI 앱."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from anime_ontology.query import NLQueryEngine, QueryAnswer

_STATIC_DIR = Path(__file__).parent / "static"


class QueryRequest(BaseModel):
    question: str


def _to_response(result: QueryAnswer) -> dict:
    return {
        "question": result.question,
        "cypher": result.cypher,
        "columns": result.columns,
        "rows": result.rows,
        "nodes": result.nodes,
        "edges": result.edges,
        "answer": result.answer,
        "error": result.error,
    }


def create_app() -> FastAPI:
    app = FastAPI(title="anime-ontology 지식그래프 질의")
    engine = NLQueryEngine()

    @app.post("/api/query")
    def query(request: QueryRequest) -> dict:
        return _to_response(engine.ask(request.question))

    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
    return app
