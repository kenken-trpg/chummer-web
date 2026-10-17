"""Commlinks and decks implanted in headware (SR5 p.451-452).

The headware `Commlink` and `Cyberdeck` hold one device each of the category
their `<allowgear>` names. The device keeps its own bucket and price; its
`parent_id` names the implant, and a .chum5 carries it in the implant's
`<gears>`, where Chummer keeps it. See `app/engine/gear/implants.py`.
"""

import xml.etree.ElementTree as ET

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute, default_attributes, find_metatype
from app.models import CharacterState, CommlinkInstall, CyberwareInstall, GearInstall, Priorities
from tests.notice_asserts import has


def _id(bucket: str, name: str) -> str:
    rows = catalog()[bucket]
    rows = rows["items"] if isinstance(rows, dict) else rows
    return next(str(row["id"]) for row in rows if row["name"] == name)


def _runner(**kwargs: object) -> CharacterState:
    return CharacterState(
        id="runner",
        name="Joe",
        metatype="Human",
        priorities=Priorities(Heritage="E", Attributes="B", Talent="C", Skills="D", Resources="A"),
        attributes=default_attributes(find_metatype("Human", None)),
        **kwargs,  # type: ignore[arg-type]
    )


def _implanted_commlink(housing: str = "Commlink") -> CharacterState:
    return _runner(
        cyberware=[CyberwareInstall(id="head", ware_id=_id("cyberware", housing))],
        commlinks=[CommlinkInstall(id="link", gear_id=_id("commlinks", "Hermes Ikon"), parent_id="head")],
    )


def _spent(out: CharacterState, key: str) -> int:
    lines = {row["notice"]["key"]: row["amount"] for row in out.derived["nuyen_spend_breakdown"]}
    return int(lines.get(key, 0))


# --- the engine -----------------------------------------------------------------


def test_a_commlink_sits_in_the_headware_that_houses_one() -> None:
    out = compute(_implanted_commlink())
    row = out.derived["commlinks"][0]
    assert row["implanted_in"] == "Commlink"
    assert row["parent_id"] == "head"
    assert out.commlinks[0].parent_id == "head"
    assert not has(out.derived["warnings"], "engine.gear.doesNotFit")


def test_the_implanted_commlink_is_priced_as_a_commlink() -> None:
    # Chummer adds the device's own cost to the implant's, unmultiplied by the
    # grade: the total is the same as the commlink's own line here
    carried = compute(_runner(commlinks=[CommlinkInstall(gear_id=_id("commlinks", "Hermes Ikon"))]))
    implanted = compute(_implanted_commlink())
    assert _spent(implanted, "engine.spend.commlinks") == _spent(carried, "engine.spend.commlinks") > 0


def test_a_deck_sits_in_the_headware_cyberdeck() -> None:
    state = _runner(
        cyberware=[CyberwareInstall(id="head", ware_id=_id("cyberware", "Cyberdeck"))],
        cyberdecks=[GearInstall(id="deck", gear_id=_id("cyberdecks", "Erika MCD-1"), parent_id="head")],
    )
    out = compute(state)
    assert out.derived["cyberdecks"][0]["implanted_in"] == "Cyberdeck"


def test_an_implant_that_holds_no_commlink_carries_it_instead() -> None:
    out = compute(_implanted_commlink("Datajack"))
    assert has(out.derived["warnings"], "engine.gear.doesNotFit")
    assert out.commlinks[0].parent_id is None
    assert "implanted_in" not in out.derived["commlinks"][0]


def test_a_deck_in_a_carried_container_is_left_alone() -> None:
    # only a parent that is ware is an implant; a briefcase is the gear writer's
    case = GearInstall(id="case", gear_id=_id("gear", "Hard-Shell Briefcase"))
    state = _runner(
        gear=[case],
        cyberdecks=[GearInstall(id="deck", gear_id=_id("cyberdecks", "Erika MCD-1"), parent_id="case")],
    )
    out = compute(state)
    assert out.cyberdecks[0].parent_id == "case"
    assert "implanted_in" not in out.derived["cyberdecks"][0]


# --- .chum5 -------------------------------------------------------------------


def test_the_implanted_commlink_survives_a_round_trip() -> None:
    first = compute(_implanted_commlink())
    xml = state_to_chum5(first)
    root = ET.fromstring(xml)
    housing = next(w for w in root.iter("cyberware") if w.findtext("name") == "Commlink")
    assert [g.findtext("name") for g in housing.findall("./gears/gear")] == ["Hermes Ikon"]
    assert "Hermes Ikon" not in [g.findtext("name") for g in root.findall("./gears/gear")]

    again, notices = chum5_to_state(xml)
    assert not [n for n in notices if n["key"] == "engine.import.hostGearSkipped"]
    second = compute(CharacterState(**again))
    assert [row["implanted_in"] for row in second.derived["commlinks"]] == ["Commlink"]
    assert second.commlinks[0].parent_id == second.cyberware[0].id
    assert _spent(second, "engine.spend.commlinks") == _spent(first, "engine.spend.commlinks")


def test_an_implanted_commlink_can_be_an_ais_home_node() -> None:
    # the device is a commlink like any other, so the mark goes on it and
    # comes back from the implant's `<gears>`
    from tests.test_ai_chargen import _ai

    state = _ai("E-Ghost")
    implanted = _implanted_commlink()
    state.cyberware, state.commlinks = implanted.cyberware, implanted.commlinks
    state.home_node = "link"
    first = compute(state)
    assert first.derived["home_node"]["name"] == "Hermes Ikon"
    again, _ = chum5_to_state(state_to_chum5(first))
    second = compute(CharacterState(**again))
    assert second.derived["home_node"]["name"] == "Hermes Ikon"
    assert second.home_node == second.commlinks[0].id
