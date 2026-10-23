"""Essence loss lowers the minimum of MAG / RES, and what was bought stacks on it.

Chummer's create-mode essence loss is an improvement on both the minimum and
the maximum (`Character` "RAW Create mode"), and an attribute's value and
karma price count from `Base + FreeBase + RawMinimum` with the minimum
clamped at zero (`TotalBase`, `TotalKarmaCost`). So the karma levels of a
cyber-laden adept are the cheap ones, and a loss deeper than the talent's
minimum does not take the levels bought above it.

The saves this matches: `Gangerbean` (adept, ESS 1, MAG 2 + 1 karma level:
MAG 1 for 5 karma), `SCSi` and `Bastion` (technomancers, ESS 1, RES 3 + 1:
RES 1 for 5).
"""

from app.engine import compute, snapshot_career_baseline
from app.models import CharacterState, CyberwareInstall, SettingsState
from tests.engine_support import DATAJACK, WIRED, _adept


def _attr_karma(derived: dict) -> int:
    rows = derived["karma_spend_breakdown"]
    return sum(r["amount"] for r in rows if r["notice"]["key"] == "engine.spend.attributesKarma")


def _bought_one_level(ware: CyberwareInstall, **kwargs: object) -> dict:
    # Talent D: the adept's MAG starts at 2; one karma level takes it to 3
    state = _adept("ess", "D", cyberware=[ware], **kwargs)
    state.attributes = {**state.attributes, "MAG": 3}
    state.attribute_karma = {"MAG": 1}
    return compute(state).derived


def test_a_loss_past_the_minimum_keeps_the_level_bought() -> None:
    # Wired Reflexes 3: ESS 1, five points off a minimum of 2
    out = _bought_one_level(CyberwareInstall(ware_id=WIRED, rating=3))
    assert out["essence"] == 1
    assert out["totals"]["MAG"] == 1
    # the level is MAG 1 now, not MAG 3
    assert _attr_karma(out) == 5


def test_the_range_the_loss_left_is_shown_beside_the_bought_one() -> None:
    # Wired Reflexes 2: ESS 3, three points off a range of 2-6
    out = _bought_one_level(CyberwareInstall(ware_id=WIRED, rating=2))
    mag = out["metatype_info"]["attributes"]["MAG"]
    assert (mag["min"], mag["max"]) == (2, 6)
    assert (mag["ess_min"], mag["ess_max"]) == (0, 3)
    assert "ess_max" not in out["metatype_info"]["attributes"]["BOD"]


def test_no_loss_adds_no_range() -> None:
    state = _adept("ess-none", "D")
    assert "ess_max" not in compute(state).derived["metatype_info"]["attributes"]["MAG"]


def test_a_shallow_loss_lowers_the_price_and_the_rating_alike() -> None:
    # a Datajack's 0.1 costs one point: the minimum falls from 2 to 1
    out = _bought_one_level(CyberwareInstall(ware_id=DATAJACK))
    assert out["totals"]["MAG"] == 2
    assert _attr_karma(out) == 10


def test_under_maximum_only_a_shallow_loss_leaves_the_minimum() -> None:
    out = _bought_one_level(
        CyberwareInstall(ware_id=DATAJACK), settings=SettingsState(ess_loss_reduces_maximum_only=True)
    )
    assert out["totals"]["MAG"] == 3
    assert _attr_karma(out) == 15


def test_a_karma_build_prices_from_the_lowered_minimum_too() -> None:
    state = _adept("ess-karma", "D", build_method="Karma")
    state.attributes = {**state.attributes, "MAG": 3}
    plain = compute(state).derived
    state.cyberware = [CyberwareInstall(ware_id=WIRED, rating=2)]
    wired = compute(state).derived
    # MAG 1 -> 3 is 10 + 15; ESS 3 takes the minimum to 0, so 5 + 10 for MAG 2
    assert (plain["totals"]["MAG"], _attr_karma(plain)) == (3, 25)
    assert (wired["totals"]["MAG"], _attr_karma(wired)) == (2, 15)


def _career_adept(cyberware: list[CyberwareInstall]) -> CharacterState:
    state = _adept("ess-career", "D", cyberware=cyberware)
    state.attributes = {**state.attributes, "MAG": 3}
    state.attribute_karma = {"MAG": 1}
    state = compute(state)
    state.career = True
    state.career_baseline = snapshot_career_baseline(state)
    return state


def test_a_career_raise_is_priced_from_the_value_after_the_loss() -> None:
    # Wired Reflexes 2: ESS 3, MAG 3 bought stands at 1
    state = compute(_career_adept([CyberwareInstall(ware_id=WIRED, rating=2)]))
    assert state.career_baseline is not None
    assert state.career_baseline.special_drop == {"MAG": 2}
    state.attributes = {**state.attributes, "MAG": 4}
    out = compute(state)
    assert out.derived["totals"]["MAG"] == 2
    # Chummer's UpgradeKarmaCost: (1 + 1) x 5, not the bought 4 x 5
    assert out.derived["career_advancement_karma"] == 10


def test_cyberware_after_a_raise_gives_no_karma_back() -> None:
    state = compute(_career_adept([]))
    state.attributes = {**state.attributes, "MAG": 4}
    raised = compute(state)
    assert raised.derived["career_advancement_karma"] == 20
    raised.cyberware = [CyberwareInstall(ware_id=DATAJACK)]
    out = compute(raised)
    assert out.derived["totals"]["MAG"] == 3
    assert out.derived["career_advancement_karma"] == 20
