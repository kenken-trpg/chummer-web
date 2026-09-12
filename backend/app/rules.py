"""``Rules`` — the settings a character is built under, resolved to numbers.

``engine/constants.py`` holds SR5's printed values. A Chummer settings file may
change most of them, so the engine reads them from here instead: ``Rules()``
with nothing supplied *is* the constants, and a character carrying a
``SettingsState`` gets its overrides folded in.

Why a ContextVar rather than a parameter. The values are read from 17 modules,
most of which are free functions (``engine/karma.py``, ``engine/limits.py``,
``engine/priority.py``) that never see a ``Ctx``. Threading a ``Rules`` through
all of them would be ~100 signature changes for a value that is constant for
the length of one ``compute()``. ``compute()`` binds it once, in a ``with``
block, and everything under it reads ``current_rules()`` — the same shape as
``data_loader.catalog()``, which the engine already reaches for globally.

The binding is per-context, so it is safe under both threads and asyncio tasks:
FastAPI runs each request in its own, and a task started inside one inherits a
copy rather than sharing the slot.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from contextvars import ContextVar
from dataclasses import dataclass, fields

from .data_loader.formulas import CHARGEN_AVAIL_MAX

# The printed SR5 values. They live here rather than in `engine/constants.py`
# because that module is imported by the whole engine, and the engine now
# imports *this* one — putting the numbers here is what keeps the two from
# importing each other. `constants.py` re-exports the handful that other code
# still refers to by name.

#: Chargen karma for Priority / Sum-to-Ten (SR5 p.65). Chummer's
#: `<buildpoints>`, which for a Karma build means the whole 800 instead.
CHARGEN_KARMA = 25
#: Chargen rating caps (SR5 p.95).
CHARGEN_SKILL_MAX = 6
CHARGEN_KNOWLEDGE_SKILL_MAX = 6


#: The table every core priority row belongs to, and the fallback when a
#: settings file names one this data does not have.
DEFAULT_PRIORITY_TABLE = "Standard"


@dataclass(frozen=True)
class Rules:
    """One resolved settings file. Every default is the printed SR5 value, so
    a character with no settings computes exactly as it did before settings
    existed."""

    # --- build ---------------------------------------------------------
    sum_to_ten_budget: int = 10
    chargen_karma: int = CHARGEN_KARMA
    karma_chargen_pool: int = 800

    # --- karma prices --------------------------------------------------
    karma_attribute: int = 5
    karma_active_skill: int = 2
    karma_skill_group: int = 5
    karma_knowledge: int = 1
    karma_specialization: int = 7
    #: `<karmaknospecialization>`: a knowledge skill's specialization, priced
    #: apart from an active skill's (Neon Anarchy: 3)
    karma_knowledge_specialization: int = 7
    karma_spell: int = 5
    karma_complex_form: int = 4
    karma_enhancement: int = 2
    karma_mystic_pp: int = 5
    karma_martial_style: int = 7
    karma_martial_technique: int = 5
    karma_initiation_flat: int = 10
    karma_initiation_per_grade: int = 3
    karma_submersion_flat: int = 10
    karma_submersion_per_grade: int = 3

    # --- caps ----------------------------------------------------------
    quality_karma_cap_positive: int = 25
    quality_karma_cap_negative: int = 25
    #: House rules on that cap: pass it without an error, and (separately)
    #: earn no karma for what lies past it.
    quality_exceed_negative: bool = False
    quality_exceed_negative_no_bonus: bool = False
    #: Movement off the cyberlegs' AGI once two legs are chrome.
    cyberleg_movement: bool = False
    chargen_skill_max: int = CHARGEN_SKILL_MAX
    chargen_knowledge_skill_max: int = CHARGEN_KNOWLEDGE_SKILL_MAX
    career_skill_max: int = 12
    career_skill_group_max: int = 12
    chargen_avail_max: int = CHARGEN_AVAIL_MAX
    #: Astral initiative is INT×2 + this many D6 (SR5 p.315: 3); Chummer
    #: rolls `min(min, max)` of the two settings.
    min_astral_initiative_dice: int = 3
    max_astral_initiative_dice: int = 5
    #: Cyberlimb averaging (Chummer's `LimbCount`): six limbs, skull
    #: included, unless a settings file says otherwise.
    limb_count: int = 6
    exclude_limb_slot: str = ""

    # --- money ---------------------------------------------------------
    karma_to_nuyen: int = 2000
    karma_nuyen_max: int = 235
    priority_karma_nuyen_base: int = 10
    nuyen_chargen_keep_max: int = 5000

    # --- misc ----------------------------------------------------------
    contact_free_mult: int = 3
    #: How many spirits a magician may hold bound, and sprites a technomancer
    #: registered: the rating of this attribute (Chummer's Standard: CHA).
    bound_spirit_attr: str = "CHA"
    registered_sprite_attr: str = "CHA"
    banned_ware_grades: tuple[str, ...] = ()
    #: Which `<prioritytable>` the priority rows come from. `priorities.xml`
    #: carries several — Standard, Prime Runner, Street Level — and a settings
    #: file picks one for the whole table.
    priority_table: str = DEFAULT_PRIORITY_TABLE


DEFAULT_RULES = Rules()

_current: ContextVar[Rules] = ContextVar("rules", default=DEFAULT_RULES)


def current_rules() -> Rules:
    """The rules in force. `DEFAULT_RULES` outside a `using_rules` block, so
    tests and one-off helpers that call into the engine still work."""
    return _current.get()


@contextlib.contextmanager
def using_rules(rules: Rules) -> Iterator[Rules]:
    token = _current.set(rules)
    try:
        yield rules
    finally:
        _current.reset(token)


#: `SettingsState` field -> `Rules` field, for the fields that are a plain
#: number carried straight through. Anything needing arithmetic or a different
#: shape (`banned_ware_grades`) is handled in `rules_for` instead.
_DIRECT: dict[str, str] = {
    "sum_to_ten": "sum_to_ten_budget",
    "chargen_karma": "chargen_karma",
    "karma_chargen_pool": "karma_chargen_pool",
    "karma_attribute": "karma_attribute",
    "karma_active_skill": "karma_active_skill",
    "karma_skill_group": "karma_skill_group",
    "karma_knowledge": "karma_knowledge",
    "karma_specialization": "karma_specialization",
    "karma_knowledge_specialization": "karma_knowledge_specialization",
    "karma_spell": "karma_spell",
    "karma_complex_form": "karma_complex_form",
    "karma_enhancement": "karma_enhancement",
    "karma_mystic_pp": "karma_mystic_pp",
    "karma_martial_technique": "karma_martial_technique",
    "karma_initiation_flat": "karma_initiation_flat",
    "karma_initiation_per_grade": "karma_initiation_per_grade",
    "karma_submersion_flat": "karma_submersion_flat",
    "karma_submersion_per_grade": "karma_submersion_per_grade",
    "chargen_skill_max": "chargen_skill_max",
    "chargen_knowledge_skill_max": "chargen_knowledge_skill_max",
    "career_skill_max": "career_skill_max",
    "career_skill_group_max": "career_skill_group_max",
    "chargen_avail_max": "chargen_avail_max",
    "min_astral_initiative_dice": "min_astral_initiative_dice",
    "max_astral_initiative_dice": "max_astral_initiative_dice",
    "limb_count": "limb_count",
    "karma_to_nuyen": "karma_to_nuyen",
    "priority_karma_nuyen_base": "priority_karma_nuyen_base",
    "contact_free_mult": "contact_free_mult",
}

#: Every `Rules` field name — `test_settings.py` asserts `_DIRECT` only names
#: real ones, so a rename on either side fails loudly instead of silently
#: dropping an override.
RULE_FIELDS = frozenset(f.name for f in fields(Rules))


def rules_for(settings: object | None) -> Rules:
    """`SettingsState` -> `Rules`. `None`, or a field left unset, keeps the
    printed SR5 value: a settings file says what it changes, not everything."""
    if settings is None:
        return DEFAULT_RULES
    overrides: dict[str, object] = {}
    for src, dest in _DIRECT.items():
        value = getattr(settings, src, None)
        if value is not None:
            overrides[dest] = int(value)
    # `<qualitykarmalimit>` is one number in Chummer and caps both directions.
    limit = getattr(settings, "quality_karma_limit", None)
    if limit is not None:
        overrides["quality_karma_cap_positive"] = int(limit)
        overrides["quality_karma_cap_negative"] = int(limit)
    for src, dest in (
        ("exceed_negative_qualities", "quality_exceed_negative"),
        ("exceed_negative_qualities_no_bonus", "quality_exceed_negative_no_bonus"),
        ("cyberleg_movement", "cyberleg_movement"),
    ):
        flag = getattr(settings, src, None)
        if flag is not None:
            overrides[dest] = bool(flag)
    grades = getattr(settings, "banned_ware_grades", None)
    if grades:
        overrides["banned_ware_grades"] = tuple(str(g) for g in grades)
    for attr_field in ("bound_spirit_attr", "registered_sprite_attr"):
        attr = getattr(settings, attr_field, None)
        if attr:
            overrides[attr_field] = str(attr)
    exclude = getattr(settings, "exclude_limb_slot", None)
    if exclude:
        overrides["exclude_limb_slot"] = str(exclude)
    table = getattr(settings, "priority_table", None)
    if table:
        overrides["priority_table"] = str(table)
    return Rules(**overrides)  # type: ignore[arg-type]
