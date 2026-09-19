#!/usr/bin/env python3
"""Phase 5 of docs/plans/translation-plan.md — build one book's worksheet.

Emits a TSV of every catalog entry a given book is the source of, to fill in
while reading that book's Japanese text, then `import_ja_worksheet.py` turns the
filled file back into `scripts/ja_curated_<slug>.py`.

Which books can be passed, and what a reader answers from, is
`scripts/ja_books.py` — for Run & Gun that is the Japanese edition, for Run
Faster, Street Grimoire and Data Trails it is the Shadowrun Codex, which has no
page in common with them (the header says so when it applies).

Rows are ordered by the page number Chummer records for each entry, so a
worksheet for a book with a Japanese edition runs in the same order as the
physical book.

The `official` column is what you fill in:

    <blank>   not looked at yet
    =         the `current` column already matches the book — pin it as is
    <term>    the term printed in the Japanese text (differs from `current`)
    -         no official term / deliberately left on English fallback

The `current` column is what the app shows today. For most rows that is an
unverified community translation from upstream `ja-jp_data.xml`, so a row
needs a decision even when it already looks Japanese.

Output goes outside the repo by default ($JA_REF_DIR, default ~/Downloads):
a half-filled worksheet is scratch, not a source file.

Usage:
  python scripts/make_ja_worksheet.py [--book RG] [--bucket armor,armor_mods]
                                      [--out PATH] [--pending-only]
                                      [--sort page|name]
"""

from __future__ import annotations

import argparse
import csv
import importlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ja_books import BOOKS, Book, book  # noqa: E402

_REF_DIR = Path(os.environ.get("JA_REF_DIR") or (Path.home() / "Downloads"))
OVERLAY = ROOT / "data" / "ja_overrides" / "data.json"

JP_RE = re.compile(r"[぀-ヿ㐀-鿿]")

COLUMNS = ("status", "bucket", "page", "english", "current", "from", "official", "note")


def default_out(bk: Book) -> Path:
    return _REF_DIR / f"{bk.slug}-worksheet.tsv"


class Entry:
    """One name, with every bucket and page the catalog files it under."""

    def __init__(self, name: str, bk: Book) -> None:
        self.name = name
        self.book = bk
        self.buckets: set[str] = set()
        self.pages: set[int] = set()

    @property
    def bucket(self) -> str:
        return "+".join(sorted(self.buckets, key=self.book.bucket_rank))

    @property
    def page(self) -> str:
        return str(min(self.pages)) if self.pages else ""

    @property
    def rank(self) -> tuple[int, int, str]:
        return (
            min((self.book.bucket_rank(b) for b in self.buckets), default=len(self.book.buckets)),
            min(self.pages, default=10**6),
            self.name,
        )


def book_entries(bk: Book) -> dict[str, Entry]:
    """Every ``source == bk.code`` name and category the catalog exposes.

    Shared with tests/test_book_coverage.py — the worksheet and the coverage
    ledger have to be counting the same set of names or the burn-down lies.
    """
    from app.data_loader import catalog

    found: dict[str, Entry] = {}

    def add(name: str, bucket: str, page: object) -> None:
        entry = found.setdefault(name, Entry(name, bk))
        entry.buckets.add(bucket)
        try:
            entry.pages.add(int(str(page)))
        except (TypeError, ValueError):
            pass

    def walk(top: str, obj: object, source: str | None = None) -> None:
        if isinstance(obj, dict):
            here = obj.get("source")
            source = here if isinstance(here, str) and here else source
            if source == bk.code:
                name = obj.get("name")
                if isinstance(name, str) and name.strip():
                    add(name.strip(), top, obj.get("page"))
                category = obj.get("category")
                if isinstance(category, str) and category.strip():
                    add(category.strip(), "category", None)
            for key, value in obj.items():
                if key in ("name", "source", "category"):
                    continue
                walk(top, value, source)
        elif isinstance(obj, list):
            for value in obj:
                walk(top, value, source)

    cat = catalog()
    for key, value in cat.items():
        if key in {"translations", "ui_strings"}:
            continue
        walk(key, value)
    return found


def current_terms(bk: Book) -> dict[str, str]:
    """The `current` / `from` columns: what the app shows for each name today.

    A name whose merged translation is not actually Japanese renders as blank
    with origin "—", so the column answers "is there a Japanese term here at
    all" rather than "is there a dictionary entry".

    Shared with import_ja_worksheet.py, which recomputes this to tell a cell
    the generator wrote from one a human typed over it. That only works because
    the two sides agree exactly, so keep this the single definition.
    """
    from app.data_loader import load_translations

    merged = load_translations()
    out: dict[str, str] = {}
    for name in book_entries(bk):
        current = merged.get(name, "")
        if not (current and JP_RE.search(current)):
            out[name] = ""
        else:
            out[name] = current
    return out


def decided(bk: Book) -> tuple[dict[str, str], tuple[str, ...]]:
    """-> (the book's verified terms, the names left on English fallback).

    Missing module means a book nobody has started; an unstarted pass and an
    empty one are the same thing here, so neither is an error.
    """
    try:
        module = importlib.import_module(f"scripts.{bk.module}")
    except ModuleNotFoundError:
        return {}, ()
    return getattr(module, bk.table, {}), getattr(module, bk.skipped_table, ())


def _origin(name: str, current: str, overlay: dict[str, str]) -> str:
    if not current:
        return "—"
    return "overlay" if name in overlay else "upstream"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--book", default="RG", help=f"source code: {', '.join(sorted(BOOKS))}")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--bucket", help="comma-separated buckets to include (default: all)")
    ap.add_argument("--pending-only", action="store_true", help="drop rows already decided")
    ap.add_argument("--sort", choices=("page", "name"), default="page")
    args = ap.parse_args(argv)

    bk = book(args.book)
    out = args.out or default_out(bk)

    overlay: dict[str, str] = json.loads(OVERLAY.read_text(encoding="utf-8"))
    current_by_name = current_terms(bk)
    verified, skipped_names = decided(bk)

    entries = list(book_entries(bk).values())
    if args.bucket:
        wanted = {b.strip() for b in args.bucket.split(",") if b.strip()}
        entries = [e for e in entries if e.buckets & wanted]
    if args.sort == "page":
        entries.sort(key=lambda e: e.rank)
    else:
        entries.sort(key=lambda e: e.name)

    rows = []
    counts = {"pending": 0, "verified": 0, "skipped": 0}
    for entry in entries:
        if entry.name in verified:
            status = "verified"
        elif entry.name in skipped_names:
            status = "skipped"
        else:
            status = "pending"
        counts[status] += 1
        if args.pending_only and status != "pending":
            continue
        current = current_by_name.get(entry.name, "")
        rows.append(
            {
                "status": status,
                "bucket": entry.bucket,
                "page": entry.page,
                "english": entry.name,
                "current": current,
                "from": _origin(entry.name, current, overlay),
                "official": "",
                "note": "",
            }
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    total = sum(counts.values())
    print(f"→ {out}  ({len(rows)} rows)")
    print(
        f"   {bk.code} ({bk.title}) names: {total}  pending {counts['pending']} / "
        f"verified {counts['verified']} / skipped {counts['skipped']}"
    )
    print(f"   answer from: {bk.ja_source}")
    if not bk.page_is_ja:
        print("   NOTE: the `page` column is the English book's — look terms up in the")
        print("         Codex's own index rather than reading straight down the worksheet.")
    blank = sum(1 for r in rows if not r["current"])
    if blank:
        print(f"   {blank} of {len(rows)} rows have no Japanese term today: '=' cannot answer those.")
    print("   fill the `official` column ('=' = `current` is right, '-' = leave on English), then:")
    print(f"     python scripts/import_ja_worksheet.py --book {bk.code} --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
