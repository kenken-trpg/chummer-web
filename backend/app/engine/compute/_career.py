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
from ..bundle_types import GearBundle
from ..constants import (
    KARMA_ACTIVE_SKILL,
    KARMA_ATTRIBUTE,
    KARMA_KNOWLEDGE,
    KARMA_SKILL_GROUP,
    KARMA_SPECIALIZATION,
)
from ..karma import (
    _active_karma_mults,
    _filter_karma_rules,
    _group_floor_map,
    _karma_cost_with_category_mods,
    _matching_karma_rules,
    _skill_category_map,
    _skill_group_category_map,
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
    )


def career_raise_karma(
    state: CharacterState,
    baseline: CareerBaseline,
    skill_totals: dict[str, int],
    skills_data: dict[str, Any],
    *,
    effects: EffectsDict | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    """Karma to raise Priority/SumToTen characters from chargen snapshot to current ratings."""
    total = 0
    lines: list[dict[str, Any]] = []
    eff = effects or empty_effects()
    base_attrs = baseline.attributes or {}
    attr_flat = _filter_karma_rules(eff.get("attribute_karma_cost"), career=True)
    for key, rating in (state.attributes or {}).items():
        if key == "ESS":
            continue
        from_r = int(base_attrs.get(key, rating))
        to_r = int(rating or 0)
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            KARMA_ATTRIBUTE,
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
        cost = _karma_cost_with_category_mods(from_r, to_r, KARMA_SKILL_GROUP, mult_pct=mult)
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
            KARMA_ACTIVE_SKILL,
            mult_pct=mult,
            flat_rules=_matching_karma_rules(active_flat, cat),
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
            KARMA_KNOWLEDGE,
            mult_pct=mult,
            flat_rules=_matching_karma_rules(know_flat, cat),
            min_rules=_matching_karma_rules(know_min, cat),
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
            amount = max(1, int(math.ceil(KARMA_SPECIALIZATION * mult / 100.0)))
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
            KARMA_ACTIVE_SKILL,
            mult_pct=100,
            flat_rules=_matching_karma_rules(active_flat, ""),
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


def nuyen_spend_breakdown(
    cyber: list[dict[str, Any]],
    bio: list[dict[str, Any]],
    gear: GearBundle,
    *,
    qi_nuyen: int = 0,
    foci_nuyen: int = 0,
    spirits_nuyen: int = 0,
) -> list[dict[str, Any]]:
    buckets: list[tuple[str, int]] = [
        ("engine.spend.cyberware", sum(int(item.get("nuyen") or 0) for item in cyber)),
        ("engine.spend.bioware", sum(int(item.get("nuyen") or 0) for item in bio)),
        ("engine.spend.armor", sum(int(row.get("nuyen") or 0) for row in (gear.get("armor_items") or []))),
        ("engine.spend.armorMods", sum(int(row.get("nuyen") or 0) for row in (gear.get("armor_mods") or []))),
        ("engine.spend.weapons", sum(int(row.get("nuyen") or 0) for row in (gear.get("weapons") or []))),
        (
            "engine.spend.weaponAccessories",
            sum(int(row.get("nuyen") or 0) for row in (gear.get("weapon_accessories") or [])),
        ),
        ("engine.spend.commlinks", sum(int(row.get("nuyen") or 0) for row in (gear.get("commlinks") or []))),
        ("engine.spend.cyberdecks", sum(int(row.get("nuyen") or 0) for row in (gear.get("cyberdecks") or []))),
        ("engine.spend.rccs", sum(int(row.get("nuyen") or 0) for row in (gear.get("rccs") or []))),
        ("engine.spend.optics", sum(int(row.get("nuyen") or 0) for row in (gear.get("optics") or []))),
        ("engine.spend.sensors", sum(int(row.get("nuyen") or 0) for row in (gear.get("sensors") or []))),
        (
            "engine.spend.programs",
            sum(int(row.get("nuyen") or 0) for row in (gear.get("programs") or []) + (gear.get("apps") or [])),
        ),
        ("engine.spend.drones", sum(int(row.get("nuyen") or 0) for row in (gear.get("drones") or []))),
        ("engine.spend.vehicles", sum(int(row.get("nuyen") or 0) for row in (gear.get("vehicles") or []))),
        (
            "engine.spend.vehicleMods",
            sum(
                int(row.get("nuyen") or 0)
                for row in (gear.get("vehicle_mods") or []) + (gear.get("weapon_mounts") or [])
            ),
        ),
        ("engine.spend.otherGear", sum(int(row.get("nuyen") or 0) for row in (gear.get("gear") or []))),
        ("engine.spend.lifestyles", sum(int(row.get("nuyen") or 0) for row in (gear.get("lifestyles") or []))),
        ("engine.spend.qiFoci", int(qi_nuyen or 0)),
        ("engine.spend.foci", int(foci_nuyen or 0)),
        ("engine.spend.spirits", int(spirits_nuyen or 0)),
    ]
    return [{"kind": "nuyen", "notice": notice(key), "amount": amount} for key, amount in buckets if amount]
