"""Armor modifications and the worn-armor total.

``_resolve_armor_mods`` walks each armor's plugins — capacity accounting,
fit rules, cost, armor bonus, wireless — and collects their ``<bonus>`` nodes;
``_recompute_worn_armor`` then folds equipped pieces into a single armor rating
(highest body + additive layers, per SR5 p.169).
"""

from __future__ import annotations

import re
from typing import Any

from ...data_loader import catalog, eval_formula
from ...improvements import (
    limit_modifiers_from_nodes,
    special_armor_from_nodes,
    substitute_rating,
)
from ...models import ArmorModInstall, CharacterState
from ..formulas import parse_armor_value
from ._common import _clamp_rating


def armor_plugin_capacity(
    expr: str | None,
    rating: int,
    extras: dict[str, int | float] | None = None,
) -> float:
    raw = (expr or "").strip()
    if not raw:
        return 0.0
    fixed = re.fullmatch(r"FixedValues\((.+)\)", raw, re.I)
    if fixed:
        parts = [p.strip() for p in fixed.group(1).split(",")]
        idx = max(0, min(len(parts) - 1, int(rating) - 1))
        return armor_plugin_capacity(parts[idx], rating, extras)
    if raw.startswith("[") and raw.endswith("]") and "/" not in raw:
        inner = raw[1:-1]
        return eval_formula(inner, rating, 0.0, extras)
    return eval_formula(raw, rating, 0.0, extras)


def armor_mod_fits(
    spec: dict[str, Any],
    armor: dict[str, Any],
    installed_names: set[str] | None = None,
) -> bool:
    names = {str(n) for n in (installed_names or set())}
    required_names = [str(n) for n in (spec.get("required_names") or []) if n]
    if required_names and armor.get("name") not in required_names:
        return False
    required_mods = [str(n) for n in (spec.get("required_mods") or []) if n]
    if required_mods and any(name not in names for name in required_mods):
        return False
    category = str(spec.get("category") or "General")
    allowed = {str(c) for c in (armor.get("addmodcategories") or []) if c}
    if category == "General":
        return True
    if category in allowed:
        return True
    return category == str(armor.get("category") or "")


def _ensure_armor_mods(state: CharacterState) -> list[str]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("armor_mods") or []}
    by_name = {item["name"]: item for item in specs.values()}
    armors = {item.id: item for item in state.armor}
    armor_specs = {item["id"]: item for item in catalog().get("armor") or []}
    kept: list[ArmorModInstall] = []
    for inst in list(state.armor_mods or []):
        spec = specs.get(inst.mod_id)
        parent = armors.get(inst.parent_id or "")
        if not spec or not parent:
            if spec:
                warnings.append(f"{spec['name']} は防具に装着してください")
            continue
        kept.append(inst)
    have = {(row.parent_id, (specs.get(row.mod_id) or {}).get("name")) for row in kept}
    extra: list[ArmorModInstall] = []
    for armor in state.armor:
        aspec = armor_specs.get(armor.armor_id) or {}
        for gift in aspec.get("included_mods") or []:
            child = by_name.get(gift.get("name"))
            if not child or (armor.id, child["name"]) in have:
                continue
            extra.append(
                ArmorModInstall(
                    mod_id=child["id"],
                    parent_id=armor.id,
                    included=True,
                    rating=int(gift.get("rating") or 1),
                )
            )
            have.add((armor.id, child["name"]))
    state.armor_mods = kept + extra
    return warnings


def _resolve_armor_mods(
    state: CharacterState,
    armor_items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[str], list[str], list[tuple[str, list[dict[str, Any]]]]]:
    warnings = _ensure_armor_mods(state)
    errors: list[str] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    specs = {item["id"]: item for item in catalog().get("armor_mods") or []}
    armor_specs = {item["id"]: item for item in catalog().get("armor") or []}
    public: list[dict[str, Any]] = []
    kept: list[ArmorModInstall] = []
    nuyen = 0
    children: dict[str, list[ArmorModInstall]] = {}
    for inst in list(state.armor_mods or []):
        children.setdefault(inst.parent_id or "", []).append(inst)

    for item in armor_items:
        used = 0.0
        cap_bonus = 0.0
        seen_names: set[str] = set()
        seen_unique: set[str] = set()
        item["mod_armor"] = 0
        cap_max_base = eval_formula(str(item.get("armorcapacity") or "0"), int(item.get("rating") or 1), 0)
        parent_unit = int(
            eval_formula(
                str((armor_specs.get(str(item.get("armor_id") or "")) or {}).get("cost") or "0"),
                int(item.get("rating") or 1),
                0,
            )
        )
        for inst in children.get(item["id"]) or []:
            spec = specs.get(inst.mod_id)
            if not spec:
                continue
            if inst.included:
                rating = max(1, int(inst.rating or 1))
            else:
                rating = _clamp_rating(spec, inst.rating)
            inst.rating = rating
            if spec["name"] in seen_names or (spec.get("unique") and spec["unique"] in seen_unique):
                warnings.append(f"{spec['name']} は {item['name']} に重複して装着できません")
                continue
            names_without = seen_names - {spec["name"]}
            if not armor_mod_fits(spec, item, names_without):
                warnings.append(f"{spec['name']} は {item['name']} に装着できません")
                continue
            cap_cost = (
                0.0
                if inst.included
                else armor_plugin_capacity(
                    str(spec.get("armorcapacity") or ""),
                    rating,
                    extras={"Capacity": cap_max_base},
                )
            )
            extra, _additive = parse_armor_value(str(spec.get("armor") or "0"), rating)
            cost = (
                0
                if inst.included
                else int(eval_formula(str(spec.get("cost") or "0"), rating, 0, extras={"Armor Cost": parent_unit}))
            )
            nuyen += cost
            if cap_cost < 0:
                cap_bonus += -cap_cost
            else:
                used += cap_cost
            if extra:
                item["mod_armor"] = int(item.get("mod_armor") or 0) + extra
            item["nuyen"] = int(item.get("nuyen") or 0) + cost
            seen_names.add(spec["name"])
            if spec.get("unique"):
                seen_unique.add(str(spec["unique"]))
            inst.wireless = bool(inst.wireless)
            mod_has_wireless = bool(spec.get("wirelessbonus"))
            wireless_on = mod_has_wireless and inst.wireless
            display_nodes = list(spec.get("bonus") or [])
            if wireless_on:
                display_nodes = display_nodes + list(spec.get("wirelessbonus") or [])
            if item.get("equipped"):
                nodes = substitute_rating(display_nodes, rating)
                if nodes:
                    bonus_sources.append((spec["name"], nodes))
            kept.append(inst)
            row: dict[str, Any] = {
                "id": inst.id,
                "mod_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "General",
                "parent_id": inst.parent_id,
                "included": bool(inst.included),
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "nuyen": cost,
                "capacity_cost": int(cap_cost) if cap_cost == int(cap_cost) else cap_cost,
                "armor": spec.get("armor") or "0",
                "unique": spec.get("unique") or "",
                "wireless": inst.wireless,
                "has_wireless": mod_has_wireless,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
            special = special_armor_from_nodes(display_nodes, rating)
            if special:
                row["special_armor"] = special
            limits = limit_modifiers_from_nodes(display_nodes, rating)
            if limits:
                row["limit_modifiers"] = limits
            public.append(row)
        cap_max = cap_max_base + cap_bonus
        item["capacity_used"] = int(used) if used == int(used) else used
        item["capacity_max"] = int(cap_max) if cap_max == int(cap_max) else cap_max
        item["mods"] = [row for row in public if row.get("parent_id") == item["id"]]
        extra = int(item.get("mod_armor") or 0)
        if extra:
            item["armor_value"] = int(item.get("armor_value") or 0) + extra
        if used > cap_max + 1e-9:
            errors.append(f"{item['name']} の容量超過（{item['capacity_used']:g}/{item['capacity_max']:g}）")
    state.armor_mods = kept
    return public, nuyen, warnings, errors, bonus_sources


def _recompute_worn_armor(armor_items: list[dict[str, Any]]) -> tuple[int, str, list[str]]:
    warnings: list[str] = []
    base_values: list[tuple[str, int]] = []
    add_total = 0
    for item in armor_items:
        if not item.get("equipped"):
            item["contributes"] = 0
            continue
        value = int(item.get("armor_value") or 0)
        if item.get("additive"):
            add_total += value
            item["contributes"] = value
        else:
            base_values.append((str(item.get("name") or ""), value))
    worn_name = ""
    worn_base = 0
    if base_values:
        worn_name, worn_base = max(base_values, key=lambda row: row[1])
        if len(base_values) > 1:
            warnings.append("防具本体は一番高い1着だけをアーマーに加算しています")
    for item in armor_items:
        if not item.get("equipped"):
            item["contributes"] = 0
        elif item.get("additive"):
            item["contributes"] = int(item.get("armor_value") or 0)
        else:
            item["contributes"] = int(item.get("armor_value") or 0) if item.get("name") == worn_name else 0
    return worn_base + add_total, worn_name, warnings
