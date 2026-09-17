"""Exotic skills, contacts and martial arts."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class ExoticSkillInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill_name: str
    extra: str = ""
    rating: int = 1


class ContactInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    role: str | None = None
    connection: int = 1
    loyalty: int = 1
    group: bool = False
    free: bool = False
    forced_loyalty: int | None = None
    force_group: bool = False
    source_quality_id: str | None = None
    free_connection: int = 0
    free_loyalty: int = 0


class MartialArtInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    art_id: str
    techniques: list[str] = Field(default_factory=list)
    free: bool = False
    source_quality_id: str | None = None
