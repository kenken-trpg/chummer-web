"""Parsers for the ``<required>`` / ``<forbidden>`` XML sub-trees."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from ._xml import _int, _text


def parse_requirement_tree(el: ET.Element | None) -> list[dict[str, Any]]:
    if el is None:
        return []
    return [_parse_requirement_node(child) for child in list(el)]


def _parse_requirement_node(el: ET.Element) -> dict[str, Any]:
    tag = el.tag
    if tag in {"oneof", "allof", "group"}:
        return {"tag": tag, "children": [_parse_requirement_node(child) for child in list(el)]}
    if tag == "skill":
        if len(el) > 0:
            return {
                "tag": "skill",
                "name": _text(el.find("name")),
                "val": _int(el.find("val"), 1),
                "spec": _text(el.find("spec")),
                "type": _text(el.find("type")),
            }
        return {"tag": "skill", "name": _text(el), "val": 1, "spec": "", "type": ""}
    if tag == "ess":
        raw = _text(el) or "0"
        try:
            value = float(raw)
        except ValueError:
            value = 0.0
        node: dict[str, Any] = {"tag": "ess", "value": value}
        if el.attrib.get("grade"):
            node["grade"] = el.attrib.get("grade")
        return node
    node = {"tag": tag, "name": _text(el)}
    if el.attrib:
        node["attrs"] = dict(el.attrib)
    return node


# Common SR5 Matrix actions for Codeslinger-style picks.


def _parent_name_requirements(el: ET.Element) -> list[str]:
    names: list[str] = []
    required_el = el.find("required")
    if required_el is None:
        return names
    for name_el in required_el.findall(".//parentdetails//name"):
        text = _text(name_el)
        if text and text not in names:
            names.append(text)
    return names


def parse_required(el: ET.Element | None) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {
        "bioware": [],
        "cyberware": [],
        "metatype": [],
        "quality": [],
        "power": [],
        "metamagicart": [],
        "metamagic": [],
    }
    if el is None:
        return out
    for group in list(el):
        for child in list(group):
            tag = child.tag
            name = _text(child)
            if tag in out and name and name not in out[tag]:
                out[tag].append(name)
    return out
