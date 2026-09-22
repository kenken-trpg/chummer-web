"""The character itself, the patch applied to it, and the request bodies."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from ._common import _reject_oversized_collections, _reject_oversized_input, clean_extra_portraits, clean_portrait
from .career import CareerBaseline, RewardEntry
from .gear import (
    ArmorInstall,
    ArmorModInstall,
    CommlinkInstall,
    CustomDrugInstall,
    CyberwareInstall,
    GearInstall,
    LifestyleInstall,
    VehicleModInstall,
    WeaponAccessoryInstall,
    WeaponInstall,
    WeaponMountInstall,
)
from .magic import (
    AdeptPowerInstall,
    ComplexFormInstall,
    FocusInstall,
    InitiationChoice,
    QiFocusInstall,
    SpellInstall,
    SpiritInstall,
    SpriteInstall,
    SubmersionChoice,
)
from .settings import CharacterOptions, SettingsState
from .social import ContactInstall, ExoticSkillInstall, MartialArtInstall


class Priorities(BaseModel):
    Heritage: str = "C"
    Attributes: str = "A"
    Talent: str = "E"
    Skills: str = "B"
    Resources: str = "D"


class CharacterPatch(BaseModel):
    name: str | None = None
    build_method: str | None = None
    priorities: Priorities | None = None
    metatype: str | None = None
    metavariant: str | None = None
    talent: str | None = None
    attributes: dict[str, int] | None = None
    attribute_karma: dict[str, int] | None = None
    skills: dict[str, int] | None = None
    skill_karma: dict[str, int] | None = None
    skill_groups: dict[str, int] | None = None
    skill_group_karma: dict[str, int] | None = None
    skill_specializations: dict[str, str] | None = None
    talent_skills: list[str] | None = None
    skill_specs_karma: list[str] | None = None
    exotic_skills: list[ExoticSkillInstall] | None = None
    knowledge_skills: dict[str, int] | None = None
    knowledge_karma: dict[str, int] | None = None
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
    custom_drugs: list[CustomDrugInstall] | None = None
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
    age: str | None = None
    sex: str | None = None
    height: str | None = None
    weight: str | None = None
    eyes: str | None = None
    hair: str | None = None
    skin: str | None = None
    appearance: str | None = None
    background: str | None = None
    concept: str | None = None
    portrait: str | None = None  # data: URI (base64 image) or ""
    extra_portraits: list[str] | None = None
    career: bool | None = None
    karma_earned: int | None = None
    nuyen_earned: int | None = None
    karma_adjust: int | None = None
    nuyen_adjust: int | None = None
    career_baseline: CareerBaseline | None = None
    street_cred: int | None = None
    burnt_street_cred: int | None = None
    notoriety_bonus: int | None = None
    public_awareness: int | None = None
    reward_log: list[RewardEntry] | None = None
    expense_log: list[RewardEntry] | None = None
    tradition_id: str | None = None
    stream_id: str | None = None
    options: CharacterOptions | None = None
    settings: SettingsState | None = None

    @model_validator(mode="before")
    @classmethod
    def _bound_input(cls, data: object) -> object:
        return _reject_oversized_input(data)

    @model_validator(mode="after")
    def _bound_collections(self) -> CharacterPatch:
        _reject_oversized_collections(self)
        return self

    @field_validator("portrait")
    @classmethod
    def _portrait(cls, v: str | None) -> str | None:
        return None if v is None else clean_portrait(v)

    @field_validator("extra_portraits")
    @classmethod
    def _extra_portraits(cls, v: list[str] | None) -> list[str] | None:
        return None if v is None else clean_extra_portraits(v)


class CustomDataUpload(BaseModel):
    """A `customdata/` tree on its way to the merge.

    `files` is keyed by the path relative to `customdata/`
    (`NTS4C08/amend_martialarts.xml`) because the directory is what a settings
    file names, and `customdata` is that settings file's enabled list, in its
    order — later entries win where two edit the same entry.
    """

    files: dict[str, str] = Field(default_factory=dict)
    customdata: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _bounded(self) -> CustomDataUpload:
        if len(self.files) > 500:
            raise ValueError("too many custom-data files")
        if len(self.customdata) > 500 or any(len(name) > 256 for name in self.customdata):
            raise ValueError("too many or too long custom-data directory names")
        return self


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
    #: Priority / Sum-to-Ten creation: of `attributes[key]`, how many of the
    #: top levels were bought with karma rather than attribute points
    #: (Chummer's `<karma>` beside `<base>`). Ignored by a Karma build, where
    #: every level is karma anyway.
    attribute_karma: dict[str, int] = Field(default_factory=dict)
    skills: dict[str, int] = Field(default_factory=dict)
    #: The same split for skills: of `skills[name]` / `knowledge_skills[name]`,
    #: the top levels bought with karma rather than skill / knowledge points.
    skill_karma: dict[str, int] = Field(default_factory=dict)
    knowledge_karma: dict[str, int] = Field(default_factory=dict)
    skill_groups: dict[str, int] = Field(default_factory=dict)
    #: of `skill_groups[name]`, the top levels bought with karma
    skill_group_karma: dict[str, int] = Field(default_factory=dict)
    skill_specializations: dict[str, str] = Field(default_factory=dict)
    #: the skills (or, for an Aspected Magician, the skill group) the priority
    #: talent hands out at its fixed rating — Chummer's Heritage `SkillBase` /
    #: `SkillGroupBase` improvements. `skills` / `skill_groups` hold the total
    #: rating, free levels included.
    talent_skills: list[str] = Field(default_factory=list)
    #: skills (active or knowledge) whose specialization the player chose to
    #: buy with karma on a priority sheet — Chummer's `<buywithkarma>`
    skill_specs_karma: list[str] = Field(default_factory=list)
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
    custom_drugs: list[CustomDrugInstall] = Field(default_factory=list)
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
    age: str = ""
    sex: str = ""
    height: str = ""
    weight: str = ""
    eyes: str = ""
    hair: str = ""
    skin: str = ""
    appearance: str = ""
    background: str = ""
    concept: str = ""
    portrait: str = ""  # data: URI (base64 image) or ""
    #: the second and third of Chummer's mugshots, after `portrait`
    extra_portraits: list[str] = Field(default_factory=list)
    career: bool = False
    karma_earned: int = 0
    nuyen_earned: int = 0
    #: a Chummer career save's balance less what this app works out from
    #: the build and the rewards: spending the app does not model (rent,
    #: purchases at their own prices). Added to what is left, either sign.
    karma_adjust: int = 0
    nuyen_adjust: int = 0
    career_baseline: CareerBaseline | None = None
    street_cred: int = 0
    # SR5 p.373: two points burned take a point of Notoriety off
    burnt_street_cred: int = 0
    notoriety_bonus: int = 0
    #: Public Awareness the GM has awarded — Chummer's `<publicawareness>`,
    #: a counter it stores as told rather than works out.
    public_awareness: int = 0
    reward_log: list[RewardEntry] = Field(default_factory=list)
    #: what a Chummer save's expense log spent (negative), kept as history:
    #: the balance itself is already met by `karma_adjust` / `nuyen_adjust`,
    #: so these rows are shown and written back, never counted again
    expense_log: list[RewardEntry] = Field(default_factory=list)
    tradition_id: str | None = None
    stream_id: str | None = None
    options: CharacterOptions = Field(default_factory=CharacterOptions)
    settings: SettingsState = Field(default_factory=SettingsState)
    # Output of compute(); kept dict[str, Any] here (Pydantic-friendly, no
    # round-trip validation). Its real shape is engine.compute.derived_types.DerivedDict.
    derived: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _bound_input(cls, data: object) -> object:
        return _reject_oversized_input(data)

    @model_validator(mode="after")
    def _bound_collections(self) -> CharacterState:
        _reject_oversized_collections(self)
        return self

    @field_validator("portrait")
    @classmethod
    def _portrait(cls, v: str) -> str:
        return clean_portrait(v)

    @field_validator("extra_portraits")
    @classmethod
    def _extra_portraits(cls, v: list[str]) -> list[str]:
        return clean_extra_portraits(v)


class StateRequest(BaseModel):
    """A client-owned `CharacterState` sent back for a stateless operation."""

    state: CharacterState


class PatchRequest(BaseModel):
    """`state` plus an optional `patch`; with no patch it's a bare recompute."""

    state: CharacterState
    patch: CharacterPatch | None = None
