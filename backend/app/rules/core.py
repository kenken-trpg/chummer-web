"""The printed SR5 values, the :class:`Rules` they seed, and the ``ContextVar``
the engine reads them through.

``engine/constants.py`` holds SR5's printed values. A Chummer settings file may
change most of them, so the engine reads them from here instead: ``Rules()``
with nothing supplied *is* the constants, and a character carrying a
``SettingsState`` gets its overrides folded in (``settings.py`` does the
folding).

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
from dataclasses import dataclass

from ..data_loader.formulas import CHARGEN_AVAIL_MAX

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
    #: `<alternatemetatypeattributekarma>`: an attribute's karma price counts
    #: levels from 1 instead of the metatype minimum, so a troll's BOD 6 costs
    #: what a human's BOD 5 would (Chummer's `CharacterAttrib.TotalKarmaCost`).
    alternate_metatype_attribute_karma: bool = False
    #: `<compensateskillgroupkarmadifference>`: at chargen, the levels every
    #: skill of a group shares, bought one skill at a time with karma, are priced
    #: as the group would have been (`Skill.RangeCost`).
    compensate_skill_group_karma_difference: bool = False
    #: `<freemartialartspecialization>`: the specialization a martial art style
    #: offers (`<addskillspecializationoption>`) comes free
    #: (`AddImprovementCollection.skillspecializationoption`).
    free_martial_art_specialization: bool = False

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
    ignore_art: bool = False
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
    unarmed_improvements_apply_to_weapons: bool = False
    #: `<allowpointbuyspecializationsonkarmaskills>`: a skill bought wholly
    #: with karma may still take its specialization for a point. Off in the
    #: Standard presets, so Chummer makes that specialization karma too.
    allow_point_buy_specializations_on_karma_skills: bool = False
    #: `<allowcyberwareessdiscounts>`: a ware piece may be entered with a
    #: percentage off its essence (Neon Anarchy's presets)
    allow_cyberware_ess_discounts: bool = False
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

    #: Free knowledge points (Chummer's `KnowledgePointsExpression`, SR5
    #: p.99), rounded up.
    knowledge_points_expression: str = "({INTUnaug} + {LOGUnaug}) * 2"

    #: `<enforcecapacity>`: gear, armor and ware over their capacity are
    #: errors.
    enforce_capacity: bool = True
    #: `<restrictrecoil>`: of the accessories sharing an `<rcgroup>` (a
    #: bipod, a tripod and a gyro mount), only the best counts.
    restrict_recoil: bool = True
    #: `<dronearmormultiplierenabled>` / `<dronearmorflatnumber>`: a drone's
    #: armor tops out at (Body + Armor) times this instead of Body + Armor
    #: (Chummer's `Vehicle.MaxArmor`, Rigger 5.0 p.159).
    drone_armor_multiplier_enabled: bool = False
    drone_armor_multiplier: int = 2
    #: `<dronemods>`: Rigger 5.0's optional drone modification rules (R5
    #: p.122) — the `<optionaldrone>` mods, one shared pool of mod slots, no
    #: armor ceiling and the speed a heavily armored drone loses.
    drone_mods: bool = False
    #: `<dronemodsmaximumpilot>`: under those rules a drone's Pilot also stops
    #: at twice its printed value (`Vehicle.MaxPilot`).
    drone_mods_maximum_pilot: bool = False
    #: `<increasedimprovedabilitymodifier>`: Improved Ability tops out at 1.5x
    #: the boosted skill's learned rating instead of 0.5x (`Power.TotalMaximumLevels`).
    increased_improved_ability_modifier: bool = False
    #: `<mysaddppcareer>`: a mystic adept may buy more power points in career
    #: (`Character.MysAdeptAllowPPCareer`).
    mystic_adept_pp_in_career: bool = False
    #: `<spiritforcebasedontotalmag>`: a spirit's Force is capped by augmented
    #: MAG instead of the natural rating (`Character.MaxSpiritForce`).
    spirit_force_based_on_total_mag: bool = False

    # --- money ---------------------------------------------------------
    #: `<unrestrictednuyen>`: chargen karma may buy any amount of nuyen
    #: (Chummer's `TotalNuyenMaximumBP`); the karma budget is the limit.
    unrestricted_nuyen: bool = False
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
    #: `<redlinerexclusion>`: limb slots Redliner leaves out of its count.
    redliner_excludes: tuple[str, ...] = ("skull", "torso")
    #: Which `<prioritytable>` the priority rows come from. `priorities.xml`
    #: carries several — Standard, Prime Runner, Street Level — and a settings
    #: file picks one for the whole table.
    priority_table: str = DEFAULT_PRIORITY_TABLE

    #: #: `<allowfreegrids>`: lifestyles hand out their free grid subscriptions even with Hard Targets off.
    allow_free_grids: bool = False


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
