"""The full ``<bonus>`` dispatch chain, verbatim from the pre-split
``apply_bonus_nodes``. Commits 3-6 of the improvements plan carve domain
slices out of here into ``nodes/{stats,skills,magic,social}.py``; whatever
has not been carved yet still lives in this fallback.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import parse_select_power_slot
from .._common import (
    ATTR_ALIASES,
    IMMUNE_TAGS,
    SPECIAL_ARMOR_TAGS,
    SPELL_DEFENSE_RESIST_TAGS,
    TEST_MOD_TAGS,
    _as_int,
    _as_text,
    _bonus_int,
    _limit_kind,
    limit_condition_label,
)


def apply(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: dict[str, Any], source: str) -> bool:
    """Apply one already-IMPLEMENTED bonus node. Return True if ``tag`` matched."""
    for _once in (True,):
        if tag == "specificattribute":
            name = ATTR_ALIASES.get((fields.get("name") or "").upper())
            if name:
                bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"), 0)
                if bonus:
                    effects["attribute_bonus"][name] = effects["attribute_bonus"].get(name, 0) + bonus
                if fields.get("max") not in (None, ""):
                    effects["attribute_max_mods"][name] = int(effects["attribute_max_mods"].get(name) or 0) + _as_int(
                        fields.get("max")
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
        elif tag == "enableattribute":
            names = fields.get("name") or node.get("value") or ""
            values = names if isinstance(names, list) else [names]
            for raw in values:
                attr = ATTR_ALIASES.get(str(raw).strip().upper())
                if attr in {"MAG", "RES"}:
                    effects["enabled_tabs"].add(attr)
                elif attr:
                    effects["enabled_tabs"].add(attr.lower())
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
        elif tag == "unarmedreach":
            effects["unarmed_reach"] += _bonus_int(node, fields)
        elif tag == "unarmedap":
            effects["unarmed_ap"] += _bonus_int(node, fields)
        elif tag == "magicianswaydiscount":
            effects["magicians_way"] = True
        elif tag == "freequality":
            qid = str(node.get("value") or fields.get("name") or "").strip()
            if qid and qid not in effects["free_qualities"]:
                effects["free_qualities"].append(qid)
        elif tag == "addqualities":
            raw = fields.get("addquality") or node.get("value") or ""
            names = raw if isinstance(raw, list) else [raw]
            for name in names:
                text = str(name).strip()
                if text and text not in effects["add_qualities"]:
                    effects["add_qualities"].append(text)
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
        elif tag == "spelldicepool":
            name = (fields.get("name") or fields.get("id") or node.get("value") or "").strip()
            bonus = _as_int(fields.get("val") or fields.get("bonus") or fields.get("value") or node.get("value"))
            if bonus == 0:
                continue
            effects["spell_dice_pool"].append(
                {
                    "name": name,
                    "id": str(fields.get("id") or "").strip(),
                    "bonus": bonus,
                    "source": source,
                }
            )
        elif tag == "actiondicepool":
            attrs = node.get("attrs") or {}
            category = str(attrs.get("category") or fields.get("category") or "").strip()
            name = str(fields.get("name") or "").strip()
            # Codeslinger XML has empty value; SR5 grants +2 to a chosen Matrix action.
            bonus = _as_int(node.get("value") or fields.get("val") or fields.get("bonus") or fields.get("value"), 0)
            if bonus == 0:
                bonus = 2
            effects["action_dice_pools"].append(
                {
                    "category": category,
                    "name": name,
                    "bonus": bonus,
                    "source": source,
                    "needs_action": not bool(name),
                }
            )
        elif tag == "spellresistance":
            effects["spell_resistance"] += _bonus_int(node, fields)
        elif tag in SPELL_DEFENSE_RESIST_TAGS:
            key = SPELL_DEFENSE_RESIST_TAGS[tag]
            effects["spell_defense_resist"][key] += _bonus_int(node, fields)
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
        elif tag == "skillwire":
            effects["skillwires"] = max(
                int(effects.get("skillwires") or 0),
                _as_int(node.get("value") or fields.get("val") or fields.get("bonus")),
            )
        elif tag == "skillsoftaccess":
            effects["skilljack"] = max(
                int(effects.get("skilljack") or 0),
                _as_int(node.get("value") or fields.get("val") or fields.get("bonus")),
            )
        elif tag == "livingpersona":
            persona = effects.setdefault(
                "living_persona",
                {"attack": 0, "sleaze": 0, "dataprocessing": 0, "firewall": 0},
            )
            for key in ("attack", "sleaze", "dataprocessing", "firewall"):
                persona[key] = int(persona.get(key) or 0) + _as_int(fields.get(key))
        elif tag == "matrixinitiativediceadd":
            effects["matrix_initiative_dice"] = int(effects.get("matrix_initiative_dice") or 0) + _as_int(
                node.get("value") or fields.get("bonus") or fields.get("val")
            )
        elif tag == "reach":
            effects["reach"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "lifestylecost":
            effects["lifestyle_cost"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "notoriety":
            effects["notoriety"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "fame":
            effects["fame"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "publicawareness":
            effects["public_awareness"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "essencepenalty":
            # Negative values mean ESS loss (e.g. -1).
            effects["essence_penalty"] += abs(_as_int(node.get("value") or fields.get("val") or fields.get("bonus")))
        elif tag == "essencepenaltyt100":
            effects["essence_penalty"] += (
                abs(_as_int(node.get("value") or fields.get("val") or fields.get("bonus"))) / 100.0
            )
        elif tag == "essencepenaltymagonlyt100":
            effects["essence_penalty_mag_exempt"] += (
                abs(_as_int(node.get("value") or fields.get("val") or fields.get("bonus"))) / 100.0
            )
        elif tag == "walkmultiplier":
            category = str(fields.get("category") or "Ground").strip() or "Ground"
            effects["walk_multiplier"][category] = int(effects["walk_multiplier"].get(category) or 0) + _as_int(
                fields.get("val") or fields.get("bonus") or node.get("value")
            )
        elif tag == "runmultiplier":
            category = str(fields.get("category") or "Ground").strip() or "Ground"
            effects["run_multiplier"][category] = int(effects["run_multiplier"].get(category) or 0) + _as_int(
                fields.get("val") or fields.get("bonus") or node.get("value")
            )
        elif tag == "movementreplace":
            category = str(fields.get("category") or "Ground").strip() or "Ground"
            speed = str(fields.get("speed") or "walk").strip().lower() or "walk"
            effects["movement_replace"][(category, speed)] = _as_int(
                fields.get("val") or fields.get("bonus") or node.get("value")
            )
        elif tag == "sprintbonus":
            category = str(fields.get("category") or "Ground").strip() or "Ground"
            effects["sprint_bonus"][category] = int(effects["sprint_bonus"].get(category) or 0) + _as_int(
                fields.get("val") or fields.get("bonus") or node.get("value")
            )
        elif tag == "fatigueresist":
            effects["fatigue_resist"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag in TEST_MOD_TAGS:
            key = TEST_MOD_TAGS[tag]
            effects["test_mods"][key] = int(effects["test_mods"].get(key) or 0) + _as_int(
                node.get("value") or fields.get("val") or fields.get("bonus")
            )
        elif tag == "selectattributes":
            nested = node.get("nested") or {}
            vals = nested.get("selectattribute") or []
            if not isinstance(vals, list):
                vals = [vals]
            exclude: list[str] = []
            max_bonus = 1
            for raw in vals:
                text = str(raw).strip()
                attr = ATTR_ALIASES.get(text.upper())
                if attr:
                    exclude.append(attr)
                elif text:
                    max_bonus = _as_int(text, max_bonus)
            # Also accept structured fields if present.
            for key in ("excludeattribute", "exclude"):
                raw_ex = fields.get(key)
                if not raw_ex:
                    continue
                items = raw_ex if isinstance(raw_ex, list) else [raw_ex]
                for item in items:
                    attr = ATTR_ALIASES.get(str(item).strip().upper())
                    if attr and attr not in exclude:
                        exclude.append(attr)
            if fields.get("max"):
                max_bonus = _as_int(fields.get("max"), max_bonus)
            effects["attribute_selects"].append(
                {
                    "exclude": exclude,
                    "max": max(1, max_bonus),
                    "source": source,
                }
            )
        elif tag == "physicalcmrecovery":
            effects["cm_recovery_physical"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "stuncmrecovery":
            effects["cm_recovery_stun"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "addesstophysicalcmrecovery":
            effects["cm_recovery_physical_add_ess"] = True
        elif tag == "addesstostuncmrecovery":
            effects["cm_recovery_stun_add_ess"] = True
        elif tag == "skilldisable":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["disabled_skills"]:
                effects["disabled_skills"].append(name)
        elif tag == "skillgroupdisable":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["disabled_skill_groups"]:
                effects["disabled_skill_groups"].append(name)
        elif tag == "skillgroupcategorydisable":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["disabled_skill_group_categories"]:
                effects["disabled_skill_group_categories"].append(name)
        elif tag == "skillgroupdisablechoice":
            # Applied in engine from quality_extras (selected skill group name).
            pass
        elif tag == "blockskillcategorydefaulting":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["blocked_default_categories"]:
                effects["blocked_default_categories"].append(name)
        elif tag == "nativelanguagelimit":
            effects["native_language_limit_bonus"] += _as_int(
                node.get("value") or fields.get("val") or fields.get("bonus")
            )
        elif tag == "knowledgeskillpoints":
            effects["knowledge_skill_points"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "prototypetranshuman":
            effects["prototype_transhuman_ess"] = round(
                float(effects.get("prototype_transhuman_ess") or 0)
                + float(_as_int(node.get("value") or fields.get("val") or fields.get("bonus"), 0)),
                4,
            )
        elif tag == "burnoutsway":
            effects["burnout_way"] = True
        elif tag == "selectquality":
            raw = fields.get("quality") or node.get("value") or []
            options = [str(item).strip() for item in (raw if isinstance(raw, list) else [raw]) if str(item).strip()]
            if options:
                effects["select_quality_slots"].append({"source": source, "options": options})
        elif tag == "activeskillkarmacost":
            effects["active_skill_karma_cost"].append(
                {
                    "name": str(fields.get("name") or "").strip(),
                    "val": _as_int(fields.get("val")),
                    "min": _as_int(fields.get("min")),
                    "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
                    "condition": str(fields.get("condition") or ""),
                }
            )
        elif tag == "knowledgeskillkarmacost":
            effects["knowledge_skill_karma_cost"].append(
                {
                    "name": str(fields.get("name") or "").strip(),
                    "val": _as_int(fields.get("val")),
                    "min": _as_int(fields.get("min")),
                    "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
                    "condition": str(fields.get("condition") or ""),
                }
            )
        elif tag == "knowledgeskillkarmacostmin":
            effects["knowledge_skill_karma_cost_min"].append(
                {
                    "name": str(fields.get("name") or "").strip(),
                    "val": _as_int(fields.get("val"), 1),
                    "min": _as_int(fields.get("min")),
                    "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
                    "condition": str(fields.get("condition") or ""),
                }
            )
        elif tag == "skillcategoryspecializationkarmacostmultiplier":
            name = str(fields.get("name") or node.get("value") or "").strip()
            if name:
                effects["skill_category_spec_karma_cost_mult"].append(
                    {
                        "name": name,
                        "val": _as_int(fields.get("val") or fields.get("bonus"), 100),
                        "condition": str(fields.get("condition") or ""),
                    }
                )
        elif tag == "skillgroupcategorykarmacostmultiplier":
            name = str(fields.get("name") or node.get("value") or "").strip()
            if name:
                effects["skill_group_category_karma_cost_mult"].append(
                    {
                        "name": name,
                        "val": _as_int(fields.get("val") or fields.get("bonus"), 100),
                        "condition": str(fields.get("condition") or ""),
                    }
                )

        elif tag == "nuyenmaxbp":
            effects["nuyen_max_bp"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "nuyenamt":
            # Conditional nuyen (e.g. Stolen Gear) is ignored until that subsystem exists.
            attrs = node.get("attrs") or {}
            if attrs.get("condition"):
                continue
            effects["nuyen_amt"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "trustfund":
            effects["trustfund"] = max(int(effects.get("trustfund") or 0), _as_int(node.get("value")))
        elif tag == "blackmarketdiscount":
            effects["black_market_discount"] = True
        elif tag == "selectcontact":
            # Contact id is stored in quality_extras["{quality_id}:contact"] (see engine).
            pass
        elif tag == "selectside":
            # Side is stored in quality_extras[quality_id] as Left/Right (see engine).
            pass
        elif tag == "dealerconnection":
            cats = fields.get("category") or node.get("value") or []
            if not isinstance(cats, list):
                cats = [cats]
            for raw in cats:
                name = str(raw).strip()
                if name and name not in effects["dealer_connection_categories"]:
                    effects["dealer_connection_categories"].append(name)
        elif tag == "friendsinhighplaces":
            effects["friends_in_high_places"] = True
        elif tag == "mademan":
            effects["made_man"] = True
        elif tag == "addcontact":
            connection = _as_int(fields.get("connection"), 1) if "connection" in fields else 1
            loyalty = _as_int(fields.get("loyalty"), 1) if "loyalty" in fields else 1
            forced_loyalty = _as_int(fields.get("forcedloyalty")) if "forcedloyalty" in fields else None
            if forced_loyalty is not None:
                loyalty = max(loyalty, forced_loyalty)
            effects["add_contacts"].append(
                {
                    "source": source,
                    "connection": connection,
                    "loyalty": loyalty,
                    "forced_loyalty": forced_loyalty,
                    "free": "free" in fields,
                    "group": "group" in fields,
                    "force_group": "forcegroup" in fields,
                }
            )
        elif tag == "contactkarma":
            effects["contact_karma_adj"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "contactkarmaminimum":
            effects["contact_karma_min"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "overclocker":
            effects["overclocker"] = True
        elif tag == "ambidextrous":
            effects["ambidextrous"] = True
        elif tag == "cyberwareessmultiplier":
            effects["cyberware_ess_multiplier"] = int(
                round(int(effects.get("cyberware_ess_multiplier") or 100) * _as_int(node.get("value"), 100) / 100.0)
            )
        elif tag == "biowareessmultiplier":
            effects["bioware_ess_multiplier"] = int(
                round(int(effects.get("bioware_ess_multiplier") or 100) * _as_int(node.get("value"), 100) / 100.0)
            )
        elif tag == "cyberwaretotalessmultiplier":
            effects["cyberware_total_ess_multiplier"] = int(
                round(
                    int(effects.get("cyberware_total_ess_multiplier") or 100) * _as_int(node.get("value"), 100) / 100.0
                )
            )
        elif tag == "essencemax":
            effects["essence_max_mod"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "disablebioware":
            effects["disable_bioware"] = True
        elif tag == "disablecyberwaregrade":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["disabled_cyberware_grades"]:
                effects["disabled_cyberware_grades"].append(name)
        elif tag == "disablebiowaregrade":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["disabled_bioware_grades"]:
                effects["disabled_bioware_grades"].append(name)
        elif tag == "martialart":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name:
                effects["free_martial_arts"].append({"name": name, "source": source})
        elif tag == "limitspellcategory":
            attrs = node.get("attrs") or {}
            effects["limit_spell_category_slots"].append(
                {
                    "source": source,
                    "value": str(node.get("value") or fields.get("category") or "").strip(),
                    "exclude": str(attrs.get("exclude") or "").strip(),
                }
            )
        elif tag == "limitspiritcategory":
            raw = fields.get("spirit")
            if raw is None:
                text = str(node.get("value") or "").strip()
                spirits = [text] if text else []
            elif isinstance(raw, list):
                spirits = [str(item).strip() for item in raw if str(item).strip()]
            else:
                text = str(raw).strip()
                spirits = [text] if text else []
            effects["limit_spirit_category_slots"].append({"source": source, "spirits": spirits})
        elif tag == "allowspellcategory":
            name = str(node.get("value") or fields.get("category") or "").strip()
            if name and name not in effects["allow_spell_categories"]:
                effects["allow_spell_categories"].append(name)
        elif tag == "allowspellrange":
            name = str(node.get("value") or fields.get("range") or "").strip()
            if name and name not in effects["allow_spell_ranges"]:
                effects["allow_spell_ranges"].append(name)
        elif tag == "blockspelldescriptor":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["block_spell_descriptors"]:
                effects["block_spell_descriptors"].append(name)
        elif tag == "specialmodificationlimit":
            effects["special_modification_limit"] += _as_int(
                node.get("value") or fields.get("val") or fields.get("bonus")
            )
        elif tag == "erased":
            effects["erased"] = True
        elif tag == "excon":
            effects["excon"] = True
        elif tag == "selectexpertise":
            attrs = node.get("attrs") or {}
            limit_raw = str(attrs.get("limittoskill") or node.get("value") or "").strip()
            skills = [part.strip() for part in limit_raw.split(",") if part.strip()]
            effects["expertise_slots"].append(
                {
                    "source": source,
                    "skills": skills,
                    "limit_to_specialization": str(attrs.get("limittospecialization") or "").strip(),
                }
            )
        elif tag == "spellcategorydrain":
            effects["spell_category_drain"].append(
                {
                    "source": source,
                    "category": str(fields.get("category") or node.get("value") or "").strip(),
                    "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
                }
            )
        elif tag == "spellcategorydamage":
            effects["spell_category_damage"].append(
                {
                    "source": source,
                    "category": str(fields.get("category") or node.get("value") or "").strip(),
                    "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
                }
            )
        elif tag == "spelldescriptordrain":
            effects["spell_descriptor_drain"].append(
                {
                    "source": source,
                    "descriptor": str(fields.get("descriptor") or node.get("value") or "").strip(),
                    "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
                }
            )
        elif tag == "spelldescriptordamage":
            effects["spell_descriptor_damage"].append(
                {
                    "source": source,
                    "descriptor": str(fields.get("descriptor") or node.get("value") or "").strip(),
                    "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
                }
            )
        elif tag == "drainvalue":
            effects["drain_value"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "fadingvalue":
            attrs = node.get("attrs") or {}
            specific = str(attrs.get("specific") or "").strip()
            value = _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
            if specific:
                effects["fading_value_specific"].append({"specific": specific, "value": value})
            else:
                effects["fading_value"] += value
        elif tag == "fadingresist":
            effects["fading_resist"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "drainresist":
            effects["drain_resist"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "selecttext":
            pass
        elif tag == "addecho":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name:
                effects["grant_echoes"].append({"source": source, "name": name})
        elif tag == "cyberadeptdaemon":
            effects["cyberadept_daemon"] = True
        elif tag == "addspell":
            attrs = node.get("attrs") or {}
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name:
                effects["grant_spells"].append(
                    {
                        "source": source,
                        "name": name,
                        "alchemical": str(attrs.get("alchemical") or "").lower() == "true",
                        "extended": str(attrs.get("extended") or "").lower() == "true",
                        "limited": str(attrs.get("limited") or "").lower() == "true",
                    }
                )
        elif tag == "specificpower":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name:
                effects["grant_powers"].append(
                    {
                        "source": source,
                        "name": name,
                        "rating": max(1, _bonus_int(node, fields)),
                        "extra": "",
                    }
                )
        elif tag == "selectpowers":
            slot = parse_select_power_slot(node)
            if slot.get("needs_select"):
                effects["select_power_slots"].append({"source": source, **slot})
        elif tag == "weaponcategorydv":
            select_attrs = (node.get("field_attrs") or {}).get("selectskill") or {}
            limit_raw = str(select_attrs.get("limittoskill") or "").strip()
            skills = [part.strip() for part in limit_raw.split(",") if part.strip()]
            fixed = str(fields.get("name") or "").strip()
            effects["weapon_category_dv_slots"].append(
                {
                    "source": source,
                    "skills": skills,
                    "name": fixed,
                    "bonus": _as_int(fields.get("bonus") or fields.get("val") or fields.get("value")),
                    "needs_select": bool(skills) or "selectskill" in (node.get("fields") or {}),
                }
            )
        elif tag == "weaponskillaccuracy":
            select_attrs = dict((node.get("field_attrs") or {}).get("selectskill") or {})
            fixed = str(fields.get("name") or "").strip()
            effects["weapon_skill_accuracy_slots"].append(
                {
                    "source": source,
                    "name": fixed,
                    "bonus": _as_int(fields.get("value") or fields.get("val") or fields.get("bonus")),
                    "select_attrs": select_attrs,
                    "needs_select": bool(select_attrs) or "selectskill" in (node.get("fields") or {}) or not fixed,
                }
            )
        elif tag == "addspirit":
            attrs = node.get("attrs") or {}
            skill = str(attrs.get("skill") or "").strip()
            add_to_selected = str(fields.get("addtoselected") or "True").lower() != "false"
            effects["add_spirit_slots"].append(
                {
                    "source": source,
                    "skill": skill,
                    "rating_divisor": max(1, _as_int(attrs.get("ratingdivisor"), 1)),
                    "add_to_selected": add_to_selected,
                    "allowed": [
                        str(name).strip()
                        for name in ((node.get("nested") or {}).get("spirit") or [])
                        if str(name).strip()
                    ],
                }
            )
        elif tag == "addmetamagic":
            name = str(node.get("value") or "").strip()
            if name:
                effects["free_metamagics"].append(
                    {
                        "name": name,
                        "source": source,
                        "forced": str((node.get("attrs") or {}).get("forced") or "").lower() == "true",
                    }
                )
        elif tag == "freespells":
            attrs = node.get("attrs") or {}
            limit = str(attrs.get("limit") or "").strip()
            skill = str(attrs.get("skill") or "").strip()
            attribute = str(attrs.get("attribute") or "").strip().upper()
            if skill:
                effects["free_spells_skill"].append({"skill": skill, "limit": limit, "source": source})
            elif attribute:
                effects["free_spells_attribute"].append({"attribute": attribute, "limit": limit, "source": source})
            else:
                effects["free_spells_flat"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "newspellkarmacost":
            attrs = node.get("attrs") or {}
            effects["new_spell_karma_cost"].append(
                {
                    "type": str(attrs.get("type") or "").strip(),
                    "value": _as_int(node.get("value") or fields.get("val") or fields.get("bonus")),
                    "condition": str(attrs.get("condition") or "").strip(),
                    "source": source,
                }
            )
        elif tag == "skillcategorypointcostmultiplier":
            name = str(fields.get("name") or node.get("value") or "").strip()
            if name:
                effects["skill_category_point_cost_mult"][name] = _as_int(fields.get("val") or fields.get("bonus"), 100)
        elif tag == "skillcategorykarmacostmultiplier":
            name = str(fields.get("name") or node.get("value") or "").strip()
            if name:
                effects["skill_category_karma_cost_mult"].append(
                    {
                        "name": name,
                        "val": _as_int(fields.get("val") or fields.get("bonus"), 100),
                        "condition": str(fields.get("condition") or ""),
                    }
                )
        elif tag == "skillcategorykarmacost":
            name = str(fields.get("name") or "").strip()
            if name:
                effects["skill_category_karma_cost"].append(
                    {
                        "name": name,
                        "val": _as_int(fields.get("val")),
                        "min": _as_int(fields.get("min")),
                        "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
                        "condition": str(fields.get("condition") or ""),
                    }
                )
        else:
            return False
        return True
    return True
