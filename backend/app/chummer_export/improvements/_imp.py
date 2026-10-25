"""One improvement as the export writes it, and the small readers every tag's
function shares."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import NamedTuple


class _Imp(NamedTuple):
    """One improvement, in the fields `Improvement.Save` writes that a bonus sets."""

    kind: str
    improved: str = ""
    target: str = ""
    unique: str = ""
    val: int = 0
    min: int = 0
    max: int = 0
    condition: str = ""
    rating: int = 1
    exclude: str = ""
    addtorating: bool = False
    aug: int = 0
    augmax: int = 0


def _text(node: ET.Element, field: str | None = None) -> str:
    return ((node.text if field is None else node.findtext(field)) or "").strip()


def _is_int(text: str | None) -> bool:
    return (text or "").strip().lstrip("-").isdigit()


def _precedence(node: ET.Element) -> str:
    """`addlimb` / `conditionmonitor`: a `precedence` attribute is the unique."""
    return f"precedence{node.get('precedence')}" if node.get("precedence") else ""
