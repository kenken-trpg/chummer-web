"""The weapon-accessory pipeline, and the recoil arithmetic that falls out of it.

An accessory can change almost anything about the weapon it mounts on — its
accuracy, its recoil compensation, its ammo capacity, the mounts still free —
and some are included with the weapon rather than bought. Recoil totals are
computed here rather than in `bonuses.py` because progressive recoil depends on
the compensation the accessories contribute.
"""

from __future__ import annotations

import re
from typing import Any

from ....data_loader import catalog, eval_formula
from ....models import CharacterState, WeaponAccessoryInstall
from ...formulas import _add_leading_int, _leading_int
from .._common import _clamp_rating, _pick_accessory_mount, accessory_fits_weapon


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
