"""シャドウラン_キャラシテンプレート (.xlsx) import — see backend/app/xlsx_import/."""

from __future__ import annotations

import zipfile
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.characters import import_character
from app.data_loader import catalog
from app.main import app
from app.notices import Notice, NoticeError
from app.xlsx_import import is_template_workbook
from app.xlsx_import import xlsx_to_state as _read
from app.xlsx_import._common import (
    SHEET_BASICS,
    SHEET_CONTACTS,
    SHEET_MAGIC,
    SHEET_SKILLS,
    SHEET_WARE,
    cell_int,
    japanese_index,
)
from app.xlsx_import._sheet import NotAWorkbook, Workbook
from app.xlsx_import.gear import SUGGEST_LIMIT, split_row
from app.xlsx_import.magic import MENTOR_ALIASES, mentor_index, resolve_mentor
from app.xlsx_import.qualities import candidates, resolve, split_name
from app.xlsx_import.skills import GROUP_ALIASES, SKILL_ALIASES
from app.xlsx_import.ware import NAME_ALIASES as WARE_ALIASES
from app.xlsx_import.ware import build_index as ware_index
from app.xlsx_import.ware import clean_name
from tests.notice_asserts import has
from tests.xlsx_fixtures import (
    BASELINE,
    contact_sheet,
    filled,
    magic_sheet,
    skill_sheet,
    ware_sheet,
    workbook,
)


def xlsx_to_state(body: bytes) -> tuple[dict[str, Any], list[Notice]]:
    """The state and the warnings, which is what almost every test is about.

    `xlsx_to_state` also hands back the 装備 rows that need confirming; those
    have their own tests, through `pending_of`.
    """
    state, warnings, _pending = _read(body)
    return state, warnings


def pending_of(body: bytes) -> list[dict[str, Any]]:
    """The 装備 rows that could not be matched."""
    return _read(body)[2]


def _quality_id(name: str) -> str:
    return next(str(row["id"]) for row in catalog()["qualities"] if row["name"] == name)


def _catalog_id(key: str, name: str) -> str:
    return next(str(row["id"]) for row in catalog()[key] if row["name"] == name)


def _mentor_id(name: str) -> str:
    return _catalog_id("mentors", name)


# --- the workbook reader -------------------------------------------------


def test_reads_both_string_kinds() -> None:
    """A real download mixes shared strings (the dropdowns) with formula results
    and inline strings. All three have to come through."""
    body = workbook(
        {"C16": "ignored", "C17": "－", "H19": "3.0"},
        shared_strings=["ヒューマン"],
        shared={"C16": 0},
    )
    cells = Workbook(body).cells(SHEET_BASICS)
    assert cells["C16"] == "ヒューマン"  # shared string
    assert cells["C17"] == "－"  # inline string
    assert cells["H19"] == "3.0"  # number


def test_empty_cells_are_absent() -> None:
    cells = Workbook(filled()).cells(SHEET_BASICS)
    assert "C50" not in cells


def test_sheet_names_are_listed_in_order() -> None:
    assert Workbook(filled()).sheet_names[0] == SHEET_BASICS


def test_refuses_a_non_zip() -> None:
    with pytest.raises(NotAWorkbook):
        Workbook(b"not a zip at all")


def test_refuses_a_zip_that_is_not_a_workbook() -> None:
    import io

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("hello.txt", "hi")
    with pytest.raises(NotAWorkbook):
        Workbook(buffer.getvalue())


def test_refuses_an_unknown_sheet() -> None:
    with pytest.raises(NotAWorkbook):
        Workbook(filled()).cells("そんなシートはない")


def test_refuses_a_part_that_unzips_too_large(monkeypatch: pytest.MonkeyPatch) -> None:
    """A small archive may still decompress into a large one."""
    monkeypatch.setattr("app.xlsx_import._sheet.MAX_PART_BYTES", 16)
    with pytest.raises(NotAWorkbook):
        Workbook(filled())


@pytest.mark.parametrize(
    ("text", "expected"),
    [("5.0", 5), ("5", 5), ("", 0), (None, 0), ("ヒューマン", 0), ("2.5", 2), ("nan", 0), ("inf", 0)],
)
def test_cell_int(text: str | None, expected: int) -> None:
    assert cell_int(text) == expected


# --- recognising the template -------------------------------------------


def test_recognises_the_template() -> None:
    assert is_template_workbook(filled()) is True


def test_does_not_recognise_an_unrelated_workbook() -> None:
    assert is_template_workbook(workbook({"A1": "hi"}, sheets=("Sheet1",))) is False
    assert is_template_workbook(b"nope") is False


def test_refuses_an_unrelated_workbook() -> None:
    with pytest.raises(NoticeError) as caught:
        xlsx_to_state(workbook({"A1": "hi"}, sheets=("Sheet1",)))
    assert caught.value.notice["key"] == "api.notACharacterTemplate"


def test_refuses_a_file_that_is_not_a_workbook() -> None:
    with pytest.raises(NoticeError) as caught:
        xlsx_to_state(b"nope")
    assert caught.value.notice["key"] == "api.notACharacterTemplate"


# --- priorities and the build method ------------------------------------


def test_priorities_come_from_their_cells() -> None:
    state, warnings = xlsx_to_state(filled())
    assert state["build_method"] == "Priority"
    assert state["priorities"] == {
        "Heritage": "A",
        "Attributes": "B",
        "Talent": "E",
        "Skills": "C",
        "Resources": "D",
    }
    assert warnings == []


def test_the_karma_level_is_a_karma_build() -> None:
    """800 カルマ割り振り is a different build method, and the priority letters
    left on the sheet mean nothing under it."""
    state, _ = xlsx_to_state(filled(W1="800カルマ割り振り"))
    assert state["build_method"] == "Karma"
    assert state["priorities"] == {}


def test_another_play_level_warns() -> None:
    state, warnings = xlsx_to_state(filled(W1="ストリートレベル"))
    assert state["build_method"] == "Priority"
    assert has(warnings, "engine.import.xlsxPlayLevel", level="ストリートレベル")


def test_a_missing_priority_falls_back_to_c() -> None:
    state, _ = xlsx_to_state(filled(C12=""))
    assert state["priorities"]["Skills"] == "C"


# --- metatype and talent -------------------------------------------------


@pytest.mark.parametrize(
    ("japanese", "english"),
    [("ヒューマン", "Human"), ("エルフ", "Elf"), ("ドワーフ", "Dwarf"), ("オーク", "Ork"), ("トロール", "Troll")],
)
def test_metatypes(japanese: str, english: str) -> None:
    state, warnings = xlsx_to_state(filled(C16=japanese))
    assert state["metatype"] == english
    assert warnings == []


def test_a_custom_metatype_warns_and_falls_back() -> None:
    """カスタム is the sheet's escape hatch, and there is nothing to read in it."""
    state, warnings = xlsx_to_state(filled(C16="カスタム"))
    assert state["metatype"] == "Human"
    assert has(warnings, "engine.import.skippedUnknown", name="カスタム")


@pytest.mark.parametrize(
    ("japanese", "talent"),
    [
        ("－", "Mundane"),
        ("テクノマンサー", "Technomancer"),
        ("アデプト", "Adept"),
        ("魔法使い（メイジ）", "Magician"),
        ("魔法使い（シャーマン）", "Magician"),
        ("ミスティック・アデプト（メイジ）", "Mystic Adept"),
        ("偏位魔法使い（シャーマン、錬金術）", "Aspected Magician"),
    ],
)
def test_talents(japanese: str, talent: str) -> None:
    state, _ = xlsx_to_state(filled(C17=japanese))
    assert state["talent"] == talent


def test_a_magical_style_warns_because_it_is_lost() -> None:
    """メイジ／シャーマン is a tradition here, and the aspected field a quality —
    neither is on the sheet anywhere this can read."""
    _, warnings = xlsx_to_state(filled(C17="魔法使い（シャーマン）"))
    assert has(warnings, "engine.import.xlsxMagicStyle", name="魔法使い（シャーマン）")


def test_a_mundane_character_warns_about_nothing() -> None:
    _, warnings = xlsx_to_state(filled(C17="－"))
    assert warnings == []


def test_an_unknown_talent_falls_back_to_mundane() -> None:
    state, warnings = xlsx_to_state(filled(C17="超能力者"))
    assert state["talent"] == "Mundane"
    assert has(warnings, "engine.import.skippedUnknown", name="超能力者")


# --- attributes ----------------------------------------------------------


def test_attributes_are_the_starting_value_plus_the_points() -> None:
    state, _ = xlsx_to_state(filled(J19="2.0", J20="5.0", J27="3.0"))
    assert state["attributes"]["BOD"] == 3
    assert state["attributes"]["AGI"] == 6
    assert state["attributes"]["EDG"] == 5
    assert state["attributes"]["LOG"] == 1


def test_karma_bought_attributes_are_kept_apart() -> None:
    """L is what karma raised the attribute by, and this app spends that karma
    itself — folding it into the rating would charge for it twice."""
    state, _ = xlsx_to_state(filled(J19="2.0", L19="1.0"))
    assert state["attributes"]["BOD"] == 3
    assert state["attribute_karma"] == {"BOD": 1}


def test_the_finished_column_is_not_read() -> None:
    """P holds the sheet's own total, bonuses from qualities and ware included.
    This app derives those, so a P that disagrees changes nothing."""
    state, _ = xlsx_to_state(filled(J19="2.0", P19="99"))
    assert state["attributes"]["BOD"] == 3


def test_a_mundane_character_has_no_magic_attribute() -> None:
    state, _ = xlsx_to_state(filled())
    assert "MAG" not in state["attributes"]
    assert "RES" not in state["attributes"]


def test_an_awakened_character_keeps_its_magic() -> None:
    state, _ = xlsx_to_state(filled(C17="アデプト", H28="1.0", J28="3.0"))
    assert state["attributes"]["MAG"] == 4


def test_no_attribute_karma_key_when_nothing_was_bought() -> None:
    state, _ = xlsx_to_state(filled())
    assert "attribute_karma" not in state


# --- qualities -----------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "name", "pick", "note"),
    [
        ("両手利き", "両手利き", "", ""),
        ("規制品(アレス・サンダートラック)", "規制品", "アレス・サンダートラック", ""),
        ("規制品（超甲状腺）", "規制品", "超甲状腺", ""),
        ("依存症／中度／クラム", "依存症 (中度)", "クラム", ""),
        ("依存症／中度", "依存症 (中度)", "", ""),
        ("アレルギー／軽度／花粉／ブタクサ", "アレルギー (軽度)", "花粉／ブタクサ", ""),
        ("  両手利き  ", "両手利き", "", ""),
        # a note trailing after the pick, which is neither name nor pick
        ("導師精霊（竜殺しの英雄）\u3000交渉に+2修正", "導師精霊", "竜殺しの英雄", "交渉に+2修正"),
        ("軽度の依存症（カフェイン）", "軽度の依存症", "カフェイン", ""),
        # a space where another sheet would use parentheses
        ("導師精霊\u3000鮫", "導師精霊", "鮫", ""),
        ("アレルギー\u3000銀\u3000軽", "アレルギー", "銀 軽", ""),
        ("規制品 超甲状腺", "規制品", "超甲状腺", ""),
        # a slash still wins over a space
        ("依存症／中度／クラム\u3000メモ", "依存症 (中度)", "クラム\u3000メモ", ""),
    ],
)
def test_split_name(raw: str, name: str, pick: str, note: str) -> None:
    assert split_name(raw) == (name, pick, note)


def test_candidates_tries_the_pick_as_part_of_the_name_first() -> None:
    """SIN持ち（国家SIN） may be one name — the catalog spells it SIN持ち：国家SIN —
    so the joined spellings come before treating the pick as a target."""
    assert candidates("SIN持ち", "国家SIN")[:2] == ["SIN持ち", "SIN持ち：国家SIN"]


def test_candidates_reorders_a_leading_degree() -> None:
    assert "依存症 (軽度)" in candidates("軽度の依存症", "カフェイン")


def test_candidates_of_a_plain_name_is_just_the_name() -> None:
    assert candidates("両手利き", "") == ["両手利き"]


def test_a_pick_that_is_part_of_the_name_leaves_no_extra() -> None:
    """SIN持ち：国家SIN is the whole quality, so 国家SIN is not a target."""
    index = {"SIN持ち：国家SIN": "sinner-national"}
    assert resolve("SIN持ち（国家SIN）", index) == ("sinner-national", "")


def test_a_leading_degree_keeps_its_pick() -> None:
    index = {"依存症 (軽度)": "addiction-mild"}
    assert resolve("軽度の依存症（カフェイン）", index) == ("addiction-mild", "カフェイン")


def test_resolve_returns_none_for_an_unknown_name() -> None:
    assert resolve("そんな資質はない", {}) is None


def test_a_plain_quality_comes_through() -> None:
    state, warnings = xlsx_to_state(filled(A50="有利", C50="両手利き"))
    assert state["quality_ids"] == [_quality_id("Ambidextrous")]
    assert warnings == []


def test_a_quality_with_a_degree_and_a_pick() -> None:
    """依存症／中度／クラム is 依存症 (中度) with クラム in its extra."""
    state, warnings = xlsx_to_state(filled(A50="不利", C50="依存症／中度／クラム"))
    addiction = _quality_id("Addiction (Moderate)")
    assert state["quality_ids"] == [addiction]
    assert state["quality_extras"] == {addiction: "クラム"}
    assert warnings == []


def test_a_quality_the_template_names_differently() -> None:
    """The Japanese data has no name for Restricted Gear yet, so 規制品 is
    matched through the alias table."""
    state, _ = xlsx_to_state(filled(A50="有利", C50="規制品(アレス・サンダートラック)"))
    assert state["quality_ids"] == [_quality_id("Restricted Gear")]


def test_a_note_on_a_quality_that_takes_no_target_warns() -> None:
    """Restricted Gear has nothing to hold what it was spent on, so the sheet's
    parenthesis is reported rather than dropped in silence."""
    _, warnings = xlsx_to_state(filled(A50="有利", C50="規制品(アレス・サンダートラック)"))
    assert has(warnings, "engine.import.xlsxQualityNote", note="アレス・サンダートラック")


def test_a_quality_whose_name_holds_the_parenthesis() -> None:
    """v2.0.11 writes SIN持ち（国家SIN）, and the parenthesis is part of the
    catalog's own name rather than a target."""
    state, warnings = xlsx_to_state(filled(A50="不利", C50="SIN持ち（国家SIN）"))
    assert state["quality_ids"] == [_quality_id("SINner (National)")]
    assert "quality_extras" not in state
    assert warnings == []


def test_a_pick_set_off_by_a_space() -> None:
    """ララ writes 導師精霊　鮫 — no parentheses, just a space."""
    state, warnings = xlsx_to_state(filled(A50="有利", C50="導師精霊\u3000鮫"))
    assert state["quality_ids"] == [_quality_id("Mentor Spirit")]
    assert state["mentor_id"] == _mentor_id("Shark")
    assert warnings == []


def test_a_loanword_written_without_its_interpunct() -> None:
    """The catalog spells it アストラル・ビーコン; the sheets are written both ways."""
    state, warnings = xlsx_to_state(filled(A50="不利", C50="アストラルビーコン"))
    assert state["quality_ids"] == [_quality_id("Astral Beacon")]
    assert warnings == []


def test_a_sin_named_by_the_sin_alone() -> None:
    """日本鬼 writes 国家SIN（日本帝国）, leaving off the SIN持ち： the catalog files
    it under; the parenthesis here really is the SIN's free text."""
    state, warnings = xlsx_to_state(filled(A50="不利", C50="国家SIN（日本帝国）"))
    national = _quality_id("SINner (National)")
    assert state["quality_ids"] == [national]
    assert state["quality_extras"] == {national: "日本帝国"}
    assert warnings == []


def test_a_degree_written_in_front_of_the_quality() -> None:
    """軽度の依存症（…） is the catalog's 依存症 (軽度) with the degree moved."""
    state, _ = xlsx_to_state(filled(A50="不利", C50="軽度の依存症（エナジードリンク / カフェイン）"))
    mild = _quality_id("Addiction (Mild)")
    assert state["quality_ids"] == [mild]
    assert state["quality_extras"] == {mild: "エナジードリンク / カフェイン"}


def test_a_note_after_the_pick_is_not_part_of_the_name() -> None:
    """導師精霊（竜殺しの英雄）　交渉に+2修正 — the player's own note trails the
    pick, and the pick itself is the mentor."""
    state, warnings = xlsx_to_state(filled(A50="有利", C50="導師精霊（竜殺しの英雄）\u3000交渉に+2修正"))
    assert state["quality_ids"] == [_quality_id("Mentor Spirit")]
    assert state["mentor_id"] == _mentor_id("Dragonslayer")
    assert warnings == []


def test_the_same_quality_taken_twice_is_two_entries() -> None:
    state, _ = xlsx_to_state(filled(A50="有利", C50="両手利き", A51="有利", C51="両手利き"))
    ambidextrous = _quality_id("Ambidextrous")
    assert state["quality_ids"] == [ambidextrous, ambidextrous]


def test_a_second_pick_for_the_same_quality_warns() -> None:
    """`quality_extras` is keyed by quality, so the second take's own pick has
    nowhere to go."""
    state, warnings = xlsx_to_state(
        filled(A50="不利", C50="依存症／中度／クラム", A51="不利", C51="依存症／中度／ノヴァコーク")
    )
    addiction = _quality_id("Addiction (Moderate)")
    assert state["quality_extras"] == {addiction: "クラム"}
    assert has(warnings, "engine.import.xlsxQualityNote", note="ノヴァコーク")


def test_an_unknown_quality_warns() -> None:
    state, warnings = xlsx_to_state(filled(A50="有利", C50="そんな資質はない"))
    assert "quality_ids" not in state
    assert has(warnings, "engine.import.skippedUnknown", name="そんな資質はない")


def test_every_quality_row_is_read() -> None:
    rows = {f"C{row}": "両手利き" for row in range(50, 60)}
    state, _ = xlsx_to_state(filled(**rows))
    assert len(state["quality_ids"]) == 10


def test_a_row_past_the_block_is_not_read() -> None:
    state, _ = xlsx_to_state(filled(C60="両手利き"))
    assert "quality_ids" not in state


def test_no_quality_keys_when_the_block_is_empty() -> None:
    state, _ = xlsx_to_state(filled())
    assert "quality_ids" not in state
    assert "quality_extras" not in state


# --- active skills and skill groups --------------------------------------


def test_a_skill_rating_is_points_plus_karma() -> None:
    """`skills` holds what the skill ends up at and `skill_karma` how much of
    that karma paid for — the same split a .chum5 read writes."""
    state, warnings = xlsx_to_state(filled(skills={"自動火器": {"I": "2.0", "J": "1.0"}}))
    assert state["skills"] == {"Automatics": 3}
    assert state["skill_karma"] == {"Automatics": 1}
    assert warnings == []


def test_a_skill_bought_with_points_alone_has_no_karma_entry() -> None:
    state, _ = xlsx_to_state(filled(skills={"知覚": {"I": "5.0"}}))
    assert state["skills"] == {"Perception": 5}
    assert "skill_karma" not in state


def test_an_untouched_skill_row_is_not_read() -> None:
    """Every skill in the book has a row, and almost all of them are left at 0."""
    state, _ = xlsx_to_state(filled(skills={"知覚": {"I": "5.0"}, "弓術": {}, "棍棒": {"L": "0"}}))
    assert state["skills"] == {"Perception": 5}


def test_a_nameless_row_is_the_same_skill_under_another_attribute() -> None:
    """コンピュータ has rows under 直観力 and 共振力 with no name of their own."""
    cells = skill_sheet(skills={"コンピュータ": {"I": "3.0"}})
    cells["C22"] = "直観力"  # the extra row, name column empty
    cells["I22"] = "9.0"
    state, warnings = xlsx_to_state(workbook(BASELINE, by_sheet={"能動技能／技能グループ": cells}))
    assert state["skills"] == {"Computer": 3}
    assert warnings == []


def test_skill_groups_come_through() -> None:
    state, warnings = xlsx_to_state(filled(groups={"隠密": {"I": "5.0"}}))
    assert state["skill_groups"] == {"Stealth": 5}
    assert warnings == []


def test_a_skill_group_bought_with_karma() -> None:
    state, _ = xlsx_to_state(filled(groups={"隠密": {"I": "3.0", "J": "2.0"}}))
    assert state["skill_groups"] == {"Stealth": 5}
    assert state["skill_group_karma"] == {"Stealth": 2}


@pytest.mark.parametrize(
    ("japanese", "english"),
    [
        # the seven groups whose name the template spells its own way
        ("小火器", "Firearms"),
        ("野外活動", "Outdoors"),
        ("対人", "Influence"),
        ("呪付", "Enchanting"),
        ("召霊術", "Conjuring"),
        ("機器整備", "Engineering"),
        ("電子工学", "Electronics"),
        # and one the catalog writes with both readings, 隠密/ステルス
        ("隠密", "Stealth"),
    ],
)
def test_group_names_the_template_spells_differently(japanese: str, english: str) -> None:
    state, warnings = xlsx_to_state(filled(groups={japanese: {"I": "2.0"}}))
    assert state["skill_groups"] == {english: 2}
    assert warnings == []


@pytest.mark.parametrize(
    ("japanese", "english"),
    [
        ("工業機械設備", "Industrial Mechanic"),
        ("応急措置", "First Aid"),
        ("医術", "Medicine"),
        ("化学実務", "Chemistry"),
        ("サイバー技術", "Cybertechnology"),
    ],
)
def test_skill_names_the_template_spells_differently(japanese: str, english: str) -> None:
    state, warnings = xlsx_to_state(filled(skills={japanese: {"I": "1.0"}}))
    assert state["skills"] == {english: 1}
    assert warnings == []


def test_every_active_skill_on_the_sheet_is_known() -> None:
    """The sheet lists the book's skills itself, so nothing on it should be a
    stranger to the catalog. This is the check that a data update has not moved
    a name out from under the aliases."""
    cat = catalog()
    index = japanese_index(cat, [str(row["name"]) for row in cat["skills"]["skills"]], "skill")
    for japanese, canonical in SKILL_ALIASES.items():
        assert japanese not in index, f"{japanese} now matches on its own — drop the alias"
        assert canonical in index, f"{canonical} no longer in the catalog"


def test_every_group_alias_is_still_needed() -> None:
    cat = catalog()
    index = japanese_index(cat, [str(name) for name in cat["skills"]["group_names"]], "skill")
    for japanese, english in GROUP_ALIASES.items():
        assert japanese not in index, f"{japanese} now matches on its own — drop the alias"
        assert english in index, f"{english} no longer in the catalog"


def test_an_unknown_skill_warns() -> None:
    state, warnings = xlsx_to_state(filled(skills={"そんな技能はない": {"I": "1.0"}}))
    assert "skills" not in state
    assert has(warnings, "engine.import.skippedUnknown", name="そんな技能はない")


def test_sections_are_found_by_their_headings() -> None:
    """A revision that inserts a row would shift every skill by one, so the
    sections are cut at the headings rather than at fixed row numbers."""
    cells = skill_sheet(groups={"隠密": {"I": "5.0"}}, skills={"知覚": {"I": "4.0"}})
    # push everything down three rows, headings included
    shifted = {}
    for ref, value in cells.items():
        column, row = ref[0], int(ref[1:])
        shifted[f"{column}{row + 3}"] = value
    state, _ = xlsx_to_state(workbook(BASELINE, by_sheet={"能動技能／技能グループ": shifted}))
    assert state["skill_groups"] == {"Stealth": 5}
    assert state["skills"] == {"Perception": 4}


def test_a_sheet_without_headings_reads_no_skills() -> None:
    state, warnings = xlsx_to_state(
        workbook(BASELINE, by_sheet={"能動技能／技能グループ": {"A4": "隠密", "I4": "5.0"}})
    )
    assert "skill_groups" not in state
    assert "skills" not in state
    assert warnings == []


# --- specializations -----------------------------------------------------


def test_a_specialization_bought_with_points() -> None:
    state, _ = xlsx_to_state(filled(skills={"自動火器": {"I": "2.0", "E": "アサルトライフル"}}))
    assert state["skill_specializations"] == {"Automatics": "Assault Rifles"}
    assert "skill_specs_karma" not in state


def test_a_specialization_bought_with_karma() -> None:
    """The sheet has a column for each way of paying, and which one was used is
    what `skill_specs_karma` records."""
    state, _ = xlsx_to_state(filled(skills={"自動火器": {"I": "2.0", "F": "アサルトライフル"}}))
    assert state["skill_specializations"] == {"Automatics": "Assault Rifles"}
    assert state["skill_specs_karma"] == ["Automatics"]


def test_a_specialization_the_book_does_not_list_is_kept_as_typed() -> None:
    """ライトピストル is not one of Pistols' four, and both sheets seen so far
    write it — a made-up specialization is the player's to keep."""
    state, warnings = xlsx_to_state(filled(skills={"ピストル": {"I": "5.0", "E": "ライトピストル"}}))
    assert state["skill_specializations"] == {"Pistols": "ライトピストル"}
    assert warnings == []


def test_a_specialization_alone_still_brings_the_skill_row_in() -> None:
    state, _ = xlsx_to_state(filled(skills={"自動火器": {"E": "アサルトライフル"}}))
    assert state["skill_specializations"] == {"Automatics": "Assault Rifles"}


# --- knowledge and language skills ---------------------------------------


def test_knowledge_skills_keep_the_name_as_typed() -> None:
    """Nothing to match: a knowledge skill is whatever the player invented."""
    state, warnings = xlsx_to_state(filled(knowledge=[{"A": "学術知識技能", "B": "バイオ技術", "H": "2.0"}]))
    assert state["knowledge_skills"] == {"バイオ技術": 2}
    assert state["knowledge_categories"] == {"バイオ技術": "Academic"}
    assert warnings == []


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("ストリート知識技能", "Street"),
        ("学術知識技能", "Academic"),
        ("職業知識技能", "Professional"),
        ("趣味知識技能", "Interest"),
        ("言語知識技能", "Language"),
        ("その他（直観力）", "Interest"),
        ("その他（論理力）", "Academic"),
    ],
)
def test_knowledge_categories(category: str, expected: str) -> None:
    state, _ = xlsx_to_state(filled(knowledge=[{"A": category, "B": "なにか", "H": "1.0"}]))
    assert state["knowledge_categories"] == {"なにか": expected}


def test_an_unknown_category_falls_back_to_academic() -> None:
    state, _ = xlsx_to_state(filled(knowledge=[{"A": "", "B": "なにか", "H": "1.0"}]))
    assert state["knowledge_categories"] == {"なにか": "Academic"}


def test_a_native_language_carries_no_rating() -> None:
    state, _ = xlsx_to_state(
        filled(
            knowledge=[{"A": "言語知識技能（Native）", "B": "日本語"}, {"A": "言語知識技能", "B": "英語", "H": "3.0"}]
        )
    )
    assert state["native_languages"] == ["日本語"]
    assert state["knowledge_skills"] == {"英語": 3}


def test_knowledge_karma_is_kept_apart() -> None:
    state, _ = xlsx_to_state(filled(knowledge=[{"A": "学術知識技能", "B": "魔法理論", "H": "2.0", "I": "2.0"}]))
    assert state["knowledge_skills"] == {"魔法理論": 4}
    assert state["knowledge_karma"] == {"魔法理論": 2}


def test_a_knowledge_specialization_joins_the_active_ones() -> None:
    """`skill_specializations` is one map for both kinds, so the knowledge pass
    must add to it rather than replace what the active pass put there."""
    state, _ = xlsx_to_state(
        filled(
            skills={"自動火器": {"I": "2.0", "E": "アサルトライフル"}},
            knowledge=[{"A": "ストリート知識技能", "B": "ストリートの噂", "H": "4.0", "E": "繁華街"}],
        )
    )
    assert state["skill_specializations"] == {"Automatics": "Assault Rifles", "ストリートの噂": "繁華街"}


def test_an_empty_knowledge_row_is_skipped() -> None:
    state, _ = xlsx_to_state(filled(knowledge=[{"A": "学術知識技能"}, {"B": "音楽", "H": "1.0"}]))
    assert state["knowledge_skills"] == {"音楽": 1}


def test_a_missing_knowledge_sheet_does_not_fail_the_import() -> None:
    """The sheet is not in REQUIRED_SHEETS: a revision that renamed it should
    still bring the rest of the character over."""
    state, _ = xlsx_to_state(workbook(BASELINE, sheets=(SHEET_BASICS, "能動技能／技能グループ", "編集不可")))
    assert "knowledge_skills" not in state
    assert state["metatype"] == "Human"


def test_no_skill_keys_when_the_sheets_are_empty() -> None:
    state, _ = xlsx_to_state(filled())
    for key in ("skills", "skill_karma", "skill_groups", "knowledge_skills", "native_languages"):
        assert key not in state


# --- skills reaching the engine ------------------------------------------


def test_the_skills_reach_the_engine() -> None:
    state, _ = xlsx_to_state(
        filled(
            J20="5.0",  # AGI 6
            skills={"ピストル": {"I": "5.0"}},
            knowledge=[{"A": "学術知識技能", "B": "バイオ技術", "H": "2.0"}],
        )
    )
    char = import_character(state)
    assert char.skills["Pistols"] == 5
    assert char.derived["points"]["skills"]["used"] == 5
    assert any(row["name"] == "バイオ技術" for row in char.derived["knowledge_skills"])


def test_a_group_and_a_skill_are_counted_against_their_own_budgets() -> None:
    state, _ = xlsx_to_state(filled(groups={"隠密": {"I": "5.0"}}, skills={"知覚": {"I": "4.0"}}))
    points = import_character(state).derived["points"]
    assert points["skill_groups"]["used"] == 5
    assert points["skills"]["used"] == 4


# --- the whole thing -----------------------------------------------------


def test_warnings_are_not_repeated() -> None:
    state, warnings = xlsx_to_state(filled(A50="有利", C50="規制品(超甲状腺)", A51="有利", C51="規制品(超甲状腺)"))
    assert len(state["quality_ids"]) == 2
    assert len([w for w in warnings if w["key"] == "engine.import.xlsxQualityNote"]) == 1


def test_the_state_computes_as_a_character() -> None:
    """The point of the import: what comes out is a character this app can open."""
    state, _ = xlsx_to_state(filled(J19="2.0", J20="5.0", A50="有利", C50="両手利き"))
    char = import_character(state)
    assert char.metatype == "Human"
    assert char.attributes["AGI"] == 6
    # the quality reached the engine, not just the state
    assert char.derived["ambidextrous"] is True


def test_the_baseline_fixture_matches_the_template() -> None:
    """The fixture is the template as it ships: every priority at its cell, a
    mundane human, every attribute at its starting value."""
    assert set(BASELINE) >= {"W1", "C3", "C7", "C8", "C12", "C13", "C16", "C17"}


# --- the route -----------------------------------------------------------


def test_the_route_imports_a_template() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/characters/import-xlsx",
        content=filled(J19="2.0", A50="有利", C50="両手利き"),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["character"]["metatype"] == "Human"
    assert body["character"]["attributes"]["BOD"] == 3
    assert body["warnings"] == []


def test_the_route_refuses_something_else() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/characters/import-xlsx",
        content=b"not a workbook",
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["key"] == "api.notACharacterTemplate"


def test_the_route_reports_what_it_could_not_map() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/characters/import-xlsx",
        content=filled(C17="魔法使い（メイジ）", H28="1.0", J28="3.0"),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 200
    assert has(response.json()["warnings"], "engine.import.xlsxMagicStyle", name="魔法使い（メイジ）")


# --- 呪文／複合体／アデプト・パワー ---------------------------------------


def test_spells_come_over_by_their_japanese_names() -> None:
    """The occult sample's seven, which the template has the player type and the
    catalog's translations answer exactly."""
    names = ["真偽分析", "精神探査", "広域魔力探知", "感化", "完全透明化", "物理障壁", "スタンボルト"]
    state, warnings = xlsx_to_state(filled(spells=names))
    assert [row["spell_id"] for row in state["spells"]] == [
        _catalog_id("spells", english)
        for english in (
            "Analyze Truth",
            "Mind Probe",
            "Detect Magic, Extended",
            "Influence",
            "Improved Invisibility",
            "Physical Barrier",
            "Stunbolt",
        )
    ]
    assert warnings == []


def test_a_spell_named_by_its_other_reading() -> None:
    """真偽分析/アナライズ・トゥルース — the catalog carries both readings joined,
    and the sheet is written with whichever the player knows."""
    state, _ = xlsx_to_state(filled(spells=["アナライズ・トゥルース"]))
    assert [row["spell_id"] for row in state["spells"]] == [_catalog_id("spells", "Analyze Truth")]


def test_a_ritual_is_in_the_same_column_as_the_spells() -> None:
    """The sheet's heading is 呪文／錬金術調整物／儀式: one column, three kinds,
    and the catalog holds all three together."""
    ritual = next(row for row in catalog()["spells"] if row.get("kind") == "ritual")
    japanese = (catalog().get("translations") or {}).get(str(ritual["name"]), str(ritual["name"]))
    state, warnings = xlsx_to_state(filled(spells=[japanese.split("/")[0]]))
    assert [row["spell_id"] for row in state["spells"]] == [str(ritual["id"])]
    assert warnings == []


def test_a_spell_is_never_alchemical() -> None:
    """The sheet has no column for it, so a preparation arrives as a plain spell."""
    state, _ = xlsx_to_state(filled(spells=["スタンボルト"]))
    assert state["spells"][0]["alchemical"] is False


def test_an_unknown_spell_warns() -> None:
    _, warnings = xlsx_to_state(filled(spells=["そんな呪文はない"]))
    assert has(warnings, "engine.import.skippedUnknown", name="そんな呪文はない")


def test_a_complex_form_comes_over_from_its_own_column() -> None:
    state, warnings = xlsx_to_state(filled(forms=["パペッティア", "レゾナンス・スパイク"]))
    assert [row["form_id"] for row in state["complex_forms"]] == [
        _catalog_id("complex_forms", "Puppeteer"),
        _catalog_id("complex_forms", "Resonance Spike"),
    ]
    assert warnings == []


def test_spells_and_complex_forms_do_not_bleed_into_each_other() -> None:
    """They share rows 3–22, one in column C and one in column V."""
    state, _ = xlsx_to_state(filled(spells=["スタンボルト"], forms=["パペッティア"]))
    assert len(state["spells"]) == 1
    assert len(state["complex_forms"]) == 1


def test_adept_powers_come_over_with_their_levels() -> None:
    """ララ's seven. 反射強化 is at 3; the ones without levels stay at 1 whatever
    the sheet's level column says."""
    powers = [("反射強化", "3.0"), ("強打", ""), ("戦闘感覚", "1.0"), ("軽身", "1.0"), ("矢薙ぎ", "1.0")]
    state, warnings = xlsx_to_state(filled(powers=powers))
    assert [(row["power_id"], row["rating"]) for row in state["adept_powers"]] == [
        (_catalog_id("powers", "Improved Reflexes"), 3),
        (_catalog_id("powers", "Critical Strike"), 1),
        (_catalog_id("powers", "Combat Sense"), 1),
        (_catalog_id("powers", "Light Body"), 1),
        (_catalog_id("powers", "Missile Parry"), 1),
    ]
    assert warnings == []


def test_a_power_marked_by_the_player_keeps_its_name() -> None:
    """※殺戮の手 — the mark says something else pays for the power."""
    state, warnings = xlsx_to_state(filled(powers=[("※殺戮の手", "")]))
    assert [row["power_id"] for row in state["adept_powers"]] == [_catalog_id("powers", "Killing Hands")]
    assert warnings == []


def test_a_power_whose_target_is_part_of_its_name() -> None:
    """潜在力強化　身体 is the catalog's 潜在力強化：(身体), not a power plus a
    target, so nothing is left over to put in `extra`."""
    state, _ = xlsx_to_state(filled(powers=[("潜在力強化\u3000身体", "")]))
    assert state["adept_powers"] == [
        {
            "id": state["adept_powers"][0]["id"],
            "power_id": _catalog_id("powers", "Improved Potential (Physical)"),
            "rating": 1,
            "extra": None,
        }
    ]


def test_a_power_that_takes_a_target_keeps_it() -> None:
    state, _ = xlsx_to_state(filled(powers=[("能力値ブースト（敏捷力）", "2.0")]))
    assert state["adept_powers"][0]["power_id"] == _catalog_id("powers", "Attribute Boost")
    assert state["adept_powers"][0]["extra"] == "敏捷力"
    assert state["adept_powers"][0]["rating"] == 2


def test_a_level_on_a_power_that_has_none_is_reported() -> None:
    """ララ's sheet buys 潜在力強化 at level 2 and charges 1.0 power points for
    it, but the power is a flat 0.5 one-off — the sheet is over-charging."""
    state, warnings = xlsx_to_state(filled(powers=[("潜在力強化\u3000身体", "2.0")]))
    assert state["adept_powers"][0]["rating"] == 1
    assert has(warnings, "engine.import.xlsxPowerLevel", level=2)


def test_a_target_a_power_cannot_hold_is_reported() -> None:
    _, warnings = xlsx_to_state(filled(powers=[("強打（拳）", "")]))
    assert has(warnings, "engine.import.xlsxPowerNote", note="拳")


def test_an_unknown_power_warns() -> None:
    _, warnings = xlsx_to_state(filled(powers=[("そんなパワーはない", "")]))
    assert has(warnings, "engine.import.skippedUnknown", name="そんなパワーはない")


def test_the_power_block_is_found_by_its_heading() -> None:
    """Every version puts the heading at row 24, but a row inserted above it
    would move the whole block."""
    cells = magic_sheet(spells=["スタンボルト"], powers=[("強打", "")])
    shifted = {f"{ref[0]}{int(ref[1:]) + 2}" if ref[0] in "ACFV" else ref: value for ref, value in cells.items()}
    state, warnings = xlsx_to_state(filled(spells=[], powers=[]))
    assert "adept_powers" not in state
    state, warnings = xlsx_to_state(workbook(dict(BASELINE), by_sheet={SHEET_MAGIC: shifted}))
    assert [row["power_id"] for row in state["adept_powers"]] == [_catalog_id("powers", "Critical Strike")]
    assert [row["spell_id"] for row in state["spells"]] == [_catalog_id("spells", "Stunbolt")]
    assert warnings == []


def test_a_missing_magic_sheet_is_tolerated() -> None:
    """The sheet is not in REQUIRED_SHEETS, so a renamed one loses the magic
    rather than the character."""
    state, _ = xlsx_to_state(workbook(dict(BASELINE), sheets=(SHEET_BASICS, SHEET_SKILLS, "編集不可")))
    assert "spells" not in state
    assert "adept_powers" not in state


def test_no_magic_keys_when_the_sheet_is_empty() -> None:
    state, warnings = xlsx_to_state(filled())
    assert not {"spells", "complex_forms", "adept_powers"} & set(state)
    assert warnings == []


# --- the mentor named on the quality sheet --------------------------------


def test_a_mentor_named_with_the_other_kanji() -> None:
    """The catalog prints 龍殺しの英雄 (ドラゴンスレイヤー) and the template
    竜殺しの英雄 — the same character, and the reading left off."""
    assert resolve_mentor("竜殺しの英雄", catalog()) == _mentor_id("Dragonslayer")
    assert resolve_mentor("龍殺しの英雄", catalog()) == _mentor_id("Dragonslayer")
    assert mentor_index(catalog())["龍殺しの英雄 (ドラゴンスレイヤー)"] == _mentor_id("Dragonslayer")


def test_the_mentor_aliases_are_still_needed() -> None:
    """A guard against catalog drift: once the Japanese data spells it the way
    the template does, the alias can go."""
    index = mentor_index(catalog())
    assert set(MENTOR_ALIASES) - set(index) == set(MENTOR_ALIASES)


def test_an_unknown_mentor_falls_back_to_a_note() -> None:
    _, warnings = xlsx_to_state(filled(A50="有利", C50="導師精霊（そんな導師はいない）"))
    assert has(warnings, "engine.import.xlsxQualityNote", note="そんな導師はいない")


def test_a_mentor_spirit_with_no_pick_is_still_the_quality() -> None:
    state, warnings = xlsx_to_state(filled(A50="有利", C50="導師精霊"))
    assert state["quality_ids"] == [_quality_id("Mentor Spirit")]
    assert "mentor_id" not in state
    assert warnings == []


# --- 身体強化／電子機器 ------------------------------------------------------


def _ware_id(name: str) -> str:
    rows = catalog()["cyberware"]["items"] + catalog()["bioware"]["items"]
    return next(str(row["id"]) for row in rows if row["name"] == name)


@pytest.mark.parametrize(
    ("raw", "name", "nested", "side", "rating"),
    [
        ("オルソスキン", "オルソスキン", False, "", 0),
        # the availability the sheet works out anyway, copied into the name
        ("サイバーアイ[9]", "サイバーアイ", False, "", 0),
        # the rating written into the name as well as its own column
        ("└視覚強化R3[3]", "視覚強化", True, "", 3),
        ("└スマートリンク[3]", "スマートリンク", True, "", 0),
        # 日本鬼 nests with parentheses instead of a box-drawing character
        ("（大光量補正）", "大光量補正", True, "", 0),
        ("(スマートリンク)", "スマートリンク", True, "", 0),
        # a side run into the name
        ("非偽装型サイバーリム右腕全体", "非偽装型サイバーリム腕全体", False, "Right", 0),
        ("　└　低光量補正", "低光量補正", True, "", 0),
        # a name whose own parenthesis is not a nesting mark
        ("骨格補綴 (チタニウム)", "骨格補綴 (チタニウム)", False, "", 0),
    ],
)
def test_clean_name(raw: str, name: str, nested: bool, side: str, rating: int) -> None:
    assert clean_name(raw) == (name, nested, side, rating)


def test_implants_split_between_cyberware_and_bioware() -> None:
    """One table on the sheet, two lists here: the player picks the grade, not
    the book the implant came from."""
    implants = [
        {"A": "声紋変調器", "N": "アルファウェア", "P": "4.0"},
        {"A": "オルソスキン", "N": "スタンダード", "P": "3.0"},
    ]
    state, warnings = xlsx_to_state(filled(implants=implants))
    assert [row["ware_id"] for row in state["cyberware"]] == [_ware_id("Voice Modulator")]
    assert [row["ware_id"] for row in state["bioware"]] == [_ware_id("Orthoskin")]
    assert warnings == []


def test_an_implant_keeps_its_grade_and_rating() -> None:
    state, _ = xlsx_to_state(filled(implants=[{"A": "声紋変調器", "N": "アルファウェア", "P": "4.0"}]))
    assert state["cyberware"][0]["grade"] == "Alphaware"
    assert state["cyberware"][0]["rating"] == 4


@pytest.mark.parametrize("japanese", ["スタンダード", "アルファウェア", "ベータウェア", "デルタウェア", "中古"])
def test_every_grade_the_dropdown_offers(japanese: str) -> None:
    """The grade is the one thing on this sheet that is a dropdown, so all five
    of its entries have to land on a grade this app knows."""
    state, warnings = xlsx_to_state(filled(implants=[{"A": "オルソスキン", "N": japanese, "P": "1.0"}]))
    grades = {str(row["name"]) for row in catalog()["bioware"]["grades"]}
    assert state["bioware"][0]["grade"] in grades
    assert warnings == []


def test_an_unreadable_grade_falls_back_to_standard() -> None:
    state, warnings = xlsx_to_state(filled(implants=[{"A": "オルソスキン", "N": "そんな等級はない", "P": "1.0"}]))
    assert state["bioware"][0]["grade"] == "Standard"
    assert has(warnings, "engine.import.xlsxWareGrade", grade="そんな等級はない")


def test_a_rating_of_zero_becomes_one() -> None:
    """The sheet leaves the column empty, or writes 0, on an implant that has no
    rating."""
    state, _ = xlsx_to_state(filled(implants=[{"A": "血小板工場", "N": "スタンダード", "P": "0.0"}]))
    assert state["bioware"][0]["rating"] == 1


def test_a_rating_column_that_is_not_a_number_is_part_of_the_name() -> None:
    """骨格補綴 with チタニウム in the rating column is the catalog's
    骨格補綴 (チタニウム) — the material is part of the name there."""
    state, warnings = xlsx_to_state(filled(implants=[{"A": "骨格補綴", "N": "中古", "P": "チタニウム"}]))
    assert state["cyberware"][0]["ware_id"] == _ware_id("Bone Lacing (Titanium)")
    assert state["cyberware"][0]["rating"] == 1
    assert warnings == []


def test_nested_implants_hang_off_the_row_above_them() -> None:
    """アッシュ's cybereyes, with three things installed in them."""
    implants = [
        {"A": "サイバーアイ[9]", "N": "スタンダード", "P": "3.0"},
        {"A": "└視覚強化R3[3]", "P": "3.0"},
        {"A": "└スマートリンク[3]"},
        {"A": "└大光量補正[1]"},
    ]
    state, warnings = xlsx_to_state(filled(implants=implants))
    eyes, *installed = state["cyberware"]
    assert eyes["ware_id"] == _ware_id("Cybereyes Basic System")
    assert eyes.get("parent_id") is None
    assert [row["parent_id"] for row in installed] == [eyes["id"]] * 3
    assert warnings == []


def test_nesting_written_with_parentheses() -> None:
    """日本鬼 writes （大光量補正） where アッシュ writes └大光量補正."""
    implants = [{"A": "サイバーアイ", "N": "スタンダード", "P": "2.0"}, {"A": "（大光量補正）", "N": "スタンダード"}]
    state, _ = xlsx_to_state(filled(implants=implants))
    eyes, flare = state["cyberware"]
    assert flare["parent_id"] == eyes["id"]


def test_an_implant_before_any_parent_is_not_nested() -> None:
    """A nesting mark on the first row has nothing to hang off."""
    state, _ = xlsx_to_state(filled(implants=[{"A": "（大光量補正）", "N": "スタンダード"}]))
    assert state["cyberware"][0].get("parent_id") is None


def test_a_limb_keeps_the_side_it_was_written_on() -> None:
    state, warnings = xlsx_to_state(filled(implants=[{"A": "非偽装型サイバーリム右腕全体", "N": "中古"}]))
    assert state["cyberware"][0]["ware_id"] == _ware_id("Obvious Full Arm")
    assert state["cyberware"][0]["side"] == "Right"
    assert warnings == []


def test_every_cyberlimb_is_reachable_the_way_the_template_writes_one() -> None:
    """非偽装型サイバーアーム(全体) is written 非偽装型サイバーリム腕全体, and the
    spellings are built from the catalog's own names rather than listed."""
    index, _ = ware_index(catalog())
    for japanese, english in [
        ("非偽装型サイバーリム腕全体", "Obvious Full Arm"),
        ("偽装型サイバーリム脚下腿部", "Synthetic Lower Leg"),
        ("非偽装型サイバーリム手手", "Obvious Hand"),
        ("非偽装型サイバースカル頭蓋", "Obvious Skull"),
    ]:
        assert index[japanese] == english


def test_the_implant_aliases_are_still_needed() -> None:
    """A guard against catalog drift: once the Japanese data spells it the way
    the template does, the alias can go."""
    index, _ = ware_index(catalog())
    assert set(WARE_ALIASES) - set(index) == set(WARE_ALIASES)


def test_an_unknown_implant_warns() -> None:
    """（特注モデル） is 日本鬼's own shorthand: the catalog has 特注:筋力向上 and
    特注:敏捷力向上 and nothing says which."""
    _, warnings = xlsx_to_state(filled(implants=[{"A": "（特注モデル）", "N": "中古"}]))
    assert has(warnings, "engine.import.skippedUnknown", name="（特注モデル）")


def test_a_commlink_comes_over_with_its_device_rating() -> None:
    """アッシュ writes トランシスアヴァロン; the catalog spells it with an
    interpunct."""
    devices = [{"A": "コムリンク", "D": "トランシスアヴァロン", "M": "6.0"}]
    state, warnings = xlsx_to_state(filled(devices=devices))
    assert state["commlinks"][0]["gear_id"] == _catalog_id("commlinks", "Transys Avalon")
    assert state["commlinks"][0]["rating"] == 6
    assert warnings == []


def test_a_cyberdeck_goes_in_its_own_list() -> None:
    state, warnings = xlsx_to_state(filled(devices=[{"A": "サイバーデッキ", "D": "エリカ MCD-1", "M": "1.0"}]))
    assert "commlinks" not in state
    assert state["cyberdecks"][0]["gear_id"] == _catalog_id("cyberdecks", "Erika MCD-1")
    assert warnings == []


def test_the_bio_persona_row_is_not_a_device() -> None:
    """生体ペルソナ／無し is the technomancer's own persona, not something bought."""
    state, warnings = xlsx_to_state(filled(devices=[{"A": "生体ペルソナ", "D": "無し"}]))
    assert "commlinks" not in state
    assert "cyberdecks" not in state
    assert warnings == []


def test_an_unknown_device_warns() -> None:
    _, warnings = xlsx_to_state(filled(devices=[{"A": "コムリンク", "D": "そんなコムリンクはない"}]))
    assert has(warnings, "engine.import.skippedUnknown", name="そんなコムリンクはない")


def test_the_device_block_is_found_by_its_heading() -> None:
    """The implant table above it could grow in a later revision."""
    cells = ware_sheet(devices=[{"A": "コムリンク", "D": "トランシスアヴァロン", "M": "6.0"}])
    shifted = {f"{ref[0]}{int(ref[1:]) + 4}": value for ref, value in cells.items()}
    state, _ = xlsx_to_state(workbook(dict(BASELINE), by_sheet={SHEET_WARE: shifted}))
    assert state["commlinks"][0]["gear_id"] == _catalog_id("commlinks", "Transys Avalon")


def test_a_missing_ware_sheet_is_tolerated() -> None:
    state, _ = xlsx_to_state(workbook(dict(BASELINE), sheets=(SHEET_BASICS, SHEET_SKILLS, "編集不可")))
    assert "cyberware" not in state
    assert "commlinks" not in state


def test_no_ware_keys_when_the_sheet_is_empty() -> None:
    state, warnings = xlsx_to_state(filled())
    assert not {"cyberware", "bioware", "commlinks", "cyberdecks"} & set(state)
    assert warnings == []


def test_the_implants_reach_the_engine_as_spent_essence() -> None:
    """Which is what makes the import worth having: the essence comes out of the
    rules rather than off the sheet. アルファウェア is 0.8 of the standard cost."""
    implants = [
        {"A": "オルソスキン", "N": "アルファウェア", "P": "3.0"},
        {"A": "超甲状腺", "N": "スタンダード", "P": "0.0"},
    ]
    state, _ = xlsx_to_state(filled(implants=implants))
    char = import_character(state)
    assert char.derived["essence"] == 6 - 0.6 - 0.7


# --- 装備 ------------------------------------------------------------------


def _item(name: str, **columns: str) -> dict[str, str]:
    """One 装備 row. A price is what makes it an item rather than a label."""
    return {"A": name, "C": "100.0", **columns}


@pytest.mark.parametrize(
    ("raw", "first", "nested", "rating", "qty"),
    [
        ("アーマージャケット", "アーマージャケット", False, 0, 0),
        ("└専用消音機", "専用消音機", True, 0, 0),
        ("→サブボーカルマイク", "サブボーカルマイク", True, 0, 0),
        ("┗スマートリンク", "スマートリンク", True, 0, 0),
        # the count, which column E holds too
        ("予備クリップ*12", "予備クリップ*12", False, 0, 12),
        ("通常弾x100", "通常弾x100", False, 0, 100),
        # the rating, in its four spellings
        ("医療キットR3", "医療キットR3", False, 3, 0),
        ("偽造SIN-R4", "偽造SIN-R4", False, 4, 0),
        ("視覚強化(R1)", "視覚強化(R1)", False, 1, 0),
        ("偽造SIN: 3", "偽造SIN: 3", False, 3, 0),
        # run onto the name with nothing between
        ("医療キット3", "医療キット3", False, 3, 0),
    ],
)
def test_split_row(raw: str, first: str, nested: bool, rating: int, qty: int) -> None:
    names, is_nested, got_rating, got_qty = split_row(raw)
    assert names[0] == first
    assert (is_nested, got_rating, got_qty) == (nested, rating, qty)


def test_a_count_in_the_name_is_not_read_as_a_rating() -> None:
    """通常弾x100 is a hundred rounds. Reading the 100 as a rating would make it
    an item no catalog has."""
    names, _nested, rating, qty = split_row("通常弾x100")
    assert (rating, qty) == (0, 100)
    assert "通常弾" in names


def test_a_model_number_is_not_stripped_before_the_name_is_tried() -> None:
    """アレス・プレデター V has to be looked up whole before anything is taken
    off the end of it."""
    assert split_row("アレスプレデターV")[0][0] == "アレスプレデターV"


def test_the_catalog_answers_for_each_kind_of_row() -> None:
    """One column holds everything, and which catalog answers is what says what
    kind of thing the row was."""
    rows = [
        _item("アレスプレデターV"),
        _item("アーマージャケット"),
        _item("レンラク・センセイ"),
        _item("ライフスタイル: 下流"),
        _item("医療キットR3"),
    ]
    state, warnings = xlsx_to_state(filled(gear=rows))
    assert [row["weapon_id"] for row in state["weapons"]] == [_catalog_id("weapons", "Ares Predator V")]
    assert [row["armor_id"] for row in state["armor"]] == [_catalog_id("armor", "Armor Jacket")]
    assert [row["gear_id"] for row in state["commlinks"]] == [_catalog_id("commlinks", "Renraku Sensei")]
    assert [row["lifestyle_id"] for row in state["lifestyles"]] == [_catalog_id("lifestyles", "Low")]
    assert [row["gear_id"] for row in state["gear"]] == [_catalog_id("gear", "Medkit")]
    assert warnings == []


def test_spacing_and_interpuncts_do_not_have_to_agree() -> None:
    """The catalog writes アレス・プレデター V; アッシュ writes アレスプレデターV."""
    state, _ = xlsx_to_state(filled(gear=[_item("アレスプレデターV")]))
    assert state["weapons"][0]["weapon_id"] == _catalog_id("weapons", "Ares Predator V")


def test_a_catalog_name_can_be_found_without_its_category() -> None:
    """The catalog files ammunition as 弾薬: 通常弾 and armor lines as
    ヴァッション・アイランド: エース・オブ・カップス; the sheets write either."""
    state, warnings = xlsx_to_state(filled(gear=[_item("通常弾"), _item("弾薬: 通常弾")]))
    regular = _catalog_id("gear", "Ammo: Regular Ammo")
    assert [row["gear_id"] for row in state["gear"]] == [regular, regular]
    assert warnings == []


def test_a_category_typed_in_front_comes_off() -> None:
    """日本鬼 writes コムリンク: レンラク・センセイ."""
    state, _ = xlsx_to_state(filled(gear=[_item("コムリンク: レンラク・センセイ")]))
    assert state["commlinks"][0]["gear_id"] == _catalog_id("commlinks", "Renraku Sensei")


def test_a_rating_written_into_the_name() -> None:
    state, _ = xlsx_to_state(filled(gear=[_item("医療キットR3"), _item("偽造SIN-R4")]))
    assert [row["rating"] for row in state["gear"]] == [3, 4]


def test_the_count_is_the_larger_of_the_column_and_the_name() -> None:
    """アッシュ writes 予備クリップ*12 with 12 in the column too; 日本鬼 writes
    通常弾x100 with 1 in the column."""
    rows = [_item("予備クリップ*12", E="12.0"), _item("通常弾x100", E="1.0")]
    state, _ = xlsx_to_state(filled(gear=rows))
    assert [row["qty"] for row in state["gear"]] == [12, 100]


def test_a_heading_is_not_an_item() -> None:
    state, warnings = xlsx_to_state(filled(gear=[{"A": "【武器】"}, _item("アレスプレデターV")]))
    assert len(state["weapons"]) == 1
    assert warnings == []


def test_a_row_with_no_price_is_a_label() -> None:
    """ピストル用 groups the ammunition under it; it was not bought."""
    rows = [{"A": "ピストル用"}, _item("通常弾", E="10.0")]
    state, warnings = xlsx_to_state(filled(gear=rows))
    assert len(state["gear"]) == 1
    assert warnings == []


def test_something_fitted_to_the_row_above_it() -> None:
    rows = [_item("偽造SIN-R4"), _item("└偽造免許-R4", E="4.0")]
    state, _ = xlsx_to_state(filled(gear=rows))
    sin, licence = state["gear"]
    assert sin["gear_id"] == _catalog_id("gear", "Fake SIN")
    assert licence["parent_id"] == sin["id"]


def test_a_label_breaks_the_chain_of_what_is_fitted_to_what() -> None:
    """The ammunition under ピストル用 is not fitted to the row above the label."""
    rows = [_item("偽造SIN-R4"), {"A": "ピストル用"}, _item("└通常弾", E="10.0")]
    state, _ = xlsx_to_state(filled(gear=rows))
    assert state["gear"][1].get("parent_id") is None


def test_a_heading_breaks_the_chain_too() -> None:
    rows = [_item("偽造SIN-R4"), {"A": "【弾薬】"}, _item("└通常弾", E="10.0")]
    state, _ = xlsx_to_state(filled(gear=rows))
    assert state["gear"][1].get("parent_id") is None


def test_a_plugin_loses_to_the_gear_of_the_same_name() -> None:
    """予備クリップ and 隠蔽ホルスター are each a weapon accessory as well as a
    piece of gear; on a row of its own the gear is what was bought."""
    state, _ = xlsx_to_state(filled(gear=[_item("予備クリップ"), _item("隠蔽ホルスター")]))
    assert len(state["gear"]) == 2
    assert "weapon_accessories" not in state


def test_a_row_naming_two_things_needs_confirming() -> None:
    """通常弾*20、スティックン・ショック*20 — one cell, two items, and nothing
    that can be made of it without being told."""
    raw = "通常弾*20、スティックン・ショック*20"
    pending = pending_of(filled(gear=[_item(raw)]))
    assert [row["name"] for row in pending] == [raw]


def test_a_note_after_the_name_comes_off() -> None:
    """アレス・ライト・ファイア70(内蔵SG) — the parenthesis is the player's note
    about the weapon, not part of its name."""
    state, warnings = xlsx_to_state(filled(gear=[_item("アレス・ライト・ファイア70(内蔵SG)")]))
    assert state["weapons"][0]["weapon_id"] == _catalog_id("weapons", "Ares Light Fire 70")
    assert warnings == []


def test_a_row_that_matched_nothing_comes_back_to_be_confirmed() -> None:
    """Nothing is dropped in silence: the row comes back with what the sheet
    said about it, and one warning says how many there were."""
    rows = [_item("そんな装備はない", E="3.0", K="メモ")]
    state, warnings = xlsx_to_state(filled(gear=rows))
    pending = pending_of(filled(gear=rows))
    assert "gear" not in state
    assert pending[0]["name"] == "そんな装備はない"
    assert pending[0]["qty"] == 3
    assert pending[0]["note"] == "メモ"
    assert has(warnings, "engine.import.xlsxGearPending", count=1)


def test_a_row_that_matched_is_not_pending() -> None:
    assert pending_of(filled(gear=[_item("医療キットR3")])) == []


def test_a_pending_row_carries_a_rating_written_into_its_name() -> None:
    pending = pending_of(filled(gear=[_item("そんな装備-R4")]))
    assert pending[0]["rating"] == 4


def test_a_pending_row_is_offered_what_it_looks_like() -> None:
    """アレス・サンダートラック is one syllable out from the catalog's
    アレス サンダーストラック, which is what the shortlist is for."""
    pending = pending_of(filled(gear=[_item("アレス・サンダートラック・ガウスライフル")]))
    names = [item["name"] for item in pending[0]["suggestions"]]
    assert names[0] == "Ares Thunderstruck Gauss Rifle"


def test_a_suggestion_says_which_list_it_would_go_in() -> None:
    """The client needs it to put the item somewhere, and a shield is both a
    weapon and a piece of armor."""
    pending = pending_of(filled(gear=[_item("FN-HAL")]))
    first = pending[0]["suggestions"][0]
    assert (first["bucket"], first["key"], first["name"]) == ("weapons", "weapons", "FN HAR")
    assert first["id"] == _catalog_id("weapons", "FN HAR")


def test_a_suggestion_carries_the_row_to_append() -> None:
    """So a client offering the shortlist never has to know which lists carry a
    count, which carry a rating and which count months."""
    pending = pending_of(filled(gear=[_item("贅沢品", E="4.0")]))
    lifestyle = next(item for item in pending[0]["suggestions"] if item["key"] == "lifestyles")
    assert lifestyle["entry"]["months"] == 4
    assert "rating" not in lifestyle["entry"]


def test_a_suggested_weapon_takes_a_count_and_no_rating() -> None:
    pending = pending_of(filled(gear=[_item("FN-HAL", E="2.0")]))
    entry = pending[0]["suggestions"][0]["entry"]
    assert entry["qty"] == 2
    assert "rating" not in entry


def test_a_suggested_row_keeps_the_rating_from_the_name() -> None:
    pending = pending_of(filled(gear=[_item("そんな医療キットR3")]))
    gear = next(item for item in pending[0]["suggestions"] if item["key"] == "gear")
    assert gear["entry"]["rating"] == 3


def test_a_name_like_nothing_in_the_book_is_offered_nothing() -> None:
    """An empty shortlist is honest; a bad guess at the top of one is not."""
    pending = pending_of(filled(gear=[_item("ZZZZZZZZZZ")]))
    assert pending[0]["suggestions"] == []


def test_suggestions_are_capped() -> None:
    pending = pending_of(filled(gear=[_item("弾薬")]))
    assert len(pending[0]["suggestions"]) <= SUGGEST_LIMIT


def test_the_gear_reaches_the_engine_as_spent_nuyen() -> None:
    state, _ = xlsx_to_state(filled(gear=[_item("アレスプレデターV", E="1.0")]))
    char = import_character(state)
    assert char.derived["nuyen_spent"] > 0


def test_a_missing_gear_sheet_is_tolerated() -> None:
    state, _ = xlsx_to_state(workbook(dict(BASELINE), sheets=(SHEET_BASICS, SHEET_SKILLS, "編集不可")))
    assert "weapons" not in state
    assert "gear" not in state


def test_no_gear_keys_when_the_sheet_is_empty() -> None:
    state, warnings = xlsx_to_state(filled())
    assert not {"weapons", "armor", "gear", "vehicles", "lifestyles"} & set(state)
    assert warnings == []


# --- コンタクト／その他カルマ消費 -----------------------------------------------


def test_contacts_keep_the_names_the_player_gave_them() -> None:
    """A contact is the player's own invention, so nothing is matched."""
    rows = [
        {"A": "ストリートドク", "E": "2.0", "G": "3.0", "Q": "2", "S": "3"},
        {"A": "繁華街の情報通", "E": "2.0", "G": "2.0", "Q": "2", "S": "2"},
    ]
    state, warnings = xlsx_to_state(filled(contacts=rows))
    assert [(row["name"], row["connection"], row["loyalty"]) for row in state["contacts"]] == [
        ("ストリートドク", 2, 3),
        ("繁華街の情報通", 2, 2),
    ]
    assert warnings == []


def test_a_contact_bought_with_karma_is_the_same_row() -> None:
    """The sheet keeps contact points (E/G) and karma (I/K) in their own columns
    and adds both into Q/S, which is the rating."""
    rows = [{"A": "Mrジョンソン", "I": "1.0", "K": "2.0", "Q": "1", "S": "2"}]
    state, _ = xlsx_to_state(filled(contacts=rows))
    assert (state["contacts"][0]["connection"], state["contacts"][0]["loyalty"]) == (1, 2)


def test_what_something_else_granted_is_not_billed() -> None:
    """ララ's fourth contact sits entirely in その他修正 (M/O)."""
    rows = [{"A": "ドクターゲオルグ", "M": "3.0", "O": "2.0", "Q": "3", "S": "2"}]
    state, _ = xlsx_to_state(filled(contacts=rows))
    row = state["contacts"][0]
    assert (row["connection"], row["loyalty"]) == (3, 2)
    assert (row["free_connection"], row["free_loyalty"]) == (3, 2)


def test_a_contact_with_only_a_name_starts_at_one() -> None:
    state, _ = xlsx_to_state(filled(contacts=[{"A": "名無しのフィクサー"}]))
    assert (state["contacts"][0]["connection"], state["contacts"][0]["loyalty"]) == (1, 1)


def test_no_contacts_key_when_the_block_is_empty() -> None:
    state, warnings = xlsx_to_state(filled(contacts=[]))
    assert "contacts" not in state
    assert warnings == []


def test_the_contacts_reach_the_engine_as_spent_points() -> None:
    """アッシュ's three, which the sheet totals as 9 contact points and 3 karma."""
    rows = [
        {"A": "ストリートドク", "Q": "2", "S": "3"},
        {"A": "繁華街の情報通", "Q": "2", "S": "2"},
        {"A": "Mrジョンソン", "Q": "1", "S": "2"},
    ]
    state, _ = xlsx_to_state(filled(contacts=rows, C23="C"))
    points = import_character(state).derived["contact_points"]
    assert points["used"] == 12
    assert points["used"] - points["free"] == points["karma"]


def test_other_karma_is_reported_rather_than_folded_in() -> None:
    """その他カルマ消費 has no counterpart here, and a number quietly taken off
    the karma would be a number nothing explains."""
    rows = [{"A": "武術：カロメレグ", "F": "7.0"}]
    _, warnings = xlsx_to_state(filled(other_karma=rows))
    assert has(warnings, "engine.import.xlsxOtherKarma", name="武術：カロメレグ", karma=7)


def test_the_other_karma_block_is_found_by_its_heading() -> None:
    cells = contact_sheet(other_karma=[{"A": "儀式の準備", "F": "3.0"}])
    shifted = {f"{ref[0]}{int(ref[1:]) + 5}": value for ref, value in cells.items()}
    _, warnings = xlsx_to_state(workbook(dict(BASELINE), by_sheet={SHEET_CONTACTS: shifted}))
    assert has(warnings, "engine.import.xlsxOtherKarma", name="儀式の準備", karma=3)


def test_a_missing_contact_sheet_is_tolerated() -> None:
    state, _ = xlsx_to_state(workbook(dict(BASELINE), sheets=(SHEET_BASICS, SHEET_SKILLS, "編集不可")))
    assert "contacts" not in state


# --- 換金したカルマ ----------------------------------------------------------


def test_karma_turned_into_nuyen_comes_over() -> None:
    """換金したカルマ on the priority sheet. Without it every character who used
    it looks over budget by what they converted."""
    state, _ = xlsx_to_state(filled(AC4="7.0"))
    assert state["karma_nuyen"] == 7


def test_no_karma_nuyen_key_when_nothing_was_converted() -> None:
    state, _ = xlsx_to_state(filled())
    assert "karma_nuyen" not in state


def test_converted_karma_raises_the_equipment_budget() -> None:
    plain, _ = xlsx_to_state(filled(gear=[]))
    converted, _ = xlsx_to_state(filled(AC4="7.0", gear=[]))
    assert import_character(converted).derived["nuyen"] > import_character(plain).derived["nuyen"]


# --- 装備: the phrasings a lifestyle is written in ---------------------------


@pytest.mark.parametrize(
    "raw",
    ["ライフスタイル下流", "ライフスタイル: 下流", "ライフスタイル（下流）一か月分", "生活費下流一か月分"],
)
def test_a_lifestyle_however_it_is_phrased(raw: str) -> None:
    """A lifestyle is filed under its bare name (下流) and the sheets wrap it in
    whatever the player thought of."""
    state, warnings = xlsx_to_state(filled(gear=[_item(raw)]))
    assert [row["lifestyle_id"] for row in state["lifestyles"]] == [_catalog_id("lifestyles", "Low")]
    assert warnings == []


def test_a_lifestyle_name_inside_other_gear_is_not_one() -> None:
    """The phrasing rule only looks at a row that says it is about a lifestyle,
    so a piece of gear is never turned into one."""
    state, _ = xlsx_to_state(filled(gear=[_item("医療キットR3")]))
    assert "lifestyles" not in state


def test_the_months_come_from_the_count_column() -> None:
    state, _ = xlsx_to_state(filled(gear=[_item("ライフスタイル: 下流", E="3.0")]))
    assert state["lifestyles"][0]["months"] == 3


def test_a_long_category_in_front_of_an_armor_name() -> None:
    """The catalog files the line as ヴァッション・アイランド: エース・オブ・カップス and
    アッシュ writes only the garment."""
    state, warnings = xlsx_to_state(filled(gear=[_item("エース・オブ・カップス")]))
    assert state["armor"][0]["armor_id"] == _catalog_id("armor", "Vashon Island: Ace of Cups")
    assert warnings == []


def test_a_kanji_variant_of_the_same_word() -> None:
    """ララ writes 偽装SIN where the catalog says 偽造SIN."""
    state, warnings = xlsx_to_state(filled(gear=[_item("偽装SIN-L4")]))
    assert state["gear"][0]["gear_id"] == _catalog_id("gear", "Fake SIN")
    assert state["gear"][0]["rating"] == 4
    assert warnings == []
