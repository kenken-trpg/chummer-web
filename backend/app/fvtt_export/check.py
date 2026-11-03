"""Known omissions of our Foundry export, rather than a simulated Foundry import."""

from __future__ import annotations

from ..engine import compute
from ..models import CharacterState
from ..notices import Notice, notice, term
from ..rules import rules_for, using_rules


def export_omissions(state: CharacterState) -> list[Notice]:
    """Report an A.I.'s programs, which the exporter does not write as
    Foundry items. (A metatype's innate powers used to be listed here too;
    they now go out as critter powers.)

    Recompute from inputs so missing or stale derived caches cannot hide them.
    This is not a complete Foundry round-trip comparison.
    """
    with using_rules(rules_for(state.settings)):
        derived = compute(state.model_copy(deep=True)).derived
    # The system's Chummer import (ItemsParser) reads no `aiprograms`, though
    # its schema names them, so writing them would only look like support.
    return [
        notice("engine.export.fvttAIProgram", name=term(str(row["name"])))
        for row in derived.get("ai_programs") or []
        if row.get("name")
    ]
