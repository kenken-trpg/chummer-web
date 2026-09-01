"""Economy, contacts, lifestyle, qualities, essence multipliers and the ware/grade toggles — plus the pick-is-stored-elsewhere no-op tags.

One slice of the pre-split ``apply_bonus_nodes`` chain. ``apply`` returns
True iff ``tag`` is one of ours.
"""

from __future__ import annotations

from typing import Any

from .._common import _as_int


def apply(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: dict[str, Any], source: str) -> bool:
    for _once in (True,):
        if tag == "cyberseeker":
            target = (node.get("value") or fields.get("name") or "").upper()
            if target:
                effects["cyberseeker"].append(target)
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
        elif tag == "prototypetranshuman":
            effects["prototype_transhuman_ess"] = round(
                float(effects.get("prototype_transhuman_ess") or 0)
                + float(_as_int(node.get("value") or fields.get("val") or fields.get("bonus"), 0)),
                4,
            )
        elif tag == "selectquality":
            raw = fields.get("quality") or node.get("value") or []
            options = [str(item).strip() for item in (raw if isinstance(raw, list) else [raw]) if str(item).strip()]
            if options:
                effects["select_quality_slots"].append({"source": source, "options": options})
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
        elif tag == "selecttext":
            pass
        else:
            return False
        return True
    return True
