"""Validated inputs for RF life-module skill transfers.

These models are independent of CharacterState while the v2 engine is being
integrated. A transfer records a choice, never the amount of available credit.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator


class LifeModuleSkillPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["rf66-76-v1"] = "rf66-76-v1"
    active_cap: Annotated[StrictInt, Field(ge=1, le=1000)] = 7
    knowledge_cap: Annotated[StrictInt, Field(ge=1, le=1000)] = 9


class LifeModuleTransfer(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    entry_id: str
    source_kind: Literal["active", "knowledge"] = "active"
    source_skill_id: Annotated[str, Field(min_length=1, max_length=200)]
    grant_fingerprint: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    destination_skill_id: Annotated[str, Field(min_length=1, max_length=200)]
    destination_specific: Annotated[str, Field(max_length=200)] = ""
    destination_category: Literal["Academic", "Professional", "Street", "Interest", "Language"] | None = None
    ranks: Annotated[StrictInt, Field(ge=1, le=1000)]

    @field_validator("id", "entry_id")
    @classmethod
    def _uuid(cls, value: str) -> str:
        return str(UUID(value))

    @field_validator("destination_specific")
    @classmethod
    def _specific(cls, value: str) -> str:
        return value.strip()


class LifeModuleSkillSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal[2] = 2
    input_signature: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    policy: LifeModuleSkillPolicy
    public: dict[str, Any]
    free_active: dict[str, Annotated[StrictInt, Field(ge=0, le=1000)]]
    free_knowledge: dict[str, Annotated[StrictInt, Field(ge=0, le=1000)]]
    knowledge_categories: dict[str, str]
    native_languages: list[str]
    creation_active: dict[str, Annotated[StrictInt, Field(ge=0, le=1000)]]
    creation_knowledge: dict[str, Annotated[StrictInt, Field(ge=0, le=1000)]]
    skill_karma: Annotated[StrictInt, Field(ge=0)]
    knowledge_karma: Annotated[StrictInt, Field(ge=0)]

    @model_validator(mode="after")
    def _consistent(self) -> LifeModuleSkillSnapshot:
        public = self.public
        if (
            public.get("complete") is not True
            or public.get("policy") != self.policy.model_dump()
            or public.get("free_active") != self.free_active
            or public.get("free_knowledge") != self.free_knowledge
            or not isinstance(public.get("purchase_preview"), dict)
            or public["purchase_preview"].get("totals") != self.creation_active
            or any(not isinstance(public.get(key), list) for key in ("pools", "losses"))
            or any(n > self.policy.active_cap for n in self.free_active.values())
            or any(n > self.policy.knowledge_cap for n in self.free_knowledge.values())
            or any(n > self.creation_active.get(key, 0) for key, n in self.free_active.items())
            or any(n > self.creation_knowledge.get(key, 0) for key, n in self.free_knowledge.items())
        ):
            raise ValueError("inconsistent life-module skill snapshot")
        return self


class LifeModuleGrowthPrice(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    per_rating: Annotated[StrictInt, Field(ge=0, le=1000)]
    first_level: Annotated[StrictInt, Field(ge=0, le=1000)] | None = None
    multiplier: Annotated[StrictInt, Field(ge=0, le=1000)] = 100
    category: str = ""
    flat_rules: list[dict[str, Any]] = Field(default_factory=list)


class LifeModuleSkillAdvancement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    kind: Literal["active", "exotic", "group", "knowledge"]
    target_id: Annotated[str, Field(min_length=1, max_length=200)]
    specific: Annotated[str, Field(max_length=200)] = ""
    category: Literal["Academic", "Professional", "Street", "Interest", "Language"] = "Professional"
    levels: Annotated[StrictInt, Field(ge=1, le=1000)]
    from_ratings: dict[str, Annotated[StrictInt, Field(ge=0, le=1000)]] = Field(default_factory=dict)
    price: LifeModuleGrowthPrice | None = None

    @field_validator("id")
    @classmethod
    def _uuid(cls, value: str) -> str:
        return str(UUID(value))

    @field_validator("specific")
    @classmethod
    def _specific(cls, value: str) -> str:
        return value.strip()


def life_skill_policy(*, active_cap: int | None = None, knowledge_cap: int | None = None) -> LifeModuleSkillPolicy:
    """Unspecified caps use RF's defaults; an explicit setting is preserved."""
    return LifeModuleSkillPolicy(
        active_cap=7 if active_cap is None else active_cap,
        knowledge_cap=9 if knowledge_cap is None else knowledge_cap,
    )


def life_module_entry_ids(character_id: str, modules: list[str], existing: list[str] | None = None) -> list[str]:
    """Assign deterministic IDs only for migration; never repair malformed IDs.

    A new acquisition must use a new UUID, supplied by the caller. Sharing an
    existing character must preserve these IDs when the character ID changes.
    """
    if len(modules) > 512:
        raise ValueError("too many life-module entries")
    if existing is None:
        return [
            str(uuid5(NAMESPACE_URL, f"chummer-web:life-entry:{character_id}:{i}:{mid}"))
            for i, mid in enumerate(modules)
        ]
    if len(existing) != len(modules):
        raise ValueError("life-module entry IDs do not match the module list")
    ids = [str(UUID(value)) for value in existing]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate life-module entry ID")
    return ids
