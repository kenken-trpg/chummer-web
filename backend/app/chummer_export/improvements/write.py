"""The improvements written under `<improvements>`, and the rows some of them
point at."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from copy import deepcopy

from ...data_loader import catalog_list
from ...data_loader._xml import parse_data
from .._common import _sub, improvements_of
from ._imp import _Imp


def _own_gear_ids() -> set[str]:
    buckets = ("gear", "commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps")
    return {str(row["id"]) for bucket in buckets for row in catalog_list(bucket)}


def _with_rows(root: ET.Element, rows: list[_Imp], guid: str, owner: str) -> list[_Imp]:
    """The rows a LimitModifier or Gear improvement names, written, and the
    improvements pointing at them by guid — `limitmodifier` and `addgear` make
    the row and the improvement together. The import reads neither back."""
    out = []
    for index, row in enumerate(rows):
        if row.kind == "LimitModifier":
            row_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{guid}:limitmodifier:{index}"))
            parent = root.find("limitmodifiers")
            el = _sub(parent if parent is not None else _sub(root, "limitmodifiers"), "limitmodifier")
            for key, value in (
                ("guid", row_guid),
                ("name", owner),
                ("limit", row.target),
                ("condition", row.condition),
            ):
                _sub(el, key, value)
            _sub(el, "bonus", row.val)
            out.append(_Imp("LimitModifier", row_guid, val=row.val, condition=row.condition))
        elif row.kind == "Gear":
            definition = next(
                (
                    gear
                    for gear in parse_data("gear.xml").findall("./gears/gear")
                    if gear.findtext("name") == row.improved and gear.findtext("category") == row.target
                ),
                None,
            )
            if definition is None or str(definition.findtext("id")) in _own_gear_ids():
                continue
            row_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{guid}:addgear:{index}"))
            parent = root.find("gears")
            el = _sub(parent if parent is not None else _sub(root, "gears"), "gear")
            _sub(el, "guid", row_guid)
            _sub(el, "sourceid", definition.findtext("id") or "")
            for field in definition:
                if field.tag not in ("id", "hide", "rating", "cost"):
                    el.append(deepcopy(field))
            _sub(el, "rating", row.rating)
            _sub(el, "qty", 1)
            _sub(el, "cost", 0)
            _sub(el, "parentid", guid)
            out.append(_Imp("Gear", row_guid))
        else:
            out.append(row)
    return out


def _write_improvements(
    root: ET.Element, rows: list[_Imp], source_name: str, source: str, enabled: bool = True
) -> None:
    """`enabled` False: the owner is off (armor not worn), whose improvements
    Chummer keeps but disables."""
    if not rows:
        return
    imps = improvements_of(root)
    for row in rows:
        imp = _sub(imps, "improvement")
        if row.unique:
            _sub(imp, "unique", row.unique)
        _sub(imp, "target", row.target)
        _sub(imp, "improvedname", row.improved)
        _sub(imp, "sourcename", source_name)
        _sub(imp, "min", row.min)
        _sub(imp, "max", row.max)
        _sub(imp, "aug", row.aug)
        _sub(imp, "augmax", row.augmax)
        _sub(imp, "val", row.val)
        _sub(imp, "rating", row.rating)
        _sub(imp, "exclude", row.exclude)
        _sub(imp, "condition", row.condition)
        _sub(imp, "improvementttype", row.kind)
        _sub(imp, "improvementsource", source)
        if row.addtorating:
            _sub(imp, "addtorating", "True")
        if not enabled:
            _sub(imp, "enabled", 0)
