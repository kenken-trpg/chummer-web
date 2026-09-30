"""Writing a character out as a キャラシテンプレート-shaped .xlsx.

The claim worth testing is a round trip: a character that came from the template
goes back into one and reads the same. So most of what follows builds a workbook
with `xlsx_fixtures`, imports it, exports it and imports that — and asserts on
what came back rather than on which cell holds what. The cell addresses are the
import's, and it already has 250 tests pinning them down.

What is asserted directly is the part a round trip cannot see: that the file is
a readable workbook at all, and that the things the template has no room or no
cell for are reported rather than dropped in silence.
"""

from __future__ import annotations

import zipfile
from io import BytesIO
from typing import Any

import pytest

from app.characters import import_character, new_character
from app.data_loader import catalog
from app.models import CharacterCreate, CharacterState
from app.notices import Notice
from app.xlsx_export import MARKER_SHEET, state_to_xlsx, xlsx_limits
from app.xlsx_export._workbook import column_index, write_workbook
from app.xlsx_export.check import roundtrip_differences
from app.xlsx_import import is_template_workbook, xlsx_to_state
from app.xlsx_import._sheet import Workbook
from tests.xlsx_fixtures import filled

# --- the writer -----------------------------------------------------------


def test_a_cell_comes_back_as_it_was_written() -> None:
    book = Workbook(write_workbook([("One", {"C3": "ヒューマン", "H19": 4})]))
    assert book.cells("One") == {"C3": "ヒューマン", "H19": "4"}


def test_the_sheets_keep_their_names_and_their_order() -> None:
    body = write_workbook([("優先度／能力値／資質", {"A1": "x"}), ("装備", {"A1": "y"})])
    assert Workbook(body).sheet_names == ["優先度／能力値／資質", "装備"]


def test_a_repeated_string_is_written_once() -> None:
    body = write_workbook([("One", {"A1": "同じ", "A2": "同じ", "A3": "違う"})])
    with zipfile.ZipFile(BytesIO(body)) as archive:
        shared = archive.read("xl/sharedStrings.xml").decode()
    assert shared.count("<si>") == 2


def test_an_empty_cell_is_not_written() -> None:
    assert Workbook(write_workbook([("One", {"A1": "", "A2": "x"})])).cells("One") == {"A2": "x"}


def test_rows_are_written_in_order() -> None:
    """A reader is entitled to stop at the first row whose number goes backwards."""
    body = write_workbook([("One", {"B10": "b", "A2": "a", "C10": "c", "A100": "d"})])
    with zipfile.ZipFile(BytesIO(body)) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml").decode()
    assert [part.split('"')[0] for part in sheet.split('<row r="')[1:]] == ["2", "10", "100"]
    assert sheet.index('r="B10"') < sheet.index('r="C10"')


def test_a_character_xml_has_no_way_to_carry_comes_out() -> None:
    """A name pasted out of a chat log can hold a control character, which would
    make the file unreadable rather than merely odd."""
    assert Workbook(write_workbook([("One", {"A1": "ア\x01シュ"})])).cells("One") == {"A1": "アシュ"}


def test_a_cell_written_only_of_control_characters_is_left_out() -> None:
    assert Workbook(write_workbook([("One", {"A1": "\x01", "A2": "x"})])).cells("One") == {"A2": "x"}


def test_a_number_is_written_as_a_number() -> None:
    with zipfile.ZipFile(BytesIO(write_workbook([("One", {"A1": 7})]))) as archive:
        assert '<c r="A1"><v>7</v></c>' in archive.read("xl/worksheets/sheet1.xml").decode()


def test_a_reference_that_is_not_one_is_refused() -> None:
    with pytest.raises(ValueError, match="not a cell reference"):
        write_workbook([("One", {"3C": "x"})])


def test_a_workbook_with_no_sheets_is_refused() -> None:
    with pytest.raises(ValueError, match="needs a sheet"):
        write_workbook([])


def test_a_true_is_not_a_number() -> None:
    """`bool` is an `int`, and a cell holding TRUE would read back as 1."""
    with pytest.raises(TypeError, match="text or a number"):
        write_workbook([("One", {"A1": True})])


def test_the_columns_past_z_are_counted_right() -> None:
    assert (column_index("A"), column_index("Z"), column_index("AC")) == (1, 26, 29)


def test_the_styles_part_is_there() -> None:
    """Excel treats a workbook with no styles as damaged and offers to repair it."""
    with zipfile.ZipFile(BytesIO(write_workbook([("One", {"A1": "x"})]))) as archive:
        assert "xl/styles.xml" in archive.namelist()


# --- the round trip -------------------------------------------------------


def _character(**kwargs: Any) -> CharacterState:
    state, _warnings, _pending = xlsx_to_state(filled(**kwargs))
    return import_character(state)


def _again(character: CharacterState) -> CharacterState:
    """`character` written out and read back."""
    state, _warnings, _pending = xlsx_to_state(state_to_xlsx(character))
    return import_character(state)


def test_our_own_file_is_one_the_import_accepts() -> None:
    assert is_template_workbook(state_to_xlsx(_character()))


def test_the_marker_sheet_says_where_the_file_came_from() -> None:
    assert Workbook(state_to_xlsx(_character())).cells(MARKER_SHEET)["A1"].startswith("chummer-web")


def test_the_build_and_the_metatype_come_back() -> None:
    first = _character(C3="B", C7="A", C12="C", C13="D", C8="E", C16="オーク")
    again = _again(first)
    assert (again.metatype, again.build_method) == ("Ork", "Priority")
    assert again.priorities.model_dump() == first.priorities.model_dump()


def test_a_karma_build_writes_the_other_setting() -> None:
    again = _again(_character(W1="800カルマ割り振り"))
    assert again.build_method == "Karma"


def test_the_kind_of_magic_user_comes_back() -> None:
    again = _again(_character(C8="C", C17="アデプト", H28="1.0", J28="5.0"))
    assert again.talent == "Adept"


def test_the_attributes_and_the_karma_that_raised_them_come_back() -> None:
    first = _character(C16="オーク", H19="4.0", J19="3.0", L19="1.0", H20="1.0", J20="2.0")
    again = _again(first)
    assert again.attributes["BOD"] == first.attributes["BOD"]
    assert again.attribute_karma == first.attribute_karma


def test_the_racial_minimum_goes_in_the_column_the_template_puts_it_in() -> None:
    """H is what the sheet fills in from the metatype and J what the player
    bought, so a player opening the file sees their own numbers in their column."""
    cells = Workbook(state_to_xlsx(_character(C16="オーク", H19="4.0", J19="3.0"))).cells("優先度／能力値／資質")
    assert (cells.get("H19"), cells.get("J19")) == ("4", "3")


def test_the_karma_turned_into_nuyen_comes_back() -> None:
    assert _again(_character(AC4="10.0")).karma_nuyen == 10


def test_a_quality_and_its_pick_come_back() -> None:
    first = _character(A50="不利", C50="依存症／中度／クラム")
    again = _again(first)
    assert again.quality_ids == first.quality_ids
    assert again.quality_extras == first.quality_extras


def test_a_quality_whose_own_name_carries_the_pick_comes_back() -> None:
    """SINner (National) is filed as 「SIN持ち：国家SIN」, so the catalog name has
    to be left to speak for itself rather than have a pick appended."""
    first = _character(A50="不利", C50="国家SIN")
    assert _again(first).quality_ids == first.quality_ids


def test_a_quality_taken_twice_comes_back_twice() -> None:
    first = _character(A50="有利", C50="規制品", A51="有利", C51="規制品")
    assert len(_again(first).quality_ids) == len(first.quality_ids) == 2


def test_a_mentor_comes_back() -> None:
    """The import takes a mentor out of the quality list and puts it in
    `mentor_id`, because the sheet writes it as the quality's pick — so the
    export has to put it back there, or the mentor is lost."""
    first = _character(C8="A", C17="魔法使い（メイジ）", H28="1.0", J28="5.0", A50="有利", C50="導師精霊（熊）")
    assert first.mentor_id
    again = _again(first)
    assert again.mentor_id == first.mentor_id
    assert again.quality_ids == first.quality_ids


def test_a_mentor_whose_name_carries_a_reading_comes_back() -> None:
    """The catalog puts the reading after the name — 「龍殺しの英雄 (ドラゴンスレイヤー)」
    — and the sheet's reader takes the first parenthesis as the pick, so the
    reading has to come off before the mentor is written as one."""
    first = _character(
        C8="A", C17="魔法使い（メイジ）", H28="1.0", J28="5.0", A50="有利", C50="導師精霊（龍殺しの英雄）"
    )
    assert first.mentor_id
    assert _again(first).mentor_id == first.mentor_id


def test_the_skills_the_groups_and_their_karma_come_back() -> None:
    first = _character(
        groups={"射撃": {"I": "3.0", "J": "1.0"}},
        skills={"ピストル": {"I": "4.0", "J": "2.0"}, "隠密": {"I": "3.0"}},
    )
    again = _again(first)
    assert again.skills == first.skills
    assert again.skill_karma == first.skill_karma
    assert again.skill_groups == first.skill_groups
    assert again.skill_group_karma == first.skill_group_karma


def test_a_specialization_the_book_prints_comes_back() -> None:
    first = _character(skills={"ピストル": {"I": "4.0", "E": "セミオートマチック"}})
    assert _again(first).skill_specializations == first.skill_specializations


def test_a_specialization_of_the_players_own_is_not_renamed() -> None:
    """The sheet lets the player write anything in that column, and what they
    wrote is theirs — translating it would come back a different word."""
    first = _character(skills={"ピストル": {"I": "4.0", "F": "祖父の拳銃"}})
    again = _again(first)
    assert again.skill_specializations == first.skill_specializations == {"Pistols": "祖父の拳銃"}
    assert again.skill_specs_karma == ["Pistols"]


def test_the_knowledge_skills_keep_their_names() -> None:
    """A knowledge skill's name *is* the skill, so nothing about it is
    translated: 「English」 coming back as 「英語」 would be a rename of the
    player's own data rather than a translation."""
    first = _character(
        knowledge=[
            {"A": "学術知識技能", "B": "English", "H": "3.0"},
            {"A": "言語知識技能（Native）", "B": "日本語"},
        ]
    )
    again = _again(first)
    assert again.knowledge_skills == first.knowledge_skills == {"English": 3}
    assert again.knowledge_categories == first.knowledge_categories
    assert again.native_languages == first.native_languages == ["日本語"]


def test_the_spells_and_the_complex_forms_come_back() -> None:
    first = _character(
        C8="A",
        C17="魔法使い（メイジ）",
        H28="1.0",
        J28="5.0",
        spells=["火の玉", "真偽分析"],
        forms=["パルス・ストーム"],
    )
    again = _again(first)
    assert {row.spell_id for row in again.spells} == {row.spell_id for row in first.spells}
    assert {row.form_id for row in again.complex_forms} == {row.form_id for row in first.complex_forms}


def test_an_adept_power_and_its_level_come_back() -> None:
    first = _character(C8="C", C17="アデプト", H28="1.0", J28="5.0", powers=[("向上した反応速度", "2.0")])
    again = _again(first)
    assert [(row.power_id, row.rating) for row in again.adept_powers] == [
        (row.power_id, row.rating) for row in first.adept_powers
    ]


def test_the_reward_ledger_comes_back_with_its_dates() -> None:
    """The log's two columns survive the trip: the import joins the date onto
    the note, and the export splits it off again."""
    first = _character(
        growth=[
            {"A": "12000.0", "B": "7.0", "C": "45658.0", "D": "デッドマンズ・ハンド"},
            {"B": "3.0", "D": "幕間"},
        ]
    )
    again = _again(first)
    assert again.career is True
    assert [(row.karma, row.nuyen, row.label) for row in again.reward_log] == [
        (7, 12000, "2025-01-01 デッドマンズ・ハンド"),
        (3, 0, "幕間"),
    ]


def test_a_character_that_was_never_played_writes_an_empty_log() -> None:
    """Nothing earned, nothing written — and it still reads back in creation."""
    again = _again(_character())
    assert again.career is not True
    assert list(again.reward_log) == []


def test_an_implant_its_grade_and_its_rating_come_back() -> None:
    first = _character(implants=[{"A": "視覚強化", "N": "アルファウェア", "P": "3.0"}])
    again = _again(first)
    assert [(row.ware_id, row.grade, row.rating) for row in again.cyberware] == [
        (row.ware_id, row.grade, row.rating) for row in first.cyberware
    ]


def test_an_implant_whose_rating_column_holds_a_material_comes_back() -> None:
    """骨格補綴 with チタニウム in the rating column is the catalog's
    「骨格補綴 (チタニウム)」 — the material is part of the name there, which is
    what the export has to write."""
    first = _character(implants=[{"A": "骨格補綴", "N": "中古", "P": "チタニウム"}])
    assert [row.ware_id for row in _again(first).cyberware] == [row.ware_id for row in first.cyberware]
    assert first.cyberware


def test_which_side_an_implant_went_on_comes_back() -> None:
    """The sheet's only place for a side is the name, which is where the import
    looks — so a sided implant has to be written with the mark back on. A
    cyberlimb is the kind of implant that takes one."""
    first = _character(implants=[{"A": "非偽装型サイバーリム右腕全体", "N": "スタンダード", "P": "1.0"}])
    assert [row.side for row in first.cyberware] == ["Right"]
    assert Workbook(state_to_xlsx(first)).cells("身体強化／電子機器")["A4"].startswith("右")
    assert [row.side for row in _again(first).cyberware] == ["Right"]


def test_an_implant_installed_in_another_comes_back_under_it() -> None:
    first = _character(
        implants=[
            {"A": "サイバーアイ", "N": "スタンダード", "P": "2.0"},
            {"A": "└視覚強化", "N": "スタンダード", "P": "3.0"},
        ]
    )

    def shape(character: CharacterState) -> list[tuple[str, bool]]:
        return sorted((row.ware_id, bool(row.parent_id)) for row in character.cyberware)

    assert shape(_again(first)) == shape(first)
    assert any(nested for _ware, nested in shape(first))


def test_a_commlink_comes_back_and_only_once() -> None:
    """The template keeps devices on the 身体強化 sheet; writing them on the
    equipment sheet as well would buy them twice."""
    first = _character(devices=[{"A": "コムリンク", "D": "レンラク・センセイ", "M": "1.0"}])
    again = _again(first)
    assert [row.gear_id for row in again.commlinks] == [row.gear_id for row in first.commlinks]
    assert len(again.commlinks) == 1
    assert not again.gear


def test_the_equipment_its_count_and_its_rating_come_back() -> None:
    first = _character(
        gear=[
            {"A": "偽造SIN", "C": "7500.0", "E": "1.0"},
            {"A": "医療キット", "C": "1500.0", "E": "2.0"},
        ]
    )
    again = _again(first)
    assert [(row.gear_id, row.rating, row.qty) for row in again.gear] == [
        (row.gear_id, row.rating, row.qty) for row in first.gear
    ]


def test_a_rating_above_one_is_written_into_the_name() -> None:
    """The equipment sheet has no rating column, so there is nowhere else."""
    cells = Workbook(state_to_xlsx(_character(gear=[{"A": "偽造SIN-R4", "C": "10000.0"}]))).cells("装備")
    assert cells["A3"].endswith("-R4")


def test_every_row_carries_a_price() -> None:
    """A row with no price is a heading or a bundle label to the import, so
    every row written has to have one — a free thing included, as a 0."""
    cells = Workbook(state_to_xlsx(_character(gear=[{"A": "通常弾", "C": "0.0", "E": "10.0"}]))).cells("装備")
    named_rows = [ref for ref in cells if ref.startswith("A")]
    assert named_rows and all(f"C{ref[1:]}" in cells for ref in named_rows)


def test_a_parents_price_is_its_own_and_not_the_assemblys() -> None:
    """A weapon's derived price is the whole assembly, and each accessory writes
    its own price on its own row, so the column has to add up."""
    cells = Workbook(
        state_to_xlsx(_character(gear=[{"A": "アレス・プレデターV", "C": "725.0"}, {"A": "└消音器", "C": "500.0"}]))
    ).cells("装備")
    assert (cells["C3"], cells["C4"]) == ("725", "500")


def test_an_accessory_comes_back_fitted_to_the_same_weapon() -> None:
    first = _character(
        gear=[
            {"A": "アレス・プレデターV", "C": "725.0"},
            {"A": "└消音器", "C": "500.0"},
        ]
    )
    again = _again(first)
    assert [row.weapon_id for row in again.weapons] == [row.weapon_id for row in first.weapons]
    bought = [row for row in again.weapon_accessories if not row.included]
    assert len(bought) == 1
    assert bought[0].parent_id == again.weapons[0].id


def test_a_lifestyles_months_come_back() -> None:
    first = _character(gear=[{"A": "ライフスタイル（下流）", "C": "2000.0", "E": "3.0"}])
    again = _again(first)
    assert [(row.lifestyle_id, row.months) for row in again.lifestyles] == [
        (row.lifestyle_id, row.months) for row in first.lifestyles
    ]


def test_what_came_with_something_else_is_not_bought_again() -> None:
    """An armor mod a jacket includes, or the weapon side of an implant, is put
    back when the character is computed — writing it would charge for it twice."""
    first = _character(implants=[{"A": "ハンドブレード", "N": "スタンダード", "P": "1.0"}])
    again = _again(first)
    assert [row.ware_id for row in again.cyberware] == [row.ware_id for row in first.cyberware]
    assert not again.weapons


def test_a_contact_and_the_part_of_it_something_else_granted_come_back() -> None:
    first = _character(
        contacts=[
            {"A": "ストリートドク", "Q": "3.0", "S": "2.0"},
            {"A": "フィクサー", "Q": "4.0", "S": "3.0", "M": "1.0", "O": "1.0"},
        ]
    )
    again = _again(first)
    shape = [(row.name, row.connection, row.loyalty, row.free_connection, row.free_loyalty) for row in again.contacts]
    assert shape == [
        (row.name, row.connection, row.loyalty, row.free_connection, row.free_loyalty) for row in first.contacts
    ]


def test_a_whole_character_comes_back_unchanged() -> None:
    first = _character(
        C16="オーク",
        C8="C",
        C17="アデプト",
        H19="4.0",
        J19="3.0",
        H28="1.0",
        J28="5.0",
        A50="不利",
        C50="依存症／中度／クラム",
        groups={"射撃": {"I": "3.0"}},
        skills={"ピストル": {"I": "4.0", "E": "セミオートマチック"}},
        knowledge=[{"A": "学術知識技能", "B": "日本の企業", "H": "3.0"}],
        powers=[("向上した反応速度", "2.0")],
        implants=[{"A": "視覚強化", "N": "アルファウェア", "P": "3.0"}],
        devices=[{"A": "コムリンク", "D": "レンラク・センセイ", "M": "1.0"}],
        gear=[{"A": "偽造SIN-R4", "C": "10000.0"}, {"A": "ライフスタイル（下流）", "C": "2000.0", "E": "1.0"}],
        contacts=[{"A": "ストリートドク", "Q": "3.0", "S": "2.0"}],
    )
    assert roundtrip_differences(first) == []


# --- what the sheet has no room or no cell for ----------------------------


def _keys(notices: list[Notice]) -> set[str]:
    return {item["key"] for item in notices}


def test_more_qualities_than_the_sheet_has_rows_is_reported() -> None:
    quality_ids = [str(row["id"]) for row in catalog()["qualities"][:12]]
    character = import_character({**_character().model_dump(), "quality_ids": quality_ids})
    assert "engine.export.xlsxNoRoom" in _keys(roundtrip_differences(character))


def test_a_metatype_the_sheet_cannot_pick_is_reported() -> None:
    character = import_character({**_character().model_dump(), "metatype": "Pixie"})
    reported = [item for item in roundtrip_differences(character) if item["key"] == "engine.export.xlsxNoCell"]
    assert reported and reported[0]["params"]["name"] == "Pixie"
    assert Workbook(state_to_xlsx(character)).cells("優先度／能力値／資質")["C16"] == "ヒューマン"


def test_a_kind_of_magic_user_the_sheet_cannot_pick_is_written_as_the_nearest() -> None:
    """Enchanter, Apprentice, Aware and Explorer are all the book's limited
    magicians, which is what 偏位魔法使い is.

    Set on the state directly: which talents a character may hold depends on the
    books in play, and what is under test is the writing, not the rule.
    """
    character = _character().model_copy(update={"talent": "Enchanter"})
    assert "engine.export.xlsxNoCell" in _keys(xlsx_limits(character))
    assert Workbook(state_to_xlsx(character)).cells("優先度／能力値／資質")["C17"].startswith("偏位魔法使い")


def test_a_build_method_the_sheet_has_no_setting_for_is_reported() -> None:
    """A SumToTen build still chose priority letters, so they survive and only
    the method is written differently."""
    character = import_character({**_character().model_dump(), "build_method": "SumToTen"})
    reported = [item for item in roundtrip_differences(character) if item["key"] == "engine.export.xlsxNoCell"]
    assert any(item["params"]["name"] == "SumToTen" for item in reported)


def test_a_character_from_the_template_loses_nothing() -> None:
    assert roundtrip_differences(_character(skills={"ピストル": {"I": "4.0"}})) == []


def test_the_settings_are_reported_in_their_own_words() -> None:
    """The template is a character-creation sheet: it has no cell for which
    rulebooks are in play. That is lost on every character that has settings, so
    it is said plainly and once rather than counted as 「その他が変わります」 —
    which would arrive on every single export and read as a fault.
    """
    character = new_character(CharacterCreate(name="Settings"))
    assert character.settings.name
    keys = _keys(roundtrip_differences(character))
    assert "engine.export.xlsxNoSettings" in keys
    assert "engine.export.changed" not in keys
