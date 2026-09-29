"""One save's bottom line: what Chummer says against what this app computes.

For a character still in creation (``<created>False``), ``<karma>`` and
``<nuyen>`` are what Chummer computed as *left* — the one place a save states
the result of the whole build, so a mismatch means an item, a price or a rule
differs without having to find which one first. In career mode the same
elements are a running balance, which the import meets by construction, so
the adjustment it needed is reported instead.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .prices import _gear_drift

#: Chummer keeps nuyen as a decimal; anything under a nuyen is rounding.
NUYEN_TOLERANCE = 1.0


def _number(root: ET.Element, tag: str) -> float:
    try:
        return float(root.findtext(tag) or 0)
    except ValueError:
        return 0.0


def _quality_drift(root: ET.Element) -> list[tuple[str, int, int]]:
    """Qualities whose stored price is not what today's catalogue charges.

    A save keeps the karma it paid for a quality (`<bp>`) rather than a
    reference to the price list, so a save written against an older
    `qualities.xml` states a price this app will never reproduce. That is not
    a rule this app gets wrong, and it is worth telling apart from one: the
    difference lands in the karma left, which is the very number the table
    above compares. Only qualities the character chose count — `Metatype` and
    priority-granted ones are free on both sides — and only unlevelled,
    plain ones, since `<bp>` on a levelled or `<extra>`-carrying quality is a
    total this cannot take apart.
    """
    from app.data_loader import catalog_list

    prices = {str(q.get("name") or ""): q.get("karma") for q in catalog_list("qualities")}
    drift: list[tuple[str, int, int]] = []
    for node in root.iter("quality"):
        name = (node.findtext("name") or "").strip()
        source = (node.findtext("qualitysource") or "").strip()
        if (source and source != "Selected") or (node.findtext("extra") or "").strip():
            continue
        listed = prices.get(name)
        if listed is None:
            continue
        try:
            stored = int(node.findtext("bp") or 0)
        except ValueError:
            continue
        if stored != int(listed):
            drift.append((name, int(listed), stored))
    return drift


def reconcile(path: Path) -> dict[str, Any]:
    """One save: what Chummer says against what this app computes."""
    from app.characters import import_character
    from app.chummer_import import chum5_to_state

    raw = path.read_bytes()
    root = ET.fromstring(raw)
    state, warnings = chum5_to_state(raw)
    derived = import_character(state).derived
    created = (root.findtext("created") or "").strip().lower() == "true"
    row: dict[str, Any] = {
        "file": path.name,
        "career": created,
        "warnings": [w["key"] for w in warnings],
        "errors": [e["key"] for e in derived.get("errors") or []],
    }
    if created:
        row["adjust"] = (int(state.get("karma_adjust") or 0), int(state.get("nuyen_adjust") or 0))
        spent = state.get("expense_log") or []
        row["spent"] = (
            sum(int(e.get("karma") or 0) for e in spent),
            sum(int(e.get("nuyen") or 0) for e in spent),
        )
    else:
        karma = derived.get("karma") or {}
        row["karma"] = (_number(root, "karma"), karma.get("remaining"))
        row["nuyen"] = (_number(root, "nuyen"), derived.get("nuyen"))
        row["quality_drift"] = _quality_drift(root)
        row["gear_drift"] = _gear_drift(root)
    return row
