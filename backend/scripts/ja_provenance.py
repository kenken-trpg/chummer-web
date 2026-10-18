"""Where each Japanese name the app shows comes from, for the import report.

A catalog name reaches the screen through three layers, each filling what the
one before left in English (see data_loader/loaders/translations.py and
data_loader/codex.py):

  1. upstream Chummer's ja-jp_data.xml — a community translation;
  2. our data.json overlay, rebuilt by import_ja_from_refs.py from several
     hand-kept tables and from chumJA's SR4 translation;
  3. the Shadowrun Codex's names, only for rows still in English.

The table is keyed by English name alone, so a translation made for one book's
item also lands on any other book's item of the same name — the complex form
Redundancy's 冗長化 is also what Data Trails' A.I. quality of that name reads.
So the report pairs every overlay entry with the kinds and books that carry
its name, and lists separately the ones no Japanese-printed row carries: by
the project's policy (supplement terms stay English) those are the ones to
look at again.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

JP_RE = re.compile(r"[぀-ヿ㐀-鿿]")

#: Top-level public catalog keys that are not rows of data.
_NOT_ROWS = {"books", "settings_presets", "translations", "translations_by_kind", "ui_strings", "weapon_ranges"}


@dataclass
class Carriers:
    """The rows that carry one English name: their kinds and books."""

    by_kind: dict[str, set[str]] = field(default_factory=dict)
    printed_ja: bool = False

    def add(self, kind: str, source: str, printed_ja: bool) -> None:
        self.by_kind.setdefault(kind, set()).add(source)
        self.printed_ja = self.printed_ja or printed_ja

    def books(self) -> set[str]:
        return set().union(*self.by_kind.values()) if self.by_kind else set()

    def render(self) -> str:
        return " / ".join(f"{kind}: {', '.join(sorted(srcs))}" for kind, srcs in sorted(self.by_kind.items()))


def ja_books(books: Iterable[Mapping[str, str]]) -> frozenset[str]:
    """Codes of the books with a Japanese edition — those with a Japanese title."""
    return frozenset(b["code"] for b in books if JP_RE.search(b.get("name_ja") or ""))


def carriers(public: Mapping[str, object], printed: frozenset[str]) -> dict[str, Carriers]:
    """English name -> the rows of the public catalog that carry it.

    A row is a dict with its own `source`. A name nested under one without a
    source of its own is a reference, not an item — a life module's granted
    skill, a quality's prerequisite tree, a metatype's built-in powers — and
    the book it would inherit is the referrer's, not its own: inheriting it
    put the RF lifestyle option Grid Subscription under SR5. A row the Codex
    reprints (`also_in`) counts as printed in Japanese. Categories are names
    too: they are listed under the kind ``category``.
    """
    out: dict[str, Carriers] = {}

    def walk(kind: str, obj: object) -> None:
        if isinstance(obj, dict):
            source = obj.get("source")
            if isinstance(source, str) and source:
                also = {str(a.get("source")) for a in obj.get("also_in") or [] if isinstance(a, dict)}
                in_ja = source in printed or bool(also & printed)
                name = obj.get("name")
                if isinstance(name, str) and name.strip():
                    out.setdefault(name.strip(), Carriers()).add(kind, source, in_ja)
                category = obj.get("category")
                if isinstance(category, str) and category.strip():
                    out.setdefault(category.strip(), Carriers()).add("category", source, in_ja)
            for key, value in obj.items():
                if key not in ("name", "source", "category", "also_in"):
                    walk(kind, value)
        elif isinstance(obj, list):
            for value in obj:
                walk(kind, value)

    for key, value in public.items():
        if key not in _NOT_ROWS:
            walk(key, value)
    return out


def layer_of(name: str, overlay: Mapping[str, str], upstream: Mapping[str, str], shown: Mapping[str, str]) -> str:
    """Which layer gives `name` the reading the app shows: one of
    ``overlay``, ``upstream``, ``codex`` or ``english``."""
    if overlay.get(name, name) != name:
        return "overlay"
    if upstream.get(name, name) != name:
        return "upstream"
    if shown.get(name, name) != name:
        return "codex"
    return "english"


LAYERS = ("upstream", "overlay", "codex", "english")


def per_book(
    found: Mapping[str, Carriers],
    overlay: Mapping[str, str],
    upstream: Mapping[str, str],
    shown: Mapping[str, str],
) -> dict[str, dict[str, int]]:
    """Book code -> how many of its names each layer translates."""
    out: dict[str, dict[str, int]] = {}
    for name, c in found.items():
        layer = layer_of(name, overlay, upstream, shown)
        for book in c.books():
            counts = out.setdefault(book, dict.fromkeys(LAYERS, 0))
            counts[layer] += 1
    return out
