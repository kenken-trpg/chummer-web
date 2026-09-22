"""Qualities, spells and rituals, adept powers and complex forms."""

from __future__ import annotations

import uuid
from typing import Any

from ..data_loader import CatalogDict
from ..notices import Notice
from ._common import _d, _extra, _Matcher, _num


def _import_items(items: list[dict[str, Any]], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    def of(*types: str) -> list[dict[str, Any]]:
        return [i for i in items if i.get("type") in types]

    qualities = _Matcher(cat["qualities"])
    st["quality_ids"] = [qid for i in of("quality") if (qid := qualities.match(i, warn, "engine.kind.quality"))]
    spells = _Matcher(cat["spells"])
    st["spells"] = [
        {"id": str(uuid.uuid4()), "spell_id": sid}
        for i in of("spell", "ritual")
        if (sid := spells.match(i, warn, "engine.kind.spell"))
    ]
    powers = _Matcher(cat["powers"])
    st["adept_powers"] = [
        {
            "id": str(uuid.uuid4()),
            "power_id": pid,
            "rating": max(1, _num(_d(i.get("system")).get("level"), 1)),
            "extra": _extra(i),
        }
        for i in of("adept_power")
        if (pid := powers.match(i, warn, "engine.kind.adeptPower"))
    ]
    forms = _Matcher(cat["complex_forms"])
    st["complex_forms"] = [
        {"id": str(uuid.uuid4()), "form_id": fid, "level": None, "extra": _extra(i)}
        for i in of("complex_form")
        if (fid := forms.match(i, warn, "engine.kind.complexForm"))
    ]
