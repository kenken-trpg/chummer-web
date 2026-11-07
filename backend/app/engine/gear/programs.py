"""Programs — the software slotted into a cyberdeck or RCC.

Only running cyberdeck programs occupy simultaneous execution slots; some carry a
``[Skill]`` / ``[Group]`` / free-text pick that ``gear_extra_options`` enumerates.
An autosoft can also run on a drone or vehicle itself, and a program need not
be installed anywhere: Chummer keeps a bought copy in the inventory.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import PROGRAM_HOSTS, catalog, eval_formula
from ...models import CharacterState, GearInstall
from ...notices import Notice, notice, term, ui
from ..selects import gear_extra_options, gear_extra_skill_kind
from ._common import _clamp_rating, _program_label
from .misc_hosts import _ware_hosts
from .vehicles import _iter_vehicle_hosts

#: SR5 p.245: while it runs, each of these raises one attribute of the deck
#: running it by 1 (ids from gear.xml). Chummer leaves this to the player (no
#: `<bonus>` on them, nothing in its code), so the .chum5 export keeps the
#: deck's own values; the sheet, the VR initiative and the VTT exports, which
#: read the deck row, get the raised ones.
PROGRAM_ATTRIBUTE_BONUS = {
    "5217388a-e2ce-4add-bcc0-b0b1672f156c": "attack",  # Decryption
    "d5877f46-03e0-4603-b77a-f27e278202ab": "sleaze",  # Stealth
    "cffae49c-30d1-42df-b47c-a407f3a86e7a": "dataprocessing",  # Toolbox
    "d3bb1242-73b0-4b8a-89ab-27c272ebc900": "firewall",  # Encryption
}


def _resolve_programs(
    state: CharacterState,
    cyberdecks: list[dict[str, Any]],
    rccs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[Notice]]:
    warnings: list[Notice] = []
    specs = {item["id"]: item for item in catalog().get("programs") or []}
    hosts: dict[str, tuple[str, dict[str, Any]]] = {}
    for row in cyberdecks:
        hosts[str(row.get("id") or "")] = ("cyberdecks", row)
    for row in rccs:
        hosts[str(row.get("id") or "")] = ("rccs", row)
    for vehicle, vehicle_spec in _iter_vehicle_hosts(state):
        hosts[vehicle.id] = ("vehicles", vehicle_spec)
    # ware that stores programs (a Datajack Plus, KC p.65): only the
    # categories its `<allowgear>` names, and none of them run there
    for ware_id, ware_host in _ware_hosts(state).items():
        hosts[ware_id] = ware_host
    kept: list[GearInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    for inst in list(state.programs or []):
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        want_kind = PROGRAM_HOSTS.get(str(spec.get("category") or ""), "cyberdecks")
        host = hosts.get(inst.parent_id or "")
        # an autosoft runs on the RCC that shares it, or on the drone itself
        kinds = (want_kind, "vehicles") if want_kind == "rccs" else (want_kind,)
        in_ware = host is not None and host[0] == "ware" and spec.get("category") in host[1].get("allow_gear", [])
        if inst.parent_id and not in_ware and (host is None or host[0] not in kinds):
            # left where nothing runs it: kept as a copy the character owns
            warnings.append(
                notice(
                    "engine.gear.needsHostKind",
                    name=term(str(spec["name"])),
                    host=ui("engine.host.cyberdeck" if want_kind == "cyberdecks" else "engine.host.rccOrVehicle"),
                )
            )
            inst.parent_id = None
        extra_kind = str(spec.get("extra_kind") or "")
        extra = (inst.extra or "").strip()
        options = gear_extra_options(spec)
        if extra_kind == "skill":
            if extra and extra not in options:
                warnings.append(notice("engine.gear.skillInvalid", name=term(str(spec["name"])), picked=term(extra)))
                extra = ""
            if not extra:
                warnings.append(notice("engine.gear.pickSkill", name=term(str(spec["name"]))))
        elif extra_kind == "group":
            if extra and extra not in options:
                warnings.append(notice("engine.gear.groupInvalid", name=term(str(spec["name"])), picked=term(extra)))
                extra = ""
            if not extra:
                warnings.append(notice("engine.gear.pickGroup", name=term(str(spec["name"]))))
        elif extra_kind == "text" and not extra:
            warnings.append(notice("engine.gear.pickExtra", name=term(str(spec["name"]))))
        inst.extra = extra or None
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        # an autosoft a drone's own entry grants comes with it
        cost = 0 if inst.included else int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "label": _program_label(spec, extra),
                "category": spec.get("category") or "",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "parent_id": inst.parent_id,
                "included": bool(inst.included),
                "running": (
                    False
                    if in_ware
                    else bool(inst.parent_id and inst.running)
                    if want_kind == "cyberdecks"
                    else inst.running
                ),
                "extra": extra,
                # the deck attribute it raises while running (SR5 p.245)
                "attribute_bonus": PROGRAM_ATTRIBUTE_BONUS.get(str(spec["id"]), ""),
                "needs_extra": bool(extra_kind),
                "extra_kind": extra_kind,
                "extra_skill_kind": gear_extra_skill_kind(spec),
                "nuyen": cost,
                "program_host": spec.get("program_host") or want_kind,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        children.setdefault(str(item.get("parent_id") or ""), []).append(item)
    deck_ids = {str(row["id"]) for row in cyberdecks}
    for row in list(cyberdecks) + list(rccs):
        kids = children.get(str(row.get("id") or "")) or []
        is_deck = str(row["id"]) in deck_ids
        used = sum(bool(kid["running"]) for kid in kids) if is_deck else len(kids)
        row["program_installed"] = len(kids)
        row["program_used"] = used
        row["program_max"] = int(row.get("programs") or 0)
        if (is_deck or row["program_max"] > 0) and used > row["program_max"]:
            warnings.append(
                notice(
                    "engine.gear.runningProgramsOver" if is_deck else "engine.gear.programsOver",
                    name=term(str(row["name"])),
                    used=used,
                    max=row["program_max"],
                )
            )
        keys = [f"{kid['name']}|{kid.get('extra') or ''}" for kid in kids]
        if len(keys) != len(set(keys)):
            warnings.append(notice("engine.gear.duplicateProgram", name=term(str(row["name"]))))
    state.programs = kept
    return public, nuyen, warnings


def apply_running_program_bonuses(cyberdecks: list[dict[str, Any]], programs: list[dict[str, Any]]) -> None:
    """Raise each deck's attribute by 1 for every running Toolbox, Encryption,
    Decryption or Stealth on it (SR5 p.245).

    Runs after the accessories and modules have had their say, so the point
    lands on the attribute wherever the array put it. ``program_bonus`` on the
    deck row says how much of each attribute came from programs. A copy that
    is stopped, loose, or stored in ware runs nowhere and raises nothing.
    """
    decks = {str(row.get("id") or ""): row for row in cyberdecks}
    for row in cyberdecks:
        row["program_bonus"] = {}
    for prog in programs:
        key = str(prog.get("attribute_bonus") or "")
        deck = decks.get(str(prog.get("parent_id") or ""))
        if not key or deck is None or not prog.get("running"):
            continue
        deck[key] = int(deck.get(key) or 0) + 1
        deck["program_bonus"][key] = int(deck["program_bonus"].get(key) or 0) + 1
