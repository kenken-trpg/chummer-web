"""The two helpers every export section uses, and the shapes they pass around."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


def _sub(parent: ET.Element, tag: str, text: Any = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = str(text)
    return el


def _note(el: ET.Element, text: str) -> None:
    """The player's own `<notes>` on a row, where something is written."""
    if text:
        _sub(el, "notes", text)


def _player_text(el: ET.Element, row: Any, name_tag: str = "") -> None:
    """The row's own note, and the player's name for it under `name_tag`
    (`<armorname>`, `<gearname>`, ...), where something is written — the
    mirror of the import's `_player_text`."""
    _note(el, getattr(row, "notes", ""))
    if name_tag and getattr(row, "nickname", ""):
        _sub(el, name_tag, row.nickname)


def _id_name(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {r["id"]: r.get("name") or "" for r in rows if r.get("id")}


#: `_id_name` maps per catalog bucket, built once and read by most sections.
_Names = dict[str, dict[str, str]]
#: Resolved metatype (including innate grants), its attribute minimums,
#: and the computed derived payload used by the individual sections.
_Ctx = dict[str, Any]


def improvements_of(root: ET.Element) -> ET.Element:
    """The one `<improvements>` under `<character>`, made on first use —
    several sections add to it, and Chummer reads only the first."""
    found = root.find("improvements")
    return found if found is not None else _sub(root, "improvements")
