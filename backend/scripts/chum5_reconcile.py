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

``--locate NAME`` narrows one save's nuyen gap to the pieces that disagree:
the save's own price for every item beside this app's, and then the arithmetic
that says what each bucket would have to be if all the others were right. A
bucket whose every item matches the save cannot be the one, which usually
leaves a single candidate. Lifestyles are the common answer, because a save
records no lifestyle total to check against.

A save stores the karma it paid for a quality, not a reference to the price
list, so a save written against an older `qualities.xml` states a price this
app will never reproduce — the difference lands in the karma left. `-v` lists
those qualities, and a row whose whole karma gap is exactly that is marked
`qdrift`: Miko's single point is `Functional Tail (Prehensile)`, saved at 7
where the catalogue now says 6. Same for `College Education` (saved 4, now 2).

The same drift happens to gear: a save records each item's own cost, so
`Ghile Mear`'s whole 2,000 nuyen gap is `Reakt`, saved at 75,000 where the
catalogue now says 73,000. A row whose nuyen gap is exactly that is marked
`gdrift`, and `-v` lists the items.

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


def _quality_drift(root: ET.Element) -> list[tuple[str, int, int]]:
    """Qualities whose stored price is not what today's catalogue charges.

    A save keeps the karma it paid for a quality (`<bp>`) rather than a
    reference to the price list, so a save written against an older
    `qualities.xml` states a price this app will never reproduce. That is not
    a rule this app gets wrong, and it is worth telling apart from one: the
    difference lands in the karma left, which is the very number the table
    above compares. Only qualities the character chose count — `Metatype` and
    priority-granted ones are free on both sides — and only unlevelled,
    plain ones, since `<bp>` on a levelled or `<extra>`-carrying quality is a
    total this cannot take apart.
    """
    from app.data_loader import catalog_list

    prices = {str(q.get("name") or ""): q.get("karma") for q in catalog_list("qualities")}
    drift: list[tuple[str, int, int]] = []
    for node in root.iter("quality"):
        name = (node.findtext("name") or "").strip()
        source = (node.findtext("qualitysource") or "").strip()
        if (source and source != "Selected") or (node.findtext("extra") or "").strip():
            continue
        listed = prices.get(name)
        if listed is None:
            continue
        try:
            stored = int(node.findtext("bp") or 0)
        except ValueError:
            continue
        if stored != int(listed):
            drift.append((name, int(listed), stored))
    return drift


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
        row["quality_drift"] = _quality_drift(root)
        row["gear_drift"] = _gear_drift(root)
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


# Elements a save stores a price on, and the bucket each belongs to. A weapon
# accessory and a piece of gear inside another are their own elements, so the
# walk is by tag rather than by nesting.
_PRICED_TAGS = {
    "armor": "armor",
    "weapon": "weapons",
    "accessory": "weaponAccessories",
    "gear": "otherGear",
    "cyberware": "ware",
    "vehicle": "vehicles",
}


def _stored_prices(root: ET.Element) -> list[tuple[str, str, float]]:
    """(bucket, name, price) for every item whose save records a plain number.

    Chummer writes the item's own cost into the save, which is the catalogue
    expression at the time it was written — so `Rating * 25` appears verbatim
    and is skipped here, as is anything that does not parse. What is left is
    directly comparable with today's price list, and that comparison is the
    gear counterpart of `_quality_drift`.

    It is *not* what the character paid: a grade multiplies ware, a rating
    scales gear, an `included` mod costs nothing. So this answers "has the
    price list moved under this save", never "what should the total be".
    """
    out: list[tuple[str, str, float]] = []
    for tag, bucket in _PRICED_TAGS.items():
        for node in root.iter(tag):
            name = (node.findtext("name") or "").strip()
            if not name:
                continue
            # A piece that came with its parent is written with `cost` 0 and a
            # `parentid`: it was never priced, so reading that 0 as a price
            # reports every such item as drift (`Camera, Micro` in three of
            # these saves). Accessories nest inside their weapon instead and
            # carry no `parentid`, which is right — those are paid for.
            if (node.findtext("parentid") or "").strip():
                continue
            try:
                price = float((node.findtext("cost") or "").strip())
            except ValueError:
                continue
            out.append((bucket, name, price))
    return out


def _gear_drift(root: ET.Element) -> list[tuple[str, float, float]]:
    """Items whose stored price is not what today's catalogue charges.

    The same problem `_quality_drift` reports for qualities: a save written
    against an older `gear.xml` states a price this app will never reproduce,
    and the difference lands in the nuyen left — the number the table compares.
    Telling it apart from a rule this app gets wrong is the whole point.
    """
    from app.data_loader import catalog

    listed: dict[str, float] = {}
    seen_twice: set[str] = set()

    def as_price(cost: object) -> float | None:
        """A catalogue cost is often an expression, which is not comparable."""
        if not isinstance(cost, (str, int, float)):
            return None
        try:
            return float(str(cost))
        except ValueError:
            return None

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            name = obj.get("name")
            price = as_price(obj.get("cost"))
            if isinstance(name, str) and name.strip() and price is not None:
                key = name.strip()
                if key in listed and listed[key] != price:
                    seen_twice.add(key)  # same name, two prices: cannot tell which
                listed.setdefault(key, price)
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    data = catalog()
    for key, value in data.items():
        if key not in {"translations", "ui_strings"}:
            walk(value)

    drift: list[tuple[str, float, float]] = []
    for _bucket, name, stored in _stored_prices(root):
        if name in seen_twice or name not in listed:
            continue
        # A catalogue price of 0 is not a price to compare against. Chummer
        # writes `Variable(20-100000)` for `Clothing`, which this app's catalogue
        # reduces to 0 and the player's own pick (1,000 in Miko's save) sits in
        # the save — a difference that says nothing about either price list.
        if not listed[name]:
            continue
        if listed[name] != stored:
            drift.append((name, listed[name], stored))
    return drift


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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, help="saves to check instead of Chummer's test files")
    ap.add_argument("--ref", default=_ref(), help="chummer5a ref to fetch the test files at")
    ap.add_argument("-v", "--verbose", action="store_true", help="list each file's warning / error keys")
    ap.add_argument("--roundtrip", action="store_true", help="also export and re-import each save")
    ap.add_argument("--items", metavar="NAME", help="list one save's prices item by item, and stop")
    ap.add_argument("--locate", metavar="NAME", help="narrow one save's nuyen gap to the pieces that disagree")
    args = ap.parse_args()

    folder = args.dir or fetch(args.ref)
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


if __name__ == "__main__":
    sys.exit(main())
