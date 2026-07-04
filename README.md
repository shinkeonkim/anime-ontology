# anime-ontology

애니메이션·영화 등 영상 시리즈의 자막 데이터를 분석하여, 시리즈별로 온톨로지 기반 지식그래프를 점진적으로 확장해나가는 프로젝트입니다.

## 개요

1. 각 시리즈는 저장소 루트에 하나의 디렉토리로 존재합니다 (예: `naruto/`). 그 안에 영상(mp4 등)과 자막(smi 등) 파일이 화별로 쌍을 이루어 들어갑니다.
2. 자막이 있는 에피소드는 자막을 1차 소스로 사용해 캐릭터, 장소, 조직, 기술/스킬, 사건 등을 추출합니다.
3. 추출은 특정 LLM 벤더에 종속되지 않도록 Provider 추상화(Proxy 패턴)를 통해 이루어지며, `.env` 설정만으로 OpenAI / Ollama(로컬) / Anthropic 중 어떤 LLM을 쓸지 바꿀 수 있습니다.
4. 추출 결과는 RDF/OWL 온톨로지(시리즈 공통 코어 스키마 + 시리즈별 확장)로 축적되며, 필요 시 Neo4j로 내보내 시각화·탐색할 수 있습니다.
5. 모든 파이프라인 단계는 재실행해도 안전(idempotent)하도록 설계합니다.

자세한 설계는 [`docs/architecture.md`](docs/architecture.md)를 참고하세요.

## 디렉토리 구조

```
naruto/1~100/            # 원본 데이터 (영상+자막, 시리즈별 예시)
src/anime_ontology/      # 파이프라인 코드
  discovery.py           # 시리즈 디렉토리에서 영상/자막 페어링
  subtitles/             # 자막 파서 (SAMI 등)
  llm/                   # LLM Provider 추상화 (Proxy)
  extraction/            # 자막 -> 개체/관계 추출
  ontology/              # RDF/OWL 온톨로지 스키마 및 빌더
  export/                # Neo4j 내보내기
  pipeline.py            # 에피소드 단위 오케스트레이션
scripts/                 # CLI 실행 스크립트
data/<series>/ontology/  # 시리즈별로 누적되는 온톨로지(.ttl) 결과물
data/<series>/extraction_cache/  # LLM 추출 원본 캐시 (재실행 방지용, git 미포함)
docs/                    # 설계 문서
```

## 시작하기

```bash
uv venv
uv pip install -e .
cp .env.example .env   # LLM_PROVIDER 등 값 채우기
```

로컬 LLM(Ollama)을 기본값으로 사용하도록 되어 있어 API 키 없이도 바로 실행할 수 있습니다.

## 실행

```bash
# 한 화만 처리
python scripts/run_episode.py naruto --episode 1

# 여러 화를 범위로 처리 (캐시된 화는 LLM을 다시 호출하지 않음)
python scripts/run_episode.py naruto --episodes 1-5

# 캐시를 무시하고 강제로 다시 추출
python scripts/run_episode.py naruto --episodes 1-5 --force
```

결과는 `data/naruto/ontology/naruto.ttl`에 누적됩니다.

## Neo4j로 시각화하기 (선택)

이 프로젝트 전용 Neo4j를 Docker로 띄웁니다 (호스트에 다른 Neo4j가 떠 있어도 포트가
겹치지 않도록 7688/7475로 매핑되어 있습니다).

```bash
# .env에 NEO4J_PASSWORD를 8자 이상으로 설정한 뒤
docker compose up -d

python scripts/export_neo4j.py naruto
```

브라우저에서 http://localhost:7475 로 접속해 Cypher로 탐색할 수 있습니다 (예:
`MATCH (n:Character)-[r]->(m) RETURN n, r, m LIMIT 100`).
