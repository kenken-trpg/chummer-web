"""The 身体強化／電子機器 sheet: implants, and the commlink or deck under them.

The implant table (rows 4–33) is the most freely written part of the template.
Nothing on it is a dropdown but the grade, so the names arrive with everything
the player wanted written next to them:

* ``サイバーアイ[9]`` — the availability in brackets, which the sheet works out
  for itself two columns over and the player copied in anyway
* ``└視覚強化R3[3]`` — the rating written into the name as well as into its own
  column, under a box-drawing character saying what it is installed in
* ``（大光量補正）`` — the same nesting, written with parentheses instead
* ``非偽装型サイバーリム右腕全体`` — a limb, its side and which part of it, run
  together in one word

So a typed implant name is stripped of its decorations, the side and the nesting
are taken out of it, and what is left is matched against the catalog. The grade
column and the rating column come over as they are — except that the rating
column is where a 骨格補綴's material goes (``チタニウム``), which the catalog
keeps as part of the name.

The commlink and deck block under it (the rows below its own heading) is easier:
a kind in column A, the name in D and the device rating in M. 生体ペルソナ is a
technomancer's own persona rather than a device, so that row is skipped.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from ..data_loader import CatalogDict
from ..notices import Notice, Phrase, notice, ui
from ._common import cell_int, japanese_index, no_interpunct

#: The implant table. Every version seen so far has it at rows 4–33.
WARE_ROWS = range(4, 34)
WARE_NAME = "A"
WARE_GRADE = "N"
WARE_RATING = "P"

#: The grade dropdown, which is the one thing on this sheet that is one.
GRADES = {
    "スタンダード": "Standard",
    "アルファウェア": "Alphaware",
    "ベータウェア": "Betaware",
    "デルタウェア": "Deltaware",
    "中古": "Used",
}

#: The heading that opens the device block, and the rows under it: a kind in
#: column A, the name in D, the device rating in M.
DEVICES_HEADING = "サイバーデッキ／コムリンク"
DEVICES_OFFSET = 3
DEVICES_COUNT = 7
DEVICE_NAME = "D"
DEVICE_RATING = "M"
#: 生体ペルソナ is the technomancer's own persona, not something bought.
DEVICE_KINDS = ("コムリンク", "サイバーデッキ")

#: What the player writes beside an implant name and the sheet does not need.
_NESTING = re.compile(r"^[└├│┗┣┃|\s　]+")
_WRAPPED = re.compile(r"^[（(](.+)[)）]$")
_AVAIL = re.compile(r"[\[［][^\]］]*[\]］]\s*$")
_RATING_IN_NAME = re.compile(r"[Rr](\d+)\s*$")
#: 右腕 / 左脚 — which side a limb or a paired implant went on.
_SIDES = {"右": "Right", "左": "Left"}

#: Implants the template names differently from the catalog's Japanese.
NAME_ALIASES = {
    "サイバーアイ": "サイバーアイ基本システム",
    "ダメージ補正機": "ダメージ補正器",
    "熱映像補正": "熱映像視野",
    # Enhanced Agility is the one Cyberlimb Enhancement whose Japanese name
    # was left without its 強化, next to 筋力強化 for Enhanced Strength.
    "敏捷力強化": "敏捷力",
    # The catalog's Japanese says サイバーガン where the English says Cyberarm.
    "サイバーアームジャイロマウント": "サイバーガン・ジャイロマウント",
}

#: How the catalog names the parts of a cyberlimb, and how the template runs
#: them together: 非偽装型サイバーアーム(全体) is written 非偽装型サイバーリム腕全体.
_LIMB_WORDS = {
    "アーム": "腕",
    "レッグ": "脚",
    "ハンド": "手",
    "フット": "足",
    "トルソ": "胴体",
    "スカル": "頭蓋",
}
_LIMB = re.compile(r"^(非偽装型|偽装型)サイバー(アーム|レッグ|ハンド|フット|トルソ|スカル)[(（]([^)）]*)[)）]$")


def _limb_spellings(japanese: str) -> list[str]:
    """The ways the template might write the cyberlimb the catalog calls
    `japanese`, or nothing if it is not a limb.

    ``非偽装型サイバーアーム(全体)`` -> ``非偽装型サイバーリム腕全体``,
    ``非偽装型サイバーアーム全体``.
    """
    matched = _LIMB.match(japanese)
    if not matched:
        return []
    prefix, limb, part = matched.groups()
    return [f"{prefix}サイバーリム{_LIMB_WORDS[limb]}{part}", f"{prefix}サイバー{limb}{part}"]


def clean_name(raw: str) -> tuple[str, bool, str, int]:
    """A typed implant name into (name, nested, side, rating written into it)."""
    text = raw.strip()
    nested = bool(_NESTING.match(text))
    text = _NESTING.sub("", text)
    wrapped = _WRAPPED.match(text)
    if wrapped:
        nested = True
        text = wrapped.group(1).strip()
    text = _AVAIL.sub("", text).strip()
    rating = 0
    in_name = _RATING_IN_NAME.search(text)
    if in_name:
        rating = int(in_name.group(1))
        text = text[: in_name.start()].strip()
    side = ""
    for mark, which in _SIDES.items():
        if mark in text:
            side, text = which, text.replace(mark, "", 1)
            break
    return text, nested, side, rating


def build_index(cat: CatalogDict) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    """(Japanese implant name -> English name, English name -> the catalog row).

    Cyberware and bioware are one table on the sheet — the player picks the
    grade, not the book — so they are one index here and told apart afterwards
    by which of the two the name came from.
    """
    rows: dict[str, dict[str, Any]] = {}
    for bucket, items in (("cyberware", cat["cyberware"]["items"]), ("bioware", cat["bioware"]["items"])):
        for row in items:
            entry = dict(row)
            entry["_bucket"] = bucket
            rows.setdefault(str(row["name"]), entry)
    index = japanese_index(cat, rows, "cyberware")
    index.update(japanese_index(cat, rows, "bioware"))
    translations = dict(cat.get("translations") or {})
    for kind in ("cyberware", "bioware"):
        translations.update((cat.get("translations_by_kind") or {}).get(kind) or {})
    for english in rows:
        for spelling in _limb_spellings(translations.get(english, "")):
            index.setdefault(spelling, english)
            index.setdefault(no_interpunct(spelling), english)
    return index, rows


def _resolve(name: str, pick: str, index: dict[str, str]) -> str:
    """An implant name, with what the rating column held if it was not a number.

    ``骨格補綴`` with ``チタニウム`` in the rating column is the catalog's
    ``骨格補綴 (チタニウム)``; the material is part of the name there.
    """
    tries = [f"{name} ({pick})", f"{name} ({pick})".replace(" (", "（").replace(")", "）")] if pick else []
    tries.append(name)
    for candidate in tries:
        aliased = NAME_ALIASES.get(candidate, "")
        found = index.get(candidate) or index.get(no_interpunct(candidate)) or index.get(aliased)
        if found:
            return found
    return ""


def _import_implants(cells: dict[str, str], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    index, rows = build_index(cat)
    out: dict[str, list[dict[str, Any]]] = {"cyberware": [], "bioware": []}
    #: the last row that was not nested, which is what a nested one sits in
    parent_id = ""
    for row in WARE_ROWS:
        raw = cells.get(f"{WARE_NAME}{row}") or ""
        if not raw.strip():
            continue
        name, nested, side, rating_in_name = clean_name(raw)
        rating_cell = (cells.get(f"{WARE_RATING}{row}") or "").strip()
        rating = cell_int(rating_cell)
        # A rating column that is not a number is a material or a model, which
        # the catalog keeps in the name (骨格補綴 (チタニウム)).
        pick = "" if (rating or not rating_cell) else rating_cell
        english = _resolve(name, pick, index)
        if not english:
            kind = ui("engine.kind.cyberware")
            warn.append(notice("engine.import.skippedUnknown", kind=kind, name=raw.strip()))
            continue
        spec = rows[english]
        grade_cell = (cells.get(f"{WARE_GRADE}{row}") or "").strip()
        grade = GRADES.get(grade_cell, "Standard")
        if grade_cell and grade_cell not in GRADES:
            warn.append(notice("engine.import.xlsxWareGrade", name=raw.strip(), grade=grade_cell))
        entry: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "ware_id": str(spec["id"]),
            "rating": max(1, rating or rating_in_name),
            "grade": grade,
            "side": side or None,
            "included": False,
        }
        if nested and parent_id:
            entry["parent_id"] = parent_id
        else:
            parent_id = entry["id"]
        out[str(spec["_bucket"])].append(entry)
    for bucket, entries in out.items():
        if entries:
            st[bucket] = entries


def _import_devices(cells: dict[str, str], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    heading = next(
        (int(ref[1:]) for ref, text in cells.items() if re.fullmatch(r"A\d+", ref) and text.strip() == DEVICES_HEADING),
        None,
    )
    if heading is None:
        return
    gear: Phrase = ui("engine.kind.gear")
    catalogs = {"コムリンク": list(cat["commlinks"]), "サイバーデッキ": list(cat["cyberdecks"])}
    keys = {"コムリンク": "commlinks", "サイバーデッキ": "cyberdecks"}
    out: dict[str, list[dict[str, Any]]] = {"commlinks": [], "cyberdecks": []}
    for row in range(heading + DEVICES_OFFSET, heading + DEVICES_OFFSET + DEVICES_COUNT):
        kind = (cells.get(f"A{row}") or "").strip()
        name = (cells.get(f"{DEVICE_NAME}{row}") or "").strip()
        if kind not in DEVICE_KINDS or not name:
            continue
        rows = catalogs[kind]
        ids = {str(item["name"]): str(item["id"]) for item in rows}
        index = japanese_index(cat, ids, "gear")
        english = index.get(name) or index.get(no_interpunct(name))
        if not english:
            warn.append(notice("engine.import.skippedUnknown", kind=gear, name=name))
            continue
        rating = max(1, cell_int(cells.get(f"{DEVICE_RATING}{row}")))
        out[keys[kind]].append({"id": str(uuid.uuid4()), "gear_id": ids[english], "rating": rating})
    for bucket, entries in out.items():
        if entries:
            st[bucket] = entries


def import_ware(cells: dict[str, str], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Fill the implant and device half of `st` from the 身体強化／電子機器 sheet."""
    _import_implants(cells, cat, st, warn)
    _import_devices(cells, cat, st, warn)


__all__ = ["GRADES", "NAME_ALIASES", "WARE_ROWS", "build_index", "clean_name", "import_ware"]
