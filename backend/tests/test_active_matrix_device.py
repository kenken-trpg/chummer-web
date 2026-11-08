"""The persona a character runs — Chummer's active commlink.

Chummer keeps one device marked `<active>` (`Character.ActiveCommlink`), and
the Matrix initiative and the sheet's Matrix attributes come from it. A player
marks the device they carry, which need not be the best one they own: 4 of
Chummer's 34 test saves run something else (resub's Meta Link beside an
LT-2100, Serpent's Meta Link beside a deck). With no pick this app runs the
persona with the highest Data Processing, as before.
"""

import xml.etree.ElementTree as ET

from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute
from app.models import CharacterPatch, CharacterState, CommlinkInstall, GearInstall
from tests.engine_support import ERIKA_DECK, META_LINK, _mundane, _techno

TRANSYS_AVALON = "01077e2d-4f67-428a-850d-250faad2007c"


def _two_links(**kwargs: object) -> CharacterState:
    return _mundane(
        "two-links",
        commlinks=[CommlinkInstall(gear_id=META_LINK), CommlinkInstall(gear_id=TRANSYS_AVALON)],
        **kwargs,
    )


def _active_names(xml: bytes) -> list[str]:
    return [
        str(g.findtext("name"))
        for g in ET.fromstring(xml).iter("gear")
        if (g.findtext("active") or "").lower() == "true"
    ]


def test_with_no_pick_the_best_device_is_run() -> None:
    out = compute(_two_links())
    assert out.derived["commlink"]["name"] == "Transys Avalon"
    assert out.derived["matrix_initiative"]["device"] == "commlink"
    assert out.derived["matrix_initiative"]["dataprocessing"] == out.derived["commlink"]["dataprocessing"]


def test_the_picked_commlink_is_the_one_run_and_shown() -> None:
    state = _two_links()
    state.active_matrix_device = state.commlinks[0].id
    out = compute(state)
    meta = next(row for row in out.derived["commlinks"] if row["name"] == "Meta Link")
    assert out.derived["commlink"]["id"] == meta["id"]
    mi = out.derived["matrix_initiative"]
    assert mi["device"] == "commlink"
    assert mi["dataprocessing"] == meta["dataprocessing"]
    assert mi["value"] == meta["dataprocessing"] + out.derived["totals"]["INT"]


def test_a_picked_commlink_wins_over_a_deck_with_more_data_processing() -> None:
    link = CommlinkInstall(gear_id=META_LINK)
    state = _mundane("link-and-deck", commlinks=[link], cyberdecks=[GearInstall(gear_id=ERIKA_DECK)])
    assert compute(state).derived["matrix_initiative"]["device"] == "cyberdeck"
    state.active_matrix_device = link.id
    assert compute(state).derived["matrix_initiative"]["device"] == "commlink"


def test_a_pick_of_something_no_longer_owned_falls_back_to_the_best() -> None:
    state = _two_links(active_matrix_device="gone")
    out = compute(state)
    assert out.derived["commlink"]["name"] == "Transys Avalon"
    assert out.derived["matrix_initiative"]["device"] == "commlink"


def test_a_technomancer_can_run_a_commlink_instead_of_their_persona() -> None:
    link = CommlinkInstall(gear_id=META_LINK)
    state = _techno("techno-link", commlinks=[link])
    assert compute(state).derived["matrix_initiative"]["device"] == "living_persona"
    state.active_matrix_device = link.id
    assert compute(state).derived["matrix_initiative"]["device"] == "commlink"
    state.active_matrix_device = "living_persona"
    assert compute(state).derived["matrix_initiative"]["device"] == "living_persona"


def test_living_persona_is_ignored_for_someone_without_one() -> None:
    out = compute(_two_links(active_matrix_device="living_persona"))
    assert out.derived["matrix_initiative"]["device"] == "commlink"
    assert out.derived["commlink"]["name"] == "Transys Avalon"


def test_the_patch_sets_and_clears_the_pick() -> None:
    state = _two_links()
    picked = apply_patch(state, CharacterPatch(active_matrix_device=state.commlinks[0].id))
    assert picked.derived["commlink"]["name"] == "Meta Link"
    cleared = apply_patch(picked, CharacterPatch(active_matrix_device=""))
    assert cleared.active_matrix_device == ""
    assert cleared.derived["commlink"]["name"] == "Transys Avalon"


def test_the_pick_survives_a_chum5_round_trip() -> None:
    state = _two_links()
    state.active_matrix_device = state.commlinks[0].id
    xml = state_to_chum5(compute(state))
    assert _active_names(xml) == ["Meta Link"]
    again, _ = chum5_to_state(xml)
    second = compute(CharacterState(**again))
    meta = next(row for row in second.commlinks if row.id == second.active_matrix_device)
    assert meta.gear_id == META_LINK
    assert second.derived["commlink"]["name"] == "Meta Link"


def test_a_technomancers_commlink_pick_survives_a_round_trip() -> None:
    link = CommlinkInstall(gear_id=META_LINK)
    state = _techno("techno-trip", commlinks=[link])
    assert _active_names(state_to_chum5(compute(state))) == ["Living Persona"]
    state.active_matrix_device = link.id
    xml = state_to_chum5(compute(state))
    assert _active_names(xml) == ["Meta Link"]
    again, _ = chum5_to_state(xml)
    assert compute(CharacterState(**again)).derived["matrix_initiative"]["device"] == "commlink"


def test_an_active_living_persona_is_read_back() -> None:
    link = CommlinkInstall(gear_id=TRANSYS_AVALON)
    state = _techno("techno-persona", commlinks=[link], active_matrix_device="living_persona")
    xml = state_to_chum5(compute(state))
    assert _active_names(xml) == ["Living Persona"]
    again, _ = chum5_to_state(xml)
    assert again["active_matrix_device"] == "living_persona"


def test_no_pick_stays_no_pick_across_a_round_trip() -> None:
    """The export still marks the best device, for Chummer, but says it chose
    it itself (`<autoactive>`), so reading it back leaves the pick unset."""
    xml = state_to_chum5(compute(_two_links()))
    assert _active_names(xml) == ["Transys Avalon"]
    again, _ = chum5_to_state(xml)
    assert again.get("active_matrix_device", "") == ""


def test_a_mark_chummer_saved_again_is_read_as_the_pick() -> None:
    """Chummer drops `<autoactive>` when it saves; the mark it keeps is then
    the active commlink it shows, and reads back as the player's pick."""
    root = ET.fromstring(state_to_chum5(compute(_two_links())))
    for el in root.iter("gear"):
        auto = el.find("autoactive")
        if auto is not None:
            el.remove(auto)
    again, _ = chum5_to_state(ET.tostring(root))
    second = compute(CharacterState(**again))
    picked = next(row for row in second.commlinks if row.id == second.active_matrix_device)
    assert picked.gear_id == TRANSYS_AVALON
