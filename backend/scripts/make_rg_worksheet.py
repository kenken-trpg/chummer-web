#!/usr/bin/env python3
"""Phase 5 of docs/plans/translation-plan.md — build the Run & Gun worksheet.

Emits a TSV of every RG-sourced catalog entry to fill in while reading the
Japanese Run & Gun, then `import_rg_worksheet.py` turns the filled file back
into `scripts/ja_curated_rg.py`.

Rows are ordered by the page number Chummer records for each entry, so the
worksheet runs in the same order as the physical book. (Whether the Japanese
edition keeps the English page numbering is an assumption — check it on the
first batch and fall back to `--sort name` if it does not hold.)

The `official` column is what you fill in:

    <blank>   not looked at yet
    <term>    the term printed in the Japanese edition
    -         no official term / deliberately left on English fallback

The `current` column is what the app shows today. For most rows that is an
unverified community translation from upstream `ja-jp_data.xml`, so a row
needs a decision even when it already looks Japanese.

Output goes outside the repo by default ($JA_REF_DIR, default ~/Downloads):
a half-filled worksheet is scratch, not a source file.

Usage:
  python scripts/make_rg_worksheet.py [--bucket armor,armor_mods] [--out PATH]
                                      [--pending-only] [--sort page|name]
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
DEFAULT_OUT = _REF_DIR / "rg-worksheet.tsv"
OVERLAY = ROOT / "data" / "ja_overrides" / "data.json"

JP_RE = re.compile(r"[぀-ヿ㐀-鿿]")
SOURCE = "RG"

COLUMNS = ("status", "bucket", "page", "english", "current", "from", "official", "note")

# batch order from the plan: most-visible first
BUCKET_ORDER = (
    "martial_arts",
    "martial_art_techniques",
    "qualities",
    "armor",
    "armor_mods",
    "weapons",
    "weapon_accessories",
    "gear",
    "commlinks",
    "category",
)


class Entry:
    """One RG name, with every bucket and page the catalog files it under."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.buckets: set[str] = set()
        self.pages: set[int] = set()

    @property
    def bucket(self) -> str:
        return "+".join(sorted(self.buckets, key=_bucket_rank))

    @property
    def page(self) -> str:
        return str(min(self.pages)) if self.pages else ""

    @property
    def rank(self) -> tuple[int, int, str]:
        return (
            min((_bucket_rank(b) for b in self.buckets), default=len(BUCKET_ORDER)),
            min(self.pages, default=10**6),
            self.name,
        )


def _bucket_rank(bucket: str) -> int:
    return BUCKET_ORDER.index(bucket) if bucket in BUCKET_ORDER else len(BUCKET_ORDER)


def rg_entries() -> dict[str, Entry]:
    """Every ``source == "RG"`` name and category the catalog exposes.

    Shared with tests/test_rg_coverage.py — the worksheet and the coverage
    ledger have to be counting the same set of names or the burn-down lies.
    """
    from app.data_loader import catalog

    found: dict[str, Entry] = {}

    def add(name: str, bucket: str, page: object) -> None:
        entry = found.setdefault(name, Entry(name))
        entry.buckets.add(bucket)
        try:
            entry.pages.add(int(str(page)))
        except (TypeError, ValueError):
            pass

    def walk(top: str, obj: object, source: str | None = None) -> None:
        if isinstance(obj, dict):
            here = obj.get("source")
            source = here if isinstance(here, str) and here else source
            if source == SOURCE:
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


def _status(name: str) -> str:
    from scripts.ja_curated_rg import RG, RG_UNVERIFIED

    if name in RG:
        return "verified"
    if name in RG_UNVERIFIED:
        return "skipped"
    return "pending"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--bucket", help="comma-separated buckets to include (default: all)")
    ap.add_argument("--pending-only", action="store_true", help="drop rows already decided")
    ap.add_argument("--sort", choices=("page", "name"), default="page")
    args = ap.parse_args(argv)

    from app.data_loader import load_translations

    overlay: dict[str, str] = json.loads(OVERLAY.read_text(encoding="utf-8"))
    merged = load_translations()

    entries = list(rg_entries().values())
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
        status = _status(entry.name)
        counts[status] += 1
        if args.pending_only and status != "pending":
            continue
        current = merged.get(entry.name, "")
        if not (current and JP_RE.search(current)):
            current, origin = "", "—"
        elif entry.name in overlay:
            origin = "overlay"
        else:
            origin = "upstream"
        rows.append(
            {
                "status": status,
                "bucket": entry.bucket,
                "page": entry.page,
                "english": entry.name,
                "current": current,
                "from": origin,
                "official": "",
                "note": "",
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    total = sum(counts.values())
    print(f"→ {args.out}  ({len(rows)} rows)")
    print(
        f"   RG names: {total}  pending {counts['pending']} / verified {counts['verified']} / skipped {counts['skipped']}"
    )
    print("   fill the `official` column ('-' = leave on English), then:")
    print("     python scripts/import_rg_worksheet.py --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
