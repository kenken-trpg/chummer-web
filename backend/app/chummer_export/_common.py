"""The two helpers every export section uses, and the shapes they pass around."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


def _sub(parent: ET.Element, tag: str, text: Any = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = str(text)
    return el


def _id_name(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {r["id"]: r.get("name") or "" for r in rows if r.get("id")}


#: `_id_name` maps per catalog bucket, built once and read by most sections.
_Names = dict[str, dict[str, str]]
#: The little that is neither the state nor a name map: the metatype's
#: attribute minimums, which only the attribute section needs.
_Ctx = dict[str, Any]
