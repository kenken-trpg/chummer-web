"""The engine's message keys and the front end's dictionary must agree.

Splitting the two — keys here, wording in `frontend/lib/i18n/messages.ts` — is
what lets the creation-check panel follow the locale switch, but it also means
nothing in Python knows whether a key has a sentence behind it. A missing one
renders as `engine.foo.bar` in the UI rather than crashing, which is exactly
the kind of failure that reaches a player instead of CI. So it is checked here.

`Record<MsgKey, string>` already stops one *locale* falling behind the other;
this stops the *dictionary* falling behind the *engine*.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend" / "app"
MESSAGES = REPO / "frontend" / "lib" / "i18n" / "messages.ts"

# Fixed engine vocabulary. Some members are named literally and some are built
# at run time (`ui(f"engine.slot.{key}")`), so a member with no literal is not
# evidence of a dead entry — the family as a whole is checked instead.
DYNAMIC_FAMILIES = (
    "engine.side.",
    "engine.slot.",
    "engine.kind.",
    "engine.host.",
    "engine.select.",
    "engine.vehicleSlot.",
    "engine.drugDuration.",
)


def _keys_used() -> set[str]:
    """Every `engine.*` key the backend names literally."""
    used: set[str] = set()
    for path in BACKEND.rglob("*.py"):
        used |= set(re.findall(r'"(engine\.[A-Za-z0-9_.]+)"', path.read_text()))
    return used


def _keys_defined() -> set[str]:
    return set(re.findall(r'^\s*"(engine\.[A-Za-z0-9_.]+)":', MESSAGES.read_text(), flags=re.M))


def test_every_engine_key_has_a_sentence() -> None:
    missing = sorted(_keys_used() - _keys_defined())
    assert not missing, f"no wording in messages.ts for: {missing}"


def test_no_orphaned_engine_keys() -> None:
    orphans = sorted(key for key in _keys_defined() - _keys_used() if not key.startswith(DYNAMIC_FAMILIES))
    assert not orphans, f"messages.ts defines keys the engine never emits: {orphans}"


def test_dynamic_families_are_still_used() -> None:
    """The families above are exempt from the orphan check, so make sure each is
    still built somewhere rather than quietly dead."""
    source = "".join(path.read_text() for path in BACKEND.rglob("*.py"))
    unused = [family for family in DYNAMIC_FAMILIES if family not in source]
    assert not unused, f"nothing builds these key families any more: {unused}"
