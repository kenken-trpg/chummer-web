"""Vendored-XML paths + the tiny element accessors every loader shares."""

from __future__ import annotations

import contextlib
import logging
import xml.etree.ElementTree as ET
from collections.abc import Iterator, Mapping
from contextvars import ContextVar
from pathlib import Path
from typing import NamedTuple

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import fromstring as _defused_fromstring

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


class Overlay(NamedTuple):
    """One custom-data set, ready to read.

    `key` identifies it — the content hash of the files plus which directories
    the settings enabled — and is what `catalog()` caches under. `trees` holds
    only the data files custom data actually touched.
    """

    key: str
    trees: Mapping[str, ET.Element]


# The active custom-data overlay, or `None` for the vendored data as shipped.
# A ContextVar for the same reason `app.rules` is one: every loader reaches for
# its file globally, and threading an overlay through 31 call sites would be a
# lot of signature churn for something constant for the length of one request.
_overlay: ContextVar[Overlay | None] = ContextVar("customdata", default=None)


@contextlib.contextmanager
def using_customdata(overlay: Overlay | None) -> Iterator[None]:
    """Serve `parse_data` from `overlay` for this block."""
    token = _overlay.set(overlay)
    try:
        yield
    finally:
        _overlay.reset(token)


def current_overlay_key() -> str:
    """What `catalog()` keys its cache on. Empty means the vendored data."""
    overlay = _overlay.get()
    return overlay.key if overlay else ""


def parse_data(name: str) -> ET.Element:
    """The root of one vendored data file, with custom data folded in.

    Every loader goes through here rather than `ET.parse(DATA_DIR / name)`, so
    a `customdata/` directory is applied once, upstream, and nothing
    downstream has to know: an added martial art is indistinguishable from one
    that shipped.

    The overlay holds only the files custom data touched; everything else is
    read from disk as before.
    """
    overlay = _overlay.get()
    if overlay is not None and name in overlay.trees:
        return overlay.trees[name]
    return ET.parse(DATA_DIR / name).getroot()


def data_root(name: str) -> ET.Element | None:
    """`parse_data`, but `None` when the file is not there.

    The loaders return an empty list for a missing data file so an un-fetched
    vendor tree still imports (docs/adding-rules.md); this keeps that while
    letting custom data supply a file the vendor tree lacks.
    """
    overlay = _overlay.get()
    if overlay is not None and name in overlay.trees:
        return overlay.trees[name]
    path = DATA_DIR / name
    if not path.exists():
        return None
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        # A truncated download, or a hand-edited vendor file. One unreadable
        # data file should cost its own section, not the whole catalog.
        log.warning("%s parse failed: %s", name, exc)
        return None


ATTR_KEYS = ("bod", "agi", "rea", "str", "cha", "int", "log", "wil", "edg", "mag", "res", "ess")
PHYSICAL_ATTRS = ("BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA")
SPECIAL_ATTRS = ("EDG", "MAG", "RES")
MATRIX_ATTRIBUTES = ("Attack", "Sleaze", "Data Processing", "Firewall")


def parse_untrusted(raw: str | bytes) -> ET.Element:
    """Parse XML that came from a visitor — a .chum5, a settings file, a
    customdata pack — rather than from `vendor/`.

    Goes through defusedxml, which refuses a DTD's entities and external
    references outright instead of relying on expat's amplification limit.
    Chummer never writes a DTD, so nothing a real file holds is lost. A refusal
    comes out as `ET.ParseError`, the same as malformed XML: to every caller
    both mean "not a file we can read".
    """
    try:
        root: ET.Element = _defused_fromstring(raw)
    except DefusedXmlException as exc:
        raise ET.ParseError(f"refused: {exc}") from exc
    return root


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
