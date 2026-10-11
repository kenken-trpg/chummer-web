"""What a character loses on the way through a .chum5.

Writes the character out, reads the file back with this app's own importer,
and lists what came back different — a whole section's worth of rows at a
time, since the rows' ids are new on every import and the catalog names are
the front end's to translate. It cannot see what Chummer.exe itself would make
of the file (that is `scripts/chum5_reconcile.py --fidelity`'s job); what it
catches is the half of the round trip this app owns.
"""

from __future__ import annotations

from ..characters import import_character
from ..chummer_import import chum5_to_state
from ..export_check import differences
from ..models import CharacterState
from ..notices import Notice, notice
from . import state_to_chum5


def roundtrip_differences(state: CharacterState) -> list[Notice]:
    """What the character would look like after an export and a re-import,
    as notices. Empty when it comes back the same."""
    first = import_character(state.model_dump())
    again = import_character(chum5_to_state(state_to_chum5(first))[0])
    growth = int(first.derived.get("career_advancement_karma") or 0) - int(
        again.derived.get("career_advancement_karma") or 0
    )
    # Chummer stores current ratings and the balance, not this app's original
    # baseline. Name the verified accounting conversion instead of calling its
    # adjustment an unspecified "other" change. Any mismatch still goes through
    # the ordinary comparison, including an actual change to the balance.
    if (
        first.career
        and again.career
        and growth > 0
        and again.karma_adjust == first.karma_adjust - growth
        and (first.derived.get("karma") or {}).get("remaining") == (again.derived.get("karma") or {}).get("remaining")
    ):
        return [notice("engine.export.chum5CareerBaseline", amount=growth)] + differences(
            first, again, skip=frozenset({"karma_adjust"})
        )
    return differences(first, again)
