# 아키텍처 설계

## 핵심 설계 결정

### 1. 온톨로지 저장 방식: 하이브리드 (RDF/OWL 기본 + Neo4j 내보내기)

- 정본(source of truth)은 RDF(Turtle, `.ttl`)로 git에 텍스트 파일 형태로 저장합니다. 클래스 계층, 속성 정의(OWL)를 통해 "온톨로지"의 의미를 갖추고, 버전 관리(diff, 커밋 단위 확장)가 쉽습니다.
- 시각화나 탐색적 질의가 필요할 때는 별도 스크립트로 Neo4j에 내보냅니다(`src/anime_ontology/export`). Neo4j는 파생 산출물이며, 언제든 RDF로부터 재생성 가능합니다(idempotent). Neo4j는 이 프로젝트 전용 `docker-compose.yml`로 띄우며(호스트의 다른 Neo4j와 겹치지 않도록 7688/7475 포트 사용), 내보내기는 URI를 유일 키로 삼아 `MERGE`만 사용하므로 몇 번을 다시 실행해도 노드/관계가 중복되지 않습니다. 온톨로지 스키마 정의(owl:Class 등)는 내보내지 않고 `ontology.strip_core_schema`로 걸러낸 인스턴스 데이터만 내보냅니다.

### 2. 개체/관계 추출: LLM Provider 추상화 (Proxy 패턴)

특정 벤더(Claude API 등)에 고정하지 않기 위해 다음과 같은 구조를 둡니다.

```
LLMProvider (ABC)          # generate(prompt, ...) -> 텍스트/JSON
 ├─ OpenAIProvider
 ├─ OllamaProvider          # 로컬 실행, API 키 불필요
 └─ AnthropicProvider

LLMProviderProxy            # LLMProvider를 구현하지만 내부적으로
                             # .env 설정에 따라 실제 provider를 선택하고,
                             # 실패 시 LLM_FALLBACK_PROVIDERS 순서로 재시도한다.
```

추출 로직(`extraction/extractor.py`)은 `LLMProviderProxy`(즉 `LLMProvider` 인터페이스)만 알고 있으며, 어떤 벤더가 실제로 호출되는지는 신경 쓰지 않습니다. `.env`의 `LLM_PROVIDER` 값만 바꾸면 벤더를 교체할 수 있습니다.

### 3. 원본 데이터 탐색: 시리즈 독립적 구조

`naruto/1~100/[제블] 나루토 001.mp4` 같은 명명 규칙은 시리즈마다 다를 수 있으므로, `discovery.py`는 다음 원칙으로 동작합니다.

1. 시리즈 디렉토리 하위에서 영상 확장자(mp4/mkv/avi)와 자막 확장자(smi/srt/ass/vtt)를 재귀적으로 탐색한다.
2. 파일명에서 확장자를 제외한 stem이 같은 영상/자막을 한 쌍으로 묶는다.
3. stem 끝의 숫자(예: `... 001`)를 에피소드 번호로 우선 사용하고, 숫자가 없으면 자연 정렬(natural sort) 순서를 번호로 사용한다.

이 덕분에 새로운 시리즈를 추가할 때 코드 수정 없이 디렉토리만 놓으면 동작합니다.

### 4. 자막 우선, 없으면 STT(+선택적 장면 분석)로 대체

`pipeline._collect_cues`가 화별로 다음 순서로 자막 텍스트를 확보합니다.

1. 자막 파일이 있으면 그것을 우선 사용한다(`subtitles.parse_subtitle`).
2. 없고 영상만 있으면 ffmpeg로 오디오를 뽑아 STT(`transcription` 패키지)로 대사를
   텍스트화한다. STT도 LLM과 동일하게 Provider 추상화(Proxy 패턴)를 적용해
   `TRANSCRIPTION_PROVIDER`(기본값 `local_whisper`, API 키 불필요) 설정만으로
   `openai`(Whisper API) 등으로 바꿀 수 있다.
3. `SCENE_ANALYSIS_ENABLED=true`면 `vision` 패키지로 기본적인 장면 분석을 추가한다.
   OpenCV 없이 ffmpeg의 scene 필터로 장면 전환 시점을 찾고, 그 시점의 프레임을
   캡처해 pytesseract(한국어)로 화면에 찍힌 텍스트(기술명 자막 등)를 읽어 대사
   큐 사이에 `(화면 텍스트) ...` 형태로 끼워 넣는다. 장면 분석은 보조 정보라
   실패해도 STT 결과만으로 계속 진행한다(하드 실패시키지 않음).

STT/OCR 결과 모두 자막과 동일한 `SubtitleCue` 형태로 변환되므로, 추출 모듈
(`extraction/extractor.py`)은 대사가 자막에서 왔는지 STT/OCR에서 왔는지 신경 쓰지
않는다. STT 결과도 화 단위로 캐시(`data/<series>/transcript_cache/`)해 재실행 시
오디오 추출/음성 인식을 다시 하지 않는다.

무거운 의존성(faster-whisper, pytesseract/Pillow)은 기본 설치에 포함하지 않고
`pip install -e ".[stt,vision]"`로 선택 설치한다. 실제 음성 인식/OCR 품질은 모델과
원본 음질/폰트에 크게 좌우되며(배경음악이 섞인 구간, 양식화된 폰트의 타이틀 카드
등에서는 결과가 부정확할 수 있음), 이는 파이프라인 통합 문제가 아니라 STT/OCR
기술 자체의 한계로 별도 사안이다.

### 5. 온톨로지 스키마: 코어 + 시리즈 확장

- `src/anime_ontology/ontology/schema/core.ttl`: 모든 시리즈에 공통되는 클래스(Character, Location, Organization, Skill, Item, Event 등)와 관계 속성을 정의하는 베이스 온톨로지.
- `data/<series>/ontology/<series>.ttl`: 코어 온톨로지를 `owl:imports`하며, 시리즈 고유 개념(나루토의 `Jutsu`, `Village` 등)을 코어 클래스의 하위 클래스로 선언하고, 실제 인스턴스 데이터(캐릭터, 사건 등)를 누적합니다.

이렇게 하면 나루토가 아닌 다른 시리즈(예: 원피스)를 추가해도 코어 스키마는 그대로 재사용하고, 시리즈 고유 개념만 확장하면 됩니다.

### 6. 자연어 질의: LLM이 Cypher로 번역 + 이중 안전장치

지식그래프를 만들어도 사람이 Cypher/SPARQL을 직접 짤 수 없으면 활용도가 떨어지므로,
자연어 질문을 그래프 질의로 바꿔주는 계층(`src/anime_ontology/query/`)을 둡니다.

```
질문(자연어)
  -> schema_context.build_schema_description()   # core.ttl에서 라벨/관계/속성 설명 생성
  -> cypher_generation.generate_cypher(llm, ...)  # LLM Provider Proxy로 Cypher 생성
  -> safety.ensure_read_only() / ensure_limit()   # 쓰기 절 차단, LIMIT 강제
  -> executor.execute_cypher()                    # RoutingControl.READ로 실행(서버도 쓰기 거부)
  -> answer.synthesize_answer(llm, ...)           # 결과를 근거로 자연어 답변 생성
```

실행이 실패하면(문법 오류 등) 오류 메시지를 다시 LLM에 보여주고 한 번 더 Cypher
생성을 시도합니다(`NLQueryEngine`, 기본 최대 2회). 쓰기 절 차단은 두 겹으로 방어합니다.

1. 정적 검사: 생성된 Cypher 문자열에 `CREATE/MERGE/DELETE/SET/REMOVE/DROP` 등이
   보이면 실행 전에 거부한다(`query/safety.py`).
2. 서버 강제: Neo4j 드라이버의 `RoutingControl.READ`로 실행해, 혹시 정적 검사를
   피해간 쓰기 절이 있어도 Neo4j 자신이 "읽기 전용 트랜잭션에서 쓰기 시도"로 거부한다.

Cypher 생성 스키마 설명은 `ontology/property_graph_mapping.py`(Neo4j 내보내기와 동일한
라벨/관계 변환 규칙)를 그대로 재사용하므로, 내보내기 규칙이 바뀌면 질의 쪽 스키마
설명도 자동으로 같이 바뀝니다. 같은 이유로 Neo4j 내보내기에는 OWL 서브클래스 폐쇄
(`build_superclass_closure`)를 반영해, `Skill`/`InnateAbility` 노드가 상위 개념인
`:Ability` 라벨도 함께 갖도록 해서 추상적인 질문("무슨 능력이 있어?")도 답할 수 있게
했습니다.

### 7. 웹 뷰: FastAPI + 자체 구현 그래프 렌더러

`src/anime_ontology/webapp/`이 위 질의 엔진을 감싸는 FastAPI 앱을 제공합니다
(`POST /api/query`). 프론트엔드(`webapp/static/`)는 답변, 생성된 Cypher(펼쳐보기),
결과 표와 함께 탐색된 서브그래프를 그립니다. 그래프 렌더링은 외부 CDN 라이브러리
없이 순수 JS로 간단한 force-directed 레이아웃(반발력 + 스프링 + 중심 인력을 고정
횟수 반복)을 구현해, 인터넷 연결이 없는 환경에서도 그대로 동작합니다.

## 파이프라인 흐름 (에피소드 1개 기준)

```
discovery.find_episode(series, ep_no)
  -> subtitles.parse(smi_path)          # SubtitleCue 리스트
  -> extraction.extract(cues, series)   # LLM Provider Proxy 호출, 캐시 저장
  -> ontology.builder.merge(series_graph, extraction_result)
  -> ontology.store.save(series_graph)  # data/<series>/ontology/<series>.ttl
  -> (선택) export.neo4j_export.push(series_graph)
```

전체는 `pipeline.run_episode(series, ep_no)`로 오케스트레이션되며, 이미 처리된 에피소드를 다시 실행해도 동일한 결과(중복 없는 병합)를 내도록 구현합니다.

## 파일럿 범위

전체 100화를 한 번에 처리하지 않고, 먼저 나루토 1~5화로 파이프라인 전체(자막 파싱 → 추출 → 온톨로지 병합 → Neo4j 내보내기)를 검증한 뒤 확장합니다.
