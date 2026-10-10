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


def _grant_guid(state: CharacterState, grant: dict[str, Any], index: int, kind: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{state.id}:metatype:{grant['origin_id']}:{kind}:{index}:{grant['id']}"))


def _definitions(filename: str, path: str) -> dict[str, ET.Element]:
    return {node.findtext("id") or "": node for node in parse_data(filename).findall(path)}


def export_metatype_qualities(qualities: ET.Element, state: CharacterState, ctx: _Ctx) -> None:
    grants = ctx["meta"].get("quality_grants") or []
    if not grants:
        return
    definitions = _definitions("qualities.xml", "./qualities/quality")
    for index, grant in enumerate(grants):
        if grant.get("unresolved"):
            continue
        quality = _sub(qualities, "quality")
        fields = {
            "sourceid": grant["id"],
            "guid": _grant_guid(state, grant, index, "quality"),
            "name": grant["name"],
            "extra": grant.get("select") or "",
            "bp": grant["karma"],
            "qualitytype": grant["category"],
            "qualitysource": "Metatype",
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
        for key in (
            "name",
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
            _sub(weapon, key, spec.get(key) or "")
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
