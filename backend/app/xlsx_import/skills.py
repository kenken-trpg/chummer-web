"""The 能動技能／技能グループ and 知識技能／言語技能 sheets.

The active sheet is the easiest thing in the template to read: it lists every
skill in the book, one per row, and the player only fills in the numbers. So the
names are the template's own rather than typed, and they match the catalog
almost completely — the aliases below are the whole of the gap.

Two things about the layout are worth knowing:

* **Rows are found by their headings, not by number.** Every version seen so far
  puts the groups at rows 4–18 and the skills from 21 on, but a row inserted in
  a later revision would silently shift every skill by one. The section headings
  (技能グループ, ⋯能動技能) are stable, so the sections are cut at those.
* **Some rows carry no name.** A skill usable through more than one attribute
  gets a row per attribute, the extra ones holding only the attribute
  (コンピュータ has 直観力 and 共振力 under it). Those are the same skill, so a
  nameless row is skipped rather than read as a skill of its own.

The knowledge sheet is the other way round: the player types the name, and
anything is allowed, so the names go through as written.
"""

from __future__ import annotations

import re
from typing import Any

from ..data_loader import CatalogDict
from ..notices import Notice, notice, ui
from ._common import cell_int, japanese_index

#: The heading that opens the skill-group block, and the pattern of the ones that
#: open a block of skills (戦闘系能動技能, 身体系能動技能, …).
GROUPS_HEADING = "技能グループ"
SKILLS_HEADING = re.compile(r"能動技能$")

#: Active sheet: E/F the specialization (bought with points / with karma),
#: I the points, J the karma. G is the starting value the sheet derives and
#: L the finished rating, group included — neither is an input.
#:
#: A rating here is points + karma, the way a .chum5 read writes it: `skills`
#: holds what the skill ends up at and `skill_karma` how much of that was
#: bought with karma, so adding the two columns is the rating and the karma
#: column alone is the split.
COLUMN_SPEC_POINTS = "E"
COLUMN_SPEC_KARMA = "F"
COLUMN_POINTS = "I"
COLUMN_KARMA = "J"

#: Knowledge sheet: A the category, B the name, E/F the specialization,
#: H the points, I the karma.
KNOWLEDGE_ROWS = range(3, 28)

#: The categories the knowledge sheet offers -> Chummer's own.
KNOWLEDGE_CATEGORIES = {
    "ストリート知識技能": "Street",
    "学術知識技能": "Academic",
    "職業知識技能": "Professional",
    "趣味知識技能": "Interest",
    "言語知識技能": "Language",
    "言語知識技能（Native）": "Language",
    "その他（直観力）": "Interest",
    "その他（論理力）": "Academic",
}

#: The category that means the language is the character's own.
NATIVE_CATEGORY = "言語知識技能（Native）"

#: Skills the template names differently from the catalog's Japanese.
SKILL_ALIASES = {
    "工業機械設備": "工業機器整備",
    "応急措置": "応急処置",
    "特殊ヴィークル操縦": "特殊ヴィークル操縦［特定］",
}

#: Skill groups the template names differently. Seven of the fifteen: the
#: template uses the names the Japanese book prints, the catalog the ones its
#: own translation file carries.
GROUP_ALIASES = {
    "小火器": "Firearms",
    "野外活動": "Outdoors",
    "対人": "Influence",
    "呪付": "Enchanting",
    "召霊術": "Conjuring",
    "機器整備": "Engineering",
    "電子工学": "Electronics",
}


def _sections(cells: dict[str, str]) -> tuple[list[int], list[int]]:
    """(group rows, skill rows) of the active sheet, cut at its headings."""
    labelled = sorted((int(ref[1:]), text) for ref, text in cells.items() if re.fullmatch(r"A\d+", ref))
    groups_at = next((row for row, text in labelled if text == GROUPS_HEADING), None)
    skills_at = [row for row, text in labelled if SKILLS_HEADING.search(text)]
    if groups_at is None or not skills_at:
        return [], []
    headings = {row for row, _ in labelled if row == groups_at or row in skills_at}
    group_rows = [row for row, _ in labelled if groups_at < row < skills_at[0] and row not in headings]
    skill_rows = [row for row, _ in labelled if row > skills_at[0] and row not in headings]
    return group_rows, skill_rows


def _specialization(cells: dict[str, str], row: int) -> tuple[str, bool]:
    """(specialization, bought with karma). The sheet has a column for each."""
    with_points = (cells.get(f"{COLUMN_SPEC_POINTS}{row}") or "").strip()
    if with_points:
        return with_points, False
    return (cells.get(f"{COLUMN_SPEC_KARMA}{row}") or "").strip(), True


def _import_groups(
    cells: dict[str, str], rows: list[int], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]
) -> None:
    index = japanese_index(cat, [str(name) for name in cat["skills"]["group_names"]], "skill")
    groups: dict[str, int] = {}
    karma: dict[str, int] = {}
    for row in rows:
        name = (cells.get(f"A{row}") or "").strip()
        points = cell_int(cells.get(f"{COLUMN_POINTS}{row}"))
        bought = cell_int(cells.get(f"{COLUMN_KARMA}{row}"))
        if not points and not bought:
            continue
        english = index.get(name) or GROUP_ALIASES.get(name)
        if not english:
            warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.skill"), name=name))
            continue
        groups[english] = points + bought
        if bought:
            karma[english] = bought
    if groups:
        st["skill_groups"] = groups
    if karma:
        st["skill_group_karma"] = karma


def _import_active(
    cells: dict[str, str], rows: list[int], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]
) -> None:
    by_name = {str(row["name"]): row for row in cat["skills"]["skills"]}
    index = japanese_index(cat, by_name, "skill")
    skills: dict[str, int] = {}
    karma: dict[str, int] = {}
    specs: dict[str, str] = {}
    specs_karma: list[str] = []
    exotic: list[dict[str, Any]] = []
    for row in rows:
        name = (cells.get(f"A{row}") or "").strip()
        if not name:
            # An extra row for the same skill under another attribute.
            continue
        points = cell_int(cells.get(f"{COLUMN_POINTS}{row}"))
        bought = cell_int(cells.get(f"{COLUMN_KARMA}{row}"))
        spec, spec_with_karma = _specialization(cells, row)
        if not points and not bought and not spec:
            continue
        english = index.get(name) or index.get(SKILL_ALIASES.get(name, ""))
        if not english:
            warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.skill"), name=name))
            continue
        spec_english = _spec_name(by_name[english], spec, cat)
        if by_name[english].get("exotic"):
            # An exotic skill is one entry per weapon rather than a rating on a
            # shared skill, and the template gives the four rows no room to say
            # which weapon: the specialization column is the only hint there is.
            exotic.append({"skill_name": english, "extra": spec_english, "rating": max(1, points + bought)})
            continue
        if points or bought:
            skills[english] = points + bought
        if bought:
            karma[english] = bought
        if spec_english:
            specs[english] = spec_english
            if spec_with_karma:
                specs_karma.append(english)
    if skills:
        st["skills"] = skills
    if karma:
        st["skill_karma"] = karma
    if specs:
        st["skill_specializations"] = specs
    if specs_karma:
        st["skill_specs_karma"] = specs_karma
    if exotic:
        st["exotic_skills"] = exotic


def _spec_name(skill: dict[str, Any], spec: str, cat: CatalogDict) -> str:
    """A typed specialization as the catalog spells it, or as typed.

    The book's own specializations translate, but the template lets the player
    write anything — ライトピストル is not one of Pistols' four — and a made-up
    one is theirs to keep.
    """
    if not spec:
        return ""
    index = japanese_index(cat, [str(option) for option in skill.get("specs") or []], "skill")
    return index.get(spec, spec)


def _import_knowledge(cells: dict[str, str], st: dict[str, Any]) -> None:
    """Knowledge and language skills, whose names are the player's own."""
    know: dict[str, int] = {}
    karma: dict[str, int] = {}
    categories: dict[str, str] = {}
    natives: list[str] = []
    specs: dict[str, str] = st.get("skill_specializations") or {}
    specs_karma: list[str] = st.get("skill_specs_karma") or []
    for row in KNOWLEDGE_ROWS:
        name = (cells.get(f"B{row}") or "").strip()
        if not name:
            continue
        category = (cells.get(f"A{row}") or "").strip()
        if category == NATIVE_CATEGORY:
            # A native language costs nothing and carries no rating.
            natives.append(name)
            continue
        bought = cell_int(cells.get(f"I{row}"))
        know[name] = cell_int(cells.get(f"H{row}")) + bought
        if bought:
            karma[name] = bought
        categories[name] = KNOWLEDGE_CATEGORIES.get(category, "Academic")
        spec, spec_with_karma = _specialization(cells, row)
        if spec:
            specs[name] = spec
            if spec_with_karma:
                specs_karma.append(name)
    if know:
        st["knowledge_skills"] = know
    if karma:
        st["knowledge_karma"] = karma
    if categories:
        st["knowledge_categories"] = categories
    if natives:
        st["native_languages"] = natives
    if specs:
        st["skill_specializations"] = specs
    if specs_karma:
        st["skill_specs_karma"] = specs_karma


def import_skills(
    active: dict[str, str], knowledge: dict[str, str], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]
) -> None:
    """Fill the skill half of `st` from the two skill sheets."""
    group_rows, skill_rows = _sections(active)
    _import_groups(active, group_rows, cat, st, warn)
    _import_active(active, skill_rows, cat, st, warn)
    _import_knowledge(knowledge, st)


__all__ = [
    "GROUP_ALIASES",
    "KNOWLEDGE_CATEGORIES",
    "KNOWLEDGE_ROWS",
    "SKILL_ALIASES",
    "import_skills",
]
