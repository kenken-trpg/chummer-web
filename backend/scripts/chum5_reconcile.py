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
elements are the running balance, which the import meets by construction: the
adjustment it needed (`karma_adjust` / `nuyen_adjust` — rent, purchases at
their own prices, or a price this app gets wrong) is listed instead, with
what the save's own expense log spent beside it.

Two limits on that. The test saves were written by Chummer 5.18x-5.202, which
kept the creation remainder there; current Chummer only sets `<nuyen>` when
creation is finished, so a newer save says nothing about it. And a character
over budget is saved with `0`, not the deficit: when the save says 0 and this
app is below zero as well, both agree the build is overspent — marked `over`
and left out of the mismatches, since by how much cannot be told.

A build over the 25 karma of negative qualities is marked `negcap`. Chummer's
default settings refund all of it and call the build invalid, which is what
this app does; the 5.202 saves stored the remainder as if the refund stopped
at 25, so their karma differs by the excess (Barrett by 53, Blindfire by 15).

The files are fetched once into ``vendor/chummer-tests/`` (gitignored), at the
same chummer5a ref as the game data::

    python scripts/chum5_reconcile.py             # table + summary
    python scripts/chum5_reconcile.py -v          # + each file's warnings / errors
    python scripts/chum5_reconcile.py --dir DIR   # other saves instead
    python scripts/chum5_reconcile.py --roundtrip # + export / re-import check
    python scripts/chum5_reconcile.py --items Mittens   # one save, item by item

`--roundtrip` writes each save back out and reads it again: what it holds
(gear by bucket, ware, vehicle mods — with whether each sits in a parent) and
what it spent must come back the same. It catches what an import reads but the
export has nowhere to write.

`--items` lists what this app charges for each piece of one save (the first
file whose name contains the text), to set beside the save's own `<cost>`
expressions when a nuyen total disagrees.
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
    if created:
        row["adjust"] = (int(state.get("karma_adjust") or 0), int(state.get("nuyen_adjust") or 0))
        spent = state.get("expense_log") or []
        row["spent"] = (
            sum(int(e.get("karma") or 0) for e in spent),
            sum(int(e.get("nuyen") or 0) for e in spent),
        )
    else:
        karma = derived.get("karma") or {}
        row["karma"] = (_number(root, "karma"), karma.get("remaining"))
        row["nuyen"] = (_number(root, "nuyen"), derived.get("nuyen"))
    return row


_GEAR_BUCKETS = ("gear", "commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps")


def _holdings(ch: Any) -> collections.Counter[tuple[Any, ...]]:
    """What a character holds, ids aside (they are new on every import)."""
    held: collections.Counter[tuple[Any, ...]] = collections.Counter()
    for bucket in _GEAR_BUCKETS:
        for r in getattr(ch, bucket):
            held[(bucket, r.gear_id, r.rating, getattr(r, "extra", None), bool(getattr(r, "parent_id", None)))] += 1
    mods = {m.id for m in ch.vehicle_mods}
    for kind in ("cyberware", "bioware"):
        for r in getattr(ch, kind):
            where = "mod" if r.parent_id in mods else bool(r.parent_id)
            held[(kind, r.ware_id, r.rating, r.grade, where)] += 1
    for m in ch.vehicle_mods:
        held[("vehicle_mods", m.mod_id, m.rating, m.included)] += 1
    return held


def roundtrip(path: Path) -> list[str]:
    """What changed when the save was exported and imported again."""
    from app.characters import import_character
    from app.chummer_export import state_to_chum5
    from app.chummer_import import chum5_to_state

    first = import_character(chum5_to_state(path.read_bytes())[0])
    again = import_character(chum5_to_state(state_to_chum5(first))[0])
    before, after = _holdings(first), _holdings(again)
    out = [f"lost {key} ×{n}" for key, n in (before - after).items()]
    out += [f"gained {key} ×{n}" for key, n in (after - before).items()]
    spent = (first.derived.get("nuyen_spent"), again.derived.get("nuyen_spent"))
    if spent[0] != spent[1]:
        out.append(f"nuyen spent {spent[0]} -> {spent[1]}")
    return out


def items(path: Path) -> None:
    """Print this app's price for every piece of one save."""
    from app.characters import import_character
    from app.chummer_import import chum5_to_state

    derived = import_character(chum5_to_state(path.read_bytes())[0]).derived
    print(f"{path.name}: pool {derived.get('nuyen_pool')}  spent {derived.get('nuyen_spent')}")
    for line in derived.get("nuyen_spend_breakdown") or []:
        print(f"  {line['notice']['key'].rsplit('.', 1)[-1]:<20} {line['amount']:>10,}")
    for key, rows in derived.items():
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict) or "nuyen" not in rows[0]:
            continue
        for row in rows:
            extra = f" R{row['rating']}" if row.get("rating") not in (None, 0, 1) else ""
            qty = f" ×{row['qty']}" if (row.get("qty") or 1) > 1 else ""
            inside = "  (in a parent)" if row.get("parent_id") else ""
            print(f"  {key:<20} {row.get('name')}{extra}{qty}  {row.get('nuyen')}{inside}")
    for vehicle in [*(derived.get("drones") or []), *(derived.get("vehicles") or [])]:
        for mod in vehicle.get("mods") or []:
            for ware in mod.get("cyberware") or []:
                print(f"  {'vehicle ware':<20} {vehicle['name']} / {mod['name']} / {ware['name']}  {ware['nuyen']}")


def _matches(pair: tuple[float, Any] | None, tolerance: float) -> bool:
    if pair is None or pair[1] is None:
        return False
    return abs(pair[0] - float(pair[1])) <= tolerance


def _both_over(pair: tuple[float, Any] | None) -> bool:
    """Chummer saved 0 and this app is short too: an overspent build both ways."""
    return pair is not None and pair[1] is not None and pair[0] == 0 and float(pair[1]) < 0


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
    ap.add_argument("--roundtrip", action="store_true", help="also export and re-import each save")
    ap.add_argument("--items", metavar="NAME", help="list one save's prices item by item, and stop")
    args = ap.parse_args()

    folder = args.dir or fetch(args.ref)
    if args.items:
        match = next((p for p in sorted(folder.glob("*.chum5")) if args.items.lower() in p.name.lower()), None)
        if match is None:
            print(f"no save matching {args.items!r} in {folder}", file=sys.stderr)
            return 1
        items(match)
        return 0
    rows = [reconcile(path) for path in sorted(folder.glob("*.chum5"))]

    width = max((len(row["file"]) for row in rows), default=4)
    print(f"{'file':<{width}}  {'karma: Chummer / ours':<26}  {'nuyen: Chummer / ours':<34}  warn  err")
    for row in rows:
        karma = row.get("karma")
        nuyen = row.get("nuyen")
        ok = [_matches(karma, 0) or _both_over(karma), _matches(nuyen, NUYEN_TOLERANCE) or _both_over(nuyen)]
        over = _both_over(karma) or _both_over(nuyen)
        mark = "" if row["career"] or all(ok) else "  ≠"
        mark += "  over" if over and not row["career"] else ""
        mark += "  negcap" if "engine.qualities.negativeCap" in row["errors"] and not row["career"] else ""
        # the save's own expense log explains part of the adjustment
        label = f"career, adj {row['adjust'][0]:+d} (log {row['spent'][0]:+d})" if row["career"] else _fmt(karma)
        nuyen_label = f"adj {row['adjust'][1]:+,d} (log {row['spent'][1]:+,d})" if row["career"] else _fmt(nuyen)
        print(
            f"{row['file']:<{width}}  {label:<26}  {nuyen_label:<34}  {len(row['warnings']):>4}  {len(row['errors']):>3}{mark}"
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
    over = sum(_both_over(row.get("karma")) or _both_over(row.get("nuyen")) for row in chargen)
    agree = sum(
        (_matches(row.get("karma"), 0) or _both_over(row.get("karma")))
        and (_matches(row.get("nuyen"), NUYEN_TOLERANCE) or _both_over(row.get("nuyen")))
        for row in chargen
    )
    print(
        f"in creation: {len(chargen)}  karma matches {karma_ok}  nuyen matches {nuyen_ok}  both {both_ok}"
        f"  (over budget both ways: {over}; agreeing, counting those: {agree})"
    )
    for kind in ("warnings", "errors"):
        counts = collections.Counter(key for row in rows for key in row[kind])
        print(f"{kind} ({sum(counts.values())}):")
        for key, count in counts.most_common():
            print(f"  {count:>4}  {key}")
    if args.roundtrip:
        changed = {path.name: roundtrip(path) for path in sorted(folder.glob("*.chum5"))}
        broken = {name: lines for name, lines in changed.items() if lines}
        print(f"round trip: {len(changed) - len(broken)} of {len(changed)} unchanged")
        for name, lines in broken.items():
            print(f"  {name}")
            for line in lines:
                print(f"    {line}")
        return 1 if broken else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
