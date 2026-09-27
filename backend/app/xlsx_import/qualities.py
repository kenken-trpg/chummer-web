"""The qualities on the 優先度／能力値／資質 sheet, rows 50–59.

The name is typed by hand into one field, so it has to be matched against the
catalog's Japanese names — and players write far more in that field than a name.
Four shapes turn up across the sheets seen so far, and no revision of the
template is stricter than another:

* ``規制品(アレス・サンダートラック・ガウスライフル)`` — the pick in parentheses
* ``依存症／中度／クラム`` — the degree and the pick joined onto the name
* ``軽度の依存症（エナジードリンク / カフェイン）`` — the same quality with the
  degree in front instead, which the catalog spells ``依存症 (軽度)``
* ``導師精霊（竜殺しの英雄）　交渉に+2修正`` — a note trailing after the pick
* ``導師精霊　鮫`` — the pick set off by a space instead of parentheses

Two more differences are about spelling rather than shape: the catalog writes a
loanword with an interpunct (``アストラル・ビーコン``) and players often leave it
out, and some qualities are known by the tail of their name (``国家SIN`` for
``SIN持ち：国家SIN``). Both are handled below.

So a typed name becomes a handful of candidate spellings, tried in order against
the catalog, rather than one string looked up once. What matches nothing is
reported; a pick the quality cannot hold is reported too, rather than dropped.
"""

from __future__ import annotations

import re
from typing import Any

from ..data_loader import CatalogDict
from ..notices import Notice, notice, ui

#: Rows 50–59 hold one quality each: A the kind (有利／不利), C the name,
#: N the karma spent, P the karma gained. The karma is the sheet's own
#: arithmetic — this app derives it — so only C is read.
QUALITY_ROWS = range(50, 60)

#: Names the template spells differently from the catalog's Japanese. Kept here
#: rather than in `ja_overrides` when the catalog's own wording is the right one
#: and only the template disagrees.
NAME_ALIASES = {
    "規制品": "Restricted Gear",
    # SINner is filed under 「SIN持ち：…」, but the SIN itself is what gets typed.
    "国家SIN": "SINner (National)",
    "企業SIN": "SINner (Corporate)",
    "限定企業SIN": "SINner (Corporate Limited)",
    "犯罪者SIN": "SINner (Criminal)",
}

#: A parenthesised pick, and whatever the player added after it. The trailing
#: group is a note — 「導師精霊（竜殺しの英雄）　交渉に+2修正」— not part of
#: either the name or the pick.
_PARENTHESISED = re.compile(r"^([^(（]*)[(（]([^()（）]*)[)）](.*)$")
_SEPARATORS = re.compile(r"[／/]")
#: 「導師精霊　鮫」— a pick set off by a space rather than parenthesised.
_SPACES = re.compile(r"[\s\u3000]+")
#: The catalog spells a loanword with an interpunct, 「アストラル・ビーコン」, and
#: the sheets are written both ways. Dropping it from both sides settles it.
_INTERPUNCT = re.compile(r"[・･]")
#: 「軽度の依存症」— a degree written in front of the quality it qualifies.
_PREFIXED = re.compile(r"^(.+?)の(.+)$")


def split_name(raw: str) -> tuple[str, str, str]:
    """A typed quality name into (name, pick, note).

    The name is not resolved here — it is whatever the player wrote, tidied —
    and `candidates` turns it into the spellings the catalog might hold.
    """
    name, pick, note = raw.strip(), "", ""
    matched = _PARENTHESISED.match(name)
    if matched:
        name, pick, note = (group.strip() for group in matched.groups())
    parts = [part.strip() for part in _SEPARATORS.split(name) if part.strip()]
    if len(parts) >= 2:
        # 依存症／中度／クラム — the first two are the quality and its degree,
        # and whatever follows is the pick, which wins over one in parentheses
        # (the sheet never writes both).
        name = f"{parts[0]} ({parts[1]})"
        pick = "／".join(parts[2:]) or pick
        return name, pick, note
    spaced = [part for part in _SPACES.split(name) if part]
    if len(spaced) >= 2:
        # 導師精霊　鮫 — a space where another sheet would use parentheses. The
        # first word is the quality and the rest is what it was taken for.
        name, pick = spaced[0], " ".join(spaced[1:]) or pick
    return name, pick, note


def candidates(name: str, pick: str) -> list[str]:
    """The spellings of `name` worth looking up, most literal first.

    A pick is not always a pick: the catalog's own name for SINner (National) is
    ``SIN持ち：国家SIN``, so ``SIN持ち（国家SIN）`` has to be tried joined back
    together before it is treated as a quality plus a target.
    """
    out = [name]
    if pick:
        # 「SIN持ち（国家SIN）」→「SIN持ち：国家SIN」/「SIN持ち (国家SIN)」
        out += [f"{name}：{pick}", f"{name}:{pick}", f"{name} ({pick})"]
    prefixed = _PREFIXED.match(name)
    if prefixed:
        # 「軽度の依存症」→「依存症 (軽度)」
        degree, quality = prefixed.group(1).strip(), prefixed.group(2).strip()
        out.append(f"{quality} ({degree})")
    return out


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
            index.setdefault(_INTERPUNCT.sub("", japanese), quality_id)
        index.setdefault(name, quality_id)
    return index


def resolve(raw: str, index: dict[str, str]) -> tuple[str, str] | None:
    """A typed name to (quality id, pick), or `None` if nothing matched.

    A candidate that matched *with* the pick folded into the name leaves no pick
    behind: ``SIN持ち：国家SIN`` is the whole quality.
    """
    name, pick, _note = split_name(raw)
    for index_of, candidate in enumerate(candidates(name, pick)):
        aliased = NAME_ALIASES.get(candidate) or NAME_ALIASES.get(_INTERPUNCT.sub("", candidate), "")
        quality_id = index.get(candidate) or index.get(_INTERPUNCT.sub("", candidate)) or index.get(aliased)
        if quality_id:
            # candidates() puts the spellings that swallow the pick at 1..3
            return quality_id, "" if 1 <= index_of <= 3 else pick
    return None


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
        resolved = resolve(raw, index)
        if not resolved:
            warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.quality"), name=raw))
            continue
        quality_id, pick = resolved
        # A quality taken twice is two entries, the way a .chum5 read writes it.
        quality_ids.append(quality_id)
        if not pick:
            continue
        if not takes_extra.get(quality_id):
            # 規制品(アレス…), 導師精霊(竜殺しの英雄) — the sheet notes what the
            # quality was taken for, but the quality has nothing to hold it.
            # (A mentor is `mentor_id` here, which this import does not read yet.)
            warn.append(notice("engine.import.xlsxQualityNote", name=raw, note=pick))
        elif quality_id in extras:
            # `quality_extras` is keyed by quality, so a second take of the same
            # one has nowhere to put its own pick.
            warn.append(notice("engine.import.xlsxQualityNote", name=raw, note=pick))
        else:
            extras[quality_id] = pick
    if quality_ids:
        st["quality_ids"] = quality_ids
    if extras:
        st["quality_extras"] = extras


__all__ = ["QUALITY_ROWS", "build_index", "candidates", "import_qualities", "resolve", "split_name"]
