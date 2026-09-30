"""The template watcher turns a difference into a piece of work.

The fetching and the reading are not tested here — one needs the network and the
other is `test_xlsx_import`'s subject. What is tested is the part that has to be
right when somebody is looking at the output six months from now: that a moved
cell, a renamed sheet, a widened block and a new dropdown entry each come out
named, with the code that has to move with them.
"""

from __future__ import annotations

from typing import Any

from app.xlsx_import._common import SHEET_BASICS, SHEET_CONTACTS, SHEET_WARE
from scripts.template_watch import FORMAT, compare, unmatched

BASE: dict[str, Any] = {
    "format": FORMAT,
    "taken": "2026-09-30",
    "sheets": [SHEET_BASICS, SHEET_WARE, "編集不可"],
    "validations": {SHEET_WARE: {"N4:N33": ["スタンダード", "中古"]}},
    "headers": {f"{SHEET_WARE}!2": {"A": "インプラント", "N": "等級"}},
    "anchors": {f"{SHEET_BASICS}!A3": "メタタイプ"},
    "blocks": {f"{SHEET_CONTACTS}!その他カルマ消費": {"heading": 25, "filled": 26, "styled": 36}},
    "sections": [[3, "技能グループ"]],
    "skills": {"groups": ["近接戦闘"], "skills": ["弓術"]},
}


def _with(**changes: Any) -> dict[str, Any]:
    return {**BASE, **changes}


def _kinds(findings: list[Any]) -> list[str]:
    return [f.kind for f in findings]


def test_nothing_to_do_when_the_sheet_is_unchanged() -> None:
    assert compare(BASE, BASE) == []


def test_a_renamed_required_sheet_names_required_sheets() -> None:
    (finding,) = [
        f for f in compare(BASE, _with(sheets=[SHEET_BASICS, SHEET_WARE, "編集不可2"])) if f.kind == "sheet gone"
    ]
    assert "編集不可" in finding.what
    assert "REQUIRED_SHEETS" in finding.owns


def test_a_moved_column_label_names_the_column_constants() -> None:
    moved = _with(headers={f"{SHEET_WARE}!2": {"A": "インプラント", "M": "等級"}})
    (finding,) = [f for f in compare(BASE, moved) if f.kind == "header changed" and "column N" in f.what]
    assert "WARE_GRADE" in finding.owns


def test_a_moved_anchor_names_the_cells_it_pins() -> None:
    (finding,) = [
        f for f in compare(BASE, _with(anchors={f"{SHEET_BASICS}!A3": "能力値"})) if f.kind == "anchor changed"
    ]
    assert "PRIORITY_CELLS" in finding.owns


def test_a_new_dropdown_entry_is_reported_against_its_mapping_table() -> None:
    added = _with(validations={SHEET_WARE: {"N4:N33": ["スタンダード", "中古", "オメガウェア"]}})
    (finding,) = [f for f in compare(BASE, added) if f.kind == "entry new"]
    assert "オメガウェア" in finding.what
    assert "ware.GRADES" in finding.owns


def test_a_widened_block_is_reported_by_both_measures() -> None:
    wider = _with(blocks={f"{SHEET_CONTACTS}!その他カルマ消費": {"heading": 25, "filled": 26, "styled": 45}})
    findings = [f for f in compare(BASE, wider) if f.kind == "block resized"]
    assert [f.owns for f in findings] == ["contacts.KARMA_OFFSET / KARMA_COUNT"]
    assert "styled" in findings[0].what


def test_a_new_skill_row_points_at_the_aliases() -> None:
    (finding,) = [
        f for f in compare(BASE, _with(skills={**BASE["skills"], "skills": ["弓術", "投擲"]})) if f.kind == "skill new"
    ]
    assert "skills.SKILL_ALIASES" in finding.owns


def test_a_baseline_from_an_older_shape_is_refused_rather_than_diffed() -> None:
    assert _kinds(compare({**BASE, "format": FORMAT - 1}, BASE)) == ["baseline stale"]


def test_an_unmapped_entry_is_found_without_a_baseline() -> None:
    """The point of checking the live sheet against the code, not just against
    the last snapshot: an entry nobody ever handled is reported on the first run."""
    current = _with(validations={SHEET_BASICS: {"C16": ["ヒューマン", "ドラゴン"]}})
    kinds = _kinds(unmatched(current))
    assert "unmapped entry" in kinds
    (finding,) = [f for f in unmatched(current) if f.kind == "unmapped entry"]
    assert "ドラゴン" in finding.what and "カスタム" not in finding.what


def test_reading_past_a_block_is_not_a_finding_but_stopping_short_is() -> None:
    short = _with(blocks={f"{SHEET_CONTACTS}!その他カルマ消費": {"heading": 25, "filled": 26, "styled": 45}})
    assert "block under-read" in _kinds(unmatched(short))
    long = _with(blocks={f"{SHEET_CONTACTS}!その他カルマ消費": {"heading": 25, "filled": 26, "styled": 30}})
    assert "block under-read" not in _kinds(unmatched(long))
