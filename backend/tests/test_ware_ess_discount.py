"""`<essdiscount>`: a percentage off one ware piece's essence, offered when the
settings file has `<allowcyberwareessdiscounts>` (Neon Anarchy's presets)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute
from app.models import CyberwareInstall, SettingsState
from app.rules import rules_for
from app.settings_file import parse_settings_xml
from tests.engine_support import WIRED, _mundane


def test_the_discount_comes_off_the_pieces_essence() -> None:
    base = compute(_mundane("essd0", cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)]))
    cut = compute(_mundane("essd1", cyberware=[CyberwareInstall(ware_id=WIRED, rating=1, ess_discount=25)]))
    more = compute(_mundane("essd2", cyberware=[CyberwareInstall(ware_id=WIRED, rating=1, ess_discount=-50)]))
    assert base.derived["essence_lost_cyber"] == 2.0
    assert cut.derived["essence_lost_cyber"] == 1.5
    assert more.derived["essence_lost_cyber"] == 3.0
    assert cut.derived["cyberware"][0]["ess_discount"] == 25


def test_the_discount_is_bounded_like_chummers() -> None:
    with pytest.raises(ValidationError):
        CyberwareInstall(ware_id=WIRED, ess_discount=101)


def test_the_discount_survives_a_chum5_round_trip() -> None:
    state = _mundane("essd3", cyberware=[CyberwareInstall(ware_id=WIRED, rating=1, ess_discount=30)])
    xml = state_to_chum5(state)
    assert b"<essdiscount>30</essdiscount>" in (xml if isinstance(xml, bytes) else xml.encode())
    back, _ = chum5_to_state(xml if isinstance(xml, bytes) else xml.encode())
    assert back["cyberware"][0]["ess_discount"] == 30


def test_the_setting_is_read_and_offered_to_the_sheet() -> None:
    parsed = parse_settings_xml(
        "<settings><name>N</name><allowcyberwareessdiscounts>True</allowcyberwareessdiscounts></settings>"
    )
    assert parsed.allow_cyberware_ess_discounts is True
    assert "allowcyberwareessdiscounts" not in parsed.unsupported
    assert rules_for(parsed).allow_cyberware_ess_discounts is True
    state = _mundane("essd4")
    assert compute(state).derived["allow_ess_discounts"] is False
    state.settings = SettingsState(allow_cyberware_ess_discounts=True)
    assert compute(state).derived["allow_ess_discounts"] is True
