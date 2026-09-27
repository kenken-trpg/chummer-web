"""What the sheet writers share: the catalog's Japanese for an English name, and
saying what the template has no room for.

The import matches a Japanese name against the catalog; this goes the other way,
which is the easy direction — there is exactly one Japanese name per entry. It
is written as the catalog holds it, including the dual readings some names carry
(``隠密/ステルス``), because the import indexes the joined form as well as each
side of it.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import CatalogDict
from ..notices import Notice, Phrase, notice


class Limits:
    """What the sheet ran out of room for, as notices.

    The template is a fixed grid: ten qualities, twenty spells, thirty implants.
    A character with more than fits does not make the file unwritable — it makes
    part of the character absent from it — so the overflow is counted and
    reported rather than silently dropped.
    """

    def __init__(self) -> None:
        self.notices: list[Notice] = []

    def fit(self, rows: list[Any], room: int, what: Phrase) -> list[Any]:
        """The first `room` of `rows`, with a notice if that was not all of them."""
        if len(rows) <= room:
            return rows
        self.notices.append(
            notice("engine.export.xlsxNoRoom", kind=what, room=room, dropped=len(rows) - room),
        )
        return rows[:room]

    def no_cell(self, kind: Phrase, name: str, instead: str) -> None:
        """`name` is something the sheet has no answer for, written as `instead`.

        Not everything this app keeps has a cell in the template: it offers five
        metatypes and six kinds of magic user where the book has more, and two
        build methods where this app has four. The nearest answer is written and
        the swap is reported, which is better than both refusing to write the
        file and writing it as though nothing had changed.
        """
        self.notices.append(notice("engine.export.xlsxNoCell", kind=kind, name=name, instead=instead))


def translator(cat: CatalogDict, kind: str = "") -> dict[str, str]:
    """``{english: japanese}``, with `kind`'s own translations layered on top.

    `kind` names a `translations_by_kind` bucket, the way `japanese_index` does
    on the import side, so both directions agree on which name an entry has.
    """
    out = dict(cat.get("translations") or {})
    if kind:
        out.update((cat.get("translations_by_kind") or {}).get(kind) or {})
    return out


def named(names: dict[str, str], english: str) -> str:
    """`english` as the catalog spells it in Japanese, or as it is.

    An untranslated name goes through in English rather than being dropped: the
    import indexes the English name too, so it still reads back, and a player
    looking at the sheet can see what it was.
    """
    return names.get(english) or english


__all__ = ["Limits", "named", "translator"]
