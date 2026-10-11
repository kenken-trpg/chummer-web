"""Run Faster life modules (RF pp.65–86), flattened to selectable versions.

A version inherits its parent's cost, stage, source and bonus. Unsupported
mechanics remain visible, with reasons, rather than silently losing effects.
"""

from __future__ import annotations

from typing import Any

from .._xml import _int, _text, data_root
from ..requirements import parse_requirement_tree
from .qualities import load_qualities
from .quality_levels import load_quality_levels

LEVELS = {
    "attributelevel": "attributes",
    "skilllevel": "skills",
    "skillgrouplevel": "skill_groups",
    "knowledgeskilllevel": "knowledge_skills",
}


def load_life_modules() -> list[dict[str, Any]]:
    root = data_root("lifemodules.xml")
    if root is None:
        return []
    qualities = {q["name"]: q for q in load_qualities(include_hidden=True)}
    quality_levels = load_quality_levels()
    rows: list[dict[str, Any]] = []
    for parent in root.findall("./modules/module"):
        for version in parent.findall("./versions/version") or [parent]:
            issues: list[str] = []
            grants: list[dict[str, Any]] = []
            choices: list[dict[str, Any]] = []
            quality_grants: list[dict[str, Any]] = []
            specialization_grants: list[dict[str, str]] = []
            contact_grants: list[dict[str, int | bool]] = []
            nuyen = 0
            free_positive_qualities = 0
            free_negative_qualities = 0
            granted_quality_levels: list[dict[str, int | str]] = []
            required_tree: list[dict[str, Any]] = []
            blocks = [parent] if version is parent else [parent, version]
            for block in blocks:
                required = parse_requirement_tree(block.find("required"))
                required_tree.extend(required)
                if any(not _supported_requirement(node) for node in required):
                    issues.append("required:unsupported")
                # Some modules place qualitylevel inside addqualities. Route
                # both forms through the same group validation and resolution.
                # These nodes do not allocate choice slots, so saved choice
                # keys retain their original positions.
                bonus_nodes = block.findall("./bonus/*") + block.findall("./bonus/addqualities/qualitylevel")
                for node in bonus_nodes:
                    if node.tag in LEVELS:
                        name = _text(node.find("name"))
                        options = [_text(el) for el in node.findall("./options/*")]
                        key = str(len(grants))
                        if not name or "[" in name:
                            if not options and node.tag != "knowledgeskilllevel":
                                issues.append(node.tag + ":select")
                                continue
                            choices.append({"key": key, "kind": LEVELS[node.tag], "options": options})
                            name = ""
                        grants.append(
                            {
                                "kind": LEVELS[node.tag],
                                "name": name,
                                "choice": key,
                                "value": _int(node.find("val"), 1),
                                "category": _text(node.find("group")) or "Professional",
                            }
                        )
                    elif node.tag == "addqualities":
                        if any(el.tag not in {"addquality", "qualitylevel"} for el in node):
                            issues.append("addqualities:level")
                        for el in node.findall("addquality"):
                            name = _text(el)
                            spec = qualities.get(name)
                            if not spec or spec.get("needs_extra") or el.attrib:
                                issues.append("addquality:" + name)
                            else:
                                quality_grants.append(spec)
                    elif node.tag == "nuyenamt":
                        nuyen += _int(node)
                    elif node.tag == "freepositivequalities":
                        free_positive_qualities += abs(_int(node))
                    elif node.tag == "freenegativequalities":
                        free_negative_qualities += abs(_int(node))
                    elif node.tag == "qualitylevel":
                        group = node.get("group", "").strip()
                        level = _int(node)
                        if group in quality_levels and level in quality_levels[group]:
                            granted_quality_levels.append({"group": group, "level": level})
                        else:
                            issues.append("qualitylevel:unknown")
                    elif node.tag == "addskillspecialization":
                        skill, spec = _text(node.find("skill")), _text(node.find("spec"))
                        if skill and spec and len(node) == 2:
                            specialization_grants.append({"skill": skill, "spec": spec})
                        else:
                            issues.append("addskillspecialization:invalid")
                    elif node.tag == "addcontact":
                        allowed = {"connection", "loyalty", "free", "canwrite"}
                        connection, loyalty = node.find("connection"), node.find("loyalty")
                        if (
                            {child.tag for child in node} <= allowed
                            and connection is not None
                            and loyalty is not None
                            and not connection.attrib
                            and not loyalty.attrib
                        ):
                            contact_grants.append(
                                {
                                    "connection": _int(connection),
                                    "loyalty": _int(loyalty),
                                    "free": node.find("free") is not None,
                                }
                            )
                        else:
                            issues.append("addcontact:invalid")
                    elif node.tag == "selectquality":
                        options = [_text(el) for el in node.findall("quality") if _text(el)]
                        if options:
                            key = str(len(grants))
                            choices.append({"key": key, "kind": "qualities", "options": options})
                            grants.append(
                                {
                                    "kind": "qualities",
                                    "name": "",
                                    "choice": key,
                                    "value": 1,
                                    "category": "",
                                }
                            )
                        else:
                            issues.append("selectquality:empty")
                    elif node.tag == "selectskill":
                        options = [name.strip() for name in node.get("limittoskill", "").split(",") if name.strip()]
                        value = _int(node.find("val"))
                        if options and value > 0:
                            key = str(len(grants))
                            choices.append({"key": key, "kind": "skills", "options": options})
                            grants.append(
                                {
                                    "kind": "skills",
                                    "name": "",
                                    "choice": key,
                                    "value": value,
                                    "category": "Professional",
                                }
                            )
                        else:
                            issues.append("selectskill:invalid")
                    elif node.tag != "pushtext":
                        issues.append(node.tag)
            rows.append(
                {
                    "id": _text(version.find("id")),
                    "name": _text(version.find("name")),
                    "parent": _text(parent.find("name")) if version is not parent else "",
                    "stage": _text(parent.find("stage")),
                    "karma": _int(parent.find("karma")),
                    "source": _text(parent.find("source")),
                    "page": _text(parent.find("page")),
                    "story": _text(version.find("story")) or _text(parent.find("story")),
                    "grants": grants,
                    "choices": choices,
                    "quality_grants": quality_grants,
                    "specialization_grants": specialization_grants,
                    "contact_grants": contact_grants,
                    "nuyen": nuyen,
                    "free_positive_qualities": free_positive_qualities,
                    "free_negative_qualities": free_negative_qualities,
                    "quality_levels": granted_quality_levels,
                    "required": required_tree,
                    "unsupported": sorted(set(issues)),
                }
            )
    return rows


def _supported_requirement(node: dict[str, Any]) -> bool:
    tag = str(node.get("tag") or "")
    if tag in {"oneof", "allof", "group"}:
        return all(_supported_requirement(child) for child in node.get("children") or [])
    return tag in {"metatype", "quality"} and bool(node.get("name"))
