"""Modifiers that land on an already-resolved weapon row.

`compute` calls these after the rows exist: reach from a quality, unarmed DV
from a martial art, category DV from Killing Hands, accuracy from a smartlink.
They mutate the rows in place, because the row is the thing the sheet renders
and there is only one of it.

The `bind_*` pair is different in kind: those resolve a `selectskill` pick
(`weaponcategorydv` on a quality the user had to choose a skill for) into the
concrete bonus rows the appliers above then read.
"""

from __future__ import annotations

from typing import Any

from ....data_loader import catalog
from ....improvements import EffectsDict, empty_effects
from ....improvements.effect_rows import WeaponDvBonusRow
from ....models import CharacterState
from ...formulas import _add_leading_int, _add_weapon_dv, _leading_int
from ...selects import selectskill_options


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


def apply_weapon_category_dice(weapons: list[dict[str, Any]] | None, effects: EffectsDict | None) -> None:
    """``<weaponcategorydice>`` — a situational attack dice-pool bonus for a
    weapon category (e.g. Master Archer: Bows +1). Surfaced on the weapon row
    as ``category_dice`` for the sheet, alongside ``focus_dice``.
    """
    rows = list((effects or empty_effects()).get("weapon_category_dice") or [])
    if not weapons or not rows:
        return
    for weapon in weapons:
        category = str(weapon.get("category") or "")
        skill = weapon_skill_dictionary_key(weapon)
        dice = 0
        for row in rows:
            name = str(row.get("category") or "").strip()
            if name and (name == category or name == skill):
                dice += int(row.get("dice") or 0)
        if dice:
            weapon["category_dice"] = int(weapon.get("category_dice") or 0) + dice


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
