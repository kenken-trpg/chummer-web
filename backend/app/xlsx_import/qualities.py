"""The qualities on the 優先度／能力値／資質 sheet, rows 50–59.

The name is typed by hand, so it has to be matched against the catalog's
Japanese names rather than looked up by an id. Two spellings show up in the
wild, and both are the player writing one field where this app keeps two:

* ``規制品(アレス・サンダートラック・ガウスライフル)`` — the pick in parentheses
* ``依存症／中度／クラム`` — the degree and the pick joined with the name

Chummer's own name for the second is ``依存症 (中度)``, with ``クラム`` in
``<extra>``, which is what this produces.
"""

from __future__ import annotations

import re
from typing import Any

from ..data_loader import CatalogDict
from ..notices import Notice, notice, ui

#: Rows 50–59 hold one quality each: A the kind (有利／不利), C the name,
#: N the karma spent, P the karma gained. The karma is the sheet's own
#: arithmetic — this app derives it — so only A and C are read.
QUALITY_ROWS = range(50, 60)

#: Names the template spells differently from the catalog's Japanese. Kept here
#: rather than in `ja_overrides` when the catalog's own wording is the right
#: one and only the template disagrees.
NAME_ALIASES = {
    "規制品": "Restricted Gear",
}

_PARENTHESISED = re.compile(r"^(.*?)[(（]([^()（）]*)[)）]\s*$")
_SEPARATORS = re.compile(r"[／/]")


def split_name(raw: str) -> tuple[str, str]:
    """A typed quality name into (name, extra).

    ``依存症／中度／クラム`` → ``("依存症 (中度)", "クラム")``;
    ``規制品(アレス…)`` → ``("規制品", "アレス…")``.
    """
    name, extra = raw.strip(), ""
    matched = _PARENTHESISED.match(name)
    if matched:
        name, extra = matched.group(1).strip(), matched.group(2).strip()
    parts = [part.strip() for part in _SEPARATORS.split(name) if part.strip()]
    if len(parts) >= 2:
        # The first two are the quality — 依存症 and its degree — and whatever
        # follows is the pick, which wins over one in parentheses (the sheet
        # never writes both).
        name = f"{parts[0]} ({parts[1]})"
        extra = "／".join(parts[2:]) or extra
    return name, extra


def build_index(cat: CatalogDict) -> dict[str, str]:
    """Japanese quality name -> id, with the English name as a second key.

    The English name is there for `NAME_ALIASES`: a quality the Japanese data
    has not translated yet (規制品 / Restricted Gear) is still reachable.
    """
    translations = dict(cat.get("translations") or {})
    translations.update((cat.get("translations_by_kind") or {}).get("qualities") or {})
    index: dict[str, str] = {}
    for row in cat["qualities"]:
        name, quality_id = str(row["name"]), str(row["id"])
        japanese = translations.get(name)
        if japanese:
            index.setdefault(japanese, quality_id)
        index.setdefault(name, quality_id)
    return index


def import_qualities(cells: dict[str, str], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Fill `quality_ids` / `quality_extras` from rows 50–59."""
    index = build_index(cat)
    takes_extra = {str(row["id"]): bool(row.get("extra_kind")) for row in cat["qualities"]}
    quality_ids: list[str] = []
    extras: dict[str, str] = {}
    for row in QUALITY_ROWS:
        raw = cells.get(f"C{row}") or ""
        if not raw:
            continue
        name, extra = split_name(raw)
        quality_id = index.get(name) or index.get(NAME_ALIASES.get(name, ""))
        if not quality_id:
            warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.quality"), name=raw))
            continue
        # A quality taken twice is two entries, the way a .chum5 read writes it.
        quality_ids.append(quality_id)
        if not extra:
            continue
        if not takes_extra.get(quality_id):
            # 規制品(アレス…) — the sheet notes what the quality was spent on,
            # but the quality itself has nothing to hold it.
            warn.append(notice("engine.import.xlsxQualityNote", name=raw, note=extra))
        elif quality_id in extras:
            # `quality_extras` is keyed by quality, so a second take of the same
            # one has nowhere to put its own pick.
            warn.append(notice("engine.import.xlsxQualityNote", name=raw, note=extra))
        else:
            extras[quality_id] = extra
    if quality_ids:
        st["quality_ids"] = quality_ids
    if extras:
        st["quality_extras"] = extras


__all__ = ["QUALITY_ROWS", "build_index", "import_qualities", "split_name"]
