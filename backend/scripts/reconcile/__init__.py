"""The .chum5 comparison, split from the terminal it usually runs in.

`scripts/chum5_reconcile.py` is the command; these modules are what it asks.
Each answers one question about a save and hands back data, so a test can ask
the same question without capturing stdout:

* `balance.reconcile` — what Chummer says it has left against what this app computes
* `roundtrip.roundtrip` — what an export-and-re-import trip lost or gained
* `fidelity.fidelity` — the export against the save Chummer wrote, field by field
* `prices._stored_prices` — the prices a save records for its own pieces
* `_saves.fetch` — the test saves themselves

`cli` is the only module that prints.
"""

from __future__ import annotations

from ._saves import CACHE, TESTFILES, fetch
from .balance import NUYEN_TOLERANCE, reconcile
from .fidelity import fidelity
from .roundtrip import roundtrip

__all__ = [
    "CACHE",
    "NUYEN_TOLERANCE",
    "TESTFILES",
    "fetch",
    "fidelity",
    "reconcile",
    "roundtrip",
]
