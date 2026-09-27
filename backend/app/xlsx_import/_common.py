"""The bits the template's sheets share: their names, reading a number the way a
spreadsheet writes one, looking a Japanese name back up in the catalog, and
making sense of a name the player typed by hand.

Wherever the template lets the player write a name — qualities, adept powers —
they write more than a name: the target the thing was taken for, the degree it
was taken at, and a note to themselves. `split_name` pulls those apart and
`candidates` turns what is left into the spellings the catalog might hold, so a
typed name is a handful of lookups rather than one.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..data_loader import CatalogDict

#: The sheets this import reads. The template's names carry a full-width slash.
SHEET_BASICS = "優先度／能力値／資質"
SHEET_SKILLS = "能動技能／技能グループ"
SHEET_KNOWLEDGE = "知識技能／言語技能"
SHEET_MAGIC = "呪文／複合体／アデプト・パワー"


def cell_int(text: str | None) -> int:
    """A sheet's number as an int.

    Everything arrives as a decimal string — a 5 typed into a cell is written
    ``5.0`` — and a cell that holds a label where a number belongs is worth 0
    rather than an error.
    """
    if not text:
        return 0
    try:
        value = float(text)
    except ValueError:
        return 0
    if value != value or value in (float("inf"), float("-inf")):  # NaN / ±inf from a hand edit
        return 0
    return int(round(value))


def japanese_index(cat: CatalogDict, names: Iterable[str], kind: str = "") -> dict[str, str]:
    """``{japanese: english}`` for `names`, with the English name as a key too.

    Some of the catalog's Japanese names carry both readings, joined with a
    slash — ``隠密/ステルス``, ``真偽分析/アナライズ・トゥルース`` — and the
    template writes whichever of the two the player knows. So each side is a key
    of its own, alongside the joined name as written.

    `kind` names a `translations_by_kind` bucket to layer on top (``"skill"``
    for anything on the skill sheets), the way the catalog view does.
    """
    translations = dict(cat.get("translations") or {})
    if kind:
        translations.update((cat.get("translations_by_kind") or {}).get(kind) or {})
    index: dict[str, str] = {}
    for english in names:
        index.setdefault(english, english)
        japanese = translations.get(english)
        if not japanese:
            continue
        for part in [japanese, *japanese.split("/")]:
            part = part.strip()
            if part:
                index.setdefault(part, english)
    return index


#: A parenthesised pick, and whatever the player added after it. The trailing
#: group is a note — 「導師精霊（竜殺しの英雄）　交渉に+2修正」— not part of
#: either the name or the pick.
_PARENTHESISED = re.compile(r"^([^(（]*)[(（]([^()（）]*)[)）](.*)$")
_SEPARATORS = re.compile(r"[／/]")
#: 「導師精霊　鮫」— a pick set off by a space rather than parenthesised.
_SPACES = re.compile(r"[\s\u3000]+")
#: 「軽度の依存症」— a degree written in front of the thing it qualifies.
_PREFIXED = re.compile(r"^(.+?)の(.+)$")
#: The catalog spells a loanword with an interpunct, 「アストラル・ビーコン」, and
#: the sheets are written both ways. Dropping it from both sides settles it.
_INTERPUNCT = re.compile(r"[・･]")


def no_interpunct(text: str) -> str:
    """`text` with its interpuncts dropped, for matching either spelling."""
    return _INTERPUNCT.sub("", text)


def split_name(raw: str) -> tuple[str, str, str]:
    """A typed name into (name, pick, note).

    The name is not resolved here — it is whatever the player wrote, tidied —
    and `candidates` turns it into the spellings the catalog might hold.
    """
    name, pick, note = raw.strip(), "", ""
    matched = _PARENTHESISED.match(name)
    if matched:
        name, pick, note = (group.strip() for group in matched.groups())
    parts = [part.strip() for part in _SEPARATORS.split(name) if part.strip()]
    if len(parts) >= 2:
        # 依存症／中度／クラム — the first two are the thing and its degree,
        # and whatever follows is the pick, which wins over one in parentheses
        # (the sheet never writes both).
        name = f"{parts[0]} ({parts[1]})"
        pick = "／".join(parts[2:]) or pick
        return name, pick, note
    spaced = [part for part in _SPACES.split(name) if part]
    if len(spaced) >= 2:
        # 導師精霊　鮫 — a space where another sheet would use parentheses. The
        # first word is the name and the rest is what it was taken for.
        name, pick = spaced[0], " ".join(spaced[1:]) or pick
    return name, pick, note


def candidates(name: str, pick: str) -> list[str]:
    """The spellings of `name` worth looking up, most literal first.

    A pick is not always a pick: the catalog's own name for SINner (National) is
    ``SIN持ち：国家SIN`` and for Improved Potential (Physical) is
    ``潜在力強化：(身体)``, so a name and its pick have to be tried joined back
    together before the pick is treated as a target.
    """
    out = [name]
    if pick:
        # 「SIN持ち（国家SIN）」→「SIN持ち：国家SIN」、
        # 「潜在力強化　身体」→「潜在力強化：(身体)」
        out += [f"{name}：{pick}", f"{name}:{pick}", f"{name} ({pick})", f"{name}：({pick})"]
    prefixed = _PREFIXED.match(name)
    if prefixed:
        # 「軽度の依存症」→「依存症 (軽度)」
        degree, thing = prefixed.group(1).strip(), prefixed.group(2).strip()
        out.append(f"{thing} ({degree})")
    return out


#: How many of `candidates`'s entries fold the pick into the name; a match on
#: one of those leaves no pick behind.
_SWALLOWING = range(1, 5)


def resolve_typed(raw: str, index: dict[str, str], aliases: dict[str, str] | None = None) -> tuple[str, str] | None:
    """A typed name to (what `index` holds, pick), or `None` if nothing matched.

    `aliases` maps a spelling the template uses to a key of `index`, for the
    names the catalog's Japanese has not caught up with.
    """
    name, pick, _note = split_name(raw)
    for position, candidate in enumerate(candidates(name, pick)):
        plain = no_interpunct(candidate)
        aliased = (aliases or {}).get(candidate) or (aliases or {}).get(plain, "")
        found = index.get(candidate) or index.get(plain) or index.get(aliased)
        if found:
            return found, "" if position in _SWALLOWING else pick
    return None
