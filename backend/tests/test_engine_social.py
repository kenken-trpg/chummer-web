"""Contacts, lifestyles and notoriety."""

from app.engine import (
    compute,
)
from app.models import (
    ContactInstall,
    LifestyleInstall,
    SettingsState,
)
from tests.engine_support import (
    LIFESTYLE_CRAMPED,
    LIFESTYLE_GYM,
    LOW_LIFESTYLE,
    MEDIUM_LIFESTYLE,
    NOVACOKE,
    _drug_state,
    _human,
    _mundane,
)
from tests.notice_asserts import has

LUXURY_LIFESTYLE = "4b513ac9-9eb3-471b-931b-839a04873b84"


def test_low_lifestyle_one_month() -> None:
    out = compute(_mundane("low-life", lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, months=1)]))
    assert out.derived["nuyen_spent"] == 2000
    assert out.derived["lifestyle"]["name"] == "Low"
    assert out.derived["errors"] == []


def test_low_lifestyle_two_months() -> None:
    out = compute(_mundane("low-life-2", lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, months=2)]))
    assert out.derived["nuyen_spent"] == 4000


def test_luxury_lifestyle_exceeds_resources() -> None:
    out = compute(_mundane("luxury", lifestyles=[LifestyleInstall(lifestyle_id=LUXURY_LIFESTYLE, months=1)]))
    assert out.derived["nuyen_spent"] == 100000
    assert has(out.derived["errors"], "engine.nuyen.negative")


def test_contact_free_points_are_charisma_times_three() -> None:
    out = compute(_human("contact-free"))
    assert out.derived["totals"]["CHA"] == 1
    assert out.derived["contact_points"]["used"] == 0
    assert out.derived["contact_points"]["free"] == 3
    assert out.derived["contact_points"]["paid"] == 0
    assert out.derived["contact_points"]["karma"] == 0
    assert out.derived["contact_points"]["karma_per_point"] == 1
    assert out.derived["points"]["contacts"] == {"used": 0, "max": 3}
    high = _human("contact-cha3")
    high.attributes["CHA"] = 3
    high_out = compute(high)
    assert high_out.derived["contact_points"]["free"] == 9
    assert high_out.derived["karma"]["remaining"] == 25


def test_contact_spends_free_points_before_karma() -> None:
    out = compute(
        _human(
            "contact-free-spend",
            contacts=[ContactInstall(name="Fixer", role="Fixer", connection=2, loyalty=1)],
        )
    )
    row = out.derived["contacts"][0]
    assert row["name"] == "Fixer"
    assert row["role"] == "Fixer"
    assert row["connection"] == 2
    assert row["loyalty"] == 1
    assert row["cost"] == 3
    assert out.derived["contact_points"]["used"] == 3
    assert out.derived["contact_points"]["free"] == 3
    assert out.derived["contact_points"]["paid"] == 0
    assert out.derived["karma"]["remaining"] == 25
    assert out.derived["errors"] == []


def test_contact_overspend_costs_karma() -> None:
    state = _human("contact-paid")
    state.attributes["CHA"] = 3
    state.contacts = [
        ContactInstall(name="Fixer", connection=4, loyalty=3),
        ContactInstall(name="Street Doc", connection=2, loyalty=2),
    ]
    out = compute(state)
    assert out.derived["contact_points"]["used"] == 11
    assert out.derived["contact_points"]["free"] == 9
    assert out.derived["contact_points"]["paid"] == 2
    assert out.derived["contact_points"]["karma"] == 2
    assert out.derived["karma"]["spent"] == 2
    assert out.derived["karma"]["remaining"] == 23


def test_contact_chargen_cost_is_capped_at_seven() -> None:
    out = compute(_human("contact-cap", contacts=[ContactInstall(name="Mr. Johnson", connection=6, loyalty=6)]))
    row = out.derived["contacts"][0]
    assert row["connection"] == 6
    assert row["loyalty"] == 1
    assert row["cost"] == 7
    assert has(out.derived["warnings"], "engine.contacts.pairMax", max=7)


def test_unnamed_contact_is_warned() -> None:
    out = compute(_human("contact-noname", contacts=[ContactInstall(connection=1, loyalty=1)]))
    assert has(out.derived["warnings"], "engine.contacts.unnamed")
    assert out.derived["contact_points"]["used"] == 2


def test_lifestyle_lp_overflow_warns() -> None:
    # Gym (2) + Cramped (1) + 2 freegrids (2) = 5 > Medium LP 4
    out = compute(
        _mundane(
            "lp-over",
            lifestyles=[
                LifestyleInstall(
                    lifestyle_id=MEDIUM_LIFESTYLE,
                    months=1,
                    quality_ids=[LIFESTYLE_GYM, LIFESTYLE_CRAMPED],
                )
            ],
        )
    )
    assert has(out.derived["warnings"], "engine.gear.lifestylePointsOver")


PRIME_DATAHAVEN = "7297d8b0-8bb8-4d7a-ab10-2d4e4381e5d0"
NETWORKER = "fc195df5-83f6-4aff-aca8-4287a56e4d4c"
MASSIVE_NETWORK = "f8384574-ce99-4e33-8a94-b5aea7ddf4bd"


def test_prime_datahaven_adds_connection_five_contact() -> None:
    out = compute(_mundane("datahaven", quality_ids=[PRIME_DATAHAVEN]))
    row = next(c for c in out.derived["contacts"] if c.get("source_quality_id") == PRIME_DATAHAVEN)
    assert row["connection"] == 5
    assert row["loyalty"] == 3
    assert row["free"] is True
    assert row["group"] is True
    assert row["billable"] == 0
    assert row["loyalty_min"] == 3


def test_networker_zeros_excess_contact_karma() -> None:
    state = _mundane(
        "networker",
        quality_ids=[NETWORKER],
        contacts=[
            ContactInstall(name="Fixer", connection=4, loyalty=3),
            ContactInstall(name="Street Doc", connection=3, loyalty=3),
        ],
    )
    state.attributes["CHA"] = 3  # free 9; used 13; paid points 4
    out = compute(state)
    assert out.derived["contact_points"]["karma_per_point"] == 0
    assert out.derived["contact_points"]["paid"] == 4
    assert out.derived["contact_points"]["karma"] == 0
    # quality karma 5 only
    assert out.derived["karma"]["spent"] == 5
    assert "contactkarma" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_massive_network_zeros_excess_contact_karma() -> None:
    state = _mundane(
        "massive-net",
        quality_ids=[MASSIVE_NETWORK],
        contacts=[ContactInstall(name="Fixer", connection=6, loyalty=1)],
    )
    state.attributes["CHA"] = 1  # free 3; used 7; paid 4
    out = compute(state)
    assert out.derived["contact_points"]["karma_per_point"] == 0
    assert out.derived["contact_points"]["karma"] == 0


def test_contact_free_points_come_off_unaugmented_charisma() -> None:
    """Chummer's `{CHAUnaug} * 3`: a dose of Novacoke raises CHA on the sheet
    but not the network a runner walked in with."""
    dosed = compute(_drug_state(True, NOVACOKE))
    assert dosed.derived["totals"]["CHA"] == 4
    assert dosed.derived["contact_points"]["free"] == 9
    assert dosed.derived["contact_points"]["free_mult"] == 3


def test_a_settings_contact_multiplier_widens_the_free_network() -> None:
    """Prime Runner's `{CHAUnaug} * 6`."""
    state = _human("contact-prime", settings=SettingsState(contact_free_mult=6))
    state.attributes["CHA"] = 3
    out = compute(state)
    assert out.derived["contact_points"]["free"] == 18
    assert out.derived["contact_points"]["free_mult"] == 6
