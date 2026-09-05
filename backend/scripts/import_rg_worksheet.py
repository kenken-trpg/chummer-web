#!/usr/bin/env python3
"""Phase 5 of docs/plans/translation-plan.md — fold a filled worksheet back in.

Reads the TSV produced by `make_rg_worksheet.py` and rewrites the two tables in
`scripts/ja_curated_rg.py`:

    official column holds a term  ->  RG[english] = term
    official column holds "="     ->  RG[english] = the row's `current` value
    official column holds "-"     ->  RG_UNVERIFIED += (english,)
    official column is empty      ->  still pending, left alone

The "=" form is what makes the verification pass tractable: most of the RG
names already carry an upstream community translation, and the common answer
is "the book says exactly that". Retyping several hundred identical terms
would introduce more errors than it caught, so "=" means "checked, and the
`current` column is right" — it pins the same term, from the same reader,
with the same authority as a typed one.

Runs are additive, so a worksheet covering one batch does not drop the batches
already done; pass `--replace` to rebuild the tables from this file alone.

Only the prose above the `RG: dict[str, str] = {` line is preserved — the two
tables below it are regenerated, grouped by catalog bucket and sorted, so the
diff of a batch is the batch.

Without `--write` it reports what would change and touches nothing.

A worksheet that has been through a spreadsheet comes back changed in ways
that have nothing to do with its content, so the reader is deliberately
forgiving about shape and strict about meaning:

  * the delimiter is sniffed (tab, comma or semicolon — a ja-locale export
    writes `;`), a UTF-8 BOM is stripped, and any preamble above the header
    row (Numbers writes the sheet's name there) is skipped;
  * `--worksheet` may name a directory, in which case the newest file matching
    `*rg-worksheet*.{tsv,csv}` in it is used, and which one is reported;
  * a `current` cell that no longer matches what the generator would write, or
    a `note` holding Japanese, is reported as an answer that landed in the
    wrong column. It is NOT imported unless `--accept-column` says so. This
    matters: most rows arrive with a `current` value nobody has verified, and
    quietly harvesting that column would turn the whole pass into a copy of
    the upstream community translation.

Usage:
  python scripts/import_rg_worksheet.py [--worksheet PATH] [--write] [--replace]
                                        [--accept-column current,note]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_REF_DIR = Path(os.environ.get("JA_REF_DIR") or (Path.home() / "Downloads"))
DEFAULT_WORKSHEET = _REF_DIR
MODULE = ROOT / "scripts" / "ja_curated_rg.py"

JP_RE = re.compile(r"[぀-ヿ㐀-鿿]")
MARKER = "RG: dict[str, str] = {"
SKIP = "-"
AGREE = "="

WORKSHEET_GLOBS = ("*rg-worksheet*.tsv", "*rg-worksheet*.csv")
DELIMITERS = "\t,;"
SPILL_COLUMNS = ("current", "note")


def resolve_worksheet(path: Path) -> tuple[Path | None, str]:
    """-> (the file to read, a line explaining the choice).

    A directory means "the newest worksheet in here", because the file comes
    back renamed as often as not (`done_rg-worksheet.csv`, `…(1).tsv`).
    """
    if path.is_dir():
        found = sorted(
            (p for glob in WORKSHEET_GLOBS for p in path.glob(glob)),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not found:
            return None, f"no {'/'.join(WORKSHEET_GLOBS)} in {path}"
        note = f"reading {found[0]}"
        if len(found) > 1:
            note += f"  (newest of {len(found)}; --worksheet to pick another)"
        return found[0], note
    if path.exists():
        return path, f"reading {path}"
    return None, f"no worksheet at {path} (run make_rg_worksheet.py first)"


class Parsed(NamedTuple):
    rows: list[dict[str, str]]
    notes: list[str]  # shape we worked around — worth saying, not worth failing over
    problems: list[str]  # the file cannot be read as a worksheet at all


class Read(NamedTuple):
    translations: dict[str, str]
    skipped: set[str]
    problems: list[str]
    notes: list[str]


def _rows(path: Path) -> Parsed:
    """Parse a worksheet however a spreadsheet handed it back.

    Rows carry a "_line" key so a problem can point back at the file.
    """
    notes: list[str] = []
    lines = path.read_text(encoding="utf-8-sig").splitlines()

    header_at = next((i for i, line in enumerate(lines) if "english" in line.lower()), None)
    if header_at is None:
        return Parsed([], notes, [f"{path.name} has no header row containing 'english'"])
    if header_at:
        notes.append(f"skipped {header_at} line(s) above the header")

    header = lines[header_at]
    delimiter = max(DELIMITERS, key=header.count)
    if not header.count(delimiter):
        return Parsed(
            [], notes, [f"{path.name}: no tab, comma or semicolon in the header — cannot tell the columns apart"]
        )
    if delimiter != "\t":
        notes.append(f"delimiter is {delimiter!r}, not tab")

    rows: list[dict[str, str]] = []
    for offset, row in enumerate(csv.DictReader(lines[header_at:], delimiter=delimiter)):
        clean = {(k or "").strip(): (v or "").strip() for k, v in row.items() if k}
        clean["_line"] = str(header_at + 2 + offset)
        rows.append(clean)
    return Parsed(rows, notes, [])


def _read_worksheet(
    path: Path,
    accept: tuple[str, ...] = (),
    expected_current: dict[str, str] | None = None,
) -> Read:
    """`expected_current` is `make_rg_worksheet.current_terms()`.

    Given it, a `current` cell that differs from what the generator wrote is
    treated as an answer typed into the wrong column: reported, and imported
    only if "current" is in `accept`.
    """
    translations: dict[str, str] = {}
    skipped: set[str] = set()
    rows, notes, problems = _rows(path)

    for row in rows:
        lineno = row.get("_line", "?")
        name = row.get("english", "")
        official = row.get("official", "")
        if not name:
            continue

        if not official:
            official, problems = _spilled(row, name, lineno, accept, expected_current, problems)
            if not official:
                continue

        if official == SKIP:
            skipped.add(name)
            continue
        if official == AGREE:
            official = row.get("current", "")
            if not official:
                problems.append(f"L{lineno}: {name!r} marked '=' but its `current` column is empty")
                continue
        if not JP_RE.search(official):
            problems.append(f"L{lineno}: {name!r} -> {official!r} has no Japanese (use '-' to leave it in English)")
            continue
        if name in translations and translations[name] != official:
            problems.append(f"L{lineno}: {name!r} given twice with different terms")
            continue
        translations[name] = official

    both = sorted(set(translations) & skipped)
    problems += [f"{name!r} is both translated and marked '-'" for name in both]
    return Read(translations, skipped, problems, notes)


def _spilled(
    row: dict[str, str],
    name: str,
    lineno: str,
    accept: tuple[str, ...],
    expected_current: dict[str, str] | None,
    problems: list[str],
) -> tuple[str, list[str]]:
    """An answer that landed somewhere other than `official`. -> (value, problems).

    `current` only counts as an answer when it differs from what the generator
    put there; otherwise every untouched row would look like one, and the
    unverified upstream translation would be imported as if a human had read it.
    """
    for column in SPILL_COLUMNS:
        value = row.get(column, "")
        if not value:
            continue
        if column == "current":
            if expected_current is None or value == expected_current.get(name, ""):
                continue
        elif not JP_RE.search(value):
            continue
        if column in accept:
            return value, problems
        problems.append(
            f"L{lineno}: {name!r} has {value!r} in `{column}` but `official` is empty "
            f"— move it, or re-run with --accept-column {column}"
        )
        return "", problems
    return "", problems


def _render(translations: dict[str, str], skipped: set[str]) -> str:
    from scripts.make_rg_worksheet import rg_entries

    entries = rg_entries()

    def bucket_of(name: str) -> str:
        entry = entries.get(name)
        return entry.bucket if entry else "(not in catalog)"

    # str() literals via json.dumps: double-quoted and escaped the way the
    # formatter wants them, so the generated file survives `ruff format --check`.
    def lit(value: str) -> str:
        return json.dumps(value, ensure_ascii=False)

    lines = [MARKER]
    for bucket in sorted({bucket_of(n) for n in translations}):
        names = sorted(n for n in translations if bucket_of(n) == bucket)
        lines.append(f"    # --- {bucket} " + "-" * max(3, 66 - len(bucket)))
        lines += [f"    {lit(name)}: {lit(translations[name])}," for name in names]
    lines.append("}")
    lines.append("")
    lines.append("# RG names deliberately left on English fallback (no official term / not pinned)")
    if skipped:
        lines.append("RG_UNVERIFIED: tuple[str, ...] = (")
        lines += [f"    {lit(name)}," for name in sorted(skipped)]
        lines.append(")")
    else:
        lines.append("RG_UNVERIFIED: tuple[str, ...] = ()")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--worksheet", type=Path, default=DEFAULT_WORKSHEET, help="a worksheet file, or a directory to search"
    )
    ap.add_argument("--write", action="store_true", help="rewrite scripts/ja_curated_rg.py")
    ap.add_argument("--replace", action="store_true", help="drop entries not in this worksheet")
    ap.add_argument(
        "--accept-column",
        default="",
        help=f"import answers found in these columns too ({','.join(SPILL_COLUMNS)})",
    )
    args = ap.parse_args(argv)

    worksheet, note = resolve_worksheet(args.worksheet)
    if worksheet is None:
        print(f"error: {note}", file=sys.stderr)
        return 2
    print(note)

    from scripts.ja_curated_rg import RG as CURRENT
    from scripts.ja_curated_rg import RG_UNVERIFIED as CURRENT_SKIPPED
    from scripts.make_rg_worksheet import current_terms, rg_entries

    accept = tuple(c.strip() for c in args.accept_column.split(",") if c.strip())
    unknown = [c for c in accept if c not in SPILL_COLUMNS]
    if unknown:
        print(f"error: --accept-column {unknown} — choose from {SPILL_COLUMNS}", file=sys.stderr)
        return 2

    translations, skipped, problems, notes = _read_worksheet(worksheet, accept, current_terms())
    for line in notes:
        print(f"  ({line})")

    if not args.replace:
        merged = dict(CURRENT)
        merged.update(translations)
        merged_skipped = (set(CURRENT_SKIPPED) | skipped) - set(translations)
    else:
        merged, merged_skipped = dict(translations), set(skipped)

    known = set(rg_entries())
    orphans = sorted((set(merged) | merged_skipped) - known)
    problems += [f"{name!r} is not an RG name in the catalog" for name in orphans]

    added = sorted(set(merged) - set(CURRENT))
    changed = sorted(k for k in set(merged) & set(CURRENT) if merged[k] != CURRENT[k])
    dropped = sorted(set(CURRENT) - set(merged))

    for name in added:
        print(f"  + {name} -> {merged[name]}")
    for name in changed:
        print(f"  ~ {name}: {CURRENT[name]} -> {merged[name]}")
    for name in dropped:
        print(f"  - {name}")
    print(
        f"\ntranslated {len(merged)} / skipped {len(merged_skipped)} / "
        f"pending {len(known) - len(merged) - len(merged_skipped)} of {len(known)} RG names"
    )

    if problems:
        sys.stdout.flush()  # or the problems land above the report they belong to
        print("\nproblems:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    if not args.write:
        print("\n(dry run — pass --write to apply, then run scripts/regen_ja.sh)")
        return 0

    text = MODULE.read_text(encoding="utf-8")
    head, sep, _ = text.partition(MARKER)
    if not sep:
        print(f"error: {MODULE} has no {MARKER!r} marker", file=sys.stderr)
        return 2
    MODULE.write_text(head + _render(merged, merged_skipped), encoding="utf-8")
    print(f"\n→ {MODULE}\n   next: scripts/regen_ja.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
