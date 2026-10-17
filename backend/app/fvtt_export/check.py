"""Known omissions of our Foundry export, rather than a simulated Foundry import."""

from __future__ import annotations

from ..engine import compute
from ..models import CharacterState
from ..notices import Notice, notice, term
from ..rules import rules_for, using_rules


def export_omissions(state: CharacterState) -> list[Notice]:
    """Report innate powers and an A.I.'s programs, which the exporter does not
    write as Foundry items.

    Recompute from inputs so missing or stale derived caches cannot hide powers.
    This is not a complete Foundry round-trip comparison.
    """
    with using_rules(rules_for(state.settings)):
        derived = compute(state.model_copy(deep=True)).derived
    powers = (derived.get("metatype_info") or {}).get("powers") or []
    # An A.I.'s programs: the system's Chummer import (ItemsParser) reads no
    # `aiprograms`, though its schema names them, so writing them would
    # only look like support.
    programs = [
        notice("engine.export.fvttAIProgram", name=term(str(row["name"])))
        for row in derived.get("ai_programs") or []
        if row.get("name")
    ]
    return programs + [
        notice(
            "engine.export.fvttInnatePower",
            name=term(str(row["name"])),
            selection=str(row.get("select") or ""),
            source=str(row.get("source") or ""),
            page=str(row.get("page") or ""),
        )
        for row in powers
        if row.get("name")
    ]
