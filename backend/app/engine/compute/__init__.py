"""``compute(state)`` — build one ``Ctx`` and run it through the phases.

Relocated from ``app.engine`` and split into ``app/engine/compute/`` (the
compute-phases refactor; see ``docs/plans/refactor-compute-phases-plan.md``).
``compute/__init__.py`` is now just the ``Ctx`` build plus the phase loop;
``app.engine`` re-exports ``compute`` and the handful of helpers
``characters.py`` / tests reference by name.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog
from ...models import CharacterState
from ._career import (  # noqa: F401  (re-exported via app.engine)
    career_raise_karma,
    nuyen_spend_breakdown,
    snapshot_career_baseline,
)
from .assemble import (
    _effective_attr_spec,  # noqa: F401  (re-exported via app.engine)
    assemble,
)
from .bootstrap import (
    bootstrap,
    sync_reward_totals,  # noqa: F401  (re-exported via app.engine)
)
from .context import Ctx
from .economy import economy
from .essence import essence
from .finalize import (
    finalize,
    resolve_movement,  # noqa: F401  (re-exported via app.engine)
    totals,
)
from .gear import (
    gear_phase,
    resolve_gear,  # noqa: F401  (re-exported via app.engine)
)
from .magic import awakened, spells
from .qualities import (
    effects_and_binders,
    gather,
    resolve_attribute_selects,  # noqa: F401  (re-exported via app.engine)
)
from .ware import ware


def default_attributes(meta: dict[str, Any]) -> dict[str, int]:
    out = {}
    for key, spec in meta["attributes"].items():
        if key == "ESS":
            out[key] = int(spec["max"] or 6)
        else:
            out[key] = int(spec["min"])
    return out


def compute(state: CharacterState) -> CharacterState:
    ctx = Ctx(state=state, data=catalog())
    bootstrap(ctx)
    gather(ctx)
    ware(ctx)
    effects_and_binders(ctx)
    essence(ctx)
    awakened(ctx)
    gear_phase(ctx)
    totals(ctx)
    spells(ctx)
    economy(ctx)
    finalize(ctx)
    assemble(ctx)
    return ctx.state
