"""An A.I.'s home node: the device it lives in (Chummer `Character.HomeNode`).

Chummer marks one commlink-like item — gear, a vehicle, cyberware or a weapon
— as the home node, saved as `<homenode>True</homenode>` on that item. This
app covers the commlinks, cyberdecks, RCCs, vehicles and drones. With one,
the A.I.:

- adds the node's Data Processing to its Matrix initiative
  (`MatrixInitiativeValue`);
- takes the node's Data Processing as its mental limit when that is higher
  (`LimitMental`), and for its social limit uses CHA + Data Processing where
  a metahuman doubles CHA (`LimitSocial`);
- has the node's Matrix condition monitor where a metahuman has a stun one
  (`StunCM`).

A vehicle or drone goes further (`HomeNode is Vehicle`): its Pilot counts
where higher than its Data Processing, its Sensor joins the mental limit, and
its own damage track, Handling and Body stand in for the A.I.'s Core track,
physical limit and Body. Lacking matrix attributes in the data, a vehicle's
Device Rating, Data Processing and Program Limit are all its Pilot
(`Vehicle.GetBaseMatrixAttribute`).

The node may be marked when its Program Limit is at least 2 if DEP is above
its Device Rating, else 1. Chummer only greys out the checkbox; here it is a
warning. Chummer also asks a vehicle to carry Persona Firmware (DT p.66) to
count as a commlink at all; this app cannot fit an electronic modification
to a vehicle, so that is a warning too.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, TypedDict

from ..models import CharacterState
from ..notices import Notice, notice, term
from .formulas import _ceil_div

#: The device buckets that can hold an A.I.
HOME_NODE_BUCKETS = ("commlinks", "cyberdecks", "rccs")
#: The vehicle buckets that can
HOME_NODE_VEHICLES = ("vehicles", "drones")


class HomeNode(TypedDict):
    id: str
    bucket: str
    name: str
    device_rating: int
    dataprocessing: int
    program_limit: int
    matrix_cm: int
    #: a vehicle or drone: the stats that stand in for the A.I.'s own
    vehicle: bool
    pilot: int
    sensor: int
    handling: int
    body: int
    physical_cm: int


def _lead(value: Any) -> int:
    """ "4/3" -> 4: a vehicle stat's on-road figure."""
    m = re.match(r"\s*(-?\d+)", str(value or ""))
    return int(m.group(1)) if m else 0


def resolve_home_node(
    state: CharacterState, gear: Mapping[str, Any], *, ai: bool, depth: int
) -> tuple[HomeNode | None, list[Notice]]:
    """The home node the state names, or None — and the mark dropped when the
    character is no A.I. or the device is gone, as a sold commlink would."""
    wanted = state.home_node
    if not wanted:
        return None, []
    row, bucket = next(
        (
            (r, b)
            for b in (*HOME_NODE_BUCKETS, *HOME_NODE_VEHICLES)
            for r in gear.get(b) or []
            if str(r.get("id") or "") == wanted
        ),
        (None, ""),
    )
    if not ai or row is None:
        state.home_node = ""
        return None, []
    if bucket in HOME_NODE_VEHICLES:
        node = _vehicle_node(wanted, bucket, row)
        warnings = [notice("engine.homeNode.personaFirmware", name=term(node["name"]))]
        return node, warnings + _program_limit_warnings(node, depth)
    rating = int(row.get("device_rating") or 0)
    node = {
        "id": wanted,
        "bucket": bucket,
        "name": str(row.get("name") or ""),
        "device_rating": rating,
        "dataprocessing": int(row.get("dataprocessing") or 0),
        # `Program Limit`: the device's `<programs>`, else its Device Rating
        "program_limit": int(row.get("programs") or 0) or rating,
        # what Electronic Modification damage left, else 8 + DR / 2
        "matrix_cm": int(row["matrix_condition_monitor"])
        if row.get("matrix_condition_monitor") is not None
        else 8 + _ceil_div(rating / 2),
        "vehicle": False,
        "pilot": 0,
        "sensor": 0,
        "handling": 0,
        "body": 0,
        "physical_cm": 0,
    }
    return node, _program_limit_warnings(node, depth)


def _vehicle_node(node_id: str, bucket: str, row: Mapping[str, Any]) -> HomeNode:
    pilot = _lead(row.get("pilot"))
    return {
        "id": node_id,
        "bucket": bucket,
        "name": str(row.get("name") or ""),
        "device_rating": pilot,
        "dataprocessing": pilot,
        "program_limit": pilot,
        "matrix_cm": 8 + _ceil_div(pilot / 2),
        "vehicle": True,
        "pilot": pilot,
        "sensor": _lead(row.get("sensor")),
        "handling": _lead(row.get("handling")),
        "body": _lead(row.get("body")),
        "physical_cm": int(row.get("condition_monitor") or 0),
    }


def _program_limit_warnings(node: HomeNode, depth: int) -> list[Notice]:
    needed = 2 if depth > node["device_rating"] else 1
    if node["program_limit"] >= needed:
        return []
    return [notice("engine.homeNode.programLimit", name=term(node["name"]), limit=node["program_limit"], needed=needed)]
