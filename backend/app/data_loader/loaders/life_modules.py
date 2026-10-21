"""Run Faster life modules (RF pp.65–86), flattened to selectable versions.

A version inherits its parent's cost, stage, source and bonus. Unsupported
mechanics remain visible, with reasons, rather than silently losing effects.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .._xml import _int, _text, data_root
from ..requirements import parse_requirement_tree
from .qualities import load_qualities
from .quality_levels import load_quality_levels
from .skills import load_skills

LEVELS = {
    "attributelevel": "attributes",
    "skilllevel": "skills",
    "skillgrouplevel": "skill_groups",
    "knowledgeskilllevel": "knowledge_skills",
}

# Exact spelling variants in the pinned Life Module data. Never use fuzzy
# matching: an unspecified level (e.g. Day Job) must remain unresolved.
QUALITY_REFERENCES = {
    "Silence Is Golden": ("Silence is Golden", ""),
    "Too Pretty to Hit": ("Too Pretty To Hit", ""),
    "Phobia (Mild, Common)": ("Phobia (Common, Mild)", ""),
    "Home Ground (You Know A Guy)": ("Home Ground", "You Know A Guy"),
    "SINner: National": ("SINner (National)", ""),
}

# Street Lethal p.128 specifies Day Job (5 Karma) for this module.
# Scope this repair to its ID; unqualified Day Job elsewhere stays unresolved.
MODULE_QUALITY_REFERENCES = {
    "d886934b-b937-4791-9512-cd7257ca721d": {"Day Job": "Day Job (10 hrs)"},
}

# Warm Body asks for "Corporate Pariah", which Street Lethal p.127 prints at two
# levels; neither the module's entry (p.129) nor the data says which. The level
# becomes the user's pick rather than a guess, scoped to this module's ID so an
# unqualified reference anywhere else stays unresolved.
MODULE_QUALITY_LEVEL_CHOICES = {
    "14dfb0c8-4748-490c-876d-f65f55e81d95": {
        "Corporate Pariah": ("Corporate Pariah I", "Corporate Pariah II"),
    },
}


def load_life_modules() -> list[dict[str, Any]]:
    root = data_root("lifemodules.xml")
    if root is None:
        return []
    lookups = _Lookups.load()
    rows: list[dict[str, Any]] = []
    for parent in root.findall("./modules/module"):
        for version in parent.findall("./versions/version") or [parent]:
            built = _Version()
            for block in [parent] if version is parent else [parent, version]:
                _read_block(block, built, lookups)
            rows.append(built.row(parent, version))
    return rows


@dataclass
class _Lookups:
    """The catalog tables a module's bonus is resolved against."""

    qualities: dict[str, dict[str, Any]]
    qualities_by_id: dict[str, dict[str, Any]]
    skill_groups: list[str]
    quality_levels: dict[str, Any]

    @classmethod
    def load(cls) -> _Lookups:
        qualities = {q["name"]: q for q in load_qualities(include_hidden=True)}
        return cls(
            qualities=qualities,
            qualities_by_id={q["id"]: q for q in qualities.values()},
            skill_groups=load_skills()["groups"],
            quality_levels=load_quality_levels(),
        )


@dataclass
class _Version:
    """One selectable version, as its parent's and its own blocks fill it in."""

    issues: list[str] = field(default_factory=list)
    grants: list[dict[str, Any]] = field(default_factory=list)
    choices: list[dict[str, Any]] = field(default_factory=list)
    quality_grants: list[dict[str, Any]] = field(default_factory=list)
    quality_choice_grants: list[dict[str, str]] = field(default_factory=list)
    specialization_grants: list[dict[str, str]] = field(default_factory=list)
    contact_grants: list[dict[str, int | bool]] = field(default_factory=list)
    nuyen: int = 0
    free_positive_qualities: int = 0
    free_negative_qualities: int = 0
    quality_levels: list[dict[str, int | str]] = field(default_factory=list)
    required: list[dict[str, Any]] = field(default_factory=list)

    def row(self, parent: ET.Element, version: ET.Element) -> dict[str, Any]:
        return {
            "id": _text(version.find("id")),
            "name": _text(version.find("name")),
            "parent": _text(parent.find("name")) if version is not parent else "",
            "family_id": _text(parent.find("id")),
            "stage": _text(parent.find("stage")),
            "karma": _int(parent.find("karma")),
            "source": _text(parent.find("source")),
            "page": _text(parent.find("page")),
            "story": _text(version.find("story")) or _text(parent.find("story")),
            "grants": self.grants,
            "choices": self.choices,
            "quality_grants": self.quality_grants,
            "quality_choice_grants": self.quality_choice_grants,
            "specialization_grants": self.specialization_grants,
            "contact_grants": self.contact_grants,
            "nuyen": self.nuyen,
            "free_positive_qualities": self.free_positive_qualities,
            "free_negative_qualities": self.free_negative_qualities,
            "quality_levels": self.quality_levels,
            "required": self.required,
            "unsupported": sorted(set(self.issues)),
        }


def _read_block(block: ET.Element, built: _Version, lookups: _Lookups) -> None:
    """A parent's or a version's `<required>` and `<bonus>`, added to `built`."""
    required = parse_requirement_tree(block.find("required"))
    built.required.extend(required)
    if any(not _supported_requirement(node) for node in required):
        built.issues.append("required:unsupported")
    # Some modules place qualitylevel inside addqualities. Route
    # both forms through the same group validation and resolution.
    # These nodes do not allocate choice slots, so saved choice
    # keys retain their original positions.
    bonus_nodes = block.findall("./bonus/*") + block.findall("./bonus/addqualities/qualitylevel")
    for node in bonus_nodes:
        handler = _BONUS.get(node.tag)
        if handler is not None:
            handler(node, block, built, lookups)
        elif node.tag != "pushtext":
            built.issues.append(node.tag)


def _skill_level(node: ET.Element, block: ET.Element, built: _Version, lookups: _Lookups) -> None:
    """`<attributelevel>`, `<skilllevel>`, `<skillgrouplevel>` and
    `<knowledgeskilllevel>`: a fixed grant, or a slot to pick one in."""
    grants, choices, issues = built.grants, built.choices, built.issues
    name = _text(node.find("name"))
    raw_options = [_text(el) for el in node.findall("./options/*") + node.findall("./option/*")]
    allow_custom = node.tag == "knowledgeskilllevel" and any("[" in option for option in raw_options)
    options = [option for option in raw_options if not (allow_custom and "[" in option)]
    category = _text(node.find("group")) or "Professional"
    # The pinned Azanian parent lists language names in
    # two option nodes (native/one level) but omits group.
    # Limit this data interpretation to that exact parent.
    if (
        _text(block.find("id")) == "baa9a6cc-2fb8-49d3-b503-d1f74bd0d915"
        and node.tag == "knowledgeskilllevel"
        and node.find("group") is None
        and node.find("option") is not None
    ):
        category = "Language"
    key = str(len(grants))
    category_options = [_text(el) for el in node.findall("./group/options/*")]
    category_choice = ""
    if category_options:
        if node.tag != "knowledgeskilllevel" or any(
            category not in {"Academic", "Professional", "Street", "Interest", "Language"}
            for category in category_options
        ):
            issues.append(node.tag + ":category")
            return
        category_choice = f"k{key}"
        choices.append({"key": category_choice, "kind": "knowledge_categories", "options": category_options})
    if not name or "[" in name:
        if not options and node.tag != "knowledgeskilllevel":
            issues.append(node.tag + ":select")
            return
        choices.append({"key": key, "kind": LEVELS[node.tag], "options": options, "allow_custom": allow_custom})
        name = ""
    grants.append(
        {
            "kind": LEVELS[node.tag],
            "name": name,
            "choice": key,
            "value": _int(node.find("val"), 1),
            "category": category,
            "category_choice": category_choice,
        }
    )
    specialization = _text(node.find("spec"))
    if specialization:
        if node.tag in {"skilllevel", "knowledgeskilllevel"} and name:
            if "[" in specialization:
                spec_choice = f"s{key}"
                choices.append(
                    {
                        "key": spec_choice,
                        "kind": "specializations",
                        "name": f"{name}: Specialization",
                        "options": [],
                    }
                )
                built.specialization_grants.append({"skill": name, "spec": "", "choice": spec_choice})
            else:
                built.specialization_grants.append({"skill": name, "spec": specialization})
        else:
            issues.append(node.tag + ":specialization")


def _add_qualities(node: ET.Element, block: ET.Element, built: _Version, lookups: _Lookups) -> None:
    if any(el.tag not in {"addquality", "qualitylevel"} for el in node):
        built.issues.append("addqualities:level")
    for el in node.findall("addquality"):
        _add_quality(el, _text(block.find("id")), built, lookups)


def _add_quality(el: ET.Element, block_id: str, built: _Version, lookups: _Lookups) -> None:
    """One `<addquality>`: a pick from options or from levels, a rated quality,
    a fixed one, or one whose free text the user fills in."""
    qualities, choices, issues = lookups.qualities, built.choices, built.issues
    name = _text(el)
    name = MODULE_QUALITY_REFERENCES.get(block_id, {}).get(name, name)
    option_nodes = el.findall("./options/quality")
    if option_nodes and not name:
        _quality_from_options(el, [_text(option) for option in option_nodes], built, lookups)
        return
    levels = MODULE_QUALITY_LEVEL_CHOICES.get(block_id, {}).get(name, ())
    if levels and all(option in qualities for option in levels):
        _quality_from_levels(el, name, levels, built, lookups)
        return
    spec = qualities.get(name) or lookups.qualities_by_id.get(name)
    reference_extra = ""
    if spec is None and name in QUALITY_REFERENCES:
        canonical, reference_extra = QUALITY_REFERENCES[name]
        spec = qualities.get(canonical)
    if spec:
        name = spec["name"]
    if spec and el.get("rating") is not None:
        try:
            rating = int(el.get("rating", ""))
        except ValueError:
            rating = 0
        if (
            set(el.attrib) == {"rating"}
            and spec.get("has_levels")
            and not spec.get("needs_extra")
            and 0 < rating <= int(spec.get("max_takes") or 0)
        ):
            built.quality_grants.append({**spec, "life_rating": rating})
        else:
            issues.append("addquality:" + name)
        return
    if (
        spec
        and spec.get("needs_extra")
        and spec.get("extra_kind") in {"text", "matrix_action", "skillgroup"}
        and not (set(el.attrib) - {"select"})
    ):
        key = f"q{len(built.quality_choice_grants)}"
        fixed = el.get("select", "").strip() or reference_extra
        if not fixed:
            choices.append(
                {
                    "key": key,
                    "kind": "qualities",
                    "name": name,
                    "options": lookups.skill_groups
                    if spec.get("extra_kind") == "skillgroup"
                    else spec.get("select_options") or [],
                }
            )
        built.quality_choice_grants.append({"quality_id": spec["id"], "choice": key, "value": fixed})
    elif not spec or spec.get("needs_extra") or el.attrib:
        issues.append("addquality:" + name)
    else:
        built.quality_grants.append(spec)


def _quality_from_options(el: ET.Element, options: list[str], built: _Version, lookups: _Lookups) -> None:
    """An `<addquality>` that lists the qualities to pick from."""
    grants, choices, issues = built.grants, built.choices, built.issues
    qualities = lookups.qualities
    if el.attrib or any(option not in qualities or qualities[option].get("needs_extra") for option in options):
        issues.append("addquality:choice")
    else:
        key = str(len(grants))
        choices.append({"key": key, "kind": "qualities", "options": options})
        grants.append({"kind": "qualities", "name": "", "choice": key, "value": 1, "category": ""})


def _quality_from_levels(
    el: ET.Element, name: str, levels: tuple[str, ...], built: _Version, lookups: _Lookups
) -> None:
    """A quality the book prints at several levels without saying which
    (`MODULE_QUALITY_LEVEL_CHOICES`): the level becomes the user's pick."""
    grants, choices, issues = built.grants, built.choices, built.issues
    qualities = lookups.qualities
    # One grant, two slots: which level, then the
    # level's own free text. Both must be the user's.
    extra_kinds = {qualities[option].get("extra_kind") or "" for option in levels}
    if el.attrib or (any(qualities[option].get("needs_extra") for option in levels) and extra_kinds != {"text"}):
        issues.append("addquality:" + name)
        return
    key = str(len(grants))
    choices.append(
        {
            "key": key,
            "kind": "qualities",
            "name": " / ".join(levels),
            "options": list(levels),
        }
    )
    grant: dict[str, Any] = {
        "kind": "qualities",
        "name": "",
        "choice": key,
        "value": 1,
        "category": "",
    }
    if extra_kinds == {"text"}:
        grant["extra_choice"] = f"x{key}"
        choices.append({"key": grant["extra_choice"], "kind": "qualities", "name": name, "options": []})
    grants.append(grant)


def _nuyen(node: ET.Element, block: ET.Element, built: _Version, lookups: _Lookups) -> None:
    built.nuyen += _int(node)


def _free_positive(node: ET.Element, block: ET.Element, built: _Version, lookups: _Lookups) -> None:
    built.free_positive_qualities += abs(_int(node))


def _free_negative(node: ET.Element, block: ET.Element, built: _Version, lookups: _Lookups) -> None:
    built.free_negative_qualities += abs(_int(node))


def _quality_level(node: ET.Element, block: ET.Element, built: _Version, lookups: _Lookups) -> None:
    group = node.get("group", "").strip()
    level = _int(node)
    if group in lookups.quality_levels and level in lookups.quality_levels[group]:
        built.quality_levels.append({"group": group, "level": level})
    else:
        built.issues.append("qualitylevel:unknown")


def _add_specialization(node: ET.Element, block: ET.Element, built: _Version, lookups: _Lookups) -> None:
    skill, fixed_spec = _text(node.find("skill")), _text(node.find("spec"))
    if skill and fixed_spec and len(node) == 2:
        built.specialization_grants.append({"skill": skill, "spec": fixed_spec})
    else:
        built.issues.append("addskillspecialization:invalid")


def _add_contact(node: ET.Element, block: ET.Element, built: _Version, lookups: _Lookups) -> None:
    allowed = {"connection", "loyalty", "free", "canwrite"}
    connection, loyalty = node.find("connection"), node.find("loyalty")
    if (
        {child.tag for child in node} <= allowed
        and connection is not None
        and loyalty is not None
        and not connection.attrib
        and not loyalty.attrib
    ):
        built.contact_grants.append(
            {
                "connection": _int(connection),
                "loyalty": _int(loyalty),
                "free": node.find("free") is not None,
            }
        )
    else:
        built.issues.append("addcontact:invalid")


def _select_quality(node: ET.Element, block: ET.Element, built: _Version, lookups: _Lookups) -> None:
    options = [_text(el) for el in node.findall("quality") if _text(el)]
    if options:
        key = str(len(built.grants))
        built.choices.append({"key": key, "kind": "qualities", "options": options})
        built.grants.append(
            {
                "kind": "qualities",
                "name": "",
                "choice": key,
                "value": 1,
                "category": "",
            }
        )
    else:
        built.issues.append("selectquality:empty")


def _select_skill(node: ET.Element, block: ET.Element, built: _Version, lookups: _Lookups) -> None:
    options = [name.strip() for name in node.get("limittoskill", "").split(",") if name.strip()]
    value = _int(node.find("val"))
    if options and value > 0:
        key = str(len(built.grants))
        built.choices.append({"key": key, "kind": "skills", "options": options})
        built.grants.append(
            {
                "kind": "skills",
                "name": "",
                "choice": key,
                "value": value,
                "category": "Professional",
            }
        )
    else:
        built.issues.append("selectskill:invalid")


#: What each `<bonus>` child does to a version. `<pushtext>` is story only;
#: any other tag makes the module unsupported rather than half-applied.
_BONUS: dict[str, Callable[[ET.Element, ET.Element, _Version, _Lookups], None]] = {
    **dict.fromkeys(LEVELS, _skill_level),
    "addqualities": _add_qualities,
    "nuyenamt": _nuyen,
    "freepositivequalities": _free_positive,
    "freenegativequalities": _free_negative,
    "qualitylevel": _quality_level,
    "addskillspecialization": _add_specialization,
    "addcontact": _add_contact,
    "selectquality": _select_quality,
    "selectskill": _select_skill,
}


def _supported_requirement(node: dict[str, Any]) -> bool:
    tag = str(node.get("tag") or "")
    if tag in {"oneof", "allof", "group"}:
        return all(_supported_requirement(child) for child in node.get("children") or [])
    return tag in {"metatype", "quality"} and bool(node.get("name"))
