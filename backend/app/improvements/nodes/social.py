"""Economy, contacts, lifestyle, qualities, essence multipliers and the ware/grade toggles — plus the pick-is-stored-elsewhere no-op tags.

One slice of the bonus-node table. Each handler claims its tags with
``@handles`` and is reached by lookup, not by falling down a chain.
"""

from __future__ import annotations

from typing import Any

from .._common import _as_int, _bonus_int, granted_quality_names
from ..effects import EffectsDict
from ._registry import handles


@handles("cyberseeker")
def _cyberseeker(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    target = (node.get("value") or fields.get("name") or "").upper()
    if target:
        effects["cyberseeker"].append(target)


@handles("freequality")
def _freequality(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    qid = str(node.get("value") or fields.get("name") or "").strip()
    if qid and qid not in effects["free_qualities"]:
        effects["free_qualities"].append(qid)


@handles("addqualities", "addquality")
def _addqualities(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    for name, _select in granted_quality_names(node):
        if name not in effects["add_qualities"]:
            effects["add_qualities"].append(name)


@handles("lifestylecost")
def _lifestylecost(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    value = _bonus_int(node, fields)
    effects["lifestyle_cost"] += value
    effects["lifestyle_cost_mods"].append({"value": value, "source": source})


@handles("notoriety")
def _notoriety(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["notoriety"] += _bonus_int(node, fields)


@handles("streetcredmultiplier")
def _streetcredmultiplier(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["street_cred_divisor"] += _bonus_int(node, fields)


@handles("fame")
def _fame(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["fame"] += _bonus_int(node, fields)


@handles("publicawareness")
def _publicawareness(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["public_awareness"] += _bonus_int(node, fields)


@handles("essencepenalty")
def _essencepenalty(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["essence_penalty"] += abs(_bonus_int(node, fields))


@handles("essencepenaltyt100")
def _essencepenaltyt100(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["essence_penalty"] += abs(_bonus_int(node, fields)) / 100.0


@handles("essencepenaltymagonlyt100")
def _essencepenaltymagonlyt100(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["essence_penalty_mag_exempt"] += abs(_bonus_int(node, fields)) / 100.0


@handles("prototypetranshuman")
def _prototypetranshuman(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["prototype_transhuman_ess"] = round(
        float(effects.get("prototype_transhuman_ess") or 0) + float(_bonus_int(node, fields)),
        4,
    )


@handles("selectquality")
def _selectquality(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    raw = fields.get("quality") or node.get("value") or []
    options = [str(item).strip() for item in (raw if isinstance(raw, list) else [raw]) if str(item).strip()]
    if options:
        effects["select_quality_slots"].append({"source": source, "options": options})


@handles("nuyenmaxbp")
def _nuyenmaxbp(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["nuyen_max_bp"] += _bonus_int(node, fields)


@handles("nuyenamt")
def _nuyenamt(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    attrs = node.get("attrs") or {}
    if attrs.get("condition"):
        return
    effects["nuyen_amt"] += _bonus_int(node, fields)


@handles("trustfund")
def _trustfund(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["trustfund"] = max(int(effects.get("trustfund") or 0), _as_int(node.get("value")))


@handles("blackmarketdiscount")
def _blackmarketdiscount(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["black_market_discount"] = True


@handles("selectcontact")
def _selectcontact(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    pass


@handles("selectside")
def _selectside(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    pass


@handles("dealerconnection")
def _dealerconnection(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    cats = fields.get("category") or node.get("value") or []
    if not isinstance(cats, list):
        cats = [cats]
    for raw in cats:
        name = str(raw).strip()
        if name and name not in effects["dealer_connection_categories"]:
            effects["dealer_connection_categories"].append(name)


@handles("friendsinhighplaces")
def _friendsinhighplaces(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["friends_in_high_places"] = True


@handles("mademan")
def _mademan(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["made_man"] = True


@handles("addcontact")
def _addcontact(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
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


@handles("contactkarma")
def _contactkarma(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["contact_karma_adj"] += _bonus_int(node, fields)


@handles("contactkarmaminimum")
def _contactkarmaminimum(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["contact_karma_min"] += _bonus_int(node, fields)


@handles("overclocker")
def _overclocker(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["overclocker"] = True


@handles("ambidextrous")
def _ambidextrous(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["ambidextrous"] = True


@handles("cyberwareessmultiplier")
def _cyberwareessmultiplier(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["cyberware_ess_multiplier"] = int(
        round(int(effects.get("cyberware_ess_multiplier") or 100) * _as_int(node.get("value"), 100) / 100.0)
    )


@handles("biowareessmultiplier")
def _biowareessmultiplier(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["bioware_ess_multiplier"] = int(
        round(int(effects.get("bioware_ess_multiplier") or 100) * _as_int(node.get("value"), 100) / 100.0)
    )


@handles("cyberwaretotalessmultiplier")
def _cyberwaretotalessmultiplier(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["cyberware_total_ess_multiplier"] = int(
        round(int(effects.get("cyberware_total_ess_multiplier") or 100) * _as_int(node.get("value"), 100) / 100.0)
    )


@handles("essencemax")
def _essencemax(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["essence_max_mod"] += _bonus_int(node, fields)


@handles("disablebioware")
def _disablebioware(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["disable_bioware"] = True


@handles("disablecyberwaregrade")
def _disablecyberwaregrade(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = str(node.get("value") or fields.get("name") or "").strip()
    if name and name not in effects["disabled_cyberware_grades"]:
        effects["disabled_cyberware_grades"].append(name)


@handles("disablebiowaregrade")
def _disablebiowaregrade(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = str(node.get("value") or fields.get("name") or "").strip()
    if name and name not in effects["disabled_bioware_grades"]:
        effects["disabled_bioware_grades"].append(name)


@handles("addgear")
def _addgear(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = str(fields.get("name") or node.get("value") or "").strip()
    if name:
        effects["grant_gear"].append(
            {
                "source": source,
                "name": name,
                "category": str(fields.get("category") or "").strip(),
                "rating": _as_int(fields.get("rating") or 1, 1),
                "children": [dict(kid) for kid in node.get("gear_children") or []],
            }
        )


@handles("addweapon")
def _addweapon(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = str(fields.get("name") or node.get("value") or "").strip()
    if name:
        effects["grant_weapons"].append({"source": source, "name": name})


@handles("addware")
def _addware(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = str(fields.get("name") or node.get("value") or "").strip()
    if name:
        effects["grant_ware"].append(
            {
                "source": source,
                "name": name,
                "kind": str(fields.get("type") or "Cyberware").strip().lower(),
                "grade": str(fields.get("grade") or "").strip(),
            }
        )


@handles("martialart")
def _martialart(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = str(node.get("value") or fields.get("name") or "").strip()
    if name:
        effects["free_martial_arts"].append({"name": name, "source": source})


@handles("specialmodificationlimit")
def _specialmodificationlimit(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["special_modification_limit"] += _bonus_int(node, fields)


@handles("erased")
def _erased(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["erased"] = True


@handles("excon")
def _excon(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["excon"] = True


@handles("selectexpertise")
def _selectexpertise(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
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


@handles("selecttext")
def _selecttext(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    pass


@handles("selectcyberware")
def _selectcyberware(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    # The grade/category the node names is read off the node itself in
    # `engine/ware/resolve.py`; there is no effect to accumulate.
    pass
