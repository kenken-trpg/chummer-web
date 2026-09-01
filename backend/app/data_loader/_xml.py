"""Vendored-XML paths + the tiny element accessors every loader shares."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

log = logging.getLogger(__name__)

# backend/  (this file is app/data_loader/_xml.py -> parents[2] == backend/)
_BACKEND = Path(__file__).resolve().parents[2]
VENDOR = _BACKEND / "vendor" / "chummer"
DATA_DIR = VENDOR / "data"
LANG_DIR = VENDOR / "lang"

# Git-tracked Japanese translation overlay. Vendored lang files come from
# chummer5a upstream and are overwritten by fetch_chummer_data.py, so local
# fixes/additions live here and are merged on top (overlay wins).
OVERRIDE_DIR = _BACKEND / "data" / "ja_overrides"

ATTR_KEYS = ("bod", "agi", "rea", "str", "cha", "int", "log", "wil", "edg", "mag", "res", "ess")
PHYSICAL_ATTRS = ("BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA")
SPECIAL_ATTRS = ("EDG", "MAG", "RES")
MATRIX_ATTRIBUTES = ("Attack", "Sleaze", "Data Processing", "Firewall")


def _text(el: ET.Element | None, default: str = "") -> str:
    if el is None or isinstance(el, str):
        return default if el is None else (el or default)
    if el.text is None:
        return default
    return el.text.strip()


def _int(el: ET.Element | None, default: int = 0) -> int:
    raw = _text(el)
    if not raw:
        return default
    try:
        return int(float(raw))
    except ValueError:
        return default


def _float(el: ET.Element | None, default: float = 0.0) -> float:
    raw = _text(el)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _child(parent: ET.Element, *names: str) -> ET.Element | None:
    for name in names:
        found = parent.find(name)
        if found is not None:
            return found
    return None
