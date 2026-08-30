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


class ArmorInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    armor_id: str
    rating: int = 1
    equipped: bool = True


class ArmorModInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mod_id: str
    parent_id: str | None = None
    included: bool = False
    rating: int = 1


class WeaponInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    weapon_id: str
    qty: int = 1
    loaded_ammo_id: str | None = None


class VehicleModInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mod_id: str
    parent_id: str | None = None
    included: bool = False
    rating: int = 1


class WeaponMountInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str | None = None
    size_id: str = ""
    visibility_id: str = ""
    flexibility_id: str = ""
    control_id: str = ""
    included: bool = False
    weapon_install_id: str | None = None
    allowedweapons: str = ""


class WeaponAccessoryInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    accessory_id: str
    parent_id: str | None = None
    included: bool = False
    rating: int = 1
    mount: str = ""


class CommlinkInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gear_id: str
    rating: int = 1


class GearInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gear_id: str
    rating: int = 1
    qty: int = 1
    parent_id: str | None = None
    included: bool = False
    capacity_override: str | None = None
    array_order: list[str] = Field(default_factory=list)
    extra: str | None = None


class LifestyleInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lifestyle_id: str
    months: int = 1
    quality_ids: list[str] = Field(default_factory=list)
    quality_extras: dict[str, str] = Field(default_factory=dict)


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


class InitiationChoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    grade: int = 1
    kind: str = "metamagic"  # metamagic | art
    option_id: str = ""


class SubmersionChoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    grade: int = 1
    echo_id: str = ""
    extra: str | None = None


class CharacterOptions(BaseModel):
    redliner_torso: bool = False
    redliner_skull: bool = False


class CareerBaseline(BaseModel):
    """Snapshot of chargen ratings when entering career mode (Priority/SumToTen raises bill from here)."""

    attributes: dict[str, int] = Field(default_factory=dict)
    skills: dict[str, int] = Field(default_factory=dict)
    skill_groups: dict[str, int] = Field(default_factory=dict)
    knowledge_skills: dict[str, int] = Field(default_factory=dict)
    skill_specializations: list[str] = Field(default_factory=list)
    exotic_skills: dict[str, int] = Field(default_factory=dict)


class RewardEntry(BaseModel):
    """Career reward ledger row (run payout, bonus, etc.)."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str = ""
    karma: int = 0
    nuyen: int = 0


class CharacterPatch(BaseModel):
    name: str | None = None
    build_method: str | None = None
    priorities: Priorities | None = None
    metatype: str | None = None
    metavariant: str | None = None
    talent: str | None = None
    attributes: dict[str, int] | None = None
    skills: dict[str, int] | None = None
    skill_groups: dict[str, int] | None = None
    skill_specializations: dict[str, str] | None = None
    exotic_skills: list[ExoticSkillInstall] | None = None
    knowledge_skills: dict[str, int] | None = None
    native_languages: list[str] | None = None
    knowledge_categories: dict[str, str] | None = None
    quality_ids: list[str] | None = None
    quality_extras: dict[str, str] | None = None
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
    spells: list[SpellInstall] | None = None
    spirits: list[SpiritInstall] | None = None
    complex_forms: list[ComplexFormInstall] | None = None
    sprites: list[SpriteInstall] | None = None
    foci: list[FocusInstall] | None = None
    armor: list[ArmorInstall] | None = None
    armor_mods: list[ArmorModInstall] | None = None
    weapons: list[WeaponInstall] | None = None
    weapon_accessories: list[WeaponAccessoryInstall] | None = None
    commlinks: list[CommlinkInstall] | None = None
    cyberdecks: list[GearInstall] | None = None
    rccs: list[GearInstall] | None = None
    optics: list[GearInstall] | None = None
    programs: list[GearInstall] | None = None
    apps: list[GearInstall] | None = None
    sensors: list[GearInstall] | None = None
    drones: list[GearInstall] | None = None
    vehicles: list[GearInstall] | None = None
    gear: list[GearInstall] | None = None
    vehicle_mods: list[VehicleModInstall] | None = None
    weapon_mounts: list[WeaponMountInstall] | None = None
    lifestyles: list[LifestyleInstall] | None = None
    contacts: list[ContactInstall] | None = None
    martial_arts: list[MartialArtInstall] | None = None
    initiate_grade: int | None = None
    initiations: list[InitiationChoice] | None = None
    submersion_grade: int | None = None
    submersions: list[SubmersionChoice] | None = None
    karma_nuyen: int | None = None
    notes: str | None = None
    career: bool | None = None
    karma_earned: int | None = None
    nuyen_earned: int | None = None
    career_baseline: CareerBaseline | None = None
    street_cred: int | None = None
    notoriety_bonus: int | None = None
    reward_log: list[RewardEntry] | None = None
    tradition_id: str | None = None
    stream_id: str | None = None
    options: CharacterOptions | None = None


class CharacterCreate(BaseModel):
    name: str = Field(default="Runner")
    build_method: str = "Priority"
    priorities: Priorities | None = None
    metatype: str = "Human"


class CharacterState(BaseModel):
    id: str
    name: str
    build_method: str = "Priority"
    priorities: Priorities
    metatype: str
    metavariant: str | None = None
    talent: str = "Mundane"
    attributes: dict[str, int]
    skills: dict[str, int] = Field(default_factory=dict)
    skill_groups: dict[str, int] = Field(default_factory=dict)
    skill_specializations: dict[str, str] = Field(default_factory=dict)
    exotic_skills: list[ExoticSkillInstall] = Field(default_factory=list)
    knowledge_skills: dict[str, int] = Field(default_factory=dict)
    native_languages: list[str] = Field(default_factory=list)
    knowledge_categories: dict[str, str] = Field(default_factory=dict)
    quality_ids: list[str] = Field(default_factory=list)
    quality_extras: dict[str, str] = Field(default_factory=dict)
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
    spells: list[SpellInstall] = Field(default_factory=list)
    spirits: list[SpiritInstall] = Field(default_factory=list)
    complex_forms: list[ComplexFormInstall] = Field(default_factory=list)
    sprites: list[SpriteInstall] = Field(default_factory=list)
    foci: list[FocusInstall] = Field(default_factory=list)
    armor: list[ArmorInstall] = Field(default_factory=list)
    armor_mods: list[ArmorModInstall] = Field(default_factory=list)
    weapons: list[WeaponInstall] = Field(default_factory=list)
    weapon_accessories: list[WeaponAccessoryInstall] = Field(default_factory=list)
    commlinks: list[CommlinkInstall] = Field(default_factory=list)
    cyberdecks: list[GearInstall] = Field(default_factory=list)
    rccs: list[GearInstall] = Field(default_factory=list)
    optics: list[GearInstall] = Field(default_factory=list)
    programs: list[GearInstall] = Field(default_factory=list)
    apps: list[GearInstall] = Field(default_factory=list)
    sensors: list[GearInstall] = Field(default_factory=list)
    drones: list[GearInstall] = Field(default_factory=list)
    vehicles: list[GearInstall] = Field(default_factory=list)
    gear: list[GearInstall] = Field(default_factory=list)
    vehicle_mods: list[VehicleModInstall] = Field(default_factory=list)
    weapon_mounts: list[WeaponMountInstall] = Field(default_factory=list)
    lifestyles: list[LifestyleInstall] = Field(default_factory=list)
    contacts: list[ContactInstall] = Field(default_factory=list)
    martial_arts: list[MartialArtInstall] = Field(default_factory=list)
    initiate_grade: int = 0
    initiations: list[InitiationChoice] = Field(default_factory=list)
    submersion_grade: int = 0
    submersions: list[SubmersionChoice] = Field(default_factory=list)
    karma_nuyen: int = 0
    notes: str = ""
    career: bool = False
    karma_earned: int = 0
    nuyen_earned: int = 0
    career_baseline: CareerBaseline | None = None
    street_cred: int = 0
    notoriety_bonus: int = 0
    reward_log: list[RewardEntry] = Field(default_factory=list)
    tradition_id: str | None = None
    stream_id: str | None = None
    options: CharacterOptions = Field(default_factory=CharacterOptions)
    derived: dict[str, Any] = Field(default_factory=dict)
