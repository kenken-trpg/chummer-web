"""Career-advancement helpers used by the economy phase (and re-exported
via ``app.engine`` for ``characters.py`` / tests): chargen baseline snapshot,
Priority/SumToTen raise-cost diff and the nuyen spend breakdown.
"""

from __future__ import annotations

import math
from typing import Any

from ...improvements import EffectsDict, empty_effects
from ...models import CareerBaseline, CharacterState
from ...notices import notice, term
from ...rules import current_rules
from ..bundle_types import GearBundle
from ..karma import (
    _active_karma_mults,
    _filter_karma_rules,
    _group_floor_map,
    _karma_cost_with_category_mods,
    _matching_karma_rules,
    _skill_category_map,
    _skill_group_category_map,
    group_first_level,
)


def snapshot_career_baseline(state: CharacterState) -> CareerBaseline:
    return CareerBaseline(
        attributes={str(k): int(v) for k, v in (state.attributes or {}).items()},
        skills={str(k): int(v) for k, v in (state.skills or {}).items()},
        skill_groups={str(k): int(v) for k, v in (state.skill_groups or {}).items()},
        knowledge_skills={str(k): int(v) for k, v in (state.knowledge_skills or {}).items()},
        skill_specializations=sorted(
            str(name) for name, spec in (state.skill_specializations or {}).items() if str(spec or "").strip()
        ),
        exotic_skills={
            str(row.id): int(row.rating or 0) for row in (state.exotic_skills or []) if getattr(row, "id", None)
        },
        quality_ids=[str(qid) for qid in state.quality_ids or []],
        item_ids=sorted({str(row.id) for field in _ITEM_FIELDS for row in getattr(state, field) or []}),
    )


#: The `CharacterState` lists whose rows a career purchase is told apart by:
#: things bought with nuyen, for the Restricted / Forbidden markup (lifestyles
#: are rent, not a buy), and the spirits / sprites chargen paid karma for.
_ITEM_FIELDS = (
    "spirits",
    "sprites",
    "cyberware",
    "bioware",
    "qi_foci",
    "foci",
    "armor",
    "armor_mods",
    "weapons",
    "weapon_accessories",
    "commlinks",
    "cyberdecks",
    "rccs",
    "optics",
    "programs",
    "apps",
    "sensors",
    "drones",
    "vehicles",
    "gear",
    "custom_drugs",
    "vehicle_mods",
    "weapon_mounts",
)

#: The published rows `restricted_markup` looks at, by `GearBundle` key.
_GEAR_ROW_KEYS = (
    "armor_items",
    "armor_mods",
    "weapons",
    "weapon_accessories",
    "commlinks",
    "cyberdecks",
    "rccs",
    "optics",
    "programs",
    "apps",
    "sensors",
    "drones",
    "vehicles",
    "vehicle_mods",
    "weapon_mounts",
    "gear",
    "custom_drugs",
)


def restricted_markup(baseline: CareerBaseline | None, rows: list[dict[str, Any]]) -> int:
    """Extra nuyen for Restricted / Forbidden things bought after chargen.

    Chummer multiplies the price of an R / F item as it is bought in career
    (`<multiplyrestrictedcost>` and the forbidden twin); what came through
    chargen is never marked up. So a row counts when its id is not in the
    baseline. A row bolted onto another new row is skipped: Chummer charges
    the whole assembly once, at the parent's availability."""
    rules = current_rules()
    factors = {"R": rules.career_restricted_cost_multiplier, "F": rules.career_forbidden_cost_multiplier}
    if baseline is None or baseline.item_ids is None or factors == {"R": 1, "F": 1}:
        return 0
    old = set(baseline.item_ids)
    new_ids = {str(row.get("id")) for row in rows if row.get("id") and str(row.get("id")) not in old}
    extra = 0
    for row in rows:
        row_id = str(row.get("id") or "")
        if not row_id or row_id in old or str(row.get("parent_id") or "") in new_ids:
            continue
        factor = factors.get(str(row.get("avail_suffix") or ""), 1)
        extra += int(row.get("nuyen") or 0) * (factor - 1)
    return extra


def career_raise_karma(
    state: CharacterState,
    baseline: CareerBaseline,
    skill_totals: dict[str, int],
    skills_data: dict[str, Any],
    *,
    effects: EffectsDict | None = None,
    ratings: dict[str, int] | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    """Karma to raise Priority/SumToTen characters from chargen snapshot to current ratings.

    ``ratings`` are the attribute ratings compute settled on (``state.attributes``
    otherwise), the same ones the baseline is taken from."""
    total = 0
    lines: list[dict[str, Any]] = []
    eff = effects or empty_effects()
    base_attrs = baseline.attributes or {}
    attr_flat = _filter_karma_rules(eff.get("attribute_karma_cost"), career=True)
    for key, rating in (state.attributes if ratings is None else ratings).items():
        if key == "ESS":
            continue
        from_r = int(base_attrs.get(key, rating))
        to_r = int(rating or 0)
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            current_rules().karma_attribute,
            flat_rules=_matching_karma_rules(attr_flat, key),
        )
        if cost:
            lines.append(
                {
                    "kind": "attribute",
                    "notice": notice("engine.spend.attribute", name=key, before=from_r, after=to_r),
                    "amount": cost,
                }
            )
            total += cost

    group_cat_map = _skill_group_category_map(skills_data)
    group_mults = _active_karma_mults(eff.get("skill_group_category_karma_cost_mult"), career=True)
    base_groups = baseline.skill_groups or {}
    for group, rating in (state.skill_groups or {}).items():
        from_r = int(base_groups.get(group, 0))
        to_r = int(rating or 0)
        cat = group_cat_map.get(group, "")
        mult = int(group_mults.get(cat, 100))
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            current_rules().karma_skill_group,
            mult_pct=mult,
            first_level=group_first_level(from_r, to_r),
        )
        if cost:
            lines.append(
                {
                    "kind": "skill_group",
                    "notice": notice("engine.spend.skillGroup", name=term(group), before=from_r, after=to_r),
                    "amount": cost,
                }
            )
            total += cost

    base_floors = _group_floor_map(base_groups, skills_data)
    now_floors = _group_floor_map(dict(state.skill_groups or {}), skills_data)
    base_skills = baseline.skills or {}
    skill_cat_map = _skill_category_map(skills_data)
    karma_mults = _active_karma_mults(eff.get("skill_category_karma_cost_mult"), career=True)
    active_flat = _filter_karma_rules(eff.get("active_skill_karma_cost"), career=True)
    for name, rating in (skill_totals or {}).items():
        from_r = max(int(base_skills.get(name, 0)), int(base_floors.get(name, 0)))
        from_r = max(from_r, int(now_floors.get(name, 0)))
        to_r = int(rating or 0)
        cat = skill_cat_map.get(name, "")
        mult = int(karma_mults.get(cat, 100))
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            current_rules().karma_active_skill,
            mult_pct=mult,
            flat_rules=_matching_karma_rules(active_flat, cat),
            first_level=current_rules().karma_new_active_skill,
        )
        if cost:
            lines.append(
                {
                    "kind": "skill",
                    "notice": notice("engine.spend.skill", name=term(name), before=from_r, after=to_r),
                    "amount": cost,
                }
            )
            total += cost

    base_know = baseline.knowledge_skills or {}
    natives = set(state.native_languages or [])
    know_flat = _filter_karma_rules(
        list(eff.get("skill_category_karma_cost") or []) + list(eff.get("knowledge_skill_karma_cost") or []),
        career=True,
    )
    know_min = _filter_karma_rules(eff.get("knowledge_skill_karma_cost_min"), career=True)
    know_cats = dict(state.knowledge_categories or {})
    catalog_know = {
        str(s.get("name") or ""): str(s.get("category") or "") for s in (skills_data.get("knowledge") or [])
    }
    for name, rating in (state.knowledge_skills or {}).items():
        if name in natives:
            continue
        cat = str(know_cats.get(name) or catalog_know.get(name) or "Street")
        mult = int(karma_mults.get(cat, 100))
        from_r = int(base_know.get(name, 0))
        to_r = int(rating or 0)
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            current_rules().karma_knowledge,
            mult_pct=mult,
            flat_rules=_matching_karma_rules(know_flat, cat),
            min_rules=_matching_karma_rules(know_min, cat),
            first_level=current_rules().karma_new_knowledge_skill,
        )
        if cost:
            lines.append(
                {
                    "kind": "knowledge",
                    "notice": notice("engine.spend.knowledge", name=term(name), before=from_r, after=to_r),
                    "amount": cost,
                }
            )
            total += cost

    spec_mults = _active_karma_mults(eff.get("skill_category_spec_karma_cost_mult"), career=True)
    base_specs = set(baseline.skill_specializations or [])
    for name, spec in (state.skill_specializations or {}).items():
        if str(spec or "").strip() and name not in base_specs:
            cat = skill_cat_map.get(name) or str(know_cats.get(name) or catalog_know.get(name) or "")
            mult = int(spec_mults.get(cat, 100))
            price = (
                current_rules().karma_specialization
                if name in skill_cat_map
                else current_rules().karma_knowledge_specialization
            )
            amount = max(1, int(math.ceil(price * mult / 100.0)))
            lines.append(
                {
                    "kind": "specialization",
                    "notice": notice("engine.spend.specialization", name=term(name), spec=term(str(spec))),
                    "amount": amount,
                }
            )
            total += amount

    base_exotic = baseline.exotic_skills or {}
    for row in state.exotic_skills or []:
        rid = str(getattr(row, "id", "") or "")
        if not rid:
            continue
        from_r = int(base_exotic.get(rid, 0))
        to_r = int(row.rating or 0)
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            current_rules().karma_active_skill,
            mult_pct=100,
            flat_rules=_matching_karma_rules(active_flat, ""),
            first_level=current_rules().karma_new_active_skill,
        )
        if cost:
            label = str(getattr(row, "name", None) or getattr(row, "skill", None) or "Exotic")
            lines.append(
                {
                    "kind": "exotic",
                    "notice": notice("engine.spend.exotic", name=term(label), before=from_r, after=to_r),
                    "amount": cost,
                }
            )
            total += cost
    return total, lines


#: (`nuyen_by_bucket` key, message key), in the order the sidebar lists them.
#: Every bucket the gear engine records must appear here, or the money would
#: vanish from the breakdown while still counting against the total —
#: `test_nuyen_breakdown` holds the two together. The message keys are spelled
#: out rather than built from the bucket name so `test_notice_keys` can still
#: see them.
_GEAR_SPEND_ORDER = (
    ("armor", "engine.spend.armor"),
    ("armorMods", "engine.spend.armorMods"),
    ("weapons", "engine.spend.weapons"),
    ("weaponAccessories", "engine.spend.weaponAccessories"),
    ("commlinks", "engine.spend.commlinks"),
    ("cyberdecks", "engine.spend.cyberdecks"),
    ("rccs", "engine.spend.rccs"),
    ("optics", "engine.spend.optics"),
    ("sensors", "engine.spend.sensors"),
    ("programs", "engine.spend.programs"),
    ("drones", "engine.spend.drones"),
    ("vehicles", "engine.spend.vehicles"),
    ("vehicleMods", "engine.spend.vehicleMods"),
    ("otherGear", "engine.spend.otherGear"),
    ("customDrugs", "engine.spend.customDrugs"),
    ("lifestyles", "engine.spend.lifestyles"),
)


def nuyen_spend_breakdown(
    cyber: list[dict[str, Any]],
    bio: list[dict[str, Any]],
    gear: GearBundle,
    *,
    qi_nuyen: int = 0,
    foci_nuyen: int = 0,
    spirits_nuyen: int = 0,
    markup_nuyen: int = 0,
) -> list[dict[str, Any]]:
    """The sidebar's "where the nuyen went", as lines that add up to what was
    spent.

    The gear half comes from the tally `resolve_gear` kept while it was
    counting, not from re-adding the rows it published: a thing bolted onto
    something else has its price folded into the row it is bolted to, so the
    rows do not partition the money and adding them up counts some of it twice.
    """
    by_bucket = gear.get("nuyen_by_bucket") or {}
    buckets: list[tuple[str, int]] = [
        ("engine.spend.cyberware", sum(int(item.get("nuyen") or 0) for item in cyber)),
        ("engine.spend.bioware", sum(int(item.get("nuyen") or 0) for item in bio)),
        *((message, int(by_bucket.get(bucket) or 0)) for bucket, message in _GEAR_SPEND_ORDER),
        ("engine.spend.qiFoci", int(qi_nuyen or 0)),
        ("engine.spend.foci", int(foci_nuyen or 0)),
        ("engine.spend.spirits", int(spirits_nuyen or 0)),
        ("engine.spend.restrictedMarkup", int(markup_nuyen or 0)),
    ]
    return [{"kind": "nuyen", "notice": notice(key), "amount": amount} for key, amount in buckets if amount]
