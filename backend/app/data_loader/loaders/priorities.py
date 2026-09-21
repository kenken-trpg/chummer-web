"""Priority-table loader."""

from __future__ import annotations

from typing import Any

from .._xml import _child, _int, _text, parse_data


def load_priorities() -> list[dict[str, Any]]:
    root = parse_data("priorities.xml")
    rows = []
    for el in root.findall("./priorities/priority"):
        category = _text(el.find("category"))
        value = _text(el.find("value"))
        if not category or not value:
            continue
        row: dict[str, Any] = {
            "id": _text(el.find("id")),
            "name": _text(el.find("name")),
            "category": category,
            "value": value,
            "gameplay": _text(_child(el, "gameplay", "prioritytable"), "Standard"),
        }
        if category == "Heritage":
            mets = []
            for m in el.findall("./metatypes/metatype"):
                mets.append(
                    {
                        "name": _text(m.find("name")),
                        "special": _int(m.find("value")),
                        "karma": _int(m.find("karma")),
                        "variants": [
                            {
                                "name": _text(v.find("name")),
                                "special": _int(v.find("value"), _int(m.find("value"))),
                                "karma": _int(v.find("karma")),
                            }
                            for v in m.findall("./metavariants/metavariant")
                        ],
                    }
                )
            row["metatypes"] = mets
        elif category == "Attributes":
            row["attribute_points"] = _int(el.find("attributes"))
        elif category == "Skills":
            row["skill_points"] = _int(el.find("skills"))
            row["skill_group_points"] = _int(el.find("skillgroups"))
        elif category == "Resources":
            row["nuyen"] = _int(el.find("resources"))
        elif category == "Talent":
            talents = []
            for t in el.findall("./talents/talent"):
                magic = _int(t.find("magic"))
                resonance = _int(t.find("resonance"))
                talents.append(
                    {
                        "name": _text(t.find("value")) or _text(t.find("name")),
                        "label": _text(t.find("name")),
                        "magic": magic,
                        "resonance": resonance,
                        "value": magic or resonance,
                        "quality": _text(t.find("./qualities/quality")),
                        "spells": _int(t.find("spells")),
                        "cfp": _int(t.find("cfp")),
                        "free_skills": _free_skills(t),
                    }
                )
            row["talents"] = talents
        rows.append(row)
    return rows


def _free_skills(t: Any) -> dict[str, Any] | None:
    """The skills a talent hands out at a fixed rating (Magician's two
    magical skills at 5, Adept's one active skill, Aspected's one group).

    ``type`` says which skills qualify, as Chummer's `SelectMetatypePriority`
    reads it: ``magic`` / ``resonance`` / ``matrix`` name a fixed filter,
    ``specific`` lists them in ``choices``, ``xpath`` carries its own filter
    in ``xpath``, and ``grouped`` picks a skill group out of ``choices``.
    """
    if t.find("skillgroupqty") is not None:
        return {
            "group": True,
            "qty": _int(t.find("skillgroupqty")),
            "val": _int(t.find("skillgroupval")),
            "type": "grouped",
            "xpath": "",
            "choices": [_text(g) for g in t.findall("./skillgroupchoices/skillgroup") if _text(g)],
        }
    if t.find("skillqty") is None:
        return None
    typ = t.find("skilltype")
    return {
        "group": False,
        "qty": _int(t.find("skillqty")),
        "val": _int(t.find("skillval")),
        "type": _text(typ).lower(),
        "xpath": typ.get("xpath", "") if typ is not None else "",
        "choices": [_text(c) for c in t.findall("./skillchoices/skill") if _text(c)],
    }
