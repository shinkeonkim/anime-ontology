#!/usr/bin/env python3
"""CLI: 자연어 질의 웹 뷰 서버를 띄운다.

사용 예:
    python scripts/run_web.py
    python scripts/run_web.py --host 0.0.0.0 --port 8080

.env에 LLM_PROVIDER, NEO4J_URI/USER/PASSWORD가 설정되어 있어야 한다.
"""

from __future__ import annotations

import argparse

import uvicorn

from anime_ontology.webapp.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="자연어 질의 웹 뷰 서버 실행")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
