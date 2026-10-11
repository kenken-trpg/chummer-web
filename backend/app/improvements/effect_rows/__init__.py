"""``TypedDict`` shapes for the row dicts inside ``EffectsDict``'s list values.

``EffectsDict`` (``effects.py``) fixed the ~134 keys; these modules fix the
shape of the rows in its ``*_mods`` / ``*_slots`` / ``grant_*`` / cost-rule
lists, so ``row.get("nam")`` (typo) is a ``mypy`` error too. Each row is
produced by exactly one ``improvements/nodes/<domain>.py`` branch (or, for a
few, a ``bind_*`` in ``app/engine``) and read by a handful of engine
consumers via string-literal keys.

The shapes live one group per module, the groups being the ones the plan
surveyed: ``mods`` (karma-cost rules and dice mods), ``grants`` (what a bonus
hands over outright), ``slots`` (a choice the player makes), ``misc`` (the
rest) and ``resolved`` (rows a ``bind_*`` produces). This module is the
barrel, so a consumer imports from ``effect_rows`` without caring which.

Imports only ``typing`` (and ``notices`` for one label) — ``effects.py``
imports from here, nothing imports back, so the ``improvements`` package stays
a DAG. See ``docs/plans/refactor-effect-rows-plan.md``.
"""

from __future__ import annotations

from .grants import (
    FreeMartialArtRow,
    FreeMetamagicRow,
    GrantEchoRow,
    GrantGearRow,
    GrantPowerRow,
    GrantSpellRow,
    GrantWareRow,
    GrantWeaponRow,
    MetamagicLimitRow,
)
from .misc import (
    ActionDicePoolRow,
    AddContactRow,
    FadingValueSpecificRow,
    FocusBindingRow,
    FreeSpellsAttributeRow,
    FreeSpellsSkillRow,
    LimitModifierRow,
    NewSpellKarmaCostRow,
    RestrictedGearRow,
    SpellCategoryValueRow,
    SpellDescriptorValueRow,
    SpellDicePoolRow,
    UnimplementedRow,
)
from .mods import (
    AttributeRangeRow,
    KarmaCostRow,
    KarmaMultRow,
    NamedBonusRow,
    SkillAttributeSwapRow,
    SkillModRow,
)
from .resolved import (
    AddSpiritPickRow,
    WeaponDvBonusRow,
)
from .slots import (
    AddSpiritSlotRow,
    AttributeSelectRow,
    ExpertiseSlotRow,
    LimitSpellCategorySlotRow,
    LimitSpiritCategorySlotRow,
    NaturalWeaponRow,
    SelectPowerSlotRow,
    SelectQualitySlotRow,
    WeaponCategoryDiceRow,
    WeaponCategoryDvSlotRow,
    WeaponSkillAccuracySlotRow,
)

__all__ = [
    "ActionDicePoolRow",
    "AddContactRow",
    "AddSpiritPickRow",
    "AddSpiritSlotRow",
    "AttributeRangeRow",
    "AttributeSelectRow",
    "ExpertiseSlotRow",
    "FadingValueSpecificRow",
    "FocusBindingRow",
    "FreeMartialArtRow",
    "FreeMetamagicRow",
    "FreeSpellsAttributeRow",
    "FreeSpellsSkillRow",
    "GrantEchoRow",
    "GrantGearRow",
    "GrantPowerRow",
    "GrantSpellRow",
    "GrantWareRow",
    "GrantWeaponRow",
    "KarmaCostRow",
    "KarmaMultRow",
    "LimitModifierRow",
    "LimitSpellCategorySlotRow",
    "LimitSpiritCategorySlotRow",
    "MetamagicLimitRow",
    "NamedBonusRow",
    "NaturalWeaponRow",
    "NewSpellKarmaCostRow",
    "RestrictedGearRow",
    "SelectPowerSlotRow",
    "SelectQualitySlotRow",
    "SkillAttributeSwapRow",
    "SkillModRow",
    "SpellCategoryValueRow",
    "SpellDescriptorValueRow",
    "SpellDicePoolRow",
    "UnimplementedRow",
    "WeaponCategoryDiceRow",
    "WeaponCategoryDvSlotRow",
    "WeaponDvBonusRow",
    "WeaponSkillAccuracySlotRow",
]
