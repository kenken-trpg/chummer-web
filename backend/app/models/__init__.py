"""Pydantic models for the character state and the API request bodies.

`__all__` lists the models in the order `scripts/gen_frontend_types.py`
emits them into `frontend/lib/types/generated.ts`.
"""

from ._common import clean_portrait
from .career import CareerBaseline, RewardEntry
from .character import (
    CharacterCreate,
    CharacterPatch,
    CharacterState,
    CustomDataUpload,
    PatchRequest,
    Priorities,
    StateRequest,
)
from .gear import (
    ArmorInstall,
    ArmorModInstall,
    CommlinkInstall,
    CustomDrugInstall,
    CustomDrugPart,
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

__all__ = [
    "CyberwareInstall",
    "Priorities",
    "AdeptPowerInstall",
    "SpellInstall",
    "QiFocusInstall",
    "SpiritInstall",
    "ComplexFormInstall",
    "SpriteInstall",
    "FocusInstall",
    "ArmorInstall",
    "ArmorModInstall",
    "WeaponInstall",
    "VehicleModInstall",
    "WeaponMountInstall",
    "WeaponAccessoryInstall",
    "CommlinkInstall",
    "GearInstall",
    "CustomDrugPart",
    "CustomDrugInstall",
    "LifestyleInstall",
    "ExoticSkillInstall",
    "ContactInstall",
    "MartialArtInstall",
    "InitiationChoice",
    "SubmersionChoice",
    "CharacterOptions",
    "SettingsState",
    "CareerBaseline",
    "RewardEntry",
    "CharacterPatch",
    "CustomDataUpload",
    "CharacterCreate",
    "CharacterState",
    "StateRequest",
    "PatchRequest",
    "clean_portrait",
]
