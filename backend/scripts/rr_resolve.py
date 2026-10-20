#!/usr/bin/env python3
"""Fill in the Chummer ids of the Role&Roll rows, and say what is left.

`data/role_and_roll/entries.tsv` is typed in from the magazine; see
docs/role-and-roll.md. For each row with no id yet:

- 英語（わかれば） filled in: the 出典原書's entries of that name (in the
  分類's sections) are its ids. Several are all taken — one name can be
  several Chummer entries, one per size or grade. `--write` saves them.
- 英語 empty: the candidates are listed, the entries whose current
  translation is the 和訳名 first. Copy the right one's English name into the
  row and run again.

Then every row is checked (`role_and_roll.problems`); the exit status is 1 if
anything is wrong.

Usage:
  python scripts/rr_resolve.py [--write] [--limit N]
  python scripts/rr_resolve.py --list BOOK [--category 分類]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.catalog_view import public_catalog  # noqa: E402
from app.data_loader import role_and_roll as rr  # noqa: E402


def _describe(section: str, row: dict[str, Any], translations: dict[str, str]) -> str:
    name = str(row.get("name") or "")
    ja = translations.get(name, "")
    shown = f" [{ja}]" if ja and ja != name else ""
    return f"{section}\tp.{row.get('page') or '?'}\t{name}{shown}"


def resolve(entries: list[rr.Entry], catalog: dict[str, Any], limit: int) -> list[rr.Entry]:
    """`entries` with the ids found by English name filled in; prints the rest."""
    translations = catalog.get("translations") or {}
    out = []
    for e in entries:
        if e.ids:
            out.append(e)
            continue
        found = rr.candidates(e, catalog)
        head = f"line {e.line}: vol.{e.vol} p.{e.page} {e.ja} ({e.source} / {e.category or '分類なし'})"
        if e.english:
            if found:
                ids = tuple(str(row["id"]) for _, row in found)
                print(f"{head} -> {e.english}: {len(ids)} id(s)")
                out.append(replace(e, ids=ids))
            else:
                print(f"{head}: no {e.source} entry is named {e.english!r}")
                out.append(e)
            continue
        out.append(e)
        if rr.source_code(e.source, catalog) is None:
            print(f"{head}: unknown 出典原書")
            continue
        found.sort(key=lambda hit: translations.get(str(hit[1].get("name"))) != e.ja)
        print(f"{head}: no English name, {len(found)} candidate(s)")
        for section, row in found[:limit]:
            print(f"    {_describe(section, row, translations)}")
        if len(found) > limit:
            print(f"    … {len(found) - limit} more (narrow it with 分類, or --list)")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="save the ids found")
    parser.add_argument("--limit", type=int, default=20, help="candidates shown per row")
    parser.add_argument("--list", metavar="BOOK", help="list a book's entries and stop")
    parser.add_argument("--category", default="", help="with --list: only this 分類")
    parser.add_argument("--file", type=Path, default=rr.DATA, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    catalog = public_catalog()
    if args.list:
        probe = rr.Entry(0, "", None, "", args.list, args.category, "", "", "", ())
        if rr.source_code(args.list, catalog) is None:
            print(f"unknown book {args.list!r}", file=sys.stderr)
            return 1
        for section, row in rr.candidates(probe, catalog):
            print(_describe(section, row, catalog.get("translations") or {}))
        return 0

    entries = rr.load(args.file)
    resolved = resolve(entries, catalog, args.limit)
    if args.write and resolved != entries:
        rr.save(resolved, args.file)
        print(f"wrote {args.file}")
    issues = rr.problems(resolved, catalog)
    for issue in issues:
        print(issue, file=sys.stderr)
    left = sum(1 for e in resolved if not e.ids)
    done = len(resolved) - left
    print(f"{done} row(s) with ids, {left} without, {len(issues)} problem(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
