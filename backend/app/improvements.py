from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

IMPLEMENTED = {
    "specificattribute",
    "armor",
    "conditionmonitor",
    "initiative",
    "initiativepass",
    "enabletab",
    "cyberseeker",
    "mentallimit",
    "sociallimit",
    "physicallimit",
    "skillgroup",
    "skillcategory",
    "specificskill",
    "selectskill",
    "adeptpowerpoints",
    "unlockskills",
    "damageresistance",
    "unarmeddv",
    "unarmeddvphysical",
    "magicianswaydiscount",
    "freequality",
    "selectmentorspirit",
    "focusbindingkarmacost",
    "skillattribute",
    "spellcategory",
    "firearmor",
    "coldarmor",
    "electricityarmor",
    "radiationresist",
    "toxincontactresist",
    "pathogencontactresist",
    "toxincontactimmune",
    "toxininhalationimmune",
    "pathogencontactimmune",
    "pathogeninhalationimmune",
    "restrictedgear",
    "limitmodifier",
}
SILENT_TAGS = {
    "disablequality",
    "selecttext",
    "selectweapon",
    "addgears",
    "addweapon",
    "limit",
    "selectspell",
    "selectpowers",
    "selectpower",
    "specificpower",
    "selecttradition",
    "selectrestricted",
    "activesoft",
    "knowsoft",
    "linguasoft",
    "weaponspecificdice",
}

SPECIAL_ARMOR_TAGS = {
    "firearmor": "fire",
    "coldarmor": "cold",
    "electricityarmor": "electricity",
    "radiationresist": "radiation",
    "toxincontactresist": "toxin_contact",
    "pathogencontactresist": "pathogen_contact",
}
IMMUNE_TAGS = {
    "toxincontactimmune": "toxin_contact",
    "toxininhalationimmune": "toxin_inhalation",
    "pathogencontactimmune": "pathogen_contact",
    "pathogeninhalationimmune": "pathogen_inhalation",
}
SPECIAL_ARMOR_KEYS = ("fire", "cold", "electricity", "radiation", "toxin_contact", "pathogen_contact")
IMMUNE_KEYS = ("toxin_contact", "toxin_inhalation", "pathogen_contact", "pathogen_inhalation")
LIMIT_KINDS = ("physical", "mental", "social")
LIMIT_KIND_ALIASES = {
    "physical": "physical",
    "physicallimit": "physical",
    "mental": "mental",
    "mentallimit": "mental",
    "social": "social",
    "sociallimit": "social",
}
LIMIT_CONDITION_JA = {
    "LimitCondition_TestSneakingThermal": "熱視覚／熱センサーに対する潜伏",
    "LimitCondition_SkillsActiveSneaking": "熱視覚／熱センサーに対する潜伏",
    "LimitCondition_Skillwires": "スキルワイヤ",
}

ATTR_ALIASES = {
    "BOD": "BOD",
    "BODY": "BOD",
    "AGI": "AGI",
    "AGILITY": "AGI",
    "REA": "REA",
    "REACTION": "REA",
    "STR": "STR",
    "STRENGTH": "STR",
    "CHA": "CHA",
    "CHARISMA": "CHA",
    "INT": "INT",
    "INTUITION": "INT",
    "LOG": "LOG",
    "LOGIC": "LOG",
    "WIL": "WIL",
    "WILLPOWER": "WIL",
    "EDG": "EDG",
    "EDGE": "EDG",
    "MAG": "MAG",
    "MAGIC": "MAG",
    "RES": "RES",
    "RESONANCE": "RES",
    "ESS": "ESS",
    "ESSENCE": "ESS",
}


def _replace_rating(value: Any, rating: int) -> Any:
    if value is None or isinstance(value, (int, float)):
        return value
    return str(value).replace("Rating", str(int(rating)))


def substitute_rating(nodes: list[dict[str, Any]], rating: int) -> list[dict[str, Any]]:
    out = []
    for node in nodes:
        copied = dict(node)
        if "value" in copied:
            copied["value"] = _replace_rating(copied["value"], rating)
        if "fields" in copied:
            copied["fields"] = {k: _replace_rating(v, rating) for k, v in (copied["fields"] or {}).items()}
        out.append(copied)
    return out


def _as_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, list):
        return str(value[0]) if value else default
    return str(value)


def _limit_kind(value: Any) -> str:
    raw = _as_text(value).strip().lower().replace(" ", "")
    return LIMIT_KIND_ALIASES.get(raw, "")


def limit_condition_label(condition: str) -> str:
    key = (condition or "").strip()
    if not key:
        return ""
    return LIMIT_CONDITION_JA.get(key, key)


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return int(value)
    raw = str(value).strip()
    try:
        return int(float(raw))
    except ValueError:
        return default


def empty_effects() -> dict[str, Any]:
    return {
        "attribute_bonus": {k: 0 for k in ATTR_ALIASES.values() if len(k) <= 3},
        "armor": 0,
        "cm_physical": 0,
        "cm_stun": 0,
        "initiative": 0,
        "initiative_dice": 0,
        "enabled_tabs": set(),
        "cyberseeker": [],
        "limit_physical": 0,
        "limit_mental": 0,
        "limit_social": 0,
        "skill_group_mods": [],
        "skill_category_mods": [],
        "skill_specific_mods": [],
        "adept_power_points": 0,
        "unlock_skills": [],
        "damage_resistance": 0,
        "unarmed_dv": 0,
        "unarmed_physical": False,
        "magicians_way": False,
        "free_qualities": [],
        "needs_mentor": False,
        "focus_binding": [],
        "skill_attribute_mods": [],
        "spell_category_mods": [],
        "special_armor": {key: 0 for key in SPECIAL_ARMOR_KEYS},
        "immunities": {key: False for key in IMMUNE_KEYS},
        "restricted_gear": [],
        "limit_modifiers": [],
        "unimplemented": [],
    }


def apply_bonus_nodes(nodes: list[dict[str, Any]], effects: dict[str, Any], source: str) -> None:
    for node in nodes:
        tag = node.get("tag", "")
        if tag not in IMPLEMENTED:
            if tag not in SILENT_TAGS:
                effects["unimplemented"].append({"source": source, "tag": tag})
            continue
        fields = node.get("fields") or {}
        if tag == "specificattribute":
            name = ATTR_ALIASES.get((fields.get("name") or "").upper())
            if name:
                effects["attribute_bonus"][name] = effects["attribute_bonus"].get(name, 0) + _as_int(
                    fields.get("bonus") or fields.get("val") or fields.get("value"), 0
                )
        elif tag == "armor":
            effects["armor"] += _as_int(node.get("value"))
        elif tag == "conditionmonitor":
            effects["cm_physical"] += _as_int(fields.get("physical"))
            effects["cm_stun"] += _as_int(fields.get("stun"))
        elif tag == "initiative":
            effects["initiative"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
        elif tag == "initiativepass":
            effects["initiative_dice"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
        elif tag == "enabletab":
            names = fields.get("name") or node.get("value") or ""
            values = names if isinstance(names, list) else [names]
            for raw in values:
                text = str(raw).strip()
                name = text.upper() if text.upper() in {"MAG", "RES"} else text.lower()
                if name:
                    effects["enabled_tabs"].add(name)
        elif tag == "cyberseeker":
            target = (node.get("value") or fields.get("name") or "").upper()
            if target:
                effects["cyberseeker"].append(target)
        elif tag == "mentallimit":
            effects["limit_mental"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
        elif tag == "sociallimit":
            effects["limit_social"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
        elif tag == "physicallimit":
            effects["limit_physical"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
        elif tag in {"skillgroup", "skillcategory"}:
            name = (fields.get("name") or node.get("value") or "").strip()
            bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
            if not name or bonus == 0:
                continue
            exclude = (fields.get("exclude") or "").strip()
            key = "skill_group_mods" if tag == "skillgroup" else "skill_category_mods"
            effects[key].append(
                {
                    "name": name,
                    "bonus": bonus,
                    "exclude": exclude,
                    "condition": (fields.get("condition") or "").strip(),
                    "source": source,
                }
            )
        elif tag == "adeptpowerpoints":
            effects["adept_power_points"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
        elif tag == "unlockskills":
            name = (node.get("attrs") or {}).get("name") or fields.get("name") or node.get("value") or ""
            name = str(name).strip()
            if name and name not in effects["unlock_skills"]:
                effects["unlock_skills"].append(name)
        elif tag == "damageresistance":
            effects["damage_resistance"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "unarmeddv":
            effects["unarmed_dv"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "unarmeddvphysical":
            effects["unarmed_physical"] = True
        elif tag == "magicianswaydiscount":
            effects["magicians_way"] = True
        elif tag == "freequality":
            qid = str(node.get("value") or fields.get("name") or "").strip()
            if qid and qid not in effects["free_qualities"]:
                effects["free_qualities"].append(qid)
        elif tag == "selectmentorspirit":
            effects["needs_mentor"] = True
        elif tag == "focusbindingkarmacost":
            effects["focus_binding"].append(
                {
                    "name": str(fields.get("name") or "").strip(),
                    "val": _as_int(fields.get("val") or fields.get("value")),
                    "extracontains": str(fields.get("extracontains") or "").strip(),
                    "source": source,
                }
            )
        elif tag == "specificskill":
            name = (fields.get("name") or node.get("value") or "").strip()
            bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
            if not name or bonus == 0:
                continue
            effects["skill_specific_mods"].append(
                {
                    "name": name,
                    "bonus": bonus,
                    "condition": (fields.get("condition") or "").strip(),
                    "source": source,
                }
            )
        elif tag == "skillattribute":
            name = (fields.get("name") or node.get("value") or "").strip().upper()
            bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
            if not name or bonus == 0:
                continue
            effects["skill_attribute_mods"].append(
                {
                    "name": name,
                    "bonus": bonus,
                    "condition": (fields.get("condition") or "").strip(),
                    "source": source,
                }
            )
        elif tag == "spellcategory":
            name = (fields.get("name") or node.get("value") or "").strip()
            bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
            if not name or bonus == 0:
                continue
            effects["spell_category_mods"].append(
                {
                    "name": name,
                    "bonus": bonus,
                    "condition": (fields.get("condition") or "").strip(),
                    "source": source,
                }
            )
        elif tag in SPECIAL_ARMOR_TAGS:
            key = SPECIAL_ARMOR_TAGS[tag]
            effects["special_armor"][key] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag in IMMUNE_TAGS:
            effects["immunities"][IMMUNE_TAGS[tag]] = True
        elif tag == "restrictedgear":
            effects["restricted_gear"].append(
                {
                    "availability": max(0, _as_int(fields.get("availability") or 24, 24)),
                    "amount": max(1, _as_int(fields.get("amount") or 1, 1)),
                    "source": source,
                }
            )
        elif tag == "limitmodifier":
            kind = _limit_kind(fields.get("limit") or node.get("value"))
            value = _as_int(fields.get("value") or node.get("value"))
            condition = _as_text(fields.get("condition") or "").strip()
            if not kind or value == 0:
                continue
            effects["limit_modifiers"].append(
                {
                    "limit": kind,
                    "value": value,
                    "condition": condition,
                    "condition_label": limit_condition_label(condition),
                    "source": source,
                }
            )


def special_armor_totals(effects: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: int(effects.get("special_armor", {}).get(key) or 0) for key in SPECIAL_ARMOR_KEYS},
        "immunities": {
            key: bool((effects.get("immunities") or {}).get(key)) for key in IMMUNE_KEYS
        },
    }


def compact_special_armor(effects: dict[str, Any]) -> dict[str, Any] | None:
    nums = {
        key: int(effects.get("special_armor", {}).get(key) or 0)
        for key in SPECIAL_ARMOR_KEYS
        if int(effects.get("special_armor", {}).get(key) or 0)
    }
    immunities = {
        key: True
        for key, value in (effects.get("immunities") or {}).items()
        if value
    }
    if not nums and not immunities:
        return None
    out: dict[str, Any] = dict(nums)
    if immunities:
        out["immunities"] = immunities
    return out


def special_armor_from_nodes(nodes: list[dict[str, Any]], rating: int = 1) -> dict[str, Any] | None:
    effects = empty_effects()
    apply_bonus_nodes(substitute_rating(nodes, rating), effects, "")
    return compact_special_armor(effects)


def compact_limit_modifiers(effects: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in effects.get("limit_modifiers") or []:
        kind = str(row.get("limit") or "")
        value = int(row.get("value") or 0)
        if kind not in LIMIT_KINDS or value == 0:
            continue
        condition = str(row.get("condition") or "")
        out.append(
            {
                "limit": kind,
                "value": value,
                "condition": condition,
                "condition_label": str(row.get("condition_label") or limit_condition_label(condition)),
                "source": str(row.get("source") or ""),
            }
        )
    return out


def limit_modifiers_from_nodes(nodes: list[dict[str, Any]], rating: int = 1) -> list[dict[str, Any]]:
    effects = empty_effects()
    apply_bonus_nodes(substitute_rating(nodes, rating), effects, "")
    return compact_limit_modifiers(effects)


def collect_effects(sources: list[tuple[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    effects = empty_effects()
    for source, nodes in sources:
        apply_bonus_nodes(nodes, effects, source)
    effects["enabled_tabs"] = sorted(effects["enabled_tabs"])
    return effects
