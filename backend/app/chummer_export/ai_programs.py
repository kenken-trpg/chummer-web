"""`<aiprograms>`: an A.I.'s programs, as Chummer's `AIProgram.Save` writes them.

The mirror of the `<aiprograms>` part of :mod:`app.chummer_import.magic`.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET

from ..models import CharacterState
from ._common import _Ctx, _Names, _sub, improvements_of
from .metatype import _grant_guid


def _export_ai_programs(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Every program the A.I. has, the free Inherent Program pick included.

    Chummer keeps that one in the list too, with `candelete` False; the
    import leaves it to the quality's `<extra>` rather than read it twice.
    An `AIProgram` improvement ties it to the quality, as
    `selectinherentaiprogram` makes one: removing the quality in Chummer
    then removes the program with it.
    """
    rows = ctx["derived"].get("ai_programs") or []
    if not rows:
        return
    programs = _sub(root, "aiprograms")
    for row in rows:
        el = _sub(programs, "aiprogram")
        row_id = str(row["id"])
        _sub(el, "sourceid", row["program_id"])
        # Chummer reads `<guid>` as a Guid; an inherent row's id is not one
        _sub(el, "guid", row_id if not row["free"] else str(uuid.uuid5(uuid.NAMESPACE_URL, row_id)))
        _sub(el, "name", row["name"])
        _sub(el, "candelete", "False" if row["free"] else "True")
        _sub(el, "isadvancedprogram", "True" if row["advanced"] else "False")
        _sub(el, "requiresprogram", "")
        _sub(el, "extra", row.get("extra") or "")
        _sub(el, "source", row.get("source") or "")
        _sub(el, "page", row.get("page") or "")
        _sub(el, "notes", "")
        if row["free"]:
            quality_guid = _quality_guid(state, ctx, row_id.removeprefix("inherent:"))
            if quality_guid:
                imp = _sub(improvements_of(root), "improvement")
                _sub(imp, "improvedname", el.findtext("guid") or "")
                _sub(imp, "sourcename", quality_guid)
                _sub(imp, "improvementttype", "AIProgram")
                _sub(imp, "improvementsource", "Quality")


def _quality_guid(state: CharacterState, ctx: _Ctx, qid: str) -> str:
    """The `<guid>` the qualities section wrote for Inherent Program: its id
    when bought, the metatype grant's own when a Protosapient is born with it."""
    if qid in state.quality_ids:
        return qid
    for index, grant in enumerate(ctx["meta"].get("quality_grants") or []):
        if grant.get("id") == qid and not grant.get("unresolved"):
            return _grant_guid(state, grant, index, "quality")
    return ""
