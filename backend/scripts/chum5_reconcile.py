#!/usr/bin/env python3
"""Check the .chum5 import against the saves Chummer itself wrote.

Chummer ships real characters in ``Chummer.Tests/TestFiles``. Each is run
through ``chum5_to_state`` -> ``import_character`` and compared with what the
save already says, so the answer comes from Chummer rather than from this
app's own export (a round trip passes when both sides share a mistake).

For a character still in creation (``<created>False``), ``<karma>`` and
``<nuyen>`` are what Chummer computed as *left*: the one place a save states
the result of the whole build. A mismatch there means an item, a price or a
rule differs, without having to find which one first. In career mode the same
elements are the running balance, so only the warnings and errors are listed.

The files are fetched once into ``vendor/chummer-tests/`` (gitignored), at the
same chummer5a ref as the game data::

    python scripts/chum5_reconcile.py             # table + summary
    python scripts/chum5_reconcile.py -v          # + each file's warnings / errors
    python scripts/chum5_reconcile.py --dir DIR   # other saves instead
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.fetch_chummer_data import DEFAULT_REF, REF_FILE, _download  # noqa: E402

CACHE = ROOT / "vendor" / "chummer-tests"
TESTFILES = "Chummer.Tests/TestFiles"
#: Chummer keeps nuyen as a decimal; anything under a nuyen is rounding.
NUYEN_TOLERANCE = 1.0


def _ref() -> str:
    return REF_FILE.read_text(encoding="utf-8").strip() if REF_FILE.exists() else DEFAULT_REF


def fetch(ref: str) -> Path:
    """The test saves at `ref`, downloaded on first use."""
    target = CACHE / ref
    if target.is_dir() and any(target.glob("*.chum5")):
        return target
    api = f"https://api.github.com/repos/chummer5a/chummer5a/contents/{TESTFILES}?ref={ref}"
    with urllib.request.urlopen(api, timeout=60) as resp:
        listing = json.load(resp)
    names = [row["name"] for row in listing if str(row.get("name", "")).endswith(".chum5")]
    print(f"fetching {len(names)} saves from chummer5a@{ref[:12]} …", file=sys.stderr)
    base = f"https://raw.githubusercontent.com/chummer5a/chummer5a/{ref}/{TESTFILES}"
    for name in names:
        _download(f"{base}/{urllib.parse.quote(name)}", target / name)
    return target


def _number(root: ET.Element, tag: str) -> float:
    try:
        return float(root.findtext(tag) or 0)
    except ValueError:
        return 0.0


def reconcile(path: Path) -> dict[str, Any]:
    """One save: what Chummer says against what this app computes."""
    from app.characters import import_character
    from app.chummer_import import chum5_to_state

    raw = path.read_bytes()
    root = ET.fromstring(raw)
    state, warnings = chum5_to_state(raw)
    derived = import_character(state).derived
    created = (root.findtext("created") or "").strip().lower() == "true"
    row: dict[str, Any] = {
        "file": path.name,
        "career": created,
        "warnings": [w["key"] for w in warnings],
        "errors": [e["key"] for e in derived.get("errors") or []],
    }
    if not created:
        karma = derived.get("karma") or {}
        row["karma"] = (_number(root, "karma"), karma.get("remaining"))
        row["nuyen"] = (_number(root, "nuyen"), derived.get("nuyen"))
    return row


def _matches(pair: tuple[float, Any] | None, tolerance: float) -> bool:
    if pair is None or pair[1] is None:
        return False
    return abs(pair[0] - float(pair[1])) <= tolerance


def _fmt(pair: tuple[float, Any] | None) -> str:
    if pair is None:
        return "-"
    theirs, ours = pair
    if ours is None:
        return f"{theirs:g} / ?"
    diff = float(ours) - theirs
    return f"{theirs:g} / {float(ours):g} ({diff:+g})"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, help="saves to check instead of Chummer's test files")
    ap.add_argument("--ref", default=_ref(), help="chummer5a ref to fetch the test files at")
    ap.add_argument("-v", "--verbose", action="store_true", help="list each file's warning / error keys")
    args = ap.parse_args()

    folder = args.dir or fetch(args.ref)
    rows = [reconcile(path) for path in sorted(folder.glob("*.chum5"))]

    width = max((len(row["file"]) for row in rows), default=4)
    print(f"{'file':<{width}}  {'karma: Chummer / ours':<26}  {'nuyen: Chummer / ours':<34}  warn  err")
    for row in rows:
        karma = row.get("karma")
        nuyen = row.get("nuyen")
        mark = "" if row["career"] or (_matches(karma, 0) and _matches(nuyen, NUYEN_TOLERANCE)) else "  ≠"
        label = "career" if row["career"] else _fmt(karma)
        print(
            f"{row['file']:<{width}}  {label:<26}  {_fmt(nuyen):<34}  {len(row['warnings']):>4}  {len(row['errors']):>3}{mark}"
        )
        if args.verbose:
            for kind in ("warnings", "errors"):
                for key, count in collections.Counter(row[kind]).most_common():
                    print(f"    {kind[:-1]}: {key} ×{count}")

    chargen = [row for row in rows if not row["career"]]
    karma_ok = sum(_matches(row.get("karma"), 0) for row in chargen)
    nuyen_ok = sum(_matches(row.get("nuyen"), NUYEN_TOLERANCE) for row in chargen)
    both_ok = sum(_matches(row.get("karma"), 0) and _matches(row.get("nuyen"), NUYEN_TOLERANCE) for row in chargen)
    print()
    print(f"in creation: {len(chargen)}  karma matches {karma_ok}  nuyen matches {nuyen_ok}  both {both_ok}")
    for kind in ("warnings", "errors"):
        counts = collections.Counter(key for row in rows for key in row[kind])
        print(f"{kind} ({sum(counts.values())}):")
        for key, count in counts.most_common():
            print(f"  {count:>4}  {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
