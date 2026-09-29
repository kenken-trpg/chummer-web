"""Export a save and read it back: what the trip lost or gained.

What it holds (gear by bucket, ware, vehicle mods — with whether each sits in
a parent) and what it spent must come back the same. It catches what an
import reads but the export has nowhere to write. What it cannot catch is a
field neither side reads, which is `fidelity`'s job.
"""

from __future__ import annotations

import collections
from pathlib import Path
from typing import Any

_GEAR_BUCKETS = ("gear", "commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps")


def _holdings(ch: Any) -> collections.Counter[tuple[Any, ...]]:
    """What a character holds, ids aside (they are new on every import)."""
    held: collections.Counter[tuple[Any, ...]] = collections.Counter()
    for bucket in _GEAR_BUCKETS:
        for r in getattr(ch, bucket):
            held[(bucket, r.gear_id, r.rating, getattr(r, "extra", None), bool(getattr(r, "parent_id", None)))] += 1
    mods = {m.id for m in ch.vehicle_mods}
    for kind in ("cyberware", "bioware"):
        for r in getattr(ch, kind):
            where = "mod" if r.parent_id in mods else bool(r.parent_id)
            held[(kind, r.ware_id, r.rating, r.grade, where)] += 1
    for m in ch.vehicle_mods:
        held[("vehicle_mods", m.mod_id, m.rating, m.included)] += 1
    return held


def roundtrip(path: Path) -> list[str]:
    """What changed when the save was exported and imported again."""
    from app.characters import import_character
    from app.chummer_export import state_to_chum5
    from app.chummer_import import chum5_to_state

    first = import_character(chum5_to_state(path.read_bytes())[0])
    again = import_character(chum5_to_state(state_to_chum5(first))[0])
    before, after = _holdings(first), _holdings(again)
    out = [f"lost {key} ×{n}" for key, n in (before - after).items()]
    out += [f"gained {key} ×{n}" for key, n in (after - before).items()]
    spent = (first.derived.get("nuyen_spent"), again.derived.get("nuyen_spent"))
    if spent[0] != spent[1]:
        out.append(f"nuyen spent {spent[0]} -> {spent[1]}")
    return out
