"""Career mode: rewards, raises, qualities taken after chargen, street cred."""

from app.data_loader import catalog
from app.engine import (
    compute,
)
from app.models import (
    GearInstall,
    SettingsState,
)
from tests.engine_support import (
    BLANDNESS,
    _career_quality,
    _into_career,
    _mundane,
    _quality_row,
)
from tests.notice_asserts import has


def test_career_mode_skips_avail_limit() -> None:
    from app.data_loader import catalog, parse_avail

    high = None
    for g in catalog()["gear"]:
        if g.get("requireparent"):
            continue
        parsed = parse_avail(str(g.get("avail") or "0"))
        value = parsed[0] if isinstance(parsed, (tuple, list)) else int(parsed or 0)
        if value > 12:
            high = g
            break
    assert high is not None
    gear = [GearInstall(gear_id=high["id"])]
    charged = compute(_mundane("career-avail-cg", gear=gear))
    assert has(charged.derived["errors"], "engine.gear.availOver")
    career = compute(_mundane("career-avail", career=True, gear=gear, nuyen_earned=10_000_000))
    assert not has(career.derived["errors"], "engine.gear.availOver")
    assert career.derived["avail_limit"] is None
    assert career.derived["career"] is True
    assert career.derived["nuyen"] == career.derived["nuyen_pool"] - career.derived["nuyen_spent"]


def test_career_priority_attribute_raise_uses_new_rating_times_5() -> None:
    from app.engine import snapshot_career_baseline

    st = _mundane("career-agi")
    st.attributes["AGI"] = 4
    st = compute(st)
    st.career = True
    st.career_baseline = snapshot_career_baseline(st)
    st.attributes["AGI"] = 5
    out = compute(st)
    assert out.derived["career_advancement_karma"] == 25
    assert out.derived["karma"]["spent"] == 25
    assert out.derived["karma"]["remaining"] == 0
    assert out.derived["skill_rating_max"] == 12


def test_career_earned_rewards_expand_pools() -> None:
    # Priority Resources D = 50_000¥; chargen karma pool = 25
    out = compute(_mundane("career-earn", career=True, karma_earned=40, nuyen_earned=5000))
    assert out.derived["karma"]["pool"] == 65
    assert out.derived["nuyen_pool"] == 55_000


JACK_OF_ALL_TRADES = "624fa943-c0a1-44ee-8cd8-3aef4bea3f4b"


def test_jack_of_all_trades_adjusts_career_active_skill_karma() -> None:
    from app.engine import snapshot_career_baseline

    base = compute(_mundane("joat0", skills={"Pistols": 4}))
    base.career = True
    base.career_baseline = snapshot_career_baseline(base)
    base.skills = {**dict(base.skills), "Pistols": 5}
    without = compute(base)

    st = compute(_mundane("joat1", quality_ids=[JACK_OF_ALL_TRADES], skills={"Pistols": 4}))
    st.career = True
    st.career_baseline = snapshot_career_baseline(st)
    st.skills = {**dict(st.skills), "Pistols": 5}
    with_q = compute(st)
    assert without.derived["career_advancement_karma"] == 10
    assert with_q.derived["career_advancement_karma"] == 9

    st.skills = {**dict(st.skills), "Pistols": 6}
    high = compute(st)
    # 4→5:9 + 5→6:14 = 23
    assert high.derived["career_advancement_karma"] == 23


def test_career_street_cred_and_public_awareness() -> None:
    out = compute(
        _mundane(
            "rep",
            career=True,
            street_cred=7,
            notoriety_bonus=2,
            quality_ids=[BLANDNESS],
        )
    )
    # quality -1 + bonus 2 = 1. Public Awareness is not earned from these
    # under Chummer's own presets: `<usecalculatedpublicawareness>` is off.
    assert out.derived["street_cred"] == 7
    assert out.derived["notoriety"] == 1
    assert out.derived["public_awareness"] == 0


def test_public_awareness_is_what_the_gm_awarded() -> None:
    """Chummer stores `<publicawareness>` as a counter the GM moves, and adds
    what qualities give. It is not worked out from Street Cred."""
    out = compute(_mundane("pa", career=True, street_cred=7, public_awareness=2))
    assert out.derived["public_awareness"] == 2


def test_the_house_rule_earns_public_awareness_from_street_cred() -> None:
    """`<usecalculatedpublicawareness>`: a point per three of Street Cred
    and Notoriety, on top of the GM's award (Chummer's
    `CalculatedPublicAwareness`)."""
    state = _mundane(
        "pa-rule", career=True, street_cred=7, notoriety_bonus=2, quality_ids=[BLANDNESS], public_awareness=1
    )
    state.settings = SettingsState(use_calculated_public_awareness=True)
    out = compute(state)
    # (7 + 1) // 3 = 2, plus the 1 awarded
    assert out.derived["public_awareness"] == 3


def test_career_reward_log_sets_earned_totals() -> None:
    from app.models import RewardEntry

    out = compute(
        _mundane(
            "rewards",
            career=True,
            reward_log=[
                RewardEntry(label="Run A", karma=6, nuyen=4000),
                RewardEntry(label="Run B", karma=4, nuyen=1000),
            ],
        )
    )
    assert out.derived["karma_earned"] == 10
    assert out.derived["nuyen_earned"] == 5000
    assert out.derived["karma"]["pool"] == 35
    assert len(out.derived["reward_log"]) == 2


def test_career_spend_breakdown_lists_attribute_raise() -> None:
    from app.engine import snapshot_career_baseline

    st = _mundane("break")
    st.attributes["AGI"] = 4
    st = compute(st)
    st.career = True
    st.career_baseline = snapshot_career_baseline(st)
    st.attributes["AGI"] = 5
    out = compute(st)
    assert out.derived["career_advancement_karma"] == 25
    assert has(
        [row["notice"] for row in out.derived["career_advancement_lines"]],
        "engine.spend.attribute",
        name="AGI",
        after=5,
    )
    assert any(row["amount"] == 25 for row in out.derived["career_advancement_lines"])
    assert any(row["amount"] == 25 for row in out.derived["karma_spend_breakdown"])


def test_a_positive_quality_taken_in_career_costs_twice() -> None:
    """SR5 p.107: after chargen a positive quality costs twice its karma."""
    amb = _career_quality("Ambidextrous")
    st = _into_career("career-pos", [])
    before = compute(st).derived["karma"]["remaining"]
    st.quality_ids = [amb["id"]]
    out = compute(st).derived
    assert out["quality_career_pricing"] is True
    assert _quality_row(out, "Ambidextrous")["career_cost"] == amb["karma"] * 2
    assert before - out["karma"]["remaining"] == amb["karma"] * 2
    line = next(row for row in out["karma_spend_breakdown"] if row["notice"]["key"] == "engine.spend.qualitiesCareer")
    assert line["amount"] == amb["karma"]


def test_a_negative_quality_taken_in_career_gives_no_karma() -> None:
    bad = _career_quality("Bad Luck")
    st = _into_career("career-neg", [])
    before = compute(st).derived["karma"]["remaining"]
    st.quality_ids = [bad["id"]]
    out = compute(st).derived
    assert _quality_row(out, "Bad Luck")["career_cost"] == 0
    assert out["karma"]["remaining"] == before


def test_a_chargen_positive_dropped_in_career_is_not_refunded() -> None:
    amb = _career_quality("Ambidextrous")
    st = _into_career("career-drop", [amb["id"]])
    held = compute(st).derived
    st.quality_ids = []
    out = compute(st).derived
    assert out["karma"]["remaining"] == held["karma"]["remaining"]
    assert out["qualities_removed"][0]["karma"] == 0


def test_doublecareer_false_takes_the_single_price_in_career() -> None:
    single = next(
        q
        for q in catalog()["qualities"]
        if q.get("double_career") is False and q["category"] == "Positive" and q["karma"] > 0
    )
    st = _into_career("career-single", [])
    before = compute(st).derived["karma"]["remaining"]
    st.quality_ids = [single["id"]]
    out = compute(st).derived
    assert before - out["karma"]["remaining"] == single["karma"]


def test_a_baseline_saved_before_qualities_keeps_chargen_prices() -> None:
    amb = _career_quality("Ambidextrous")
    st = _into_career("career-old", [])
    before = compute(st).derived["karma"]["remaining"]
    st.career_baseline.quality_ids = None
    st.quality_ids = [amb["id"]]
    out = compute(st).derived
    assert out["quality_career_pricing"] is False
    assert before - out["karma"]["remaining"] == amb["karma"]
    assert "career_cost" not in _quality_row(out, "Ambidextrous")


def test_taking_the_current_qualities_as_chargen_cancels_career_charges() -> None:
    """The Qualities tab's reset: patching the baseline's quality list to the
    current one drops the buy-off and the ×2 purchase."""
    from app.characters import apply_patch
    from app.models import CharacterPatch

    amb = _career_quality("Ambidextrous")
    bad = _career_quality("Bad Luck")
    st = _into_career("career-reset", [bad["id"]])
    clean = compute(st).derived["karma"]["remaining"]
    st.quality_ids = [amb["id"]]
    charged = compute(st)
    assert charged.derived["qualities_removed"]
    baseline = charged.career_baseline.model_dump()
    out = apply_patch(charged, CharacterPatch(career_baseline={**baseline, "quality_ids": [amb["id"]]})).derived
    assert out["qualities_removed"] == []
    assert "career_cost" not in _quality_row(out, "Ambidextrous")
    # held at the chargen price now: Bad Luck's gain and Ambidextrous at ×1
    assert out["karma"]["remaining"] == clean + bad["karma"] - amb["karma"]


def test_street_cred_is_earned_from_career_karma() -> None:
    """SR5 p.372: one point per 10 karma earned, plus the table's own
    adjustment; Consummate Professional (AP p.17) makes it 20 karma a point."""
    st = _into_career("sc", [])
    st.karma_earned = 25
    st.street_cred = 3
    out = compute(st).derived
    assert (out["street_cred_earned"], out["street_cred_divisor"], out["street_cred"]) == (2, 10, 5)

    st.quality_ids = [_career_quality("Consummate Professional")["id"]]
    out = compute(st).derived
    assert (out["street_cred_earned"], out["street_cred_divisor"], out["street_cred"]) == (1, 20, 4)


def test_street_cred_outside_career_is_only_the_adjustment() -> None:
    st = compute(_mundane("sc-chargen"))
    st.karma_earned = 40
    st.street_cred = 2
    out = compute(st).derived
    assert (out["street_cred_earned"], out["street_cred"]) == (0, 2)


def test_burning_street_cred_takes_notoriety_off_two_for_one() -> None:
    """SR5 p.373 (Chummer `BurntStreetCred`): burned points leave Street Cred,
    and every two of them take a point of Notoriety with them."""
    st = _into_career("burn", [])
    st.karma_earned = 50
    st.notoriety_bonus = 3
    before = compute(st).derived
    assert (before["street_cred"], before["notoriety"]) == (5, 3)
    st.burnt_street_cred = 4
    out = compute(st).derived
    assert (out["street_cred"], out["notoriety"], out["street_cred_burnt"]) == (1, 1, 4)


def test_burnt_street_cred_round_trips_through_chum5() -> None:
    from app.chummer_export import state_to_chum5
    from app.chummer_import import chum5_to_state

    st = _into_career("burn-io", [])
    st.street_cred = 6
    st.burnt_street_cred = 2
    back, _skipped = chum5_to_state(state_to_chum5(compute(st)))
    assert (back["street_cred"], back["burnt_street_cred"]) == (6, 2)


def test_the_house_rule_charges_career_qualities_once() -> None:
    """`<dontdoublequalities>`: a positive quality taken in play costs its
    table karma (Chummer skips the ×2 when the setting is on)."""
    amb = _career_quality("Ambidextrous")
    st = _into_career("career-once", [])
    st.settings = SettingsState(dont_double_quality_purchases=True)
    before = compute(st).derived["karma"]["remaining"]
    st.quality_ids = [amb["id"]]
    out = compute(st).derived
    assert _quality_row(out, "Ambidextrous")["career_cost"] == amb["karma"]
    assert before - out["karma"]["remaining"] == amb["karma"]


def test_the_house_rule_buys_off_negatives_once() -> None:
    """`<dontdoublequalityrefunds>`: buying a negative quality off costs the
    karma it gave, not twice it."""
    bad = _career_quality("Bad Luck")
    st = _into_career("career-refund", [bad["id"]])
    st.settings = SettingsState(dont_double_quality_refunds=True)
    held = compute(st).derived["karma"]["remaining"]
    st.quality_ids = []
    out = compute(st).derived
    assert out["qualities_removed"][0]["karma"] == -bad["karma"]
    assert held - out["karma"]["remaining"] == -bad["karma"]


def _weapon_named(name: str) -> dict:
    return next(w for w in catalog()["weapons"] if w["name"] == name)


def _career_with_predators(settings: SettingsState | None, *, old: int, new: int) -> dict:
    """`old` Ares Predator Vs (5R) owned at chargen, then `new` more bought."""
    from app.engine import snapshot_career_baseline
    from app.models import WeaponInstall

    predator = _weapon_named("Ares Predator V")["id"]
    st = _mundane("markup", career=True, nuyen_earned=100_000)
    st.weapons = [WeaponInstall(weapon_id=predator) for _ in range(old)]
    st.career_baseline = snapshot_career_baseline(st)
    st.weapons += [WeaponInstall(weapon_id=predator) for _ in range(new)]
    if settings is not None:
        st.settings = settings
    return compute(st).derived


def test_restricted_items_bought_in_career_cost_the_house_multiplier() -> None:
    """`<multiplyrestrictedcost>` ×3: the pistol bought after chargen costs
    725 ¥ × 3; the one carried in from chargen stays at list price."""
    rule = SettingsState(multiply_restricted_cost=True, restricted_cost_multiplier=3)
    plain = _career_with_predators(None, old=1, new=1)
    marked = _career_with_predators(rule, old=1, new=1)
    assert marked["nuyen_spent"] - plain["nuyen_spent"] == 725 * 2
    assert any(line["amount"] == 1450 for line in marked["nuyen_spend_breakdown"])


def test_the_multiplier_is_off_unless_the_switch_is_on() -> None:
    """A multiplier without `<multiplyrestrictedcost>` does nothing, and a
    forbidden multiplier leaves a Restricted pistol alone."""
    plain = _career_with_predators(None, old=0, new=1)
    for rule in (
        SettingsState(restricted_cost_multiplier=3),
        SettingsState(multiply_forbidden_cost=True, forbidden_cost_multiplier=3),
    ):
        assert _career_with_predators(rule, old=0, new=1)["nuyen_spent"] == plain["nuyen_spent"]
