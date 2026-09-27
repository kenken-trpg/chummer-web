"""シャドウラン_キャラシテンプレート (.xlsx) import — see backend/app/xlsx_import/."""

from __future__ import annotations

import zipfile

import pytest
from fastapi.testclient import TestClient

from app.characters import import_character
from app.data_loader import catalog
from app.main import app
from app.notices import NoticeError
from app.xlsx_import import is_template_workbook, xlsx_to_state
from app.xlsx_import._common import SHEET_BASICS, cell_int, japanese_index
from app.xlsx_import._sheet import NotAWorkbook, Workbook
from app.xlsx_import.qualities import candidates, resolve, split_name
from app.xlsx_import.skills import GROUP_ALIASES, SKILL_ALIASES
from tests.notice_asserts import has
from tests.xlsx_fixtures import BASELINE, filled, skill_sheet, workbook


def _quality_id(name: str) -> str:
    return next(str(row["id"]) for row in catalog()["qualities"] if row["name"] == name)


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


def test_a_degree_written_in_front_of_the_quality() -> None:
    """軽度の依存症（…） is the catalog's 依存症 (軽度) with the degree moved."""
    state, _ = xlsx_to_state(filled(A50="不利", C50="軽度の依存症（エナジードリンク / カフェイン）"))
    mild = _quality_id("Addiction (Mild)")
    assert state["quality_ids"] == [mild]
    assert state["quality_extras"] == {mild: "エナジードリンク / カフェイン"}


def test_a_note_after_the_pick_is_not_part_of_the_name() -> None:
    """導師精霊（竜殺しの英雄）　交渉に+2修正 — the player's own note trails the
    pick, and the mentor itself is `mentor_id`, which this import does not read
    yet, so the pick is reported."""
    state, warnings = xlsx_to_state(filled(A50="有利", C50="導師精霊（竜殺しの英雄）\u3000交渉に+2修正"))
    assert state["quality_ids"] == [_quality_id("Mentor Spirit")]
    assert has(warnings, "engine.import.xlsxQualityNote", note="竜殺しの英雄")


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
