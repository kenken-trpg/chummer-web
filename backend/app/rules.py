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
    #: The first level of a skill is priced apart from the rest: Chummer's
    #: `RangeCost` charges `karmanew*` for it and `karmaimprove*` for every
    #: level above. The Standard presets set the two to the same number, so
    #: this only shows up under a house rule.
    karma_new_active_skill: int = 2
    karma_new_knowledge_skill: int = 1
    karma_new_skill_group: int = 5
    #: Bonding a focus costs Force x the multiplier for its kind
    #: (`Focus.BindingKarmaCost`), not Force flat.
    karma_alchemical_focus: int = 3
    karma_banishing_focus: int = 2
    karma_binding_focus: int = 2
    karma_centering_focus: int = 3
    karma_counterspelling_focus: int = 2
    karma_disenchanting_focus: int = 3
    karma_flexible_signature_focus: int = 3
    karma_masking_focus: int = 3
    karma_power_focus: int = 6
    karma_qi_focus: int = 2
    karma_ritual_spellcasting_focus: int = 2
    karma_spell_shaping_focus: int = 3
    karma_spellcasting_focus: int = 2
    karma_summoning_focus: int = 2
    karma_sustaining_focus: int = 2
    karma_weapon_focus: int = 3
    #: `<karmaspirit>`: chargen karma per service a spirit / sprite owes
    karma_spirit: int = 1
    #: `<karmacarryover>`: unspent chargen karma kept into play
    karma_carryover: int = 7
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
    #: `<exceedpositivequalities>`: positive qualities may pass the cap.
    quality_exceed_positive: bool = False
    #: `<dontdoublequalities>` / `<dontdoublequalityrefunds>`: a positive
    #: quality taken in career, or a negative one bought off, at its table
    #: karma instead of twice it.
    quality_dont_double_purchases: bool = False
    quality_dont_double_refunds: bool = False
    #: `<usecalculatedpublicawareness>`: Public Awareness also earns
    #: (Street Cred + Notoriety) / 3 on its own. Off in every preset Chummer
    #: ships, where it is only what the GM awards plus what qualities give.
    use_calculated_public_awareness: bool = False
    #: `<noarmorencumbrance>`: stacked armor never costs AGI / REA.
    no_armor_encumbrance: bool = False
    #: `<uncappedarmoraccessorybonuses>`: what stacks on the worn armor is
    #: not capped at Strength (Chummer's `TotalArmorRating`). Encumbrance
    #: still counts the whole stack either way.
    uncapped_armor_accessory_bonuses: bool = False
    #: `<esslossreducesmaximumonly>`: essence loss lowers the MAG / RES
    #: maximum only, so the rating drops just where that maximum falls below
    #: what was bought (Chummer's `RefreshEssenceLossImprovements`).
    ess_loss_reduces_maximum_only: bool = False
    #: `<donotroundessenceinternally>`: Essence is not rounded to two decimals
    #: before MAG / RES loss and the sheet are worked out from it.
    dont_round_essence_internally: bool = False
    #: `<allowinitiationincreatemode>`: initiation and submersion grades may
    #: be taken at chargen (Chummer's `AddInitiationsAllowed`). Off in the
    #: Standard preset, so a grade is career-only.
    allow_initiation_in_create_mode: bool = False
    #: `<usepointsonbrokengroups>`: at chargen a skill whose group holds
    #: group points may still take skill points of its own (Chummer's
    #: `Skill.BaseUnlocked`). Off in Standard: karma only.
    use_points_on_broken_groups: bool = False
    #: `<breakskillgroupsincreatemode>` (Chummer's misleadingly named
    #: `StrictSkillGroupsInCreateMode`): at chargen a skill whose group has a
    #: rating takes no level of its own at all.
    strict_skill_groups_in_create_mode: bool = False
    #: Movement off the cyberlegs' AGI once two legs are chrome.
    cyberleg_movement: bool = False
    #: `<allowpointbuyspecializationsonkarmaskills>`: a skill bought wholly
    #: with karma may still take its specialization for a point. Off in the
    #: Standard presets, so Chummer makes that specialization karma too.
    allow_point_buy_specializations_on_karma_skills: bool = False
    chargen_skill_max: int = CHARGEN_SKILL_MAX
    chargen_knowledge_skill_max: int = CHARGEN_KNOWLEDGE_SKILL_MAX
    #: `<maxnumbermaxattributescreate>`: how many of BOD..WIL may sit at
    #: their natural maximum when creation ends (SR5 p.65: one)
    chargen_attributes_at_max: int = 1
    career_skill_max: int = 12
    career_knowledge_skill_max: int = 12
    chargen_avail_max: int = CHARGEN_AVAIL_MAX
    #: Astral initiative is INT×2 + this many D6 (SR5 p.315: 3); Chummer
    #: rolls `min(min, max)` of the two settings.
    #: Physical initiative starts at the minimum and is capped at the
    #: maximum, however many dice augmentations add (Chummer's
    #: `InitiativeDice`: SR5 p.159, five at most). Cold-sim and hot-sim VR
    #: work the same way off their own pair (SR5 p.229: 3 and 4 dice).
    min_initiative_dice: int = 1
    max_initiative_dice: int = 5
    min_coldsim_initiative_dice: int = 3
    max_coldsim_initiative_dice: int = 5
    min_hotsim_initiative_dice: int = 4
    max_hotsim_initiative_dice: int = 5
    min_astral_initiative_dice: int = 3
    max_astral_initiative_dice: int = 5
    #: Cyberlimb averaging (Chummer's `LimbCount`): six limbs, skull
    #: included, unless a settings file says otherwise.
    limb_count: int = 6
    exclude_limb_slot: str = ""
    #: Chummer's `CyberlimbAttributeBonusCap`: Enhancement plus Redliner /
    #: Cyberseeker adds at most this to a cyberlimb's STR / AGI.
    cyberlimb_attribute_bonus_cap: int = 4
    #: `<dontusecyberlimbcalculation>`: the body's STR / AGI stays the meat
    #: value however many cyberlimbs it has.
    dont_use_cyberlimb_calculation: bool = False

    # --- money ---------------------------------------------------------
    karma_to_nuyen: int = 2000
    #: `<metatypecostskarmamultiplier>`: a Karma build pays the metatype's
    #: `<karma>` times this (Chummer's `CalculateBP`; Priority is untouched).
    metatype_costs_karma_multiplier: int = 1
    karma_nuyen_max: int = 235
    priority_karma_nuyen_base: int = 10
    nuyen_chargen_keep_max: int = 5000
    #: What a Restricted / Forbidden item bought in career costs, times
    #: (`<multiplyrestrictedcost>` + `<restrictedcostmultiplier>`, and the
    #: forbidden pair). 1 unless the file turns the multiplier on — Chummer
    #: charges it at purchase in career mode only (`CharacterCareer.cs`).
    career_restricted_cost_multiplier: int = 1
    career_forbidden_cost_multiplier: int = 1

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
    "karma_new_active_skill": "karma_new_active_skill",
    "karma_new_knowledge_skill": "karma_new_knowledge_skill",
    "karma_new_skill_group": "karma_new_skill_group",
    "karma_alchemical_focus": "karma_alchemical_focus",
    "karma_banishing_focus": "karma_banishing_focus",
    "karma_binding_focus": "karma_binding_focus",
    "karma_centering_focus": "karma_centering_focus",
    "karma_counterspelling_focus": "karma_counterspelling_focus",
    "karma_disenchanting_focus": "karma_disenchanting_focus",
    "karma_flexible_signature_focus": "karma_flexible_signature_focus",
    "karma_masking_focus": "karma_masking_focus",
    "karma_power_focus": "karma_power_focus",
    "karma_qi_focus": "karma_qi_focus",
    "karma_ritual_spellcasting_focus": "karma_ritual_spellcasting_focus",
    "karma_spell_shaping_focus": "karma_spell_shaping_focus",
    "karma_spellcasting_focus": "karma_spellcasting_focus",
    "karma_summoning_focus": "karma_summoning_focus",
    "karma_sustaining_focus": "karma_sustaining_focus",
    "karma_weapon_focus": "karma_weapon_focus",
    "karma_initiation_flat": "karma_initiation_flat",
    "karma_initiation_per_grade": "karma_initiation_per_grade",
    "karma_submersion_flat": "karma_submersion_flat",
    "karma_submersion_per_grade": "karma_submersion_per_grade",
    "chargen_skill_max": "chargen_skill_max",
    "chargen_knowledge_skill_max": "chargen_knowledge_skill_max",
    "chargen_attributes_at_max": "chargen_attributes_at_max",
    "career_skill_max": "career_skill_max",
    "career_knowledge_skill_max": "career_knowledge_skill_max",
    "chargen_avail_max": "chargen_avail_max",
    "min_initiative_dice": "min_initiative_dice",
    "max_initiative_dice": "max_initiative_dice",
    "min_coldsim_initiative_dice": "min_coldsim_initiative_dice",
    "max_coldsim_initiative_dice": "max_coldsim_initiative_dice",
    "min_hotsim_initiative_dice": "min_hotsim_initiative_dice",
    "max_hotsim_initiative_dice": "max_hotsim_initiative_dice",
    "min_astral_initiative_dice": "min_astral_initiative_dice",
    "max_astral_initiative_dice": "max_astral_initiative_dice",
    "limb_count": "limb_count",
    "cyberlimb_attribute_bonus_cap": "cyberlimb_attribute_bonus_cap",
    "karma_to_nuyen": "karma_to_nuyen",
    "metatype_costs_karma_multiplier": "metatype_costs_karma_multiplier",
    "karma_spirit": "karma_spirit",
    "karma_carryover": "karma_carryover",
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
        ("exceed_positive_qualities", "quality_exceed_positive"),
        ("dont_double_quality_purchases", "quality_dont_double_purchases"),
        ("dont_double_quality_refunds", "quality_dont_double_refunds"),
        ("cyberleg_movement", "cyberleg_movement"),
        ("dont_use_cyberlimb_calculation", "dont_use_cyberlimb_calculation"),
        ("use_calculated_public_awareness", "use_calculated_public_awareness"),
        ("no_armor_encumbrance", "no_armor_encumbrance"),
        ("uncapped_armor_accessory_bonuses", "uncapped_armor_accessory_bonuses"),
        ("ess_loss_reduces_maximum_only", "ess_loss_reduces_maximum_only"),
        ("dont_round_essence_internally", "dont_round_essence_internally"),
        ("allow_initiation_in_create_mode", "allow_initiation_in_create_mode"),
        ("use_points_on_broken_groups", "use_points_on_broken_groups"),
        ("strict_skill_groups_in_create_mode", "strict_skill_groups_in_create_mode"),
        (
            "allow_point_buy_specializations_on_karma_skills",
            "allow_point_buy_specializations_on_karma_skills",
        ),
    ):
        flag = getattr(settings, src, None)
        if flag is not None:
            overrides[dest] = bool(flag)
    for switch, factor, dest in (
        ("multiply_restricted_cost", "restricted_cost_multiplier", "career_restricted_cost_multiplier"),
        ("multiply_forbidden_cost", "forbidden_cost_multiplier", "career_forbidden_cost_multiplier"),
    ):
        if getattr(settings, switch, None):
            overrides[dest] = max(1, int(getattr(settings, factor, None) or 1))
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


#: A focus's name, as `foci.xml` spells it, cut down to the kind Chummer
#: prices: everything from the first `(` or `,` is dropped, so
#: `Counterspelling Focus, Combat` and `Weapon Focus (2050)` both land on
#: their kind. A name that matches nothing (Spell Lock) binds at Force flat,
#: which is Chummer's multiplier of 1.
_FOCUS_KARMA_FIELDS: dict[str, str] = {
    "Alchemical Focus": "karma_alchemical_focus",
    "Banishing Focus": "karma_banishing_focus",
    "Binding Focus": "karma_binding_focus",
    "Centering Focus": "karma_centering_focus",
    "Counterspelling Focus": "karma_counterspelling_focus",
    "Disenchanting Focus": "karma_disenchanting_focus",
    "Flexible Signature Focus": "karma_flexible_signature_focus",
    "Masking Focus": "karma_masking_focus",
    "Power Focus": "karma_power_focus",
    "Qi Focus": "karma_qi_focus",
    "Ritual Spellcasting Focus": "karma_ritual_spellcasting_focus",
    "Spell Shaping Focus": "karma_spell_shaping_focus",
    "Spellcasting Focus": "karma_spellcasting_focus",
    "Summoning Focus": "karma_summoning_focus",
    "Sustaining Focus": "karma_sustaining_focus",
    "Weapon Focus": "karma_weapon_focus",
}


def focus_karma_multiplier(name: str) -> int:
    """Karma per point of Force for bonding this focus (`Focus.BindingKarmaCost`)."""
    kind = str(name or "").split("(")[0].split(",")[0].strip()
    field = _FOCUS_KARMA_FIELDS.get(kind)
    return int(getattr(current_rules(), field)) if field else 1
