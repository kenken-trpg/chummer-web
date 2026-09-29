"""Everything this tool prints, and the arguments that choose which.

The modules beside this one answer questions and hand back data; this is the
only one that writes to a terminal. `scripts/chum5_reconcile.py` is the entry
point, and its docstring is the manual.
"""

from __future__ import annotations

import argparse
import collections
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from ._saves import _ref, fetch
from .balance import NUYEN_TOLERANCE, _number, reconcile
from .fidelity import _accepted_drop, fidelity
from .prices import _gear_drift
from .roundtrip import roundtrip


def report_fidelity(folder: Path) -> int:
    saves = sorted(folder.glob("*.chum5"))
    dropped_counts: collections.Counter[str] = collections.Counter()
    changed_counts: collections.Counter[tuple[str, str, str]] = collections.Counter()
    clean = 0
    for path in saves:
        dropped, changed = fidelity(path)
        if not changed and not any(_accepted_drop(tag) is None for tag in dropped):
            clean += 1
        dropped_counts.update(dropped)
        changed_counts.update(changed)
    gaps = {tag: count for tag, count in dropped_counts.items() if _accepted_drop(tag) is None}
    print(f"export fidelity: {clean} of {len(saves)} saves come back saying everything Chummer reads back")
    print(f"  {len(gaps)} fields missing, {len(dropped_counts) - len(gaps)} dropped on purpose")
    if gaps:
        print("\nmissing — Chummer states it, reads it back, and the export drops it:")
        for tag, count in sorted(gaps.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {count:>4}  {tag}")
    if dropped_counts:
        print(f"\ndropped on purpose ({len(dropped_counts) - len(gaps)} fields):")
        for tag, count in dropped_counts.most_common():
            reason = _accepted_drop(tag)
            if reason is not None:
                print(f"  {count:>4}  {tag} — {reason}")
    if changed_counts:
        print("\nchanged — both state it, with different text:")
        for (tag, theirs, ours), count in changed_counts.most_common():
            print(f"  {count:>4}  {tag}: Chummer {theirs!r}, ours {ours!r}")
    # Two ways to fail. A *changed* field is a contradiction: both sides state
    # it and disagree. A *missing* one is a field Chummer reads back and the
    # export does not write — the character opens in Chummer without it. A
    # drop listed in `_ACCEPTED_DROPS` is neither: it is a field Chummer
    # writes for other readers, or an older spelling of one the export writes
    # the current way.
    return 1 if changed_counts or gaps else 0


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


# Elements a save stores a price on, and the bucket each belongs to. A weapon
# accessory and a piece of gear inside another are their own elements, so the
def locate(path: Path) -> None:
    """Narrow one save's nuyen gap down to the pieces that disagree.

    Two halves. First, every item this app charges for, beside the price the
    save recorded for the same name: a mismatch there is either price drift or
    a rule about that item. Second, the arithmetic that finds what is left —
    Chummer's own total spend, minus everything whose price both sides agree
    on, is what Chummer charged for the rest. That is how the 32 nuyen on
    Ocelot2.0 turned out to be its lifestyle (605 against this app's 573) with
    every other line matching to the nuyen.
    """
    from app.characters import import_character
    from app.chummer_import import chum5_to_state

    raw = path.read_bytes()
    root = ET.fromstring(raw)
    derived = import_character(chum5_to_state(raw)[0]).derived
    pool = float(derived.get("nuyen_pool") or 0)
    ours_spent = float(derived.get("nuyen_spent") or 0)
    theirs_left = _number(root, "nuyen")

    print(f"{path.name}: pool {pool:,.0f}")
    print(f"  this app spent {ours_spent:,.2f}, leaving {pool - ours_spent:,.2f}")
    if (root.findtext("created") or "").strip().lower() == "true":
        print("  career save — <nuyen> is a running balance, not a remainder; nothing to locate")
        return
    print(f"  Chummer left {theirs_left:,.2f}, so Chummer spent {pool - theirs_left:,.2f}")
    if theirs_left == 0:
        print(
            "  ...but a build over budget is saved as 0, not as the deficit, so that\n"
            "  figure is a floor and the arithmetic below cannot be trusted for this save."
        )

    print("\n  per bucket, this app:")
    for line in derived.get("nuyen_spend_breakdown") or []:
        print(f"    {line['notice']['key'].rsplit('.', 1)[-1]:<20} {line['amount']:>12,}")

    drift = _gear_drift(root)
    if drift:
        print("\n  price drift (the save's number is not today's catalogue price):")
        for name, catalogue, stored in drift:
            print(f"    {name:<44} save {stored:>10,.0f}  catalogue {catalogue:>10,.0f}")
        print(f"    {'total':<44} {sum(stored - c for _, c, stored in drift):>+10,.0f}")
    else:
        print("\n  price drift: none — every stored price matches the catalogue")

    gap = (pool - theirs_left) - ours_spent
    if abs(gap) <= NUYEN_TOLERANCE:
        print("\n  no gap to locate.")
        return
    print(f"\n  gap {gap:+,.2f} — if every other line is right, one bucket would have to be:")
    for line in derived.get("nuyen_spend_breakdown") or []:
        name = line["notice"]["key"].rsplit(".", 1)[-1]
        ours = float(line["amount"])
        print(f"    {name:<20} {ours + gap:>12,.2f}   (this app: {ours:,.2f})")
    print(
        "\n  Read that as one row at a time, not all at once. A bucket whose every item"
        "\n  matches the save above cannot be the one, which usually leaves a single"
        "\n  candidate — and lifestyles are the common answer, because a save records"
        "\n  no lifestyle total to check against."
    )


def _drift_explains(row: dict[str, Any]) -> bool:
    """The karma gap is exactly the qualities this save priced differently."""
    karma = row.get("karma")
    drift = row.get("quality_drift") or []
    if row["career"] or not drift or karma is None or karma[1] is None:
        return False
    # we charge the catalogue price, so a save that paid more has us keeping
    # that much extra karma
    gap = float(karma[1]) - karma[0]
    return bool(gap == sum(stored - listed for _, listed, stored in drift))


def _gear_drift_explains(row: dict[str, Any]) -> bool:
    """The nuyen gap is exactly the items this save priced differently."""
    nuyen = row.get("nuyen")
    drift = row.get("gear_drift") or []
    if row["career"] or not drift or nuyen is None or nuyen[1] is None:
        return False
    gap = float(nuyen[1]) - nuyen[0]
    return bool(abs(gap - sum(stored - listed for _, listed, stored in drift)) <= NUYEN_TOLERANCE)


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


def main(manual: str | None = None) -> int:
    """`manual` is what `--help` prints: the entry point's docstring, which is
    where the notes on what each mismatch means live."""
    ap = argparse.ArgumentParser(description=manual or __doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, help="saves to check instead of Chummer's test files")
    ap.add_argument("--ref", default=_ref(), help="chummer5a ref to fetch the test files at")
    ap.add_argument("-v", "--verbose", action="store_true", help="list each file's warning / error keys")
    ap.add_argument("--roundtrip", action="store_true", help="also export and re-import each save")
    ap.add_argument(
        "--fidelity",
        action="store_true",
        help="compare the export with the save Chummer wrote, field by field, and stop",
    )
    ap.add_argument("--items", metavar="NAME", help="list one save's prices item by item, and stop")
    ap.add_argument("--locate", metavar="NAME", help="narrow one save's nuyen gap to the pieces that disagree")
    args = ap.parse_args()

    folder = args.dir or fetch(args.ref)
    if args.fidelity:
        return report_fidelity(folder)
    for flag, run in (("items", items), ("locate", locate)):
        wanted = getattr(args, flag)
        if not wanted:
            continue
        match = next((p for p in sorted(folder.glob("*.chum5")) if wanted.lower() in p.name.lower()), None)
        if match is None:
            print(f"no save matching {wanted!r} in {folder}", file=sys.stderr)
            return 1
        run(match)
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
        mark += "  qdrift" if _drift_explains(row) else ""
        mark += "  gdrift" if _gear_drift_explains(row) else ""
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
            for name, listed, stored in row.get("quality_drift") or []:
                print(f"    quality price: {name} — save {stored}, catalogue {listed}")
            for name, listed_cost, stored_cost in row.get("gear_drift") or []:
                print(f"    item price: {name} — save {stored_cost:,.0f}, catalogue {listed_cost:,.0f}")

    chargen = [row for row in rows if not row["career"]]
    karma_ok = sum(_matches(row.get("karma"), 0) for row in chargen)
    nuyen_ok = sum(_matches(row.get("nuyen"), NUYEN_TOLERANCE) for row in chargen)
    both_ok = sum(_matches(row.get("karma"), 0) and _matches(row.get("nuyen"), NUYEN_TOLERANCE) for row in chargen)
    print()
    over_count = sum(_both_over(row.get("karma")) or _both_over(row.get("nuyen")) for row in chargen)
    agree = sum(
        (_matches(row.get("karma"), 0) or _both_over(row.get("karma")))
        and (_matches(row.get("nuyen"), NUYEN_TOLERANCE) or _both_over(row.get("nuyen")))
        for row in chargen
    )
    print(
        f"in creation: {len(chargen)}  karma matches {karma_ok}  nuyen matches {nuyen_ok}  both {both_ok}"
        f"  (over budget both ways: {over_count}; agreeing, counting those: {agree})"
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
