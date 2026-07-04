"""추출 결과(ExtractionResult)를 RDF 트리플로 변환해 시리즈 그래프에 병합한다.

이름(및 별칭) 기준으로 기존 엔티티를 찾아 재사용하므로, 같은 화를 다시 처리하거나
여러 화에 걸쳐 같은 인물이 등장해도 URI가 중복 생성되지 않는다.
"""

from __future__ import annotations

import re
import sys

from rdflib import RDF, RDFS, Graph, Literal, URIRef

from anime_ontology.extraction.schema import ExtractionResult
from anime_ontology.ontology.namespaces import CORE, series_namespace

_UNSAFE_IRI_CHARS = re.compile(r'[\s<>"{}|\^`]')

# 매칭(동일 엔티티 판단)에서만 무시할 존칭/호칭 접미사. 표시용 이름(rdfs:label)은
# 원래 텍스트 그대로 두고, 이름이 같은 엔티티인지 비교할 때만 이 접미사를 뗀다.
# 예: "카카시 선생님"과 "카카시"(하타케 카카시의 별칭)가 같은 사람으로 매칭되게 함.
_HONORIFIC_SUFFIXES = ("선생님", "님", "쨩", "군", "양", "씨")

_CLASS_LOCAL_NAME = {
    CORE.Character: "Character",
    CORE.Location: "Location",
    CORE.Organization: "Organization",
    CORE.Clan: "Clan",
    CORE.Ability: "Ability",
    CORE.Skill: "Skill",
    CORE.InnateAbility: "InnateAbility",
    CORE.Item: "Item",
    CORE.Artifact: "Artifact",
    CORE.Event: "Event",
    CORE.Episode: "Episode",
}

_RELATION_PROPERTY = {
    "ally_of": CORE.allyOf,
    "enemy_of": CORE.enemyOf,
    "rival_of": CORE.rivalOf,
    "family_member_of": CORE.familyMemberOf,
    "mentor_of": CORE.mentorOf,
    "student_of": CORE.studentOf,
    "affiliated_with": CORE.affiliatedWith,
    "current_location": CORE.currentLocation,
    "located_in": CORE.locatedIn,
}

# predicate -> (subject 클래스, object 클래스)
_RELATION_ENDPOINT_CLASSES = {
    "ally_of": (CORE.Character, CORE.Character),
    "enemy_of": (CORE.Character, CORE.Character),
    "rival_of": (CORE.Character, CORE.Character),
    "family_member_of": (CORE.Character, CORE.Character),
    "mentor_of": (CORE.Character, CORE.Character),
    "student_of": (CORE.Character, CORE.Character),
    "affiliated_with": (CORE.Character, CORE.Organization),
    "current_location": (CORE.Character, CORE.Location),
    "located_in": (CORE.Location, CORE.Location),
}


def _slugify(name: str) -> str:
    slug = _UNSAFE_IRI_CHARS.sub("_", name.strip())
    return slug or "unknown"


def _match_key(name: str) -> str:
    """동일 엔티티 판단에 쓰는 정규화된 이름. 존칭 접미사를 떼고 대소문자를 무시한다."""
    normalized = name.strip()
    for suffix in _HONORIFIC_SUFFIXES:
        if normalized.endswith(suffix) and len(normalized) > len(suffix):
            normalized = normalized[: -len(suffix)]
            break
    return normalized.casefold()


class OntologyBuilder:
    """추출 결과를 하나의 시리즈 RDF 그래프에 병합하는 빌더."""

    def __init__(self, graph: Graph, series: str) -> None:
        self._graph = graph
        self._ns = series_namespace(series)
        self._name_index: dict[tuple[URIRef, str], URIRef] = {}
        self._build_name_index()

    def _build_name_index(self) -> None:
        for class_uri in _CLASS_LOCAL_NAME:
            for subject in self._graph.subjects(RDF.type, class_uri):
                for label in self._graph.objects(subject, RDFS.label):
                    self._name_index[(class_uri, _match_key(str(label)))] = subject
                for alias in self._graph.objects(subject, CORE.aliasName):
                    self._name_index[(class_uri, _match_key(str(alias)))] = subject

    def _episode_uri(self, episode_no: int) -> URIRef:
        return self._ns[f"Episode_{episode_no}"]

    def ensure_episode(self, episode_no: int) -> URIRef:
        uri = self._episode_uri(episode_no)
        if (uri, RDF.type, CORE.Episode) not in self._graph:
            self._graph.add((uri, RDF.type, CORE.Episode))
            self._graph.add((uri, CORE.episodeNumber, Literal(episode_no)))
            self._graph.add((uri, RDFS.label, Literal(f"{episode_no}화", lang="ko")))
        return uri

    def _resolve_or_create(
        self,
        class_uri: URIRef,
        name: str,
        *,
        aliases: list[str] | None = None,
        description: str = "",
    ) -> URIRef:
        name = name.strip()
        key = (class_uri, _match_key(name))
        uri = self._name_index.get(key)

        if uri is None:
            for alias in aliases or []:
                uri = self._name_index.get((class_uri, _match_key(alias)))
                if uri is not None:
                    break

        if uri is None:
            # 다른 클래스로 이미 같은 이름의 엔티티가 있으면, 잘못된 타입의 중복
            # 엔티티를 새로 만들지 않고 기존 엔티티를 재사용한다. 대부분의 경우
            # LLM이 관계의 predicate/대상 타입을 잘못 짝지어 생긴 것이라, 새로 만들면
            # (예: 캐릭터 "나루토"가 Location으로도 생성되는) 오염된 데이터가 된다.
            conflict_key = next(
                (k for k in self._name_index if k[1] == _match_key(name) and k[0] != class_uri), None
            )
            if conflict_key is not None:
                print(
                    f"경고: '{name}'이(가) 이미 {_CLASS_LOCAL_NAME[conflict_key[0]]} 타입으로 존재하는데 "
                    f"{_CLASS_LOCAL_NAME[class_uri]} 타입으로도 참조되었습니다. 기존 엔티티를 재사용합니다 "
                    "(LLM이 관계의 predicate/대상을 잘못 짝지었을 가능성이 있음).",
                    file=sys.stderr,
                )
                uri = self._name_index[conflict_key]

        if uri is None:
            local_name = _CLASS_LOCAL_NAME[class_uri]
            uri = self._ns[f"{local_name}_{_slugify(name)}"]
            self._graph.add((uri, RDF.type, class_uri))
            self._graph.add((uri, RDFS.label, Literal(name, lang="ko")))
            if description:
                self._graph.add((uri, RDFS.comment, Literal(description, lang="ko")))

        self._name_index[key] = uri
        for alias in aliases or []:
            alias_key = (class_uri, _match_key(alias))
            if alias_key not in self._name_index:
                self._graph.add((uri, CORE.aliasName, Literal(alias.strip(), lang="ko")))
            self._name_index[alias_key] = uri
        return uri

    def _link_mentioned(self, entity_uri: URIRef, episode_uri: URIRef) -> None:
        self._graph.add((entity_uri, CORE.mentionedIn, episode_uri))

    def merge_extraction(self, episode_no: int, result: ExtractionResult) -> None:
        """한 화의 추출 결과를 그래프에 반영한다."""

        episode_uri = self.ensure_episode(episode_no)

        for character in result.characters:
            uri = self._resolve_or_create(
                CORE.Character,
                character.name,
                aliases=character.aliases,
                description=character.description,
            )
            self._link_mentioned(uri, episode_uri)

        for location in result.locations:
            uri = self._resolve_or_create(CORE.Location, location.name, description=location.description)
            self._link_mentioned(uri, episode_uri)

        for organization in result.organizations:
            class_uri = CORE.Clan if organization.is_clan else CORE.Organization
            uri = self._resolve_or_create(class_uri, organization.name, description=organization.description)
            self._link_mentioned(uri, episode_uri)

        for ability in result.abilities:
            class_uri = CORE.InnateAbility if ability.kind == "innate" else CORE.Skill
            ability_uri = self._resolve_or_create(class_uri, ability.name, description=ability.description)
            self._link_mentioned(ability_uri, episode_uri)
            for user_name in ability.used_by:
                character_uri = self._resolve_or_create(CORE.Character, user_name)
                self._graph.add((character_uri, CORE.hasAbility, ability_uri))

        for item in result.items:
            class_uri = CORE.Artifact if item.is_artifact else CORE.Item
            uri = self._resolve_or_create(class_uri, item.name, description=item.description)
            self._link_mentioned(uri, episode_uri)

        for index, event in enumerate(result.events):
            # 화 번호 + 화 내 순서로 URI를 정하면, 같은 추출 결과를 다시 병합해도
            # (캐시 재사용 등) 새 이벤트가 계속 늘어나지 않고 같은 URI로 수렴한다.
            event_uri = self._ns[f"Event_{episode_no}_{index}"]
            self._graph.add((event_uri, RDF.type, CORE.Event))
            self._graph.add((event_uri, RDFS.label, Literal(event.description, lang="ko")))
            self._link_mentioned(event_uri, episode_uri)
            for participant_name in event.participants:
                character_uri = self._resolve_or_create(CORE.Character, participant_name)
                self._graph.add((character_uri, CORE.participatesIn, event_uri))
            if event.location:
                location_uri = self._resolve_or_create(CORE.Location, event.location)
                self._graph.add((event_uri, CORE.occursAt, location_uri))

        for relation in result.relations:
            subject_class, object_class = _RELATION_ENDPOINT_CLASSES[relation.predicate]
            subject_uri = self._resolve_or_create(subject_class, relation.subject)
            object_uri = self._resolve_or_create(object_class, relation.object)
            self._graph.add((subject_uri, _RELATION_PROPERTY[relation.predicate], object_uri))
