"""Lifestyles and the drugs a character mixed for themselves.

The mirror of :mod:`app.chummer_import.lifestyles`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ..data_loader import catalog
from ..models import CharacterState
from ._common import _Ctx, _id_name, _Names, _sub


def _export_lifestyles(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write lifestyles and the qualities picked for them (the built-in free
    ones Chummer derives again, as this app does)."""
    lq_names = _id_name(catalog().get("lifestyle_qualities") or [])
    ls = _sub(root, "lifestyles")
    for lrow in state.lifestyles:
        base = names["lifestyle"].get(lrow.lifestyle_id, "")
        el = _sub(ls, "lifestyle")
        _sub(el, "baselifestyle", base)
        _sub(el, "name", base)
        _sub(el, "months", lrow.months)
        for key in ("comforts", "area", "security"):
            _sub(el, key, getattr(lrow, key))
        if lrow.quality_ids:
            quals = _sub(el, "lifestylequalities")
            for qid in lrow.quality_ids:
                q = _sub(quals, "lifestylequality")
                _sub(q, "id", qid)
                _sub(q, "name", lq_names.get(qid, ""))
                _sub(q, "extra", lrow.quality_extras.get(qid, ""))
                _sub(q, "lifestylequalitysource", "Selected")


def _export_custom_drugs(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write mixed drugs as Chummer's `<drugs><drug>` with their components.

    Chummer rebuilds a custom drug from the components it was mixed from, so
    the component ids and their levels are the whole payload — every total
    (cost, availability, addiction, onset) is recomputed on load, here and
    there alike.

    `<active>` is this app's own: Chummer has no "currently dosed" flag, and
    it ignores elements it does not know.
    """
    drugs = _sub(root, "drugs")
    for drow in state.custom_drugs:
        el = _sub(drugs, "drug")
        _sub(el, "guid", drow.id)
        _sub(el, "name", drow.name)
        _sub(el, "category", "Custom Drugs")
        _sub(el, "quantity", drow.qty)
        _sub(el, "grade", drow.grade)
        _sub(el, "active", "True" if drow.active else "False")
        parts = _sub(el, "drugcomponents")
        for part in drow.parts:
            comp = _sub(parts, "drugcomponent")
            _sub(comp, "sourceid", part.component_id)
            _sub(comp, "name", names["drugcomponent"].get(part.component_id, ""))
            _sub(comp, "level", part.level)
