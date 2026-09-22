"""`gear_extra_skill_kind`: which translation kind a gear pick's name is."""

from __future__ import annotations

from app.catalog_view import public_catalog


def _row(key: str, name: str) -> dict:
    return next(row for row in public_catalog()[key] if row["name"] == name)


def test_skillsofts_carry_the_kind_of_skill_they_pick() -> None:
    assert _row("gear", "Activesoft")["extra_skill_kind"] == "skill"
    assert _row("gear", "Knowsoft")["extra_skill_kind"] == "knowledge_skill"
    assert _row("gear", "Linguasoft")["extra_skill_kind"] == "knowledge_skill"
    assert _row("programs", "Skill Autosoft (Knowledge)")["extra_skill_kind"] == "knowledge_skill"
    assert _row("programs", "Skill Autosoft (Restricted)")["extra_skill_kind"] == "skill"


def test_a_mixed_or_non_skill_list_has_no_kind() -> None:
    # Tool Kit lists active and knowledge skills together; Chemistry is both
    assert _row("gear", "Tool Kit")["extra_skill_kind"] == ""
    assert _row("gear", "Magical Lodge Materials")["extra_skill_kind"] == ""
    assert _row("programs", "[Weapon] Melee Autosoft")["extra_skill_kind"] == ""
