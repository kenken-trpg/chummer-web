"""`<aiprograms>`: an A.I.'s programs, as Chummer's `AIProgram.Save` writes them.

The mirror of the `<aiprograms>` part of :mod:`app.chummer_import.magic`.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET

from ..models import CharacterState
from ._common import _Ctx, _Names, _sub


def _export_ai_programs(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Every program the A.I. has, the free Inherent Program pick included.

    Chummer keeps that one in the list too, with `candelete` False; the
    import leaves it to the quality's `<extra>` rather than read it twice.
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
