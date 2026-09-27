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
from app.xlsx_import._common import SHEET_BASICS, cell_int
from app.xlsx_import._sheet import NotAWorkbook, Workbook
from app.xlsx_import.qualities import split_name
from tests.notice_asserts import has
from tests.xlsx_fixtures import BASELINE, filled, workbook


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
    ("raw", "name", "extra"),
    [
        ("両手利き", "両手利き", ""),
        ("規制品(アレス・サンダートラック)", "規制品", "アレス・サンダートラック"),
        ("規制品（超甲状腺）", "規制品", "超甲状腺"),
        ("依存症／中度／クラム", "依存症 (中度)", "クラム"),
        ("依存症／中度", "依存症 (中度)", ""),
        ("アレルギー／軽度／花粉／ブタクサ", "アレルギー (軽度)", "花粉／ブタクサ"),
        ("  両手利き  ", "両手利き", ""),
    ],
)
def test_split_name(raw: str, name: str, extra: str) -> None:
    assert split_name(raw) == (name, extra)


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
