"""Validated inputs for RF life-module skill transfers.

These models are independent of CharacterState while the v2 engine is being
integrated. A transfer records a choice, never the amount of available credit.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class LifeModuleSkillPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["rf66-76-v1"] = "rf66-76-v1"
    active_cap: Annotated[StrictInt, Field(ge=1, le=1000)] = 7
    knowledge_cap: Annotated[StrictInt, Field(ge=1, le=1000)] = 9


class LifeModuleTransfer(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    entry_id: str
    source_skill_id: Annotated[str, Field(min_length=1, max_length=200)]
    grant_fingerprint: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    destination_skill_id: Annotated[str, Field(min_length=1, max_length=200)]
    destination_specific: Annotated[str, Field(max_length=200)] = ""
    ranks: Annotated[StrictInt, Field(ge=1, le=1000)]

    @field_validator("id", "entry_id")
    @classmethod
    def _uuid(cls, value: str) -> str:
        return str(UUID(value))

    @field_validator("destination_specific")
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
