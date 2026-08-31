"""Ammunition: does a round fit a given weapon, and how does a loaded round
change the weapon's damage / AP / mode.

``_weapon_details_match`` evaluates Chummer's tiny ``weapon_details`` predicate
language (``contains(ammo, 'foo') and name != 'bar'``); the rest apply a loaded
round's ``weaponbonus`` to the resolved weapon row.
"""

from __future__ import annotations

import re
from typing import Any

from ..formulas import _add_signed_stat, _leading_int, _set_damage_type
from ..lookups import _item_by_id


def _weapon_details_match(weapon: dict[str, Any], expr: str) -> bool:
    raw = (expr or "").strip()
    if not raw:
        return True
    ammo = str(weapon.get("ammo") or "")
    name = str(weapon.get("name") or "")

    def _contains_ammo(match: re.Match[str]) -> str:
        return "True" if match.group(1) in ammo else "False"

    text = re.sub(r"contains\(\s*ammo\s*,\s*'([^']*)'\s*\)", _contains_ammo, raw)
    text = re.sub(r'contains\(\s*ammo\s*,\s*"([^"]*)"\s*\)', _contains_ammo, text)
    text = re.sub(r"name\s*!=\s*'([^']*)'", lambda m: "True" if name != m.group(1) else "False", text)
    text = re.sub(r"name\s*=\s*'([^']*)'", lambda m: "True" if name == m.group(1) else "False", text)
    text = re.sub(r"\band\b", "and", text)
    text = re.sub(r"\bor\b", "or", text)
    if not re.fullmatch(r"(?:True|False|and|or|\(|\)|\s)+", text):
        return False
    try:
        return bool(eval(text, {"__builtins__": {}}, {}))
    except Exception:
        return False


def ammo_fits_weapon(ammo: dict[str, Any], weapon: dict[str, Any]) -> bool:
    if (ammo.get("category") or "") != "Ammunition":
        return False
    details = str(ammo.get("weapon_details") or "").strip()
    if details:
        return _weapon_details_match(weapon, details)
    types = [part for part in (ammo.get("ammo_weapon_types") or []) if part]
    if not types:
        return False
    weapon_type = str(weapon.get("weapon_type") or "")
    return weapon_type in types


def _apply_ammo_bonus(weapon: dict[str, Any], bonus: dict[str, Any] | None) -> None:
    if not bonus:
        return
    if bonus.get("apreplace"):
        weapon["ap"] = str(bonus["apreplace"])
    elif bonus.get("ap"):
        weapon["ap"] = _add_signed_stat(str(weapon.get("ap") or ""), _leading_int(str(bonus.get("ap"))) or 0)
    if bonus.get("damagereplace"):
        weapon["damage"] = str(bonus["damagereplace"])
    elif bonus.get("damage"):
        weapon["damage"] = _add_signed_stat(
            str(weapon.get("damage") or ""), _leading_int(str(bonus.get("damage"))) or 0
        )
    if bonus.get("damagetype"):
        weapon["damage"] = _set_damage_type(str(weapon.get("damage") or ""), str(bonus["damagetype"]))
    if bonus.get("modereplace"):
        weapon["mode"] = str(bonus["modereplace"])


def _apply_loaded_ammo(weapon: dict[str, Any], ammo: dict[str, Any] | None) -> None:
    if not ammo:
        return
    add_id = str(ammo.get("add_weapon_id") or "")
    if add_id:
        spec = _item_by_id("weapons", add_id)
        if spec:
            if spec.get("damage"):
                weapon["damage"] = str(spec.get("damage") or "")
            if spec.get("ap"):
                weapon["ap"] = str(spec.get("ap") or "")
    _apply_ammo_bonus(weapon, ammo.get("weaponbonus"))


def _pick_loaded_ammo(kids: list[dict[str, Any]], loaded_id: str | None) -> dict[str, Any] | None:
    loadable = [kid for kid in kids if kid.get("ammo_weapon_types")]
    if not loadable:
        return None
    if loaded_id:
        for kid in loadable:
            if kid.get("id") == loaded_id:
                return kid
    return loadable[0]
