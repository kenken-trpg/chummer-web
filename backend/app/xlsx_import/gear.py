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
from ._common import cell_int, japanese_index, no_interpunct

#: The table runs from row 3 to the end of the sheet; the reader stops looking
#: when it runs out of rows rather than at a fixed number.
FIRST_ROW = 3
GEAR_NAME = "A"
GEAR_PRICE = "C"
GEAR_BOUGHT = "E"
GEAR_NOTE = "K"

#: A heading the player typed to group the rows under it.
_HEADING = re.compile(r"^\s*【.*】\s*$")
#: What marks a row as belonging to the one above it.
_NESTING = re.compile(r"^[└├│┗┣┃▶→▷➤>\s　]+")
#: 「予備クリップ*12」「通常弾x100」— the count, which column E holds anyway.
_QTY = re.compile(r"[*＊×xX]\s*\d+\s*$")
#: 「医療キットR3」「偽造SIN-R4」「視覚強化(R1)」「偽造SIN: 3」「覚醒パッチ 6」
_RATING = re.compile(r"(?:[-‐‑–]?\s*[RrLlFf]\s*(\d+)|[（(]\s*[RrLlFf]?\s*(\d+)\s*[)）]|[:：]\s*(\d+)|\s+(\d+))\s*$")
#: 「医療キット3」— a rating run straight onto the name, tried last because a
#: model number looks exactly the same (アレス・プレデター V is not a rating).
_RATING_RUN_ON = re.compile(r"(?<=[^\W\d])(\d+)\s*$")
#: 「コムリンク: レンラク・センセイ」「偽造ID: 偽造SIN」— a category in front.
#: The longest is ヴァッション・アイランド:, at twelve characters.
_CATEGORY = re.compile(r"^[^:：]{1,24}[:：]\s*")
#: 「アレス・ライト・ファイア70(内蔵SG)」— a note the player added about the item,
#: tried only after the name as typed, because a catalog name can end in a
#: parenthesis of its own (骨格補綴 (チタニウム)).
_TRAILING_NOTE = re.compile(r"\s*[（(][^()（）]*[)）]\s*$")
#: 偽装 for 偽造 — the same word, and the sheets are written both ways.
_VARIANTS = {"偽装": "偽造"}

#: 「ライフスタイル下流」「ライフスタイル（下流）一か月分」「生活費下流一か月分」— a
#: lifestyle is filed under its own bare name (下流), and the sheets wrap it in
#: whatever phrasing the player thought of. The count of months is already in
#: the row's own column.
_LIFESTYLE_WORDS = ("ライフスタイル", "生活費", "生活水準")

#: Spacing and interpuncts differ freely between the catalog and the sheets
#: (アレス・プレデター V / アレスプレデターV), so they come off both sides.
_LOOSE = re.compile(r"[\s　・･]+")

#: Which catalogs to try, in order, and where what they answer belongs.
#:
#: The order settles the names that are in more than one list. 予備クリップ and
#: 隠蔽ホルスター are each a weapon accessory as well as a piece of gear, and on
#: a row of its own the gear is what was bought — so the two plugin lists come
#: last and only answer for a name nothing else has (消音器).
BUCKETS: tuple[tuple[str, str, str, str], ...] = (
    ("weapons", "weapons", "weapon_id", ""),
    ("armor", "armor", "armor_id", "armor"),
    ("commlinks", "commlinks", "gear_id", "gear"),
    ("cyberdecks", "cyberdecks", "gear_id", "gear"),
    ("vehicles", "vehicles", "gear_id", ""),
    ("drones", "drones", "gear_id", ""),
    ("lifestyles", "lifestyles", "lifestyle_id", ""),
    ("gear", "gear", "gear_id", "gear"),
    ("armor_mods", "armor_mods", "mod_id", "armor"),
    ("weapon_accessories", "weapon_accessories", "accessory_id", ""),
)

#: The state lists whose rows can say what they are installed in.
TAKES_PARENT = {"armor_mods", "weapon_accessories", "cyberdecks", "gear"}
#: The lists whose rows only exist fitted to something: an accessory or a mod
#: with nothing to sit on is dropped by the engine rather than kept loose, so
#: one with no parent to name has to be confirmed instead of imported.
NEEDS_PARENT = {"armor_mods", "weapon_accessories"}
#: The state lists whose rows carry a count rather than a rating.
TAKES_QTY = {"weapons", "commlinks", "cyberdecks", "vehicles", "drones", "gear"}

#: How close a name has to look to be worth offering, and how many to offer.
SUGGEST_THRESHOLD = 0.30
SUGGEST_LIMIT = 6


def _loose(text: str) -> str:
    return _LOOSE.sub("", text)


def _bigrams(text: str) -> set[str]:
    return {text[i : i + 2] for i in range(len(text) - 1)} or {text}


def _likeness(left: str, right: str) -> float:
    """How much two loose names look alike, 0 to 1 (Dice on their bigrams).

    Chosen because the misses are mostly one syllable out —
    ``サンダートラック`` for ``サンダーストラック``, ``錠前キット`` for ``錠前セット``
    — which share almost every pair of characters.
    """
    a, b = _bigrams(left), _bigrams(right)
    return 2 * len(a & b) / (len(a) + len(b))


def suggest(name: str, index: dict[str, list[tuple[str, str]]]) -> list[tuple[str, str]]:
    """The (bucket, id) pairs whose name looks most like `name`.

    This is the shortlist a person is offered for a row that matched nothing; it
    never decides anything on its own.
    """
    target = _loose(name)
    if not target:
        return []
    scored: list[tuple[float, tuple[str, str]]] = []
    seen: set[tuple[str, str]] = set()
    for key, found in index.items():
        score = _likeness(target, key)
        if score < SUGGEST_THRESHOLD:
            continue
        for entry in found:
            if entry not in seen:
                seen.add(entry)
                scored.append((score, entry))
    scored.sort(key=lambda pair: -pair[0])
    return [entry for _score, entry in scored[:SUGGEST_LIMIT]]


def _lifestyle_in(name: str, lifestyles: list[str]) -> str:
    """The lifestyle `name` is a phrasing of, or "".

    Only a name that says it is about a lifestyle is looked at this way, so a
    piece of gear that happens to contain 下流 is not mistaken for one.
    """
    if not any(word in name for word in _LIFESTYLE_WORDS):
        return ""
    found = [lifestyle for lifestyle in lifestyles if lifestyle in name]
    # 入院：通常 contains neither 通常 alone nor another lifestyle's name, but
    # 下流 is inside nothing else, so the longest match is the one meant.
    return max(found, key=len) if found else ""


def build_index(cat: CatalogDict) -> dict[str, list[tuple[str, str]]]:
    """``{loose japanese: [(bucket, id), …]}`` over every catalog this sheet holds.

    A name can be in more than one catalog — 予備クリップ is gear and a weapon
    accessory both — so the buckets it was found in are kept in `BUCKETS` order
    and the caller picks.

    A catalog name that carries its line or its kind in front — ``弾薬: 通常弾``,
    ``ヴァッション・アイランド: エース・オブ・カップス`` — is indexed without that
    part as well, because the sheets are written both ways.
    """
    index: dict[str, list[tuple[str, str]]] = {}
    for bucket, _key, _id_key, kind in BUCKETS:
        rows = {str(row["name"]): str(row["id"]) for row in cat[bucket]}  # type: ignore[literal-required]
        for japanese, english in japanese_index(cat, rows, kind).items():
            for form in (japanese, _CATEGORY.sub("", japanese)):
                found = index.setdefault(_loose(form), [])
                if (bucket, rows[english]) not in found:
                    found.append((bucket, rows[english]))
    return index


def split_row(raw: str) -> tuple[list[str], bool, int, int]:
    """A typed row into (candidate names, nested, rating, count) from its name.

    The candidates are ordered: the name as typed first, then with the count and
    the rating taken off it, then without a category typed in front, and last
    with a run-on number read as a rating.
    """
    text = _NESTING.sub("", raw.strip())
    nested = text != raw.strip()
    out = [text]
    rating = qty = 0
    for _ in range(3):
        counted = _QTY.search(text)
        stripped = _QTY.sub("", text).strip()
        if counted:
            qty = qty or int(re.sub(r"\D", "", counted.group(0)))
        found = _RATING.search(stripped)
        if found:
            rating = rating or int(next(group for group in found.groups() if group))
            stripped = stripped[: found.start()].strip()
        if stripped == text:
            break
        text = stripped
        out.append(text)
    for name in list(out):
        for shorter in (_CATEGORY.sub("", name).strip(), _TRAILING_NOTE.sub("", name).strip()):
            if shorter and shorter != name:
                out.append(shorter)
    # Only the fully stripped name is read for a run-on rating, and only when no
    # count was written: 通常弾x100 is a hundred rounds, not rating 100.
    run_on = _RATING_RUN_ON.search(out[-1]) if not qty else None
    if run_on:
        out.append(out[-1][: run_on.start()].strip())
        rating = rating or int(run_on.group(1))
    return [name for name in out if name], nested, rating, qty


def _resolve(
    names: list[str], index: dict[str, list[tuple[str, str]]], lifestyles: list[str]
) -> tuple[str, str] | None:
    for name in names:
        spellings = [name, no_interpunct(name)]
        for old, new in _VARIANTS.items():
            if old in name:
                spellings.append(name.replace(old, new))
        for spelling in spellings:
            for found in index.get(_loose(spelling)) or []:
                return found
    for name in names:
        lifestyle = _lifestyle_in(name, lifestyles)
        if lifestyle:
            for found in index.get(_loose(lifestyle)) or []:
                return found
    return None


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
        resolved = _resolve(names, index, lifestyles)
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


__all__ = ["BUCKETS", "build_index", "import_gear", "split_row", "suggest"]
