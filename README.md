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
python scripts/run_episode.py --series naruto --episode 1
```

(추출/온톨로지 빌더 구현이 진행되며 사용법이 채워집니다.)
