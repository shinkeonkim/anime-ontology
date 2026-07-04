# anime-ontology

애니메이션·영화 등 영상 시리즈의 자막 데이터를 분석하여, 시리즈별로 온톨로지 기반 지식그래프를 점진적으로 확장해나가는 프로젝트입니다.

<img width="1158" height="1048" alt="image" src="https://github.com/user-attachments/assets/034ae0c6-a202-47b2-9c34-90e77fc762d8" />


## 개요

1. 각 시리즈는 저장소 루트에 하나의 디렉토리로 존재합니다 (예: `naruto/`). 그 안에 영상(mp4 등)과 자막(smi 등) 파일이 화별로 쌍을 이루어 들어갑니다.
2. 자막이 있는 에피소드는 자막을 1차 소스로 사용하고, 자막이 없으면 영상에서 음성 인식(STT)으로, 필요하면 화면 텍스트 OCR까지 더해 대사를 확보한 뒤 캐릭터, 장소, 조직, 기술/스킬, 사건 등을 추출합니다.
3. 추출은 특정 LLM 벤더에 종속되지 않도록 Provider 추상화(Proxy 패턴)를 통해 이루어지며, `.env` 설정만으로 OpenAI / Ollama(로컬) / Anthropic 중 어떤 LLM을 쓸지 바꿀 수 있습니다.
4. 추출 결과는 RDF/OWL 온톨로지(시리즈 공통 코어 스키마 + 시리즈별 확장)로 축적되며, 필요 시 Neo4j로 내보내 시각화·탐색할 수 있습니다.
5. 모든 파이프라인 단계는 재실행해도 안전(idempotent)하도록 설계합니다.

자세한 설계는 [`docs/architecture.md`](docs/architecture.md)를 참고하세요.

## 디렉토리 구조

```
naruto/1~100/            # 원본 데이터 (영상+자막, 시리즈별 예시, git 미포함)
src/anime_ontology/      # 파이프라인 코드
  discovery.py           # 시리즈 디렉토리에서 영상/자막 페어링
  subtitles/             # 자막 파서 (SAMI 등)
  llm/                   # LLM Provider 추상화 (Proxy)
  extraction/            # 자막 -> 개체/관계 추출
  ontology/              # RDF/OWL 온톨로지 스키마 및 빌더
  export/                # Neo4j 내보내기
  query/                 # 자연어 질문 -> Cypher 생성/실행/답변 합성
  webapp/                # 자연어 질의 웹 뷰 (FastAPI + 정적 프론트엔드)
  transcription/         # 자막 없는 영상용 STT Provider 추상화 (Proxy)
  vision/                # 기본 장면 분석 (장면 전환 감지 + 화면 텍스트 OCR)
  neo4j_client.py        # Neo4j 연결 설정 (export/query 공유)
  pipeline.py            # 에피소드 단위 오케스트레이션
scripts/                 # CLI 실행 스크립트
data/<series>/ontology/  # 시리즈별로 누적되는 온톨로지(.ttl) 결과물
data/<series>/extraction_cache/  # LLM 추출 원본 캐시 (재실행 방지용, git 미포함)
data/<series>/transcript_cache/  # STT 결과 캐시 (재실행 방지용, git 미포함)
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

## 자막이 없는 영상 처리하기 (선택)

시리즈 디렉토리에 영상만 있고 자막 파일이 없으면, `run_episode`/`run_episodes`가
자동으로 음성 인식(STT)으로 대체합니다. 별도 명령이 필요 없고, 자막이 있는 화와
같은 명령(`python scripts/run_episode.py <series> --episode N`)을 쓰면 됩니다.

```bash
uv pip install -e ".[stt]"       # faster-whisper 설치 (로컬 실행, API 키 불필요)
# 시스템에 ffmpeg가 설치되어 있어야 합니다.
```

`.env`의 `TRANSCRIPTION_PROVIDER`로 `local_whisper`(기본값) / `openai`를 선택할 수
있습니다(LLM Provider와 동일한 Proxy 패턴). 추가로 화면에 찍힌 텍스트(기술명 자막
등)까지 읽고 싶다면:

```bash
uv pip install -e ".[vision]"    # pytesseract 설치
# 시스템에 tesseract(+한국어 언어팩)가 설치되어 있어야 합니다.
```

그리고 `.env`에서 `SCENE_ANALYSIS_ENABLED=true`로 설정하면, ffmpeg의 장면 전환
감지 + OCR로 얻은 화면 텍스트가 대사 큐 사이에 섞여 추출에 함께 쓰입니다. 장면
분석은 보조 정보라 실패해도 음성 인식 결과만으로 계속 진행합니다.

STT/OCR 결과 모두 화 단위로 캐시되어 재실행 시 다시 계산하지 않으며, 실제 인식
품질은 음질/폰트 등 원본 상태에 따라 달라질 수 있습니다(자막이 있는 경우보다
정확도가 낮을 수 있음).

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

## 자연어로 질문하기 (웹 뷰)

Neo4j로 내보낸 뒤, 자연어 질문 -> Cypher 자동 생성 -> 실행 -> 답변 + 그래프
시각화까지 보여주는 웹 서버를 띄울 수 있습니다.

```bash
python scripts/run_web.py            # http://127.0.0.1:8000
python scripts/run_web.py --port 8080
```

- 질문을 입력하면 LLM(Provider Proxy)이 온톨로지 스키마를 참고해 읽기 전용 Cypher를
  생성하고, Neo4j에서 실행한 결과로 자연어 답변을 만듭니다.
- 생성된 Cypher는 화면에서 펼쳐볼 수 있어 "어떻게 탐색했는지" 그대로 확인할 수
  있습니다.
- 결과에 포함된 노드/관계는 페이지 내 그래프 뷰에 그대로 그려집니다(드래그로 위치
  조정 가능). 외부 JS 라이브러리 없이 자체 구현되어 있어 인터넷 연결이 없어도
  동작합니다.
- 안전장치: 생성된 Cypher에 `CREATE/MERGE/DELETE/SET` 등 쓰기 절이 있으면 실행 전에
  차단하고, 실행 자체도 Neo4j의 읽기 전용 트랜잭션으로만 수행해 이중으로 방어합니다.
  실행이 실패하면 오류를 LLM에 피드백해 한 번 더 쿼리를 고쳐 재시도합니다.
