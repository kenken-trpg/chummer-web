"""An A.I.'s own programs: `programs.xml` (DT p.158 for the advanced ones).

Not the gear of the same names. `gear.xml` sells Browse and Exploit to run on
a deck; this file is what an A.I. *is* made of, bought with karma (Chummer's
`AIProgram`, picked in SelectAIProgram).
"""

from __future__ import annotations

from typing import Any

from .._xml import _text, data_root

#: The category whose programs cost the advanced price
#: (`<karmanewaiadvancedprogram>`), as Chummer's `AIProgram.IsAdvancedProgram`.
ADVANCED_CATEGORY = "Advanced Programs"

#: What `Inherent Program` may pick: SelectAIProgram is opened with
#: `blnInherentProgram`, which keeps only these two categories.
INHERENT_CATEGORIES = ("Common Programs", "Hacking Programs")


def load_ai_programs() -> list[dict[str, Any]]:
    root = data_root("programs.xml")
    if root is None:
        return []
    items: list[dict[str, Any]] = []
    for el in root.findall("./programs/program"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        program_id = _text(el.find("id"))
        if not name or not program_id:
            continue
        category = _text(el.find("category"))
        bonus = el.find("bonus")
        tags = [child.tag for child in bonus] if bonus is not None else []
        items.append(
            {
                "id": program_id,
                "name": name,
                "category": category,
                "advanced": category == ADVANCED_CATEGORY,
                # `<required><oneof><program>`: one of these must already be
                # among the character's programs (SelectionShared's "program").
                "required": [_text(p) for p in el.findall("./required/oneof/program") if _text(p)],
                # The autosofts' model, weapon or skill: a free-text pick
                # Chummer asks for when the program is added.
                "needs_extra": "selecttext" in tags or "selectskill" in tags,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items
