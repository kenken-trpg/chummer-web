"""A name typed on the 装備 sheet, matched against the catalog.

Split out of `gear` because it answers a different question. `gear` reads a
table: which rows are items, what each row is fitted to, where the answers
belong in the character. This reads one *name* — the thing the player typed —
and it is the half that has to guess, because the sheet's equipment column is
free text and the book is 6,000 names long:

* **`split_row`** takes a typed name apart into the spellings worth trying,
  plus the rating and the count that were written into it.
* **`build_index`** is every catalog this sheet can hold, keyed by a loosened
  Japanese name.
* **`resolve`** is the answer, or nothing.
* **`suggest`** is what to offer a person when there is no answer. It never
  decides anything.

Nothing here reads a cell or touches a `CharacterState`; nothing in `gear`
compares two names. So the guessing can be tried on its own, and the table
reading stays readable.
"""

from __future__ import annotations

import re

from ..data_loader import CatalogDict
from ._common import japanese_index, no_interpunct

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


def resolve(names: list[str], index: dict[str, list[tuple[str, str]]], lifestyles: list[str]) -> tuple[str, str] | None:
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


__all__ = [
    "BUCKETS",
    "SUGGEST_LIMIT",
    "SUGGEST_THRESHOLD",
    "build_index",
    "resolve",
    "split_row",
    "suggest",
]
