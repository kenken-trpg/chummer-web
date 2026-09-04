"""Character-creation options: metatypes, skills, qualities, priorities.

The priority table is the one section that is *computed* rather than projected —
`priority_value()` resolves each cell and `talent_options()` fills the Talent
column, so the UI never has to know how priorities are stored.
"""

from __future__ import annotations

from ..data_loader import CatalogDict
from ..engine import all_talent_options, is_way_quality, priority_value, talent_options

#: The five metatypes the priority table offers. Chummer's data has many more
#: (metavariants, critters); the UI only ever builds from these.
CORE_METATYPES = {"Human", "Elf", "Dwarf", "Ork", "Troll"}


def section(raw: CatalogDict) -> dict:
    qualities = [
        {
            "id": q["id"],
            "name": q["name"],
            "karma": q["karma"],
            "category": q["category"],
            "source": q["source"],
            "page": q["page"],
            "bonus_tags": [n["tag"] for n in q.get("bonus") or []],
            "forbidden_qualities": list((q.get("forbidden") or {}).get("quality") or []),
            "is_way": is_way_quality(q["name"]),
            "metagenic": bool(q.get("metagenic")),
            "needs_extra": bool(q.get("needs_extra")),
            "extra_kind": q.get("extra_kind") or "",
            "select_options": list(q.get("select_options") or []),
            "spirit_options": list(q.get("spirit_options") or []),
            "expertise_skill": q.get("expertise_skill") or "",
            "max_takes": q.get("max_takes"),
            "required_tree": q.get("required_tree") or [],
            "forbidden_tree": q.get("forbidden_tree") or [],
        }
        for q in raw["qualities"]
        if not q.get("onlyprioritygiven")
    ]
    table: dict[str, dict[str, dict]] = {}
    for cat in ("Heritage", "Attributes", "Talent", "Skills", "Resources"):
        table[cat] = {}
        for letter in "ABCDE":
            row = priority_value(cat, letter)
            mets = [m for m in (row.get("metatypes") or []) if m["name"] in CORE_METATYPES]
            table[cat][letter] = {
                "name": row.get("name"),
                "attribute_points": row.get("attribute_points"),
                "skill_points": row.get("skill_points"),
                "skill_group_points": row.get("skill_group_points"),
                "nuyen": row.get("nuyen"),
                "metatypes": mets,
                "talents": talent_options(letter) if cat == "Talent" else row.get("talents") or [],
            }
    return {
        "metatypes": raw["metatypes"],
        "skills": raw["skills"],
        "qualities": qualities,
        "martial_arts": [
            {
                "id": art["id"],
                "name": art["name"],
                "cost": int(art.get("cost") or 7),
                "techniques": list(art.get("techniques") or []),
                "source": art.get("source") or "",
                "page": art.get("page") or "",
                "is_quality": bool(art.get("is_quality")),
                "all_techniques": bool(art.get("all_techniques")),
                "spec_options": [
                    {"skill": skill, "spec": spec}
                    for node in (art.get("bonus") or [])
                    if node.get("tag") == "addskillspecializationoption"
                    for skill in [str((node.get("fields") or {}).get("skill") or "").strip()]
                    for spec in [str((node.get("fields") or {}).get("spec") or "").strip()]
                    if skill and spec
                ],
            }
            for art in raw.get("martial_arts") or []
            if not art.get("is_quality")
        ],
        "martial_art_techniques": [
            {
                "id": tech["id"],
                "name": tech["name"],
                "source": tech.get("source") or "",
                "page": tech.get("page") or "",
            }
            for tech in raw.get("martial_art_techniques") or []
        ],
        "priority_table": table,
        "karma_talents": [
            {
                "name": t["name"],
                "label": t.get("label") or t["name"],
                "magic": int(t.get("magic") or 0),
                "resonance": int(t.get("resonance") or 0),
            }
            for t in all_talent_options()
        ],
    }
