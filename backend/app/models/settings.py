"""The Chummer settings file and per-character options."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CharacterOptions(BaseModel):
    redliner_torso: bool = False
    redliner_skull: bool = False


class SettingsState(BaseModel):
    """A Chummer settings file, as much of one as this app honours.

    Chummer's `<settings>` carries ~160 house-rule knobs. This holds the ones
    the engine can act on — the enabled books, the build budget, the karma
    price list and the chargen caps — plus the name for the pulldown and a
    list of what had to be ignored. See docs/plans/settings-plan.md.

    `books` is the list of enabled `<source>` codes. **Empty means
    unrestricted**, not "no books": a character saved before this field
    existed, or one built without picking a preset, must keep seeing the whole
    catalog rather than suddenly owning gear from disabled books.
    """

    name: str = ""
    books: list[str] = Field(default_factory=list)
    #: Which `<prioritytable>` in `priorities.xml` the rows come from —
    #: Standard, Prime Runner, Street Level, or one custom data adds.
    priority_table: str = Field(default="Standard", max_length=100)

    # Every knob below is `None` when the settings file did not change it, so
    # an unset field keeps the printed SR5 value. `app.rules.rules_for` folds
    # them into a `Rules`; see `app/settings_file.py` for the XML side.
    sum_to_ten: int | None = None
    chargen_karma: int | None = None
    karma_chargen_pool: int | None = None
    karma_attribute: int | None = None
    karma_active_skill: int | None = None
    karma_skill_group: int | None = None
    karma_knowledge: int | None = None
    karma_specialization: int | None = None
    karma_knowledge_specialization: int | None = None
    karma_spell: int | None = None
    karma_complex_form: int | None = None
    karma_enhancement: int | None = None
    karma_mystic_pp: int | None = None
    karma_martial_technique: int | None = None
    #: The first level of a skill, priced apart from the rest
    #: (`<karmanewactiveskill>` and friends; Chummer's `RangeCost`).
    karma_new_active_skill: int | None = None
    karma_new_knowledge_skill: int | None = None
    karma_new_skill_group: int | None = None
    #: Karma per point of Force to bond a focus, by kind
    #: (`<karmaweaponfocus>` and friends; Chummer's `Focus.BindingKarmaCost`).
    karma_alchemical_focus: int | None = None
    karma_banishing_focus: int | None = None
    karma_binding_focus: int | None = None
    karma_centering_focus: int | None = None
    karma_counterspelling_focus: int | None = None
    karma_disenchanting_focus: int | None = None
    karma_flexible_signature_focus: int | None = None
    karma_masking_focus: int | None = None
    karma_power_focus: int | None = None
    karma_qi_focus: int | None = None
    karma_ritual_spellcasting_focus: int | None = None
    karma_spell_shaping_focus: int | None = None
    karma_spellcasting_focus: int | None = None
    karma_summoning_focus: int | None = None
    karma_sustaining_focus: int | None = None
    karma_weapon_focus: int | None = None
    karma_spirit: int | None = None
    karma_carryover: int | None = None
    karma_initiation_flat: int | None = None
    karma_initiation_per_grade: int | None = None
    karma_submersion_flat: int | None = None
    karma_submersion_per_grade: int | None = None
    quality_karma_limit: int | None = None
    chargen_skill_max: int | None = None
    chargen_knowledge_skill_max: int | None = None
    chargen_attributes_at_max: int | None = None
    career_skill_max: int | None = None
    career_knowledge_skill_max: int | None = None
    chargen_avail_max: int | None = None
    min_initiative_dice: int | None = None
    max_initiative_dice: int | None = None
    min_coldsim_initiative_dice: int | None = None
    max_coldsim_initiative_dice: int | None = None
    min_hotsim_initiative_dice: int | None = None
    max_hotsim_initiative_dice: int | None = None
    min_astral_initiative_dice: int | None = None
    max_astral_initiative_dice: int | None = None
    #: `<limbcount>` / `<excludelimbslot>`: how many limbs a cyberlimb's
    #: STR / AGI is averaged across, and a slot left out of that average
    limb_count: int | None = None
    exclude_limb_slot: str | None = Field(default=None, max_length=20)
    #: `<cyberlimbattributebonuscap>`: the most a cyberlimb's STR / AGI rises
    #: above its Customization; `<dontusecyberlimbcalculation>`: the body's
    #: STR / AGI ignores the cyberlimb average
    cyberlimb_attribute_bonus_cap: int | None = None
    dont_use_cyberlimb_calculation: bool | None = None
    #: `<knowledgepointsexpression>`, kept only when it is attribute tokens
    #: and arithmetic (`app.engine.formulas.eval_attribute_expression`)
    knowledge_points_expression: str | None = Field(default=None, max_length=200)
    karma_to_nuyen: int | None = None
    priority_karma_nuyen_base: int | None = None
    #: `<metatypecostskarmamultiplier>`: a Karma build pays the metatype's
    #: karma times this.
    metatype_costs_karma_multiplier: int | None = None
    #: `<contactpointsexpression>`'s multiplier: free contact points are
    #: unaugmented CHA times this (3 in Standard, 6 in Prime Runner).
    contact_free_mult: int | None = None
    #: `<exceednegativequalities>`: negative qualities may pass the karma
    #: limit at chargen; `<exceednegativequalitiesnobonus>`: the part past it
    #: gives no karma.
    exceed_negative_qualities: bool | None = None
    exceed_negative_qualities_no_bonus: bool | None = None
    #: `<exceedpositivequalities>`: positive qualities may pass the limit.
    exceed_positive_qualities: bool | None = None
    #: `<dontdoublequalities>` / `<dontdoublequalityrefunds>`
    dont_double_quality_purchases: bool | None = None
    dont_double_quality_refunds: bool | None = None
    #: `<usecalculatedpublicawareness>`
    use_calculated_public_awareness: bool | None = None
    #: `<noarmorencumbrance>` / `<uncappedarmoraccessorybonuses>`
    no_armor_encumbrance: bool | None = None
    uncapped_armor_accessory_bonuses: bool | None = None
    #: `<esslossreducesmaximumonly>` / `<donotroundessenceinternally>`
    ess_loss_reduces_maximum_only: bool | None = None
    dont_round_essence_internally: bool | None = None
    #: `<multiplyrestrictedcost>` / `<restrictedcostmultiplier>` and the
    #: forbidden pair: what an R / F item bought in career costs, times.
    multiply_restricted_cost: bool | None = None
    restricted_cost_multiplier: int | None = None
    multiply_forbidden_cost: bool | None = None
    forbidden_cost_multiplier: int | None = None
    #: `<allowinitiationincreatemode>`
    allow_initiation_in_create_mode: bool | None = None
    #: `<usepointsonbrokengroups>` / `<breakskillgroupsincreatemode>`
    use_points_on_broken_groups: bool | None = None
    strict_skill_groups_in_create_mode: bool | None = None
    #: `<enforcecapacity>` / `<restrictrecoil>` / `<unrestrictednuyen>`
    enforce_capacity: bool | None = None
    restrict_recoil: bool | None = None
    unrestricted_nuyen: bool | None = None
    #: `<cyberlegmovement>`: two cyberlegs set the AGI movement runs off
    cyberleg_movement: bool | None = None
    #: `<allowpointbuyspecializationsonkarmaskills>`
    allow_point_buy_specializations_on_karma_skills: bool | None = None
    #: `<dronearmormultiplierenabled>`
    drone_armor_multiplier_enabled: bool | None = None
    #: `<dronearmorflatnumber>`
    drone_armor_multiplier: int | None = None
    #: `<alternatemetatypeattributekarma>`
    alternate_metatype_attribute_karma: bool | None = None
    #: `<compensateskillgroupkarmadifference>`
    compensate_skill_group_karma_difference: bool | None = None
    #: `<increasedimprovedabilitymodifier>`
    increased_improved_ability_modifier: bool | None = None
    #: `<mysaddppcareer>`
    mystic_adept_pp_in_career: bool | None = None
    #: `<spiritforcebasedontotalmag>`
    spirit_force_based_on_total_mag: bool | None = None
    #: The attribute capping bound spirits / registered sprites
    #: (`<boundspiritexpression>` / `<registeredspriteexpression>`).
    bound_spirit_attr: str | None = Field(default=None, max_length=3)
    registered_sprite_attr: str | None = Field(default=None, max_length=3)
    banned_ware_grades: list[str] = Field(default_factory=list)
    #: `<customdatadirectorynames>`, enabled ones only, in the order the file
    #: gave them — order decides who wins when two directories edit the same
    #: entry, so it is not sorted.
    customdata: list[str] = Field(default_factory=list)
    #: Content hash of the custom-data files this character was built against.
    #: The client sends the files once and this token thereafter; see
    #: `app/customdata.py`.
    dataset: str = ""
    #: Tags the file changed away from Chummer's Standard that this app does
    #: not implement. Surfaced as a warning rather than swallowed — a house
    #: rule silently dropped is worse than one the sheet says it ignored.
    unsupported: list[str] = Field(default_factory=list)
