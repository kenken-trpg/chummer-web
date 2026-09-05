"""Phase 4b of docs/plans/translation-plan.md — punctuation in the ja overlay.

`test_terminology.py` guards the *words*; this guards the *marks around them*.
The two slips that got through the first Run & Gun batch were both notation —
a full-width bracket closed by a half-width one, and a colon in the other
width from its five neighbours — and neither is the kind of thing a reader
notices in a 500-row diff.

The conventions below are not chosen on taste. They are what the corpus
already did before the RG batch touched it, so applying them is a matter of
counting rather than deciding:

    brackets   half-width ()      33 entries did this, 5 did not
    colon      full-width ：      5 entries did this, 0 did not
    space      only before a numeric rating suffix, mirroring the English
               name's own " (6)" — the 18 `Liner - …` entries

The five surviving full-width bracket entries are pinned in
`FULLWIDTH_BRACKETS_KEPT` rather than rewritten. They were checked against the
Japanese core rulebook, and quietly restyling a term somebody verified is the
same class of move as guessing at one — see the same reasoning behind
`DECIDED_FLOOR` in test_rg_coverage.py. Shrink the list when a person decides,
not to make a run go green.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

OVERLAY = Path(__file__).resolve().parents[1] / "data" / "ja_overrides"

# Checked against the Japanese core rulebook with full-width brackets. Decide
# them one at a time; do not add rows here to silence a new import.
FULLWIDTH_BRACKETS_KEPT = {
    "(Synth)Leather",
    "Power Swimming (Elf or Troll)",
    "Silencer (Ares Light Fire 70)",
    "Silencer (Ares Light Fire 75)",
    "Way of Unified Mana (Hapsum-Do)",
}

RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("full-width bracket", re.compile(r"[（）]"), "use ( ) — 33 of 38 bracketed entries do"),
    ("mixed bracket widths", re.compile(r"（[^）]*\)|\([^)]*）"), "open and close must match"),
    ("half-width colon", re.compile(r":"), "use ： — every colon in the overlay predating RG is full-width"),
    ("full-width space", re.compile("　"), "use a normal space, or none"),
    ("space before a bracket", re.compile(r"\s\((?!\d+\))"), "only a numeric rating suffix keeps its space"),
)


def _entries() -> list[tuple[str, str, str]]:
    out = []
    for name in ("data.json", "ui.json"):
        loaded: dict[str, str] = json.loads((OVERLAY / name).read_text(encoding="utf-8"))
        out += [(name, key, value) for key, value in loaded.items()]
    assert out, "no overlay entries — is backend/data/ja_overrides populated?"
    return out


@pytest.mark.parametrize(("label", "pattern", "fix"), RULES, ids=[r[0] for r in RULES])
def test_notation(label: str, pattern: re.Pattern[str], fix: str) -> None:
    hits = [
        f"{file}: {key!r} -> {value!r}"
        for file, key, value in _entries()
        if pattern.search(value) and not (label == "full-width bracket" and key in FULLWIDTH_BRACKETS_KEPT)
    ]
    assert not hits, f"{label} ({fix}):\n  " + "\n  ".join(hits)


def test_the_kept_list_is_still_accurate() -> None:
    """A pinned exception that no longer applies is worse than none at all.

    It reads as a decision somebody made, when really the entry was renamed or
    already fixed, and the next person leaves it alone for a reason that has
    stopped being true.
    """
    entries = {key: value for _, key, value in _entries()}
    stale = sorted(
        key for key in FULLWIDTH_BRACKETS_KEPT if key not in entries or not re.search(r"[（）]", entries[key])
    )
    assert not stale, "no longer full-width (or no longer in the overlay) — drop from the list:\n  " + "\n  ".join(
        stale
    )
