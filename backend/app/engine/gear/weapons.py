"""Weapon resolution: the public weapon row, weapons granted by gear/ware,
ware-limb attribute substitution, the weapon-bonus appliers driven by
``compute`` (reach / unarmed / category-DV / skill-accuracy), and the
weapon-accessory pipeline (recoil totals included).

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.
"""

from __future__ import annotations

import re
from typing import Any

from ...data_loader import catalog, eval_formula
from ...improvements import EffectsDict, empty_effects
from ...improvements.effect_rows import WeaponDvBonusRow
from ...models import CharacterState, WeaponAccessoryInstall
from ..formulas import _add_leading_int, _add_weapon_dv, _eval_attr_stat, _leading_int
from ..lookups import _item_by_id
from ..selects import selectskill_options
from ._common import (
    _clamp_rating,
    _leading_vehicle_stat,
    _limb_attr_effect,
    _pick_accessory_mount,
    accessory_fits_weapon,
)

_THROW_RECOIL_CATEGORIES = {"Throwing Weapons"}


def _public_weapon(
    spec: dict[str, Any],
    *,
    inst_id: str,
    qty: int,
    nuyen: int,
    loaded_ammo_id: str | None = None,
    from_gear: bool = False,
    source_gear_id: str | None = None,
    from_ware: bool = False,
    source_ware_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": inst_id,
        "weapon_id": spec["id"],
        "name": spec["name"],
        "category": spec.get("category") or "",
        "type": spec.get("type") or "",
        "weapon_type": spec.get("weapon_type") or "",
        "accuracy": spec.get("accuracy") or "",
        "reach": spec.get("reach") or "",
        "damage": spec.get("damage") or "",
        "ap": spec.get("ap") or "",
        "mode": spec.get("mode") or "",
        "rc": spec.get("rc") or "",
        "ammo": spec.get("ammo") or "",
        "conceal": spec.get("conceal") or "",
        "range": spec.get("range") or "",
        "alt_range": spec.get("alt_range") or "",
        "mounts": list(spec.get("mounts") or []),
        "qty": qty,
        "nuyen": nuyen,
        "accessories": [],
        "ammo_gear": [],
        "loaded_ammo_id": loaded_ammo_id or "",
        "from_gear": from_gear,
        "source_gear_id": source_gear_id or "",
        "from_ware": from_ware,
        "source_ware_id": source_ware_id or "",
        "useskill": spec.get("useskill") or "",
        "avail": spec.get("avail") or "",
        "source": spec.get("source") or "",
        "page": spec.get("page") or "",
        "limb_str": None,
        "limb_agi": None,
    }


def _append_gear_weapons(weapons: list[dict[str, Any]], gear_items: list[dict[str, Any]]) -> None:
    taken = {str(row.get("id") or "") for row in weapons}
    for item in gear_items:
        if item.get("parent_id"):
            continue
        spec_id = str(item.get("add_weapon_id") or "")
        if not spec_id:
            continue
        spec = _item_by_id("weapons", spec_id)
        if not spec:
            continue
        gear_id = str(item.get("id") or "")
        if not gear_id or gear_id in taken:
            continue
        weapons.append(
            _public_weapon(
                spec,
                inst_id=gear_id,
                qty=max(1, int(item.get("qty") or 1)),
                nuyen=int(item.get("nuyen") or 0),
                from_gear=True,
                source_gear_id=gear_id,
            )
        )
        taken.add(gear_id)


def _drone_mod_limb_attrs(
    mod_id: str,
    ware_by_id: dict[str, dict[str, Any]],
    state: CharacterState,
) -> tuple[int, int]:
    inst = next((row for row in list(state.vehicle_mods or []) if row.id == mod_id), None)
    if not inst:
        return 0, 0
    spec = _item_by_id("vehicle_mods", inst.mod_id)
    if not spec:
        return 0, 0
    name = (spec.get("name") or "").lower()
    if "arm" not in name and "leg" not in name:
        return 0, 0
    body = 0
    pilot = 0
    parent_id = inst.parent_id or ""
    for kind in ("drones", "vehicles"):
        host = next((row for row in list(getattr(state, kind) or []) if row.id == parent_id), None)
        if not host:
            continue
        host_spec = _item_by_id(kind, host.gear_id)
        if not host_spec:
            continue
        body = _leading_vehicle_stat(host_spec.get("body"))
        pilot = _leading_vehicle_stat(host_spec.get("pilot"))
        break
    str_val = max(body, 0)
    agi_val = max(pilot, 0)
    str_bonus = 0
    agi_bonus = 0
    for kid in ware_by_id.values():
        if kid.get("parent_id") != mod_id:
            continue
        effect = _limb_attr_effect(kid.get("name") or "")
        if not effect:
            continue
        attr, mode = effect
        rating = int(kid.get("rating") or 1)
        if attr == "STR":
            if mode == "set":
                str_val = rating
            else:
                str_bonus = rating
        else:
            if mode == "set":
                agi_val = rating
            else:
                agi_bonus = rating
    return (
        min(str_val + str_bonus, max(body * 2, 1)),
        min(agi_val + agi_bonus, max(pilot * 2, 1)),
    )


def _ware_weapon_attr_values(
    ware: dict[str, Any],
    ware_by_id: dict[str, dict[str, Any]],
    state: CharacterState,
    attr_totals: dict[str, int] | None,
) -> tuple[int, int, bool]:
    node: dict[str, Any] | None = ware
    seen: set[str] = set()
    while node:
        nid = str(node.get("id") or "")
        if nid in seen:
            break
        seen.add(nid)
        if node.get("limb_str") is not None:
            return int(node.get("limb_str") or 0), int(node.get("limb_agi") or 0), True
        parent_id = str(node.get("parent_id") or "")
        if not parent_id:
            break
        nxt = ware_by_id.get(parent_id)
        if nxt:
            node = nxt
            continue
        str_val, agi_val = _drone_mod_limb_attrs(parent_id, ware_by_id, state)
        if str_val or agi_val:
            return str_val, agi_val, True
        break
    totals = attr_totals or {}
    raw = state.attributes or {}
    return (
        int(totals.get("STR") or raw.get("STR") or 1),
        int(totals.get("AGI") or raw.get("AGI") or 1),
        False,
    )


def _apply_ware_weapon_attrs(
    weapon: dict[str, Any],
    ware: dict[str, Any],
    ware_by_id: dict[str, dict[str, Any]],
    state: CharacterState,
    attr_totals: dict[str, int] | None,
) -> None:
    str_val, agi_val, from_limb = _ware_weapon_attr_values(ware, ware_by_id, state, attr_totals)
    attrs = {"STR": str_val, "AGI": agi_val}
    for key in ("damage", "ap", "accuracy", "reach"):
        weapon[key] = _eval_attr_stat(str(weapon.get(key) or ""), attrs)
    if from_limb:
        weapon["limb_str"] = str_val
        weapon["limb_agi"] = agi_val


def _append_ware_weapons(
    weapons: list[dict[str, Any]],
    ware_items: list[dict[str, Any]],
    state: CharacterState,
    attr_totals: dict[str, int] | None = None,
) -> None:
    taken = {str(row.get("id") or "") for row in weapons}
    ware_by_id = {str(item.get("id") or ""): item for item in ware_items if item.get("id")}
    for item in ware_items:
        spec_id = str(item.get("add_weapon_id") or "")
        if not spec_id:
            continue
        spec = _item_by_id("weapons", spec_id)
        if not spec:
            continue
        ware_id = str(item.get("id") or "")
        if not ware_id or ware_id in taken:
            continue
        row = _public_weapon(
            spec,
            inst_id=ware_id,
            qty=1,
            nuyen=int(item.get("nuyen") or 0),
            from_ware=True,
            source_ware_id=ware_id,
        )
        _apply_ware_weapon_attrs(row, item, ware_by_id, state, attr_totals)
        weapons.append(row)
        taken.add(ware_id)


def apply_reach_bonus(weapons: list[dict[str, Any]] | None, reach: int) -> None:
    if not reach:
        return
    for weapon in weapons or []:
        if str(weapon.get("type") or "") != "Melee":
            continue
        weapon["reach"] = _add_leading_int(str(weapon.get("reach") or "0"), int(reach))


def _is_unarmed_weapon(weapon: dict[str, Any]) -> bool:
    category = str(weapon.get("category") or "")
    skill = str(weapon.get("useskill") or weapon.get("skill") or "")
    return category == "Unarmed" or skill == "Unarmed Combat"


def apply_unarmed_bonuses(
    weapons: list[dict[str, Any]] | None,
    unarmed_reach: int,
    unarmed_ap: int,
) -> None:
    if not unarmed_reach and not unarmed_ap:
        return
    for weapon in weapons or []:
        if not _is_unarmed_weapon(weapon):
            continue
        if unarmed_reach:
            weapon["reach"] = _add_leading_int(str(weapon.get("reach") or "0"), int(unarmed_reach))
        if unarmed_ap:
            weapon["ap"] = _add_leading_int(str(weapon.get("ap") or ""), int(unarmed_ap))


def apply_weapon_category_dv(weapons: list[dict[str, Any]] | None, effects: EffectsDict | None) -> None:
    rows = list((effects or empty_effects()).get("weapon_category_dv") or [])
    if not weapons or not rows:
        return
    for weapon in weapons:
        category = str(weapon.get("category") or "")
        if category == "Unarmed":
            category = "Unarmed Combat"
        useskill = str(weapon.get("useskill") or "").strip() or category
        bonus = 0
        for row in rows:
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            if name == category or name == useskill:
                bonus += int(row.get("bonus") or 0)
        if bonus:
            weapon["damage"] = _add_weapon_dv(str(weapon.get("damage") or ""), bonus)


def weapon_skill_dictionary_key(weapon: dict[str, Any]) -> str:
    """Map a weapon to its active skill name (Chummer Weapon.GetSkillDictionaryKey)."""
    useskill = str(weapon.get("useskill") or "").strip()
    if useskill:
        return useskill
    category = str(weapon.get("category") or "").strip()
    if category == "Special Weapons":
        category = str(weapon.get("range") or category).strip()
    mapping = {
        "Bows": "Archery",
        "Crossbows": "Archery",
        "Assault Rifles": "Automatics",
        "Carbines": "Automatics",
        "Machine Pistols": "Automatics",
        "Submachine Guns": "Automatics",
        "Blades": "Blades",
        "Clubs": "Clubs",
        "Improvised Weapons": "Clubs",
        "Assault Cannons": "Heavy Weapons",
        "Grenade Launchers": "Heavy Weapons",
        "Missile Launchers": "Heavy Weapons",
        "Light Machine Guns": "Heavy Weapons",
        "Medium Machine Guns": "Heavy Weapons",
        "Heavy Machine Guns": "Heavy Weapons",
        "Shotguns": "Longarms",
        "Sniper Rifles": "Longarms",
        "Sporting Rifles": "Longarms",
        "Throwing Weapons": "Throwing Weapons",
        "Unarmed": "Unarmed Combat",
    }
    return mapping.get(category, "Pistols")


def apply_weapon_skill_accuracy(weapons: list[dict[str, Any]] | None, effects: EffectsDict | None) -> None:
    rows = list((effects or empty_effects()).get("weapon_skill_accuracy") or [])
    if not weapons or not rows:
        return
    for weapon in weapons:
        skill = weapon_skill_dictionary_key(weapon)
        name = str(weapon.get("name") or "")
        bonus = 0
        for row in rows:
            target = str(row.get("name") or "").strip()
            if not target:
                continue
            if target == skill or target == name:
                bonus += int(row.get("bonus") or 0)
        if bonus:
            weapon["accuracy"] = _add_leading_int(str(weapon.get("accuracy") or ""), bonus)


def apply_smartlink_accuracy(weapons: list[dict[str, Any]] | None, effects: EffectsDict | None) -> None:
    """Add a smartgun system's Accuracy only when the character has a smartlink.

    SR5: a smartgun grants +2 Accuracy with an implanted smartlink, +1 with one
    built into an imaging device, nothing on its own. ``effects["smartlink"]``
    carries that value (0 / 1 / 2); the smartgun accessory's own Accuracy (2)
    was withheld in ``_resolve_weapon_accessories``.
    """
    smartlink = int((effects or empty_effects()).get("smartlink") or 0)
    if not weapons or smartlink <= 0:
        return
    for weapon in weapons:
        smartgun_acc = max(
            (
                _leading_int(acc.get("accuracy")) or 0
                for acc in weapon.get("accessories") or []
                if "Smartgun" in str(acc.get("name") or "")
            ),
            default=0,
        )
        if smartgun_acc:
            weapon["accuracy"] = _add_leading_int(str(weapon.get("accuracy") or ""), min(smartgun_acc, smartlink))


def _ensure_weapon_accessories(state: CharacterState) -> list[str]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("weapon_accessories") or []}
    by_name = {item["name"]: item for item in specs.values()}
    weapons = {item.id: item for item in state.weapons}
    weapon_specs = {item["id"]: item for item in catalog().get("weapons") or []}
    kept: list[WeaponAccessoryInstall] = []
    for inst in list(state.weapon_accessories or []):
        spec = specs.get(inst.accessory_id)
        parent = weapons.get(inst.parent_id or "")
        if not spec or not parent:
            if spec:
                warnings.append(f"{spec['name']} は武器に装着してください")
            continue
        kept.append(inst)
    have_included = {(row.parent_id, (specs.get(row.accessory_id) or {}).get("name")) for row in kept if row.included}
    extra: list[WeaponAccessoryInstall] = []
    for weapon in state.weapons:
        wspec = weapon_specs.get(weapon.weapon_id) or {}
        for gift_name in wspec.get("included") or []:
            child = by_name.get(gift_name)
            if not child or (weapon.id, child["name"]) in have_included:
                continue
            extra.append(
                WeaponAccessoryInstall(
                    accessory_id=child["id"],
                    parent_id=weapon.id,
                    included=True,
                )
            )
            have_included.add((weapon.id, child["name"]))
    preferred: dict[tuple[str, str], WeaponAccessoryInstall] = {}
    for inst in kept + extra:
        key = (inst.parent_id or "", inst.accessory_id)
        prev = preferred.get(key)
        if prev is None or (inst.included and not prev.included):
            preferred[key] = inst
    state.weapon_accessories = list(preferred.values())
    return warnings


def _apply_modify_ammo_capacity(weapon: dict[str, Any], formula: str | None) -> None:
    raw = str(formula or "").strip()
    if not raw:
        return
    ammo = str(weapon.get("ammo") or "").strip()
    match = re.match(r"^([+-]?\d+)(.*)$", ammo)
    if not match:
        return
    base = int(match.group(1))
    expr = raw[1:].strip() if raw.startswith("+") else raw
    delta = eval_formula(expr, 1, 0.0, extras={"Weapon": base, "weapon": base})
    weapon["ammo"] = f"{base + int(round(delta))}{match.group(2)}"


def _apply_recoil_totals(weapons: list[dict[str, Any]], attrs: dict[str, int]) -> dict[str, int]:
    """Fill weapon['rc_total'] the way Chummer does (SR5 p.175):

        total RC = (weapon base RC + fitted accessory RC) + ⌈STR ÷ 3⌉ + 1

    ``weapon['rc']`` already carries the base + accessory sum; here we add the
    universal free point and the Strength contribution. Melee weapons get 0.
    """
    str_val = max(0, int(attrs.get("STR") or 0))
    str_rc = -(-str_val // 3)  # ceil division
    for weapon in weapons:
        if (weapon.get("type") or "") == "Melee":
            weapon["rc_total"] = 0
            continue
        gun_rc = _leading_int(weapon.get("rc")) or 0
        weapon["rc_total"] = gun_rc + str_rc + 1
    return {"str": str_val, "str_rc": str_rc, "free": 1}


def _resolve_weapon_accessories(
    state: CharacterState,
    weapons: list[dict[str, Any]],
    special_modification_limit: int = 0,
) -> tuple[list[dict[str, Any]], int, list[str], list[str], int]:
    warnings = _ensure_weapon_accessories(state)
    errors: list[str] = []
    specs = {item["id"]: item for item in catalog().get("weapon_accessories") or []}
    weapon_specs = {item["id"]: item for item in catalog().get("weapons") or []}
    qty_by_id = {item.id: max(1, int(item.qty or 1)) for item in state.weapons}
    public: list[dict[str, Any]] = []
    kept: list[WeaponAccessoryInstall] = []
    nuyen = 0
    special_used = 0
    limit = max(0, int(special_modification_limit or 0))
    children: dict[str, list[WeaponAccessoryInstall]] = {}
    for inst in list(state.weapon_accessories or []):
        children.setdefault(inst.parent_id or "", []).append(inst)

    for weapon in weapons:
        used_mounts: set[str] = set()
        installed_names = {
            str((specs.get(row.accessory_id) or {}).get("name") or "") for row in children.get(weapon["id"]) or []
        }
        for inst in children.get(weapon["id"]) or []:
            spec = specs.get(inst.accessory_id)
            if not spec:
                continue
            rating = _clamp_rating(spec, inst.rating)
            inst.rating = rating
            names_without = installed_names - {spec["name"]}
            if not accessory_fits_weapon(spec, weapon, names_without):
                warnings.append(f"{spec['name']} は {weapon['name']} に装着できません")
                continue
            is_special = bool(spec.get("specialmodification"))
            special_cost = int(spec.get("special_modification_cost") or 0) if is_special else 0
            if is_special:
                if limit <= 0:
                    warnings.append(f"{spec['name']} には Special Modifications が必要です")
                    continue
                if special_used + special_cost > limit:
                    warnings.append(
                        f"Special Modifications の上限を超えています（{special_used + special_cost}/{limit}・{spec['name']}）"
                    )
                    continue
            mount = _pick_accessory_mount(list(weapon.get("mounts") or []), used_mounts, list(spec.get("mounts") or []))
            if mount is None:
                errors.append(f"{weapon['name']} のマウントが足りません（{spec['name']}）")
                mount = ""
            elif mount:
                used_mounts.add(mount)
            inst.mount = mount
            parent_unit = int(
                eval_formula(str((weapon_specs.get(str(weapon.get("weapon_id") or "")) or {}).get("cost") or "0"), 1, 0)
            )
            cost = (
                0
                if inst.included
                else int(eval_formula(str(spec.get("cost") or "0"), rating, 0, extras={"Weapon Cost": parent_unit}))
            )
            cost *= int(qty_by_id.get(weapon["id"]) or 1)
            nuyen += cost
            acc_bonus = {
                "accuracy": _leading_int(spec.get("accuracy")) or 0,
                "rc": _leading_int(spec.get("rc")) or 0,
                "conceal": _leading_int(spec.get("conceal")) or 0,
                "damage": _leading_int(spec.get("damage")) or 0,
                "ap": _leading_int(spec.get("ap")) or 0,
                "reach": _leading_int(spec.get("reach")) or 0,
            }
            # A smartgun system's Accuracy is conditional on a smartlink — held
            # back here and added by ``apply_smartlink_accuracy`` once the
            # smartlink improvement (implant or imaging device) is known.
            if "Smartgun" not in str(spec.get("name") or ""):
                weapon["accuracy"] = _add_leading_int(str(weapon.get("accuracy") or ""), acc_bonus["accuracy"])
            weapon["rc"] = _add_leading_int(str(weapon.get("rc") or "0") or "0", acc_bonus["rc"])
            weapon["conceal"] = _add_leading_int(str(weapon.get("conceal") or "0") or "0", acc_bonus["conceal"])
            weapon["damage"] = _add_leading_int(str(weapon.get("damage") or ""), acc_bonus["damage"])
            weapon["ap"] = _add_leading_int(str(weapon.get("ap") or ""), acc_bonus["ap"])
            if acc_bonus["reach"]:
                weapon["reach"] = _add_leading_int(str(weapon.get("reach") or "0") or "0", acc_bonus["reach"])
            _apply_modify_ammo_capacity(weapon, spec.get("modifyammocapacity"))
            if is_special:
                special_used += special_cost
            weapon["nuyen"] = int(weapon.get("nuyen") or 0) + cost
            kept.append(inst)
            public.append(
                {
                    "id": inst.id,
                    "accessory_id": spec["id"],
                    "name": spec["name"],
                    "parent_id": inst.parent_id,
                    "included": bool(inst.included),
                    "mount": mount,
                    "rating": rating,
                    "rating_max": int(spec.get("maxrating") or 0),
                    "nuyen": cost,
                    "accuracy": spec.get("accuracy") or "",
                    "rc": spec.get("rc") or "",
                    "avail": spec.get("avail") or "",
                    "source": spec.get("source") or "",
                    "page": spec.get("page") or "",
                    "specialmodification": is_special,
                    "special_modification_cost": special_cost,
                }
            )
        weapon["accessories"] = [item for item in public if item.get("parent_id") == weapon["id"]]
        weapon["mounts_used"] = sorted(used_mounts)

    state.weapon_accessories = kept
    return public, nuyen, warnings, errors, special_used


def bind_weapon_category_dv(
    effects: EffectsDict,
    qualities: list[dict[str, Any]],
    state: CharacterState,
    warnings: list[str],
) -> None:
    """Resolve weaponcategorydv selectskill picks into concrete category/skill DV bonuses."""
    by_name = {q["name"]: q for q in qualities}
    extras = state.quality_extras or {}
    resolved: list[WeaponDvBonusRow] = []
    for slot in effects.get("weapon_category_dv_slots") or []:
        source = str(slot.get("source") or "")
        bonus = int(slot.get("bonus") or 0)
        if not bonus:
            continue
        skills = [str(name).strip() for name in (slot.get("skills") or []) if str(name).strip()]
        fixed = str(slot.get("name") or "").strip()
        if slot.get("needs_select"):
            spec = by_name.get(source)
            if not spec:
                continue
            picked = str(extras.get(spec["id"]) or "").strip()
            if not picked:
                warnings.append(f"{source} の武器技能を選んでください")
                continue
            if skills and picked not in skills:
                warnings.append(f"{source} に {picked} は選べません")
                continue
            resolved.append({"name": picked, "bonus": bonus, "source": source})
        elif fixed:
            resolved.append({"name": fixed, "bonus": bonus, "source": source})
    effects["weapon_category_dv"] = resolved


def bind_weapon_skill_accuracy(
    effects: EffectsDict,
    qualities: list[dict[str, Any]],
    state: CharacterState,
    warnings: list[str],
    skills_data: dict[str, Any] | None = None,
) -> None:
    """Resolve weaponskillaccuracy selectskill picks into skill accuracy bonuses."""
    by_name = {q["name"]: q for q in qualities}
    extras = state.quality_extras or {}
    data = skills_data if skills_data is not None else catalog().get("skills") or {}
    resolved: list[WeaponDvBonusRow] = []
    for slot in effects.get("weapon_skill_accuracy_slots") or []:
        source = str(slot.get("source") or "")
        bonus = int(slot.get("bonus") or 0)
        if not bonus:
            continue
        fixed = str(slot.get("name") or "").strip()
        if slot.get("needs_select"):
            spec = by_name.get(source)
            if not spec:
                continue
            picked = str(extras.get(spec["id"]) or "").strip()
            if not picked:
                warnings.append(f"{source} の技能を選んでください")
                continue
            attrs = dict(slot.get("select_attrs") or {})
            options = list(spec.get("select_options") or [])
            if not options and attrs:
                options = selectskill_options(
                    {
                        "limittoskill": attrs.get("limittoskill") or "",
                        "limittocategory": attrs.get("limittocategory") or attrs.get("skillcategory") or "",
                        "excludecategory": attrs.get("excludecategory") or "",
                        "knowledgeskills": str(attrs.get("knowledgeskills") or "").lower() == "true",
                    },
                    data,
                    {},
                )
            if options and picked not in options:
                warnings.append(f"{source} に {picked} は選べません")
                continue
            resolved.append({"name": picked, "bonus": bonus, "source": source})
        elif fixed:
            resolved.append({"name": fixed, "bonus": bonus, "source": source})
    effects["weapon_skill_accuracy"] = resolved
