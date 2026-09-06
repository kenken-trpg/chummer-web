"""Career-advancement helpers used by the economy phase (and re-exported
via ``app.engine`` for ``characters.py`` / tests): chargen baseline snapshot,
Priority/SumToTen raise-cost diff and the nuyen spend breakdown.
"""

from __future__ import annotations

import math
from typing import Any

from ...improvements import EffectsDict, empty_effects
from ...models import CareerBaseline, CharacterState
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
    _karma_raise_cost,
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
    for key, rating in (state.attributes or {}).items():
        if key == "ESS":
            continue
        from_r = int(base_attrs.get(key, rating))
        to_r = int(rating or 0)
        cost = _karma_raise_cost(from_r, to_r, KARMA_ATTRIBUTE)
        if cost:
            lines.append({"kind": "attribute", "label": f"能力値 {key} {from_r}→{to_r}", "amount": cost})
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
            lines.append({"kind": "skill_group", "label": f"技能グループ {group} {from_r}→{to_r}", "amount": cost})
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
            lines.append({"kind": "skill", "label": f"技能 {name} {from_r}→{to_r}", "amount": cost})
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
            lines.append({"kind": "knowledge", "label": f"知識 {name} {from_r}→{to_r}", "amount": cost})
            total += cost

    spec_mults = _active_karma_mults(eff.get("skill_category_spec_karma_cost_mult"), career=True)
    base_specs = set(baseline.skill_specializations or [])
    for name, spec in (state.skill_specializations or {}).items():
        if str(spec or "").strip() and name not in base_specs:
            cat = skill_cat_map.get(name) or str(know_cats.get(name) or catalog_know.get(name) or "")
            mult = int(spec_mults.get(cat, 100))
            amount = max(1, int(math.ceil(KARMA_SPECIALIZATION * mult / 100.0)))
            lines.append({"kind": "specialization", "label": f"専門化 {name}（{spec}）", "amount": amount})
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
            lines.append({"kind": "exotic", "label": f"特殊技能 {label} {from_r}→{to_r}", "amount": cost})
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
        ("サイバーウェア", sum(int(item.get("nuyen") or 0) for item in cyber)),
        ("バイオウェア", sum(int(item.get("nuyen") or 0) for item in bio)),
        ("防具", sum(int(row.get("nuyen") or 0) for row in (gear.get("armor_items") or []))),
        ("防具改造", sum(int(row.get("nuyen") or 0) for row in (gear.get("armor_mods") or []))),
        ("武器", sum(int(row.get("nuyen") or 0) for row in (gear.get("weapons") or []))),
        ("武器アクセサリ", sum(int(row.get("nuyen") or 0) for row in (gear.get("weapon_accessories") or []))),
        ("通信機", sum(int(row.get("nuyen") or 0) for row in (gear.get("commlinks") or []))),
        ("サイバーデッキ", sum(int(row.get("nuyen") or 0) for row in (gear.get("cyberdecks") or []))),
        ("RCC", sum(int(row.get("nuyen") or 0) for row in (gear.get("rccs") or []))),
        ("光学／音響", sum(int(row.get("nuyen") or 0) for row in (gear.get("optics") or []))),
        ("センサー", sum(int(row.get("nuyen") or 0) for row in (gear.get("sensors") or []))),
        (
            "プログラム",
            sum(int(row.get("nuyen") or 0) for row in (gear.get("programs") or []) + (gear.get("apps") or [])),
        ),
        ("ドローン", sum(int(row.get("nuyen") or 0) for row in (gear.get("drones") or []))),
        ("車両", sum(int(row.get("nuyen") or 0) for row in (gear.get("vehicles") or []))),
        (
            "車両改造",
            sum(
                int(row.get("nuyen") or 0)
                for row in (gear.get("vehicle_mods") or []) + (gear.get("weapon_mounts") or [])
            ),
        ),
        ("その他ギア", sum(int(row.get("nuyen") or 0) for row in (gear.get("gear") or []))),
        ("ライフスタイル", sum(int(row.get("nuyen") or 0) for row in (gear.get("lifestyles") or []))),
        ("気収束具", int(qi_nuyen or 0)),
        ("収束具", int(foci_nuyen or 0)),
        ("精霊", int(spirits_nuyen or 0)),
    ]
    return [{"kind": "nuyen", "label": label, "amount": amount} for label, amount in buckets if amount]
