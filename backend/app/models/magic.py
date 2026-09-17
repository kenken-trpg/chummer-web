"""Magic and resonance rows, and the initiation / submersion ledger."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class AdeptPowerInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    power_id: str
    rating: int = 1
    extra: str | None = None
    discounted: bool = False
    force: int | None = None


class SpellInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    spell_id: str
    force: int | None = None
    source_quality_id: str | None = None
    alchemical: bool = False


class QiFocusInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rating: int = 2
    power_id: str
    extra: str | None = None
    power_rating: int = 1


class SpiritInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    spirit_id: str
    force: int = 1
    services: int = 1
    bound: bool = True
    hits: int | None = None
    opposed_hits: int | None = None


class ComplexFormInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    form_id: str
    level: int | None = None
    extra: str | None = None


class SpriteInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sprite_id: str
    level: int = 1
    services: int = 1
    registered: bool = True
    hits: int | None = None
    opposed_hits: int | None = None


class FocusInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gear_id: str
    force: int = 1
    crafted: bool = False
    formula_bought: bool = True
    hits: int | None = None
    opposed_hits: int | None = None
    extra: str | None = None


class InitiationChoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    grade: int = 1
    kind: str = "metamagic"  # metamagic | art
    option_id: str = ""
    group: bool = False  # member of an initiatory group (−10% Karma)
    ordeal: bool = False  # underwent an ordeal (−10% Karma)
    schooling: bool = False  # formal schooling (−10% Karma, costs nuyen/time)


class SubmersionChoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    grade: int = 1
    echo_id: str = ""
    extra: str | None = None
    group: bool = False  # member of a network (−10% Karma)
    ordeal: bool = False  # completed a submersion task (−10% Karma)
    schooling: bool = False  # formal schooling (−10% Karma)
