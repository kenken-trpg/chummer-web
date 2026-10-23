"""A quality taken more than once whose pick is a line of text: each take
answers for itself.

Records on File is one megacorp per take (RF), Close Combat Mage one spell;
Chummer asks for the text on every take and saves each `<quality>` with its
own `<extra>`. The first take keeps its text under the quality's id, as
before; the later ones under `<id>:take:<n>`.
"""

import xml.etree.ElementTree as ET

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute, default_attributes, find_metatype
from app.models import CharacterState, Priorities


def _quality_id(name: str) -> str:
    return next(str(row["id"]) for row in catalog()["qualities"] if row["name"] == name)


RECORDS = _quality_id("Records on File")
AMBIDEXTROUS = _quality_id("Ambidextrous")


def _character(quality_ids: list[str], extras: dict[str, str]) -> CharacterState:
    return CharacterState(
        id="per-take",
        name="Ledger",
        metatype="Human",
        priorities=Priorities(Heritage="E", Attributes="A", Talent="E", Skills="B", Resources="C"),
        attributes=default_attributes(find_metatype("Human", None)),
        settings={"books": ["SR5", "RF"]},
        quality_ids=quality_ids,
        quality_extras=extras,
    )


def _rows(state: CharacterState, qid: str) -> list[dict]:
    return [row for row in state.derived["qualities"] if row["id"] == qid]


def _text_warnings(state: CharacterState) -> list[dict]:
    return [w for w in state.derived["warnings"] if w["key"] == "engine.qualities.pickText"]


def test_each_take_shows_its_own_text() -> None:
    state = compute(_character([RECORDS] * 3, {RECORDS: "Ares", f"{RECORDS}:take:1": "Aztechnology"}))
    rows = _rows(state, RECORDS)
    assert [row["extra"] for row in rows] == ["Ares", "Aztechnology", ""]
    assert [row["extra_key"] for row in rows] == [RECORDS, f"{RECORDS}:take:1", f"{RECORDS}:take:2"]
    # still three takes, each paid for
    assert [row["karma"] for row in rows] == [-1, -1, -1]


def test_a_take_without_its_text_is_named() -> None:
    state = compute(_character([RECORDS] * 2, {RECORDS: "Ares"}))
    assert len(_text_warnings(state)) == 1
    filled = compute(_character([RECORDS] * 2, {RECORDS: "Ares", f"{RECORDS}:take:1": "Horizon"}))
    assert _text_warnings(filled) == []


def test_a_take_that_is_gone_takes_its_text_with_it() -> None:
    state = compute(
        _character([RECORDS], {RECORDS: "Ares", f"{RECORDS}:take:1": "Horizon", f"{RECORDS}:take:4": "NeoNET"})
    )
    assert state.quality_extras == {RECORDS: "Ares"}


def test_a_quality_without_a_text_pick_has_no_take_key() -> None:
    state = compute(_character([AMBIDEXTROUS], {}))
    assert "extra_key" not in _rows(state, AMBIDEXTROUS)[0]


def test_the_takes_survive_a_chum5_round_trip() -> None:
    state = compute(_character([RECORDS] * 2, {RECORDS: "Ares", f"{RECORDS}:take:1": "Aztechnology"}))
    root = ET.fromstring(state_to_chum5(state))
    extras = [q.findtext("extra") for q in root.findall("./qualities/quality") if q.findtext("sourceid") == RECORDS]
    assert extras == ["Ares", "Aztechnology"]
    again, _ = chum5_to_state(state_to_chum5(state))
    assert again["quality_ids"].count(RECORDS) == 2
    assert again["quality_extras"][RECORDS] == "Ares"
    assert again["quality_extras"][f"{RECORDS}:take:1"] == "Aztechnology"
