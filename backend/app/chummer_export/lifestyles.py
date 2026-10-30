"""Lifestyles and the drugs a character mixed for themselves.

The mirror of :mod:`app.chummer_import.lifestyles`.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET

from ..data_loader import catalog
from ..data_loader._xml import parse_data
from ..models import CharacterState
from ._common import _Ctx, _id_name, _Names, _sub
from .data_fields import _from_data
from .improvements import _bonus_improvements, _write_improvements

#: Chummer's `ConvertToLifestyleQualityType`: the categories that are a type
#: of their own; every other one (the entertainment assets) is Entertainment.
_QUALITY_TYPES = {"Negative": "Negative", "Positive": "Positive", "Contracts": "Contracts"}


def _export_lifestyles(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write lifestyles and the qualities picked for them (the built-in free
    ones Chummer derives again, as this app does).

    Chummer reads a lifestyle's price, dice and multipliers from the save
    alone. Before 5.197 it filled them from the data on load, which is why an
    export without a version came out priced; one saved as 5.226 without them
    costs nothing."""
    lq_names = _id_name(catalog().get("lifestyle_qualities") or [])
    bonuses = {
        node.findtext("id") or "": node.find("bonus")
        for node in parse_data("lifestyles.xml").findall("./qualities/quality")
    }
    ls = _sub(root, "lifestyles")
    for lrow in state.lifestyles:
        base = names["lifestyle"].get(lrow.lifestyle_id, "")
        el = _sub(ls, "lifestyle")
        _sub(el, "sourceid", lrow.lifestyle_id)
        _sub(el, "baselifestyle", base)
        _sub(el, "name", base)
        _sub(el, "months", lrow.months)
        for key in ("comforts", "area", "security"):
            _sub(el, key, getattr(lrow, key))
        _from_data(el, "lifestyle", lrow.lifestyle_id)
        if lrow.quality_ids:
            quals = _sub(el, "lifestylequalities")
            for index, qid in enumerate(lrow.quality_ids):
                q = _sub(quals, "lifestylequality")
                _sub(q, "id", qid)
                _sub(q, "name", lq_names.get(qid, ""))
                extra = lrow.quality_extras.get(qid, "")
                _sub(q, "extra", extra)
                _sub(q, "lifestylequalitysource", "Selected")
                _from_data(q, "lifestylequality", qid)
                category = q.findtext("category") or ""
                # Chummer reads the type from its own field, not the category.
                _sub(q, "lifestylequalitytype", _QUALITY_TYPES.get(category, "Entertainment"))
                bonus = bonuses.get(qid)
                # Chummer also uses <extra> for a formatted price label (for
                # example "Special Work Area [1,000¥]"). That is no text pick
                # and its saves contain no Text improvement.
                pick = None if extra.startswith(f"{lq_names.get(qid, '')} [") else extra or None
                rows = _bonus_improvements(bonus, 1, pick) if bonus is not None else []
                if rows:
                    # Chummer owns a lifestyle quality's improvements by its
                    # instance guid, not by the catalog id in <id>.
                    guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"lifestyle-quality:{lrow.id}:{index}:{qid}"))
                    _sub(q, "guid", guid)
                    _write_improvements(root, rows, guid, "Quality")


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
