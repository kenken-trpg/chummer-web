"""Role&Roll (ロール＆ロール), the Japanese TRPG magazine.

Some issues carry, under an official licence, Japanese translations of parts
of SR5 supplements that have no Japanese edition. Like the Shadowrun Codex
(codex.py) that makes an issue a second place an item Chummer already has is
printed, so each issue is a book of its own (`RR213` …) that names its page in
`also_in`.

One difference from the Codex: an issue's Japanese names apply only while
that issue is ticked. `stamp` therefore returns them per book instead of
folding them into the global `translations`.

The data is typed in by hand from the magazine, into one TSV
(`backend/data/role_and_roll/entries.tsv`, columns `COLUMNS`). The English
name is often not printed, so a row may start with only its Japanese name and
original book; `scripts/rr_resolve.py` lists the candidates and fills in the
Chummer id. A row without an id is work in progress and changes nothing.
See docs/role-and-roll.md.

`public_catalog` carries the stamps and `book_translations`, but not the
issues themselves in `books`: they show up in the book list only once the UI
can fold them away.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._xml import _BACKEND

PREFIX = "RR"
FIRST_ISSUE = 213
#: The latest issue (2026-10). Raise it when a new one comes out.
LAST_ISSUE = 241

DATA = _BACKEND / "data" / "role_and_roll" / "entries.tsv"

#: The TSV header, in order. All but `id` are read off the magazine.
COLUMNS = ("URL", "vol.", "頁", "出典原書", "分類", "和訳名", "英語（わかれば）", "備考", "id")

#: 分類 -> the catalog sections it searches. Only narrows the candidates: an
#: unknown 分類 searches every section.
CATEGORIES: dict[str, tuple[str, ...]] = {
    "資質": ("qualities",),
    "武器": ("weapons",),
    "武器改造": ("weapon_accessories", "weapon_mounts"),
    "防具": ("armor", "armor_mods"),
    "サイバーウェア": ("cyberware",),
    "バイオウェア": ("bioware",),
    "装備": ("gear", "commlinks", "cyberdecks", "rccs", "sensors", "optics"),
    "ドラッグ": ("drugs", "drug_components"),
    "呪文": ("spells",),
    "アデプトパワー": ("powers", "enhancements"),
    "メタマジック": ("metamagics",),
    "エコー": ("echoes",),
    "複合体": ("complex_forms",),
    "プログラム": ("programs", "ai_programs", "apps"),
    "ヴィークル": ("vehicles", "drones"),
    "ヴィークル改造": ("vehicle_mods",),
    "格闘技": ("martial_arts", "martial_art_techniques"),
    "メンター": ("mentors", "paragons"),
    "伝統": ("traditions",),
    "ライフスタイル": ("lifestyles", "lifestyle_qualities"),
    "メタタイプ": ("metatypes",),
    "クリッターパワー": ("buyable_critter_powers",),
}

#: Not rows: walking into these would match their keys as names.
_SKIP = ("translations", "translations_by_kind", "text_translations", "ui_strings", "books")


def code(vol: int) -> str:
    return f"{PREFIX}{vol}"


def books() -> list[dict[str, Any]]:
    """One book per issue, oldest first. `group` lets the UI fold them."""
    return [
        {
            "code": code(vol),
            "name": f"Role&Roll Vol.{vol}",
            "name_ja": f"Role&Roll Vol.{vol}",
            "group": PREFIX,
        }
        for vol in range(FIRST_ISSUE, LAST_ISSUE + 1)
    ]


@dataclass(frozen=True)
class Entry:
    """One TSV row. `line` is its line in the file, for messages."""

    line: int
    url: str
    vol: int | None
    page: str
    source: str
    category: str
    ja: str
    english: str
    note: str
    ids: tuple[str, ...]

    @property
    def book(self) -> str:
        return code(self.vol) if self.vol is not None else ""

    def row(self) -> list[str]:
        """Back to the TSV's cells, as `COLUMNS` orders them."""
        vol = "" if self.vol is None else str(self.vol)
        return [
            self.url,
            vol,
            self.page,
            self.source,
            self.category,
            self.ja,
            self.english,
            self.note,
            " ".join(self.ids),
        ]


def _vol(text: str) -> int | None:
    match = re.fullmatch(r"(?:vol\.?\s*)?(\d+)", text.strip(), re.IGNORECASE)
    return int(match.group(1)) if match else None


def load(path: Path = DATA) -> list[Entry]:
    """The rows of `path`. A header other than `COLUMNS` raises ValueError,
    so a column pasted in the wrong place fails loudly instead of landing a
    Japanese name in the page column."""
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh, delimiter="\t"))
    if not rows or tuple(cell.strip() for cell in rows[0]) != COLUMNS:
        raise ValueError(f"{path}: the header must be {' / '.join(COLUMNS)}")
    out = []
    for line, cells in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in cells):
            continue
        cells = [cell.strip() for cell in cells] + [""] * (len(COLUMNS) - len(cells))
        url, vol, page, source, category, ja, english, note, ids = cells[: len(COLUMNS)]
        out.append(Entry(line, url, _vol(vol), page, source, category, ja, english, note, tuple(ids.split())))
    return out


def save(entries: Iterable[Entry], path: Path = DATA) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(entry.row() for entry in entries)


def _rows(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, list):
        for child in node:
            yield from _rows(child)
    elif isinstance(node, dict):
        if "source" in node and "id" in node:
            yield node
        for key, child in node.items():
            if key not in _SKIP:
                yield from _rows(child)


def source_code(text: str, catalog: dict[str, Any]) -> str | None:
    """The book code 出典原書 names: its code (`CF`) or its English or
    Japanese title, any case."""
    wanted = text.strip().casefold()
    for book in catalog.get("books") or []:
        names = (book.get("code"), book.get("name"), book.get("name_ja"))
        if wanted and wanted in {str(n).casefold() for n in names if n}:
            return str(book["code"])
    return None


def sections(category: str, catalog: dict[str, Any]) -> tuple[str, ...]:
    return CATEGORIES.get(category.strip()) or tuple(k for k in catalog if k not in _SKIP)


def candidates(entry: Entry, catalog: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """(section, row) for every catalog row this entry could be: its 出典原書's
    rows in its 分類's sections, by English name too when it has one. The
    same row can sit in several places (a quality also listed under a
    metatype), so each id appears once."""
    book = source_code(entry.source, catalog)
    english = entry.english.casefold()
    seen: set[str] = set()
    out = []
    for section in sections(entry.category, catalog):
        for row in _rows(catalog.get(section)):
            if row.get("source") != book or str(row["id"]) in seen:
                continue
            if english and str(row.get("name") or "").casefold() != english:
                continue
            seen.add(str(row["id"]))
            out.append((section, row))
    return out


def problems(entries: Iterable[Entry], catalog: dict[str, Any]) -> list[str]:
    """What is wrong with the rows, one message each. Rows without an id yet
    are not wrong, just unfinished; `rr_resolve.py` lists those."""
    by_id: dict[str, dict[str, Any]] = {}
    for found in _rows({k: v for k, v in catalog.items() if k not in _SKIP}):
        by_id.setdefault(str(found["id"]), found)
    urls: dict[int, str] = {}
    seen: set[tuple[int, str]] = set()
    out = []
    for e in entries:
        where = f"line {e.line}"
        if e.vol is None or not FIRST_ISSUE <= e.vol <= LAST_ISSUE:
            out.append(f"{where}: vol. must be {FIRST_ISSUE}-{LAST_ISSUE}")
            continue
        if e.url and urls.setdefault(e.vol, e.url) != e.url:
            out.append(f"{where}: vol.{e.vol} has another URL on an earlier line")
        if not e.ja:
            out.append(f"{where}: 和訳名 is empty")
        book = source_code(e.source, catalog)
        if book is None:
            out.append(f"{where}: unknown 出典原書 {e.source!r}")
        for id_ in e.ids:
            row = by_id.get(id_)
            if row is None:
                out.append(f"{where}: no catalog entry has id {id_}")
                continue
            if book is not None and row.get("source") != book:
                out.append(f"{where}: {row.get('name')} is from {row.get('source')}, not {book}")
            if e.english and str(row.get("name") or "").casefold() != e.english.casefold():
                out.append(f"{where}: id {id_} is {row.get('name')!r}, not {e.english!r}")
            if (e.vol, id_) in seen:
                out.append(f"{where}: {row.get('name')} is listed twice in vol.{e.vol}")
            seen.add((e.vol, id_))
    return out


def stamp(catalog: dict[str, Any], entries: Iterable[Entry]) -> dict[str, dict[str, str]]:
    """Add each issue to `also_in` of the rows it reprints.

    Returns book code -> English name -> the issue's Japanese, for the
    frontend to apply only while that issue is ticked."""
    hits: dict[str, list[Entry]] = {}
    for e in entries:
        if e.vol is not None and e.ja:
            for id_ in e.ids:
                hits.setdefault(id_, []).append(e)
    names: dict[str, dict[str, str]] = {}
    for row in _rows({k: v for k, v in catalog.items() if k not in _SKIP}):
        for e in hits.get(str(row["id"]), ()):
            also_in = row.setdefault("also_in", [])
            if not any(a.get("source") == e.book for a in also_in):
                also_in.append({"source": e.book, "page": e.page})
            names.setdefault(e.book, {})[str(row.get("name") or "")] = e.ja
    return names


def book_translations(catalog: dict[str, Any], codex_names: dict[str, str]) -> dict[str, dict[str, str]]:
    """`stamp` with the shipped entries, minus the names the Codex prints.

    The Codex is in the 日本語環境 every Japanese table starts from, so its
    name is the one players know; an issue only names what it alone prints.
    Over everything else — the community translations from upstream, this
    app's own — the ticked issue wins: it is the licensed Japanese."""
    names = stamp(catalog, load())
    for table in names.values():
        for english in codex_names:
            table.pop(english, None)
    return {book: table for book, table in names.items() if table}
