"""``Ctx`` — the working set threaded through the ``compute()`` phases.

``compute(state)`` builds one ``Ctx`` and each phase reads/writes ``ctx.*``.
Every field is typed and (bar ``state`` / ``data``) has a default so
``Ctx(state=..., data=...)`` constructs. The field set is the honest
top-to-bottom working set of the old monolithic ``compute()`` — see
``docs/refactor-compute-phases-plan.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...models import CharacterState
from ..bundle_types import (
    ContactsBundle,
    InitiationBundle,
    MartialBundle,
    MovementBundle,
    SkillMods,
    SkillPicks,
    SubmersionBundle,
    empty_contacts,
    empty_initiation,
    empty_martial,
    empty_movement,
    empty_skill_mods,
    empty_skill_picks,
    empty_submersion,
)


@dataclass
class Ctx:
    state: CharacterState
    data: dict[str, Any]

    # --- bootstrap -------------------------------------------------------
    is_karma: bool = False
    career: bool = False
    skill_rating_cap: int = 0
    skill_group_cap: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    attrs_spec: dict[str, Any] = field(default_factory=dict)
    talent: dict[str, Any] = field(default_factory=dict)
    sources: list[tuple[str, list[dict[str, Any]]]] = field(default_factory=list)

    # --- qualities / mentor -------------------------------------------------
    qualities: list[dict[str, Any]] = field(default_factory=list)
    free_quality_ids: list[str] = field(default_factory=list)
    quality_names: set[str] = field(default_factory=set)
    needs_mentor: bool = False
    mentor: dict[str, Any] = field(default_factory=dict)

    # --- ware ------------------------------------------------------------
    cyber_installed: list[dict[str, Any]] = field(default_factory=list)
    bio_installed: list[dict[str, Any]] = field(default_factory=list)
    installed: list[dict[str, Any]] = field(default_factory=list)
    ware_attr_bonus: dict[str, int] = field(default_factory=dict)

    # --- effects / binders ------------------------------------------------
    effects: dict[str, Any] = field(default_factory=dict)
    attr_max_bonus: dict[str, int] = field(default_factory=dict)
    limb_quality: dict[str, Any] | None = None
    special_key: str | None = None
    talent_start: int = 0
    enabled: set[str] = field(default_factory=set)

    # --- essence / attributes ------------------------------------------------
    ess: float = 0.0
    ess_lost: float = 0.0
    ess_lost_cyber: float = 0.0
    ess_lost_bio: float = 0.0
    ratings: dict[str, int] = field(default_factory=dict)

    # --- magic (initiation / submersion / foci / adept) --------------------
    initiation: InitiationBundle = field(default_factory=empty_initiation)
    submersion: SubmersionBundle = field(default_factory=empty_submersion)
    qi: dict[str, Any] = field(default_factory=dict)
    foci: dict[str, Any] = field(default_factory=dict)
    focus_limits: dict[str, Any] = field(default_factory=dict)
    adept: dict[str, Any] = field(default_factory=dict)
    enhancements: dict[str, Any] = field(default_factory=dict)
    attr_totals: dict[str, int] = field(default_factory=dict)

    # --- gear ----------------------------------------------------------------
    gear: dict[str, Any] = field(default_factory=dict)
    bmp_active: bool = False
    bmp_category: str = ""
    bmp_contact_id: str = ""
    active_drugs: list[dict[str, Any]] = field(default_factory=list)

    # --- totals ------------------------------------------------------------
    total: dict[str, int] = field(default_factory=dict)
    limb_replace: dict[str, Any] | None = None
    power_pool: float = 0.0
    power_spent: float = 0.0

    # --- magic / resonance -------------------------------------------------
    magic: dict[str, Any] = field(default_factory=dict)
    spirits: dict[str, Any] = field(default_factory=dict)
    resonance: dict[str, Any] = field(default_factory=dict)
    techno_sprites: dict[str, Any] = field(default_factory=dict)

    # --- priority points / nuyen -----------------------------------------
    special_from_meta: int = 0
    spent_physical: int = 0
    spent_special: int = 0
    attr_points: int = 0
    skill_points: int = 0
    group_points: int = 0
    group_spent: int = 0
    metatype_karma_cost: int = 0
    heritage_karma_cost: int = 0
    nuyen_karma_max: int = 0
    nuyen_pool: int = 0
    nuyen_spent: int = 0
    nuyen: int = 0

    # --- skills ---------------------------------------------------------
    skill_spent: int = 0
    skill_totals: dict[str, int] = field(default_factory=dict)
    skill_picks: SkillPicks = field(default_factory=empty_skill_picks)
    exotic: dict[str, Any] = field(default_factory=dict)
    knowledge: dict[str, Any] = field(default_factory=dict)
    know_spent: int = 0
    know_max: int = 0
    skill_mods: SkillMods = field(default_factory=empty_skill_mods)
    skillsofts: dict[str, Any] = field(default_factory=dict)
    expertises: list[dict[str, Any]] = field(default_factory=list)
    specs: dict[str, Any] = field(default_factory=dict)
    effective_skills: dict[str, int] = field(default_factory=dict)
    effective_knowledge: dict[str, int] = field(default_factory=dict)

    # --- karma totals -------------------------------------------------------
    karma_from_q: int = 0
    mystic_karma: int = 0
    extra_adept_karma: int = 0
    spell_karma: int = 0
    attr_karma: int = 0
    skill_buy_karma: int = 0
    knowledge_karma: int = 0
    spec_karma: int = 0
    career_adv_karma: int = 0
    career_adv_lines: list[dict[str, Any]] = field(default_factory=list)
    karma_pool: int = 0
    karma_spent: int = 0
    karma_left: int = 0

    # --- social ----------------------------------------------------------
    contacts: ContactsBundle = field(default_factory=empty_contacts)
    martial: MartialBundle = field(default_factory=empty_martial)
    karma_spend_lines: list[dict[str, Any]] = field(default_factory=list)
    nuyen_spend_lines: list[dict[str, Any]] = field(default_factory=list)
    quality_notoriety: int = 0
    notoriety_total: int = 0
    street_cred_total: int = 0
    public_awareness_total: int = 0

    # --- derived stats ----------------------------------------------------
    physical_limit: int = 0
    mental_limit: int = 0
    social_limit: int = 0
    cm_phys: int = 0
    cm_stun: int = 0
    initiative: int = 0
    initiative_dice: int = 0
    movement: MovementBundle = field(default_factory=empty_movement)

    # --- quality rules ----------------------------------------------------
    quality_report: dict[str, Any] = field(default_factory=dict)
    negative_quality_karma: int = 0
