"""Metatype grants in Chummer's saved collections, with their ownership links.

The web state derives these from the species. Chummer saves actual quality,
power and weapon instances, so exporting purchases alone loses innate grants.
Quality.Save / CritterPower.Save / Weapon.Save at the vendored commit define
these fields; Chummer GUI round-trip validation remains a separate check.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from copy import deepcopy
from typing import Any

from ..data_loader import catalog
from ..data_loader._xml import parse_data
from ..models import CharacterState
from ._common import _Ctx, _sub, improvements_of
from .data_fields import _from_data


def _grant_guid(state: CharacterState, grant: dict[str, Any], index: int, kind: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{state.id}:metatype:{grant['origin_id']}:{kind}:{index}:{grant['id']}"))


def _definitions(filename: str, path: str) -> dict[str, ET.Element]:
    return {node.findtext("id") or "": node for node in parse_data(filename).findall(path)}


def export_metatype_qualities(
    qualities: ET.Element, state: CharacterState, ctx: _Ctx
) -> list[tuple[str, ET.Element, str]]:
    """Returns (guid, bonus, extra) for each grant written with a `<bonus>` or
    `<firstlevelbonus>`, whose improvements the caller writes."""
    grants = ctx["meta"].get("quality_grants") or []
    if not grants:
        return []
    bonuses: list[tuple[str, ET.Element, str]] = []
    definitions = _definitions("qualities.xml", "./qualities/quality")
    removed = set(state.removed_innate_qualities)
    for index, grant in enumerate(grants):
        if grant.get("unresolved"):
            continue
        quality = _sub(qualities, "quality")
        if grant.get("removable") and grant["id"] in removed:
            _removed_at_chargen(quality, state, grant, index)
            continue
        fields = {
            "sourceid": grant["id"],
            "guid": _grant_guid(state, grant, index, "quality"),
            "name": grant["name"],
            # a fixed pick, or the player's (an Inherent Program, a
            # Codeslinger action), which has nowhere else to go
            "extra": grant.get("select") or state.quality_extras.get(grant["id"], ""),
            "bp": grant["karma"],
            "qualitytype": grant["category"],
            # Chummer's QualitySource for a `removable="True"` grant.
            "qualitysource": "MetatypeRemovable" if grant.get("removable") else "Metatype",
            "contributetobp": "False",
            "contributetolimit": "False",
            "implemented": "True",
            "print": "True",
            "metagenic": str(bool(grant.get("metagenic"))),
            "source": grant.get("source") or "",
            "page": grant.get("page") or "",
        }
        if grant.get("add_weapon_id"):
            fields["weaponguid"] = _grant_guid(state, grant, index, "weapon")
        for key, value in fields.items():
            _sub(quality, key, value)
        definition = definitions.get(grant["id"])
        if definition is not None:
            for tag in ("bonus", "firstlevelbonus", "naturalweapons"):
                node = definition.find(tag)
                if node is not None:
                    quality.append(deepcopy(node))
                    if tag != "naturalweapons":
                        bonuses.append((fields["guid"], node, fields["extra"]))
    return bonuses


def _removed_at_chargen(quality: ET.Element, state: CharacterState, grant: dict[str, Any], index: int) -> None:
    """The row Chummer's CharacterCreate leaves in place of a removable grant
    taken off: the same quality turned the other way (a negative one bought
    off is a positive cost), its value negated, no bonus, not printed, and
    outside the quality limits."""
    negative = grant["category"] == "Negative"
    for key, value in {
        "sourceid": grant["id"],
        "guid": _grant_guid(state, grant, index, "quality"),
        "name": grant["name"],
        "extra": "Removed Negative Quality" if negative else "Removed Positive Quality",
        "bp": -int(grant["karma"]),
        "qualitytype": "Positive" if negative else "Negative",
        "qualitysource": "MetatypeRemovedAtChargen",
        "contributetobp": "True",
        "contributetolimit": "False",
        "implemented": "True",
        "print": "False",
        "metagenic": str(bool(grant.get("metagenic"))),
        "source": grant.get("source") or "",
        "page": grant.get("page") or "",
    }.items():
        _sub(quality, key, value)


def export_metatype_powers(root: ET.Element, state: CharacterState, ctx: _Ctx) -> None:
    grants = ctx["meta"].get("power_grants") or []
    if not grants:
        return
    powers = root.find("critterpowers")
    if powers is None:
        powers = _sub(root, "critterpowers")
    definitions = _definitions("critterpowers.xml", "./powers/power")
    for index, grant in enumerate(grants):
        if grant.get("unresolved"):
            continue
        power = _sub(powers, "critterpower")
        for key in ("name", "category", "type", "action", "range", "duration", "source", "page"):
            _sub(power, key, grant.get(key) or "")
        for key, value in {
            "sourceid": grant["id"],
            "guid": _grant_guid(state, grant, index, "power"),
            "extra": grant.get("select") or "",
            "rating": grant.get("rating") or 0,
            # Character.Create uses the default grade (0), not the quality-grant grade (-1).
            "grade": 0,
            "counttowardslimit": "False",
            "karma": 0,
            "points": 0,
        }.items():
            _sub(power, key, value)
        definition = definitions.get(grant["id"])
        bonus = definition.find("bonus") if definition is not None else None
        if bonus is not None:
            power.append(deepcopy(bonus))
        # Character.Create links the power's instance to a Metatype
        # improvement; RemoveImprovements follows this link on species changes.
        improvement = _sub(improvements_of(root), "improvement")
        for key, value in {
            "improvedname": _grant_guid(state, grant, index, "power"),
            "sourcename": "",
            "improvementttype": "CritterPower",
            "improvementsource": "Metatype",
            "val": 0,
            "rating": 1,
            "enabled": 1,
        }.items():
            _sub(improvement, key, value)


def export_metatype_weapons(weapons: ET.Element, state: CharacterState, ctx: _Ctx) -> None:
    specs = {weapon["id"]: weapon for weapon in catalog()["weapons"]}
    for index, grant in enumerate(ctx["meta"].get("quality_grants") or []):
        spec = specs.get(grant.get("add_weapon_id") or "")
        if not spec:
            continue
        weapon = _sub(weapons, "weapon")
        _sub(weapon, "name", spec.get("name") or "")
        for key, value in {
            "sourceid": spec["id"],
            "guid": _grant_guid(state, grant, index, "weapon"),
            "parentid": _grant_guid(state, grant, index, "quality"),
            "weapontype": spec.get("weapon_type") or "",
            "cost": 0,
            "qty": 1,
            "allowaccessory": "False",
            "equipped": "True",
            "included": "False",
            "cyberware": "False",
        }.items():
            _sub(weapon, key, value)
        _from_data(weapon, "weapon", spec["id"])
        # what the data file lacks keeps the catalogue's value
        for key in (
            "category",
            "type",
            "reach",
            "damage",
            "ap",
            "accuracy",
            "mode",
            "rc",
            "ammo",
            "conceal",
            "avail",
            "useskill",
            "source",
            "page",
        ):
            if weapon.find(key) is None:
                _sub(weapon, key, spec.get(key) or "")
