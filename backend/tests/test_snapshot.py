"""Golden-snapshot regression tests for :func:`app.engine.compute`.

Each fixture builds a full character that exercises a broad slice of the rules
engine; the *entire* ``derived`` blob is frozen to ``tests/snapshots/<name>.json``.
A refactor meant to preserve behaviour must leave every snapshot byte-identical
(``make check`` runs this). The targeted assertions in ``test_engine.py`` pin
individual rules; these pin the shape and every field of a realistic result, so a
code-motion change that silently drops or reorders part of ``derived`` is caught
even where no unit test looks.

Regenerate after an *intentional* rules or payload change, then eyeball the diff
before committing::

    UPDATE_SNAPSHOTS=1 pytest backend/tests/test_snapshot.py
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from app.engine import compute
from app.models import (
    AdeptPowerInstall,
    ArmorInstall,
    ComplexFormInstall,
    CyberwareInstall,
    GearInstall,
    Priorities,
    SpellInstall,
    SpiritInstall,
    SpriteInstall,
    WeaponInstall,
)
from tests.test_engine import (
    ARMOR_JACKET,
    CLEANER,
    COURIER_SPRITE,
    CRITICAL_STRIKE,
    DATAJACK,
    DEALER_CONNECTION,
    EDITOR,
    ERIKA_DECK,
    HEAL,
    HERMETIC,
    IMPROVED_REFLEXES,
    MANABOLT,
    PREDATOR,
    SPIRIT_FIRE,
    WIRED,
    _adept,
    _mage,
    _mundane,
    _techno,
)

SNAP_DIR = Path(__file__).parent / "snapshots"
UPDATE = os.environ.get("UPDATE_SNAPSHOTS") == "1"

# Keys whose value is a per-instance UUID minted fresh on every run (the Install
# models default ``id`` to ``uuid4``). They carry no behavioural meaning, so we
# rewrite each distinct one to a stable ``#N`` token — equal UUIDs still map to
# the same token, so ``parent_id`` -> row ``id`` links stay verifiable.
VOLATILE_KEYS = {"id", "parent_id"}


def _normalize(obj: Any) -> Any:
    """Render ``derived`` deterministically and JSON-safely.

    * dict keys are sorted (insertion order must not matter for a snapshot)
    * sets/frozensets become sorted lists (``enabled_tabs`` etc. are sets)
    * lists/tuples keep their order (``array_order`` and friends are meaningful)
    * floats are rounded to kill 1e-15 formula noise
    """
    if isinstance(obj, dict):
        return {str(k): _normalize(obj[k]) for k in sorted(obj, key=str)}
    if isinstance(obj, (set, frozenset)):
        return sorted((_normalize(x) for x in obj), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(obj, (list, tuple)):
        return [_normalize(x) for x in obj]
    if isinstance(obj, float):
        return round(obj, 6)
    return obj


def _scrub_ids(obj: Any, registry: dict[str, str]) -> Any:
    """Replace instance UUIDs under :data:`VOLATILE_KEYS` with stable ``#N`` tokens."""
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if key in VOLATILE_KEYS and isinstance(value, str) and value:
                out[key] = registry.setdefault(value, f"#{len(registry) + 1}")
            else:
                out[key] = _scrub_ids(value, registry)
        return out
    if isinstance(obj, list):
        return [_scrub_ids(x, registry) for x in obj]
    return obj


def _derived(state: Any) -> dict[str, Any]:
    out = compute(state)
    return _scrub_ids(_normalize(out.derived), {})


CHARACTERS: dict[str, Callable[[], Any]] = {
    "street_samurai": lambda: _mundane(
        "snap-samurai",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
        cyberware=[
            CyberwareInstall(ware_id=WIRED, rating=2),
            CyberwareInstall(ware_id=DATAJACK),
        ],
        weapons=[WeaponInstall(weapon_id=PREDATOR)],
        armor=[ArmorInstall(armor_id=ARMOR_JACKET)],
        skills={"Automatics": 6, "Sneaking": 4, "Perception": 3, "Unarmed Combat": 2},
    ),
    "hermetic_mage": lambda: _mage(
        "snap-mage",
        tradition_id=HERMETIC,
        spells=[SpellInstall(spell_id=MANABOLT), SpellInstall(spell_id=HEAL)],
        spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, services=2)],
        skills={"Spellcasting": 5, "Summoning": 4, "Counterspelling": 3},
    ),
    "adept": lambda: _adept(
        "snap-adept",
        adept_powers=[
            AdeptPowerInstall(power_id=IMPROVED_REFLEXES, rating=2),
            AdeptPowerInstall(power_id=CRITICAL_STRIKE, rating=3, extra="Unarmed Combat"),
        ],
        skills={"Unarmed Combat": 6, "Gymnastics": 4},
    ),
    "technomancer": lambda: _techno(
        "snap-techno",
        complex_forms=[
            ComplexFormInstall(form_id=CLEANER),
            ComplexFormInstall(form_id=EDITOR),
        ],
        sprites=[SpriteInstall(sprite_id=COURIER_SPRITE, level=3, services=2, registered=True)],
        skills={"Compiling": 4, "Software": 5, "Electronic Warfare": 3},
    ),
    "street_rigger": lambda: _mundane(
        "snap-rigger",
        priorities=Priorities(Heritage="D", Attributes="C", Talent="E", Skills="B", Resources="A"),
        quality_ids=[DEALER_CONNECTION],
        cyberdecks=[GearInstall(gear_id=ERIKA_DECK)],
        skills={"Pilot Ground Craft": 5, "Gunnery": 4, "Perception": 2},
    ),
}


@pytest.mark.parametrize("name", sorted(CHARACTERS))
def test_derived_matches_snapshot(name: str) -> None:
    got = _derived(CHARACTERS[name]())
    path = SNAP_DIR / f"{name}.json"

    if UPDATE or not path.exists():
        SNAP_DIR.mkdir(exist_ok=True)
        path.write_text(json.dumps(got, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        if not UPDATE:
            pytest.skip(f"wrote initial snapshot {path.name}; re-run to assert against it")
        return

    want = json.loads(path.read_text(encoding="utf-8"))
    assert got == want, (
        f"derived output drifted from tests/snapshots/{name}.json. "
        f"If this change is intentional, regenerate with "
        f"UPDATE_SNAPSHOTS=1 pytest backend/tests/test_snapshot.py and review the diff."
    )


def test_snapshot_fixtures_are_error_free() -> None:
    """The fixtures are meant to be legal builds — keep the snapshots meaningful."""
    for name, build in sorted(CHARACTERS.items()):
        derived = compute(build()).derived
        assert derived["errors"] == [], f"{name}: {derived['errors']}"
