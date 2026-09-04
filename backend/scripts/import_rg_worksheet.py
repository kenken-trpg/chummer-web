#!/usr/bin/env python3
"""Phase 5 of docs/plans/translation-plan.md — fold a filled worksheet back in.

Reads the TSV produced by `make_rg_worksheet.py` and rewrites the two tables in
`scripts/ja_curated_rg.py`:

    official column holds a term  ->  RG[english] = term
    official column holds "-"     ->  RG_UNVERIFIED += (english,)
    official column is empty      ->  still pending, left alone

Runs are additive, so a worksheet covering one batch does not drop the batches
already done; pass `--replace` to rebuild the tables from this file alone.

Only the prose above the `RG: dict[str, str] = {` line is preserved — the two
tables below it are regenerated, grouped by catalog bucket and sorted, so the
diff of a batch is the batch.

Without `--write` it reports what would change and touches nothing.

Usage:
  python scripts/import_rg_worksheet.py [--worksheet PATH] [--write] [--replace]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_REF_DIR = Path(os.environ.get("JA_REF_DIR") or (Path.home() / "Downloads"))
DEFAULT_WORKSHEET = _REF_DIR / "rg-worksheet.tsv"
MODULE = ROOT / "scripts" / "ja_curated_rg.py"

JP_RE = re.compile(r"[぀-ヿ㐀-鿿]")
MARKER = "RG: dict[str, str] = {"
SKIP = "-"


def _read_worksheet(path: Path) -> tuple[dict[str, str], set[str], list[str]]:
    """-> (translations, skipped names, problems)."""
    translations: dict[str, str] = {}
    skipped: set[str] = set()
    problems: list[str] = []
    with path.open(encoding="utf-8", newline="") as fh:
        for lineno, row in enumerate(csv.DictReader(fh, delimiter="\t"), start=2):
            name = (row.get("english") or "").strip()
            official = (row.get("official") or "").strip()
            if not name or not official:
                continue
            if official == SKIP:
                skipped.add(name)
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
    return translations, skipped, problems


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
    ap.add_argument("--worksheet", type=Path, default=DEFAULT_WORKSHEET)
    ap.add_argument("--write", action="store_true", help="rewrite scripts/ja_curated_rg.py")
    ap.add_argument("--replace", action="store_true", help="drop entries not in this worksheet")
    args = ap.parse_args(argv)

    if not args.worksheet.exists():
        print(f"error: no worksheet at {args.worksheet} (run make_rg_worksheet.py first)", file=sys.stderr)
        return 2

    translations, skipped, problems = _read_worksheet(args.worksheet)

    from scripts.ja_curated_rg import RG as CURRENT
    from scripts.ja_curated_rg import RG_UNVERIFIED as CURRENT_SKIPPED
    from scripts.make_rg_worksheet import rg_entries

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
