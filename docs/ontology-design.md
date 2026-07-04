# 온톨로지 스키마 설계

`src/anime_ontology/ontology/schema/core.ttl`에 정의된 코어 온톨로지와, 그 설계가
애니메이션 특유의 요소(실제 세계에 대응하지 않는 캐릭터/세계관/기술 등)를 어떻게
수용하는지 정리한다.

## 클래스 계층

```
owl:Thing
 ├─ anime:Series                # 작품 전체 (예: 나루토)
 ├─ anime:Episode                # 화
 ├─ anime:Character              # 인간 여부와 무관한 "행위 주체"
 ├─ anime:Organization
 │   └─ anime:Clan               # 혈통/가문 기반 조직
 ├─ anime:Location
 ├─ anime:Ability
 │   ├─ anime:Skill              # 학습으로 습득하는 기술
 │   └─ anime:InnateAbility      # 태생적/혈통 능력
 ├─ anime:Item
 │   └─ anime:Artifact           # 서사적으로 특별한 물건
 └─ anime:Event
```

## 애니메이션 고유 요소를 어떻게 담았는가

- **비인간 캐릭터**: `anime:Character`는 "인간"으로 제한하지 않고 요괴·짐승·정령
  등도 포함하는 넓은 개념으로 정의했다. 나루토의 구미호(큐라마)처럼 처음엔 괴물/사건의
  대상으로만 언급되다가 이후 인격을 가진 캐릭터로 재해석되는 존재도, 시리즈 확장
  스키마에서 `naruto:TailedBeast rdfs:subClassOf anime:Character`로 표현하면 된다.
- **다중 상속으로 표현되는 개체**: "마을"은 지리적 장소이면서 동시에 정치적 조직이기도
  하다. 이런 이중적 성격은 OWL의 다중 상속으로 자연스럽게 표현할 수 있다.
  예: `naruto:HiddenLeafVillage rdfs:subClassOf anime:Location, anime:Organization .`
  하나의 클래스 계층으로는 표현이 어려운 세계관 요소를, 클래스 다중 상속으로
  해결하는 것이 코어 스키마를 굳이 "마을" 클래스로 하드코딩하지 않은 이유다.
- **기술/능력의 두 갈래**: 닌자토(나루토), 마법, 초능력 등 애니메이션의 "기술"은
  대체로 (1) 훈련으로 배우는 것과 (2) 태생적으로 주어지는 것으로 나뉜다. 이를
  `anime:Skill`과 `anime:InnateAbility`로 미리 나눠 두면, 나루토의 인술(닌자토)은
  `naruto:Jutsu rdfs:subClassOf anime:Skill`, 혈계한계(샤리간 등)는
  `naruto:KekkeiGenkai rdfs:subClassOf anime:InnateAbility`로 자연스럽게 붙는다.
  다른 시리즈(예: 마법 학교물의 태생 마력, 배틀물의 각성 능력)도 동일한 축으로
  분류할 수 있어 코어 스키마를 바꾸지 않고 재사용 가능하다.
- **시간에 따라 변하는 관계**: 적이었다가 동료가 되는 관계 변화(나루토와 사스케 등)는
  이번 스키마에서는 단순화해서, 추출될 때마다 관계 트리플(`allyOf`, `enemyOf` 등)을
  누적하는 방식으로 처리한다. 즉 한 시점의 "진실"을 덮어쓰지 않고 역사적으로
  누적되는 관계로 기록하며, 각 트리플이 어느 화에서 왔는지는 `mentionedIn`으로
  추적한다. 관계의 시점별 유효성 추론(예: "지금은 적이 아니다")은 이후 필요해지면
  n-ary 관계(관계를 별도 개체로 승격)로 확장할 수 있도록 여지를 남겨둔다.
- **출처 추적(provenance)**: 모든 개체/사건은 `anime:mentionedIn`으로 최초 또는 추가로
  등장한 화(`Episode`)를 가리킬 수 있다. 이는 "이 트리플이 왜 존재하는가"를 나중에
  검증하거나, 특정 화만 다시 추출해 반영할 때 근거로 쓴다.

## 코어 vs 시리즈 확장

- `core.ttl`은 어떤 시리즈에도 등장할 수 있는 뼈대만 정의한다. 시리즈 고유 개념(나루토의
  마을, 인술, 성격의 요괴 등)은 시리즈 네임스페이스(`https://anime-ontology.local/series/naruto#`)
  아래에 `rdfs:subClassOf`로 코어 클래스를 상속해 추가한다.
- 저장 시(`ontology/store.py`) 코어 스키마 트리플은 시리즈 파일에 다시 쓰지 않는다.
  `data/naruto/ontology/naruto.ttl`에는 나루토 고유 확장 클래스와 인스턴스 데이터만
  남고, 로드할 때 코어 스키마와 자동으로 합쳐진다. 다른 시리즈를 추가해도 코어
  스키마 파일은 그대로 재사용된다.

## 저장 형식

- 정본은 Turtle(`.ttl`) 텍스트 파일이며 git으로 버전 관리한다. 화 단위로 추가되는
  트리플이 diff에 그대로 드러나 어떤 화가 어떤 지식을 추가했는지 리뷰하기 쉽다.
- 시각화/탐색이 필요하면 `export/neo4j_export.py`(추후 구현)로 Neo4j에 내보낸다.
  Neo4j 쪽 데이터는 항상 `.ttl`로부터 재생성 가능한 파생 산출물로 취급한다.
