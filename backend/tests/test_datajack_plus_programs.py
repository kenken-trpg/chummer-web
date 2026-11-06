"""A Datajack Plus stores programs (KC p.65): Rating of them, from the
categories its `<allowgear>` names, none of them running there."""

import xml.etree.ElementTree as ET

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.models import CharacterState, CyberwareInstall, GearInstall
from tests.engine_support import _human, _ware_id


def _program(name: str) -> str:
    return next(row["id"] for row in catalog()["programs"] if row["name"] == name)


def _state(rating: int = 2, names: tuple[str, ...] = ("Armor", "Exploit")) -> CharacterState:
    return compute(
        _human(
            "dj",
            cyberware=[CyberwareInstall(id="dj", ware_id=_ware_id("cyberware", "Datajack Plus"), rating=rating)],
            programs=[GearInstall(id=f"p{i}", gear_id=_program(name), parent_id="dj") for i, name in enumerate(names)],
        )
    )


def _jack(state: CharacterState) -> dict:
    return next(row for row in state.derived["cyberware"] if row["id"] == "dj")


def test_the_programs_stay_in_the_jack():
    state = _state()
    jack = _jack(state)
    assert jack["program_max"] == 2
    assert [p["name"] for p in jack["programs"]] == ["Armor", "Exploit"]
    assert all(p["parent_id"] == "dj" and not p["running"] for p in state.derived["programs"])
    assert [p.parent_id for p in state.programs] == ["dj", "dj"]
    assert not [w for w in state.derived["warnings"] if "needsHostKind" in str(w)]


def test_more_programs_than_its_rating_is_warned():
    state = _state(rating=1)
    assert any("programsOver" in str(w) for w in state.derived["warnings"])


def test_a_program_is_paid_for_once():
    with_programs = _state()
    without = compute(
        _human("dj", cyberware=[CyberwareInstall(id="dj", ware_id=_ware_id("cyberware", "Datajack Plus"), rating=2)])
    )
    prices = sum(int(p["nuyen"]) for p in with_programs.derived["programs"])
    assert prices > 0
    assert int(with_programs.derived["nuyen_spent"]) - int(without.derived["nuyen_spent"]) == prices


def test_the_programs_go_out_inside_the_jack_and_come_back():
    state = _state()
    root = ET.fromstring(state_to_chum5(state))
    jack = next(el for el in root.iter("cyberware") if el.findtext("name") == "Datajack Plus")
    assert sorted(g.findtext("name") for g in jack.findall("./gears/gear")) == ["Armor", "Exploit"]
    again = compute(CharacterState.model_validate(chum5_to_state(ET.tostring(root))[0]))
    jack_id = next(row["id"] for row in again.derived["cyberware"] if row["name"] == "Datajack Plus")
    assert sorted(p.gear_id for p in again.programs if p.parent_id == jack_id) == sorted(
        _program(n) for n in ("Armor", "Exploit")
    )
