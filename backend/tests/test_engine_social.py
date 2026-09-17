"""Contacts, lifestyles and notoriety."""

from app.data_loader import catalog
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


EXTRA_SECURE = "4fb84713-6171-409d-ad7c-ccbc44b891ad"


def test_lifestyle_lp_overflow_warns() -> None:
    # On Low (3 LP), where Gym is not `<allowed>`: Gym 2 + Cramped 1 + Extra
    # Secure 1 = 4. The built-in Grid Subscription takes none.
    out = compute(
        _mundane(
            "lp-over",
            lifestyles=[
                LifestyleInstall(
                    lifestyle_id=LOW_LIFESTYLE,
                    months=1,
                    quality_ids=[LIFESTYLE_GYM, LIFESTYLE_CRAMPED, EXTRA_SECURE],
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


GRID_SUBSCRIPTION = "adaf6b3d-874a-42e5-b08b-37adf1222f23"
DANGEROUS_AREA = "ae63d09f-22a1-4c27-bc99-d82887fcef15"
DATAHOST = "4d2bac20-5051-4035-8959-2286c0879686"


def test_lifestyle_cost_follows_chummers_stages() -> None:
    """Chummer's `Lifestyle.CostPreSplit` (HT p.139): multipliers compound
    stage by stage — an entertainment asset's price goes in before the
    Cramped / Dangerous Area multipliers — and a contract is added last."""
    out = compute(
        _mundane(
            "ls-stages",
            lifestyles=[
                LifestyleInstall(
                    lifestyle_id=LOW_LIFESTYLE,
                    quality_ids=[GRID_SUBSCRIPTION, LIFESTYLE_CRAMPED, DANGEROUS_AREA, DATAHOST],
                )
            ],
        )
    )
    # (2000 + 50 Grid) x 0.9 x 0.8 = 1476, + 250 Datahost = 1726
    assert out.derived["lifestyles"][0]["monthly"] == 1726
    # a Low lifestyle may buy a Grid Subscription — `<allowed>` only lists where it takes no LP
    grids = [q for q in out.derived["lifestyles"][0]["qualities"] if q["name"] == "Grid Subscription"]
    assert [(q["cost"], q["from_freegrid"]) for q in grids] == [(0, True), (50, False)]


def test_raising_comforts_neighborhood_security_costs_lp_and_ten_percent_each() -> None:
    """RF p.219 / Chummer's `CostPreSplit`: each point raised above the
    lifestyle's own costs a point of LP and 10% of the base cost (plus its
    own price where the lifestyle has one); no further than the table allows."""
    out = compute(_mundane("ls-raise", lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, comforts=5, area=1)]))
    row = out.derived["lifestyles"][0]
    assert row["raised"] == {"comforts": 1, "area": 1, "security": 0}  # Low's comforts 2 → limit 3
    assert row["monthly"] == 2400  # 2000 x (1 + 0.1 x 2)
    assert row["lp_used"] == 2
    assert out.lifestyles[0].comforts == 1


BAD_CREDIT = "e4bceac5-8f1d-4090-90fc-ad5e94bca8d7"
PARAPLEGIC = "dca0897f-532a-43ab-8796-4ef761e829af"
SUBSISTENCE_HUNTING_II = "c0051319-9565-49f1-b59d-ee1f835cf1df"


def test_a_characters_lifestyle_percentages_compound_before_the_outings() -> None:
    """Chummer's `Lifestyle.GetTotalMonthlyCost`: two +10% qualities make
    x1.21, not x1.2, and they scale the lifestyle before an outing's flat
    price is added — not after."""
    out = compute(
        _mundane(
            "ls-char-mods",
            quality_ids=[BAD_CREDIT, PARAPLEGIC],
            lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, quality_ids=[SUBSISTENCE_HUNTING_II])],
        )
    )
    row = out.derived["lifestyles"][0]
    assert out.derived["lifestyle_cost_mod"] == 20  # what the sheet shows
    assert row["monthly"] == 2450  # 2000 x 1.1 x 1.1 + 30
    assert row["nuyen"] == 2450
    assert "_pre_mod" not in row


DOCWAGON_BASIC = next(
    row["id"] for row in catalog()["lifestyle_qualities"] if row["name"] == "DocWagon Contract, Basic"
)


def test_a_yearly_contract_costs_its_twelfth_each_month() -> None:
    """`5000 div 12` is XPath's division. Read as nothing, the DocWagon
    contract was free (BLUE: 416.67¥ a month)."""
    out = compute(
        _mundane("docwagon", lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, quality_ids=[DOCWAGON_BASIC])])
    )
    row = out.derived["lifestyles"][0]
    assert next(q["cost"] for q in row["qualities"] if q["quality_id"] == DOCWAGON_BASIC) == 416.67
    assert row["monthly"] == 2417  # 2000 + 416.67
