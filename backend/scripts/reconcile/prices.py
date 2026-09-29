"""What a save says each of its own pieces cost.

Chummer writes the item's own price into the save rather than a reference to
the price list, so these are the numbers the character was actually built
against — which is what makes them worth setting beside today's catalogue.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

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
