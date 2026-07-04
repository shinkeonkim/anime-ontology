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

### 4. 자막 우선, 영상은 후순위

현재 파이프라인은 자막 텍스트만으로 추출을 수행합니다. 자막이 없는 에피소드(향후 영상 STT/OCR 등)는 범위 밖이며, 필요해지면 `subtitles` 패키지와 동일한 인터페이스로 별도 모듈을 추가할 수 있습니다.

### 5. 온톨로지 스키마: 코어 + 시리즈 확장

- `src/anime_ontology/ontology/schema/core.ttl`: 모든 시리즈에 공통되는 클래스(Character, Location, Organization, Skill, Item, Event 등)와 관계 속성을 정의하는 베이스 온톨로지.
- `data/<series>/ontology/<series>.ttl`: 코어 온톨로지를 `owl:imports`하며, 시리즈 고유 개념(나루토의 `Jutsu`, `Village` 등)을 코어 클래스의 하위 클래스로 선언하고, 실제 인스턴스 데이터(캐릭터, 사건 등)를 누적합니다.

이렇게 하면 나루토가 아닌 다른 시리즈(예: 원피스)를 추가해도 코어 스키마는 그대로 재사용하고, 시리즈 고유 개념만 확장하면 됩니다.

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
