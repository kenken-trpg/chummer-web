from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class CyberwareInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ware_id: str
    rating: int = 1
    grade: str = "Standard"
    wireless: bool = True
    parent_id: str | None = None
    included: bool = False
    side: str | None = None


class Priorities(BaseModel):
    Heritage: str = "C"
    Attributes: str = "A"
    Talent: str = "E"
    Skills: str = "B"
    Resources: str = "D"


class AdeptPowerInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    power_id: str
    rating: int = 1
    extra: str | None = None
    discounted: bool = False
    force: int | None = None


class QiFocusInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rating: int = 2
    power_id: str
    extra: str | None = None
    power_rating: int = 1


class CharacterOptions(BaseModel):
    redliner_torso: bool = False
    redliner_skull: bool = False


class CharacterPatch(BaseModel):
    name: str | None = None
    priorities: Priorities | None = None
    metatype: str | None = None
    metavariant: str | None = None
    talent: str | None = None
    attributes: dict[str, int] | None = None
    skills: dict[str, int] | None = None
    skill_groups: dict[str, int] | None = None
    knowledge_skills: dict[str, int] | None = None
    quality_ids: list[str] | None = None
    cyberware: list[CyberwareInstall] | None = None
    bioware: list[CyberwareInstall] | None = None
    skill_picks: dict[str, str] | None = None
    adept_powers: list[AdeptPowerInstall] | None = None
    mystic_pp: int | None = None
    mentor_id: str | None = None
    mentor_choices: list[str] | None = None
    mentor_extras: dict[str, str] | None = None
    adept_enhancements: list[str] | None = None
    qi_foci: list[QiFocusInstall] | None = None
    options: CharacterOptions | None = None


class CharacterCreate(BaseModel):
    name: str = Field(default="Runner")
    priorities: Priorities | None = None
    metatype: str = "Human"


class CharacterState(BaseModel):
    id: str
    name: str
    priorities: Priorities
    metatype: str
    metavariant: str | None = None
    talent: str = "Mundane"
    attributes: dict[str, int]
    skills: dict[str, int] = Field(default_factory=dict)
    skill_groups: dict[str, int] = Field(default_factory=dict)
    knowledge_skills: dict[str, int] = Field(default_factory=dict)
    quality_ids: list[str] = Field(default_factory=list)
    cyberware: list[CyberwareInstall] = Field(default_factory=list)
    bioware: list[CyberwareInstall] = Field(default_factory=list)
    skill_picks: dict[str, str] = Field(default_factory=dict)
    adept_powers: list[AdeptPowerInstall] = Field(default_factory=list)
    mystic_pp: int = 0
    mentor_id: str | None = None
    mentor_choices: list[str] = Field(default_factory=list)
    mentor_extras: dict[str, str] = Field(default_factory=dict)
    adept_enhancements: list[str] = Field(default_factory=list)
    qi_foci: list[QiFocusInstall] = Field(default_factory=list)
    options: CharacterOptions = Field(default_factory=CharacterOptions)
    derived: dict[str, Any] = Field(default_factory=dict)
