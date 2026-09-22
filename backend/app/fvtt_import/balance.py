"""The karma, nuyen and reputation Foundry had, kept as adjustments."""

from __future__ import annotations

import copy
from typing import Any

from ..models._common import clamp_input_ints
from ._common import _d, _num


def _import_balance(system: dict[str, Any], st: dict[str, Any]) -> None:
    """Karma and nuyen left as Foundry had them, the rest kept as an adjustment
    (as for a Chummer career save without its expense log); street cred,
    notoriety and public awareness likewise, as the part not worked out here."""
    from ..engine import compute
    from ..models import CharacterState

    def derived() -> dict[str, Any]:
        # clamped here as well as on the way out: this validates the state
        # mid-read, before the caller ever sees it.
        bare = clamp_input_ints(copy.deepcopy({k: v for k, v in st.items() if not k.startswith("_")}))
        return compute(CharacterState.model_validate(bare)).derived

    d = derived()
    st["karma_adjust"] = _num(_d(system.get("karma")).get("value")) - _num(_d(d.get("karma")).get("remaining"))
    st["nuyen_adjust"] = _num(system.get("nuyen")) - _num(d.get("nuyen"))
    # karma earned counts toward street cred: worked out again with it in
    d = derived()
    st["street_cred"] = max(0, _num(system.get("street_cred")) - _num(d.get("street_cred")))
    st["notoriety_bonus"] = _num(system.get("notoriety")) - _num(d.get("notoriety"))
    st["public_awareness"] = max(0, _num(system.get("public_awareness")) - _num(d.get("public_awareness")))
