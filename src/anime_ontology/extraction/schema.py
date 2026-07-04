"""LLM 추출 결과의 구조를 정의하는 pydantic 스키마.

여기 정의된 필드는 온톨로지 빌더(ontology/builder.py)가 core.ttl의 클래스/속성에
매핑하는 대상이 되므로, 두 파일을 함께 볼 때 대응 관계가 드러나도록 이름을 맞춘다.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RelationPredicate = Literal[
    "ally_of",
    "enemy_of",
    "family_member_of",
    "mentor_of",
    "student_of",
    "affiliated_with",
    "current_location",
    "located_in",
]


class CharacterExtract(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    is_human: bool = True
    description: str = ""


class LocationExtract(BaseModel):
    name: str
    description: str = ""


class OrganizationExtract(BaseModel):
    name: str
    is_clan: bool = False
    description: str = ""


class AbilityExtract(BaseModel):
    name: str
    kind: Literal["skill", "innate"] = "skill"
    used_by: list[str] = Field(default_factory=list)
    description: str = ""


class ItemExtract(BaseModel):
    name: str
    is_artifact: bool = False
    description: str = ""


class EventExtract(BaseModel):
    description: str
    participants: list[str] = Field(default_factory=list)
    location: str | None = None


class RelationExtract(BaseModel):
    subject: str
    predicate: RelationPredicate
    object: str


class ExtractionResult(BaseModel):
    characters: list[CharacterExtract] = Field(default_factory=list)
    locations: list[LocationExtract] = Field(default_factory=list)
    organizations: list[OrganizationExtract] = Field(default_factory=list)
    abilities: list[AbilityExtract] = Field(default_factory=list)
    items: list[ItemExtract] = Field(default_factory=list)
    events: list[EventExtract] = Field(default_factory=list)
    relations: list[RelationExtract] = Field(default_factory=list)

    def merged_with(self, other: "ExtractionResult") -> "ExtractionResult":
        """다른 추출 결과와 리스트를 이어붙인다 (여러 청크의 결과를 합칠 때 사용)."""
        return ExtractionResult(
            characters=self.characters + other.characters,
            locations=self.locations + other.locations,
            organizations=self.organizations + other.organizations,
            abilities=self.abilities + other.abilities,
            items=self.items + other.items,
            events=self.events + other.events,
            relations=self.relations + other.relations,
        )
