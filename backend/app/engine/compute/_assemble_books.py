"""Phase 19 helper — the warning for what the character holds from books the
settings no longer allow. Reads the finished ``derived`` blob."""

from __future__ import annotations

from ...data_loader import catalog
from ...notices import Notice, notice, terms
from .derived_types import DerivedDict

#: How many names the out-of-book warning spells out before it stops. A
#: character imported against the wrong settings can be wrong in fifty places,
#: and a warning that is fifty names long is not read.
OUT_OF_BOOK_NAMES_SHOWN = 8


def _owned_sources(node: object, books: set[str], out: dict[str, set[str]]) -> None:
    """Every ``{name, source}`` the derived blob holds, as ``name -> sources``.

    A generic walk rather than a list of sections. The blob has forty places a
    sourced thing can sit — a weapon's accessories, a lifestyle's qualities,
    a drone's sensors — and they are also reachable by more than one path, so
    naming them would be both long and out of date by the next section anyone
    adds. Keying by name collapses the duplicate paths for free.

    Only a ``source`` that is a book code counts: an effect row's ``source``
    names what granted it instead (the dice pool Quick Healer adds to Heal is
    ``{name: "Heal", source: "Quick Healer"}``). And every source a name has is
    kept, not the last one walked, so the answer does not hang on which key
    of the blob comes first.
    """
    if isinstance(node, dict):
        name, source = node.get("name"), node.get("source")
        if isinstance(name, str) and isinstance(source, str) and source in books:
            out.setdefault(name, set()).add(source)
        for value in node.values():
            _owned_sources(value, books, out)
    elif isinstance(node, list):
        for value in node:
            _owned_sources(value, books, out)


def _out_of_book_warning(derived: DerivedDict, books: list[str]) -> Notice | None:
    """What the character holds that the settings' books do not allow.

    Nothing stops the character being built or printed: a GM who drops a book
    mid-campaign has not confiscated the gear, and a save imported from
    Chummer arrives with whatever it arrives with. But the pick lists no
    longer offer these, so without this the only clue is an entry you cannot
    buy a second one of.

    An entry with no ``source`` is allowed, the same rule the pick lists use:
    house-ruled and generated entries belong to no book.
    """
    if not books:  # empty means unrestricted, not "no books at all"
        return None
    allowed = set(books)
    owned: dict[str, set[str]] = {}
    _owned_sources(derived, {book["code"] for book in catalog().get("books") or []}, owned)
    outside = {name: sources - allowed for name, sources in owned.items() if sources - allowed}
    offending = sorted(outside)
    if not offending:
        return None
    more = max(0, len(offending) - OUT_OF_BOOK_NAMES_SHOWN)
    return notice(
        # two keys rather than one with an empty tail: "…: A / B ほか 0 件" is
        # not a sentence anyone wants to read
        "engine.settings.outOfBooksMore" if more else "engine.settings.outOfBooks",
        count=len(offending),
        names=terms(offending[:OUT_OF_BOOK_NAMES_SHOWN]),
        more=more,
        books=", ".join(sorted(set().union(*outside.values()))),
    )
