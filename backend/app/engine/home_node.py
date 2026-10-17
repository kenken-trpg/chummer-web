"""An A.I.'s home node: the device it lives in (Chummer `Character.HomeNode`).

Chummer marks one commlink-like item — gear, a vehicle, cyberware or a weapon
— as the home node, saved as `<homenode>True</homenode>` on that item. This
app covers the commlinks, cyberdecks and RCCs. With one, the A.I.:

- adds the node's Data Processing to its Matrix initiative
  (`MatrixInitiativeValue`);
- takes the node's Data Processing as its mental limit when that is higher
  (`LimitMental`), and for its social limit uses CHA + Data Processing where
  a metahuman doubles CHA (`LimitSocial`);
- has the node's Matrix condition monitor where a metahuman has a stun one
  (`StunCM`).

The node may be marked when its Program Limit is at least 2 if DEP is above
its Device Rating, else 1. Chummer only greys out the checkbox; here it is a
warning.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict

from ..models import CharacterState
from ..notices import Notice, notice, term
from .formulas import _ceil_div

#: The device buckets that can hold an A.I.
HOME_NODE_BUCKETS = ("commlinks", "cyberdecks", "rccs")


class HomeNode(TypedDict):
    id: str
    bucket: str
    name: str
    device_rating: int
    dataprocessing: int
    program_limit: int
    matrix_cm: int


def resolve_home_node(
    state: CharacterState, gear: Mapping[str, Any], *, ai: bool, depth: int
) -> tuple[HomeNode | None, list[Notice]]:
    """The home node the state names, or None — and the mark dropped when the
    character is no A.I. or the device is gone, as a sold commlink would."""
    wanted = state.home_node
    if not wanted:
        return None, []
    row, bucket = next(
        ((r, b) for b in HOME_NODE_BUCKETS for r in gear.get(b) or [] if str(r.get("id") or "") == wanted),
        (None, ""),
    )
    if not ai or row is None:
        state.home_node = ""
        return None, []
    rating = int(row.get("device_rating") or 0)
    # `Program Limit`: the device's `<programs>`, else its Device Rating
    limit = int(row.get("programs") or 0) or rating
    node: HomeNode = {
        "id": wanted,
        "bucket": bucket,
        "name": str(row.get("name") or ""),
        "device_rating": rating,
        "dataprocessing": int(row.get("dataprocessing") or 0),
        "program_limit": limit,
        # what Electronic Modification damage left, else 8 + DR / 2
        "matrix_cm": int(row["matrix_condition_monitor"])
        if row.get("matrix_condition_monitor") is not None
        else 8 + _ceil_div(rating / 2),
    }
    needed = 2 if depth > rating else 1
    warnings = (
        [notice("engine.homeNode.programLimit", name=term(node["name"]), limit=limit, needed=needed)]
        if limit < needed
        else []
    )
    return node, warnings
