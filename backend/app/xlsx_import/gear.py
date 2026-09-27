"""The 装備 sheet: one flat table holding everything the character owns.

This is the template's loosest sheet by a wide margin. Weapons, ammunition,
armor, medical supplies, drugs, fake SINs, vehicles and lifestyles all go in the
same column, nothing is a dropdown, and the player writes whatever they need to
remember:

* ``【武器】`` — a heading they typed themselves, to group the rows below
* ``ピストル用`` — a label for a bundle of ammunition, which is not an item
* ``└専用消音機`` / ``→サブボーカルマイク`` — what the row above it is fitted with
* ``予備クリップ*12`` / ``通常弾x100`` — the count written into the name as well
  as into its own column
* ``医療キットR3`` / ``偽造SIN-R4`` / ``視覚強化(R1)`` / ``偽造SIN: 3`` — the
  rating, in four spellings
* ``コムリンク: レンラク・センセイ`` — a category typed in front of the name
* ``VI・スチームパンク`` — the line the armor comes from, abbreviated by the player

So a row becomes a handful of candidate spellings, tried against each catalog in
turn, and the catalog that answers decides what kind of thing it is. A row with
no price in its own column is a heading or a bundle label rather than an item,
and is passed over without comment.

**A good deal of this sheet cannot be read, and that is what `pending` is
for.** Some rows are several items at once (``通常弾*20、スティックン・ショック
*20``), some are things the book does not have under that name, and some are the
player's own shorthand (``VI・スチームパンク`` for the Vashon Island line). Rather
than a warning per row, every unread row comes back as a `pending` entry with
what the sheet said and a shortlist of what it looks like, for someone to
confirm. Nothing is dropped in silence.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from ..data_loader import CatalogDict
from ..notices import Notice, notice
from ._common import cell_int
from ._match import BUCKETS, build_index, resolve, split_row, suggest

#: The table runs from row 3 to the end of the sheet; the reader stops looking
#: when it runs out of rows rather than at a fixed number.
FIRST_ROW = 3
GEAR_NAME = "A"
GEAR_PRICE = "C"
GEAR_BOUGHT = "E"
GEAR_NOTE = "K"

#: A heading the player typed to group the rows under it.
_HEADING = re.compile(r"^\s*【.*】\s*$")
#: The state lists whose rows can say what they are installed in.
TAKES_PARENT = {"armor_mods", "weapon_accessories", "cyberdecks", "gear"}
#: The lists whose rows only exist fitted to something: an accessory or a mod
#: with nothing to sit on is dropped by the engine rather than kept loose, so
#: one with no parent to name has to be confirmed instead of imported.
NEEDS_PARENT = {"armor_mods", "weapon_accessories"}
#: The state lists whose rows carry a count rather than a rating.
TAKES_QTY = {"weapons", "commlinks", "cyberdecks", "vehicles", "drones", "gear"}


def _entry(bucket: str, item_id: str, rating: int, qty: int, parent_id: str = "") -> dict[str, Any]:
    """The character-state row for one item, ready to be appended.

    Built here for a suggestion as well as for a row that matched, so a client
    offering a shortlist never has to know which lists carry a count, which
    carry a rating and which count months.
    """
    keys = {name: key for name, key, _id_key, _kind in BUCKETS}
    id_keys = {name: id_key for name, _key, id_key, _kind in BUCKETS}
    key = keys[bucket]
    entry: dict[str, Any] = {"id": str(uuid.uuid4()), id_keys[bucket]: item_id}
    if parent_id and key in TAKES_PARENT:
        entry["parent_id"] = parent_id
    if key == "lifestyles":
        entry["months"] = qty
        return entry
    if key in TAKES_QTY:
        entry["qty"] = qty
    if key not in {"weapons", "vehicles", "drones"}:
        entry["rating"] = max(1, rating)
    return entry


def import_gear(
    cells: dict[str, str],
    cat: CatalogDict,
    st: dict[str, Any],
    warn: list[Notice],
    pending: list[dict[str, Any]],
) -> None:
    """Fill the equipment lists from the 装備 sheet.

    What could not be read goes into `pending` for someone to confirm, and one
    warning says how many there were — so a caller that ignores `pending`
    still knows the character arrived short.
    """
    if not cells:
        return
    index = build_index(cat)
    translations = dict(cat.get("translations") or {})
    lifestyles = [translations.get(str(row["name"]), str(row["name"])) for row in cat["lifestyles"]]
    keys = {bucket: key for bucket, key, _id_key, _kind in BUCKETS}
    out: dict[str, list[dict[str, Any]]] = {key: [] for key in keys.values()}
    names_by_id = {
        str(row["id"]): str(row["name"])
        for bucket, _key, _id_key, _kind in BUCKETS
        for row in cat[bucket]  # type: ignore[literal-required]
    }
    last = max((int(ref[1:]) for ref in cells if re.fullmatch(r"A\d+", ref)), default=0)
    parent_id = ""
    for row in range(FIRST_ROW, last + 1):
        raw = (cells.get(f"{GEAR_NAME}{row}") or "").strip()
        if not raw or _HEADING.match(raw):
            # a heading starts a new group, so nothing below it is installed in
            # anything above it
            parent_id = ""
            continue
        if not (cells.get(f"{GEAR_PRICE}{row}") or "").strip():
            # a bundle label (ピストル用) or the template's own ◯入力例 block:
            # something with no price is not something that was bought, and it
            # is not something the rows under it are installed in either
            parent_id = ""
            continue
        names, nested, rating_in_name, qty_in_name = split_row(raw)
        # The count is in its own column, and often in the name as well; when
        # they disagree the larger is what was written down on purpose.
        qty = max(1, cell_int(cells.get(f"{GEAR_BOUGHT}{row}")), qty_in_name)
        # A nested row is fitted to the last row that was not nested.
        fitted_to = parent_id if nested else ""
        resolved = resolve(names, index, lifestyles)
        # An accessory or a mod with nothing to sit on cannot be installed, so
        # it is held for someone to attach rather than imported and dropped.
        installable = resolved and not (keys[resolved[0]] in NEEDS_PARENT and not fitted_to)
        if not resolved or not installable:
            pending.append(
                {
                    "name": raw,
                    "rating": rating_in_name,
                    "qty": qty,
                    "note": (cells.get(f"{GEAR_NOTE}{row}") or "").strip(),
                    "suggestions": [
                        {
                            "bucket": bucket,
                            "key": keys[bucket],
                            "id": item_id,
                            "name": names_by_id[item_id],
                            "entry": _entry(bucket, item_id, rating_in_name, qty, fitted_to),
                        }
                        # what can only be fitted to something is no use here
                        for bucket, item_id in ([resolved] if resolved else suggest(names[-1], index))
                        if fitted_to or keys[bucket] not in NEEDS_PARENT
                    ],
                }
            )
            continue
        bucket, item_id = resolved
        key = keys[bucket]
        entry = _entry(bucket, item_id, rating_in_name, qty, fitted_to)
        if not nested:
            parent_id = entry["id"]
        out[key].append(entry)
    for key, entries in out.items():
        if entries:
            st[key] = (st.get(key) or []) + entries
    if pending:
        warn.append(notice("engine.import.xlsxGearPending", count=len(pending)))


__all__ = ["import_gear"]
