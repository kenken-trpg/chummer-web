"""Armor and weapons: the mods on a suit, the ranges a gun prints, the skill
the importer matches it to and the clips it carries."""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog
from ..engine.gear.weapons.bonuses import weapon_skill_dictionary_key
from ._common import _flag, _html, _money
from .gear import _cost_for, _rounds


def _armors(derived: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """The finished rating, "+n" for one that stacks: the importer marks an
    armor with a "+" in it as an accessory. Mods stay inside the value and
    the price; the importer never reads `armormods`, so they are also listed
    in `notes`, which it takes as the item's description."""
    out = []
    for row in derived.get("armor_items") or []:
        name = str(row.get("name") or "")
        if not name:
            continue
        value = int(row.get("armor_value") or 0)
        category = str(row.get("category") or "")
        mods = _armor_mods(row, tr)
        out.append(
            {
                "guid": str(row.get("id") or ""),
                "sourceid": str(row.get("armor_id") or ""),
                "name": tr(name, "armor"),
                "name_english": name,
                "category": tr(category),
                "category_english": category,
                "armor": f"+{value}" if row.get("additive") else str(value),
                "rating": str(int(row.get("rating") or 0)),
                "avail": str(row.get("avail") or ""),
                "owncost": _money(row.get("nuyen")),
                "equipped": _flag(row.get("equipped")),
                "armormods": {"armormod": mods} if mods else None,
                "notes": _html("\n".join(mod["fullname"] for mod in mods)) if mods else None,
                "source": str(row.get("source") or ""),
                "page": str(row.get("page") or ""),
            }
        )
    return out


def _armor_mods(row: dict[str, Any], tr: Any) -> list[dict[str, Any]]:
    out = []
    for mod in row.get("mods") or []:
        name = str(mod.get("name") or "")
        if not name:
            continue
        rating = int(mod.get("rating") or 0)
        shown = tr(name, "armor")
        category = str(mod.get("category") or "")
        out.append(
            {
                "guid": str(mod.get("id") or ""),
                "sourceid": str(mod.get("mod_id") or ""),
                "name": shown,
                "name_english": name,
                "fullname": f"{shown} {rating}" if mod.get("rating_max") else shown,
                "fullname_english": f"{name} {rating}" if mod.get("rating_max") else name,
                "category": tr(category),
                "category_english": category,
                "armor": str(mod.get("armor") or "0"),
                "maxrating": str(int(mod.get("rating_max") or 0)),
                "rating": str(rating),
                "avail": str(mod.get("avail") or ""),
                "owncost": _money(mod.get("nuyen")),
                "included": _flag(mod.get("included")),
                "equipped": _flag(True),
                "wirelesson": _flag(mod.get("wireless")),
                "source": str(mod.get("source") or ""),
                "page": str(mod.get("page") or ""),
            }
        )
    return out


#: weapon categories with no ranges.xml entry of their own (the frontend's
#: `RANGE_CAT_ALIAS`)
_RANGE_ALIAS = {"Heavy Machine Guns": "Medium/Heavy Machinegun", "Medium Machine Guns": "Medium/Heavy Machinegun"}
_BANDS = ("short", "medium", "long", "extreme")


def _range_band(formula: object, strength: int) -> int | None:
    """A ranges.xml band ("5", "{STR}*10", "{STR}/2"; "-1" for none), the
    frontend's `evalRangeBand`."""
    text = str(formula or "").strip().replace("{STR}", str(strength))
    if not text or text == "-1":
        return None
    left, op, right = text.partition("*") if "*" in text else text.partition("/")
    try:
        value = float(left)
        if op == "*":
            value *= float(right)
        elif op == "/":
            value /= float(right)
    except ValueError:
        return None
    return int(value)


def _ranges(row: dict[str, Any], derived: dict[str, Any]) -> dict[str, str] | None:
    """The four bands as Chummer prints them ("0-5", "6-20", ...), with the
    STR the sheet uses: the importer reads the number after the dash, and
    only when all four are there."""
    category = str(row.get("category") or "")
    name = str(row.get("range") or "").strip() or _RANGE_ALIAS.get(category) or category
    bands = (catalog().get("weapon_ranges") or {}).get(name)
    if not bands:
        return None
    strength = int((derived.get("totals") or {}).get("STR") or 0)
    if row.get("useskill") == "Throwing Weapons":
        strength += int(derived.get("throw_range_str") or 0)
    highs = [_range_band(bands.get(key), strength) for key in _BANDS]
    if any(high is None for high in highs):
        return None
    tops = [int(high or 0) for high in highs]
    lows = [_range_band(bands.get("min"), strength) or 0, *(high + 1 for high in tops[:3])]
    return {key: f"{low}-{high}" for key, low, high in zip(_BANDS, lows, tops, strict=True)}


_PISTOLS = frozenset({"Tasers", "Holdouts", "Light Pistols", "Heavy Pistols"})


def _weapon_skill(row: dict[str, Any]) -> str | None:
    """The skill Chummer prints, which the importer lower-cases into the
    Foundry skill id ("Heavy Weapons" -> heavy_weapons). The engine's lookup
    falls back to Pistols; a category it does not know (exotic, laser) goes
    out blank instead, and the importer works those out from the category."""
    skill = weapon_skill_dictionary_key(row)
    if skill == "Pistols" and not row.get("useskill") and row.get("category") not in _PISTOLS:
        return None
    return skill


def _weapons(derived: dict[str, Any], tr: Any, owners: dict[str, str], owner: str = "") -> list[dict[str, Any]]:
    """The figures the sheet shows ({STR} already worked out by the engine).
    Those include what the accessories add, so the accessories go along
    with their own accuracy and RC at zero — Foundry would add a mod's on
    top."""
    cost_for = _cost_for()
    out = []
    for row in derived.get("weapons") or []:
        if owners.get(str(row.get("id") or ""), "") != owner:
            continue
        name = str(row.get("name") or "")
        if not name:
            continue
        category = str(row.get("category") or "")
        raw_mode = str(_noammo(row, "mode") or "").strip()
        mode = None if raw_mode in ("", "0", "-") else raw_mode
        accessories = [
            {
                "guid": str(acc.get("id") or ""),
                "sourceid": str(acc.get("accessory_id") or ""),
                "name": tr(str(acc["name"])),
                "name_english": str(acc["name"]),
                "mount": str(acc.get("mount") or "None"),
                "rating": str(int(acc.get("rating") or 0)),
                "accuracy": "0",
                "rc": "0",
                "conceal": "0",
                "avail": str(acc.get("avail") or ""),
                "owncost": _money(acc.get("nuyen")),
                "source": str(acc.get("source") or ""),
                "page": str(acc.get("page") or ""),
            }
            for acc in row.get("accessories") or []
            if acc.get("name")
        ]
        out.append(
            {
                "guid": str(row.get("id") or ""),
                "sourceid": str(row.get("weapon_id") or ""),
                "name": tr(name),
                "name_english": name,
                "category": tr(category),
                "category_english": category,
                "type": str(row.get("type") or ""),
                "skill": _weapon_skill(row),
                "rawaccuracy": str(row.get("accuracy") or "0"),
                "rawap": str(_noammo(row, "ap") or "0"),
                "damage_noammo_english": str(_noammo(row, "damage") or ""),
                "rawrc": str(row.get("rc") or "0"),
                "rawreach": str(row.get("reach") or "0"),
                "mode": mode,
                "mode_noammo": mode,
                "mode_english_noammo": mode,
                "ammo_english": str(row.get("ammo") or ""),
                "ranges": _ranges(row, derived),
                "conceal": str(row.get("conceal") or "0"),
                "qty": str(int(row.get("qty") or 1)),
                "avail": str(row.get("avail") or ""),
                "owncost": _money(row.get("nuyen")),
                "equipped": "True",
                "accessories": {"accessory": accessories},
                **_clips(row, tr, cost_for),
                "source": str(row.get("source") or ""),
                "page": str(row.get("page") or ""),
            }
        )
    return out


def _noammo(row: dict[str, Any], key: str) -> Any:
    """The weapon's value before its loaded round: Foundry adds the equipped
    clip's bonus on top."""
    return row.get(f"{key}_noammo", row.get(key))


def _clips(row: dict[str, Any], tr: Any, cost_for: dict[str, int]) -> dict[str, Any]:
    """The ammo stowed with the weapon: the importer makes each clip an ammo
    item, equips the one named `currentammo` and works out the spare clips
    from `availableammo`. Only a bonus that adds to the gun goes along —
    Foundry's ammo can't replace the damage or AP."""
    clips = []
    current = current_english = ""
    for kid in row.get("ammo_gear") or []:
        if kid.get("category") != "Ammunition" or not kid.get("name"):
            continue
        name = str(kid["name"])
        shown = str(kid.get("custom_name") or "") or tr(name, "gear")
        clip: dict[str, Any] = {
            "name": shown,
            "english_name": name,
            "count": str(_rounds(kid, cost_for)),
            "location": None,
            "id": str(kid.get("id") or ""),
        }
        bonus = kid.get("weaponbonus") or {}
        damage = "" if bonus.get("damagereplace") else str(bonus.get("damage") or "")
        damage += str(bonus.get("damagetype") or "")
        ap = "" if bonus.get("apreplace") else str(bonus.get("ap") or "")
        accuracy = str(bonus.get("accuracy") or "")
        if damage or ap or accuracy:
            clip["ammotype"] = {
                "weaponbonusap": ap,
                "weaponbonusap_english": ap,
                "weaponbonusacc": accuracy,
            }
            # the importer reads the damage only when this key is there
            if damage:
                clip["ammotype"]["weaponbonusdamage"] = damage
                clip["ammotype"]["weaponbonusdamage_english"] = damage
        clips.append(clip)
        if kid.get("loaded"):
            current, current_english = shown, name
    if not clips:
        return {}
    return {
        "clips": {"clip": clips},
        "currentammo": current,
        "currentammo_english": current_english,
        "availableammo": str(sum(int(clip["count"]) for clip in clips)),
    }
