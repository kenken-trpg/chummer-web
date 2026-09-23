"""The small shared pieces: the translator, and the shapes Chummer's print
XML uses for a flag, a block of notes, a name with its option and money."""

from __future__ import annotations

import html
from typing import Any

from ..data_loader import catalog


def _translator(locale: str) -> Any:
    """English data name -> display name, the backend twin of the frontend's
    `makeTr` / `scopeTr`: a per-kind table first, then the flat one."""
    if locale != "ja":
        return lambda name, *kinds: name
    cat = catalog()
    flat = cat.get("translations") or {}
    by_kind = cat.get("translations_by_kind") or {}

    def tr(name: str, *kinds: str) -> str:
        for kind in kinds:
            hit = (by_kind.get(kind) or {}).get(name)
            if hit:
                return hit
        return flat.get(name) or name

    return tr


def _flag(on: object) -> str:
    return "True" if on else "False"


def _html(text: str | None) -> str | None:
    """Plain text as the HTML the importer expects (Chummer prints rich text):
    escaped, one paragraph per blank-line block, line breaks kept."""
    if not text or not text.strip():
        return None
    blocks = [b for b in text.replace("\r\n", "\n").split("\n\n") if b.strip()]
    return "".join(f"<p>{html.escape(b.strip()).replace(chr(10), '<br/>')}</p>" for b in blocks)


def _fullname(name: str, extra: str) -> str:
    """Chummer's `fullname`, the name the importer shows: the pick in brackets."""
    return f"{name} ({extra})" if extra else name


def _money(value: object) -> str:
    return str(int(float(str(value or 0))))
