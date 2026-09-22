"""Parsers for the ``<bonus>`` XML sub-tree and the select-power-slot shape.
Shared by every loader that reads a bonus block. Requirements live in
`requirements.py`, the quality pick inspectors in `bonus_extra.py`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from ._xml import _text


def _parse_weaponbonus(el: ET.Element | None) -> dict[str, str]:
    if el is None:
        return {}
    out: dict[str, str] = {}
    for child in list(el):
        text = _text(child)
        if text:
            out[child.tag] = text
    return out


def _bonus_fields(
    child: ET.Element,
) -> tuple[dict[str, Any], dict[str, list[str]], dict[str, dict[str, str]]]:
    fields: dict[str, Any] = {}
    nested: dict[str, list[str]] = {}
    field_attrs: dict[str, dict[str, str]] = {}
    for sub in list(child):
        if sub.attrib:
            field_attrs[sub.tag] = dict(sub.attrib)
        if len(sub) > 0:
            nested[sub.tag] = [_text(item) for item in list(sub) if _text(item)]
            continue
        value = _text(sub)
        existing = fields.get(sub.tag)
        if existing is None:
            fields[sub.tag] = value
        elif isinstance(existing, list):
            existing.append(value)
        else:
            fields[sub.tag] = [existing, value]
    return fields, nested, field_attrs


def parse_bonus(bonus_el: ET.Element | None) -> list[dict[str, Any]]:
    if bonus_el is None:
        return []
    nodes: list[dict[str, Any]] = []
    for child in list(bonus_el):
        tag = child.tag
        payload: dict[str, Any] = {"tag": tag}
        if child.attrib:
            payload["attrs"] = dict(child.attrib)
        if len(child) == 0:
            payload["value"] = _text(child)
        else:
            fields, nested, field_attrs = _bonus_fields(child)
            payload["fields"] = fields
            if tag == "metamagiclimit":
                # `<metamagic grade="N">Name</metamagic>` repeats, and the
                # generic field flattening keeps only the last element's
                # attributes; the grade/name pairing is rebuilt here so it
                # survives (same reason as `selectpowers` below).
                limits = [
                    {"grade": str(mm.attrib.get("grade") or ""), "name": _text(mm)}
                    for mm in child.findall("metamagic")
                    if _text(mm)
                ]
                if limits:
                    payload["metamagic_grades"] = limits
            if tag == "addqualities":
                # `<addquality select="X">Name</addquality>` repeats, and the
                # generic field flattening keeps only the last child's
                # attributes; name and pick are paired back up here (same
                # reason as `metamagiclimit` above).
                grants = [
                    {"name": _text(q), "select": str(q.attrib.get("select") or "")}
                    for q in child.findall("addquality")
                    if _text(q)
                ]
                if grants:
                    payload["quality_grants"] = grants
            if tag == "addgear":
                # `<children><child>…</child></children>` is a list of whole
                # gear specs, which the generic flattening drops; Dead SIN's
                # four fake licenses live there, so they are rebuilt (same
                # reason as `metamagiclimit` above).
                kids = [
                    {sub.tag: _text(sub) for sub in list(kid)}
                    for kid in child.findall("./children/child")
                    if _text(kid.find("name"))
                ]
                if kids:
                    payload["gear_children"] = kids
            if tag == "replaceattributes":
                # `<replaceattribute>` repeats, and the generic flattening
                # loses which min/max/aug belongs to which attribute — the
                # rows are rebuilt here (same reason as `metamagiclimit`).
                ranges = [
                    {sub.tag: _text(sub) for sub in list(rep)}
                    for rep in child.findall("replaceattribute")
                    if _text(rep.find("name"))
                ]
                if ranges:
                    payload["attribute_ranges"] = ranges
            if tag == "selectpowers":
                specs: list[dict[str, Any]] = []
                for sp in child.findall("selectpower"):
                    sp_fields: dict[str, Any] = {}
                    for sub in list(sp):
                        sp_fields[sub.tag] = _text(sub)
                    specs.append({"attrs": dict(sp.attrib), "fields": sp_fields})
                if specs:
                    payload["selectpower_specs"] = specs
            if nested:
                payload["nested"] = nested
            if field_attrs:
                payload["field_attrs"] = field_attrs
        nodes.append(payload)
    return nodes


def parse_select_power_slot(node: dict[str, Any]) -> dict[str, Any]:
    specs = list(node.get("selectpower_specs") or [])
    sp = specs[0] if specs else {}
    attrs = dict(sp.get("attrs") or {})
    if not attrs:
        attrs = dict((node.get("field_attrs") or {}).get("selectpower") or {})
    fields = dict(sp.get("fields") or {})
    limit_raw = str(attrs.get("limittopowers") or "").strip()
    options = [part.strip() for part in limit_raw.split(",") if part.strip()]
    val_raw = str(fields.get("val") or "").strip()
    limit_field = str(fields.get("limit") or "").strip()
    ignore_rating = str(fields.get("ignorerating") or "").lower() == "true"
    points_per_level = 0.25
    points_raw = fields.get("pointsperlevel")
    if points_raw not in (None, ""):
        try:
            points_per_level = float(points_raw)
        except (TypeError, ValueError):
            pass
    nested_vals = (node.get("nested") or {}).get("selectpower") or []
    rating = 1
    rating_expr = ""
    if val_raw.lower() == "rating":
        rating_expr = "Rating"
    elif val_raw:
        try:
            rating = max(1, int(float(val_raw)))
        except (TypeError, ValueError):
            pass
    else:
        for item in nested_vals:
            try:
                rating = max(1, int(float(item)))
                break
            except (TypeError, ValueError):
                continue
    limit_expr = "Rating" if limit_field.lower() == "rating" else ""
    open_select = not options
    return {
        "options": options,
        "rating": rating,
        "rating_expr": rating_expr,
        "limit_expr": limit_expr,
        "points_per_level": points_per_level,
        "ignore_rating": ignore_rating,
        "open_select": open_select,
        "needs_select": bool(options) or open_select,
    }


def _specific_powers(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in nodes:
        if node.get("tag") != "specificpower":
            continue
        fields = node.get("fields") or {}
        name = str(fields.get("name") or "").strip()
        if not name:
            continue
        out.append(
            {
                "name": name,
                "rating": max(1, _int_text(fields.get("val"), 1)),
                "select": "skill" if "selectskill" in str(node.get("nested") or {}) else None,
            }
        )
    return out


def _int_text(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default
