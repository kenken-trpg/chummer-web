"""Drugs, BTLs and mixed drugs."""

from app.data_loader import catalog
from app.engine import (
    compute,
)
from app.models import (
    CharacterState,
    CustomDrugInstall,
    CustomDrugPart,
    CyberwareInstall,
    GearInstall,
)
from tests.engine_support import (
    JAZZ,
    NOVACOKE,
    _drug_state,
    _human,
    _mundane,
)
from tests.notice_asserts import has

DRUG_TOLERANT = "00c827f6-aaa7-4003-87c9-f14e36263252"  # CF p.54
ELEVATED_STRESS = "0b28f554-8929-4b8b-b8c6-4203ca856b33"  # TCT p.189
STREET_COOKED = "f22e79fa-fb04-4369-a761-a1a46e242bc8"
PHARMACEUTICAL = "21f33089-cb7a-4bef-80ae-03d04f1c47ad"


def test_jazz_street_cooked_parent_cost() -> None:
    jazz = GearInstall(gear_id=JAZZ, id="jazz1")
    grade = GearInstall(gear_id=STREET_COOKED, parent_id="jazz1", id="grade1")
    out = compute(_mundane("jazz-street", gear=[jazz, grade]))
    by_name = {row["name"]: row for row in out.derived["gear"]}
    assert by_name["Jazz"]["nuyen"] == 75
    assert by_name["Street Cooked"]["nuyen"] == -37  # Parent Cost * -0.5
    assert out.derived["nuyen_spent"] == 38


def test_jazz_pharmaceutical_parent_cost() -> None:
    jazz = GearInstall(gear_id=JAZZ, id="jazz2")
    grade = GearInstall(gear_id=PHARMACEUTICAL, parent_id="jazz2", id="grade2")
    out = compute(_mundane("jazz-pharma", gear=[jazz, grade]))
    by_name = {row["name"]: row for row in out.derived["gear"]}
    assert by_name["Pharmaceutical"]["nuyen"] == 75
    assert out.derived["nuyen_spent"] == 150


def test_active_drug_folds_bonus_into_totals() -> None:
    base = compute(_drug_state(False))
    dosed = compute(_drug_state(True))

    assert base.derived["totals"]["REA"] == 4
    assert dosed.derived["totals"]["REA"] == 5  # Jazz: +1 REA
    assert dosed.derived["initiative"]["dice"] == base.derived["initiative"]["dice"] + 2
    assert base.derived["active_drugs"] == []
    assert [d["name"] for d in dosed.derived["active_drugs"]] == ["Jazz"]
    row = dosed.derived["active_drugs"][0]
    assert has(row["effect"], "engine.drugEffect.attribute", name="REA", value="+1")
    assert row["vectors"] == ["Inhalation"]


INFILTRATOR_BTL = "c153d7ec-af89-4c6f-a31d-fc3a6a490de4"  # CF p.193


def test_a_quality_moves_the_addiction_test() -> None:
    """The Addiction Test (SR5 p.414) is BOD + WIL / LOG + WIL against the
    drug's threshold. `Drug Tolerant` (CF p.54) helps only on the first dose;
    `Elevated Stress` (TCT p.189) hurts both tests, addicted or not."""
    tolerant = compute(_human("tolerant", quality_ids=[DRUG_TOLERANT])).derived["test_mods"]
    assert tolerant["addiction_physiological_first"] == 2
    assert tolerant["addiction_psychological_first"] == 2
    assert tolerant["addiction_physiological_addicted"] == 0
    assert tolerant["addiction_psychological_addicted"] == 0

    stressed = compute(_human("stressed", quality_ids=[ELEVATED_STRESS])).derived["test_mods"]
    assert stressed["addiction_physiological_first"] == -1
    assert stressed["addiction_physiological_addicted"] == -1
    assert stressed["addiction_psychological_first"] == -1
    assert stressed["addiction_psychological_addicted"] == -1


def test_a_btl_is_taken_the_way_a_drug_is() -> None:
    """A BTL is a chip, not a chemical, but upstream gives it a drug's
    `<bonus>` and the character wears it the same way (CF p.193)."""
    base = compute(_drug_state(False, INFILTRATOR_BTL))
    dosed = compute(_drug_state(True, INFILTRATOR_BTL))

    assert base.derived["totals"]["AGI"] == 3
    assert dosed.derived["totals"]["AGI"] == 5  # Infiltrator: AGI +2
    assert dosed.derived["totals"]["CHA"] == 1  # and CHA -2
    row = dosed.derived["active_drugs"][0]
    assert row["name"] == "Infiltrator"
    assert row["category"] == "BTLs"
    assert has(row["effect"], "engine.drugEffect.skill", value="+2")


def test_a_drug_grade_is_not_burned_onto_a_chip() -> None:
    """Drug grades (CF p.190) come out of a lab, so they stay on the chemicals
    even though a BTL now counts as a drug everywhere else."""
    grades = [row for row in catalog()["gear"] if row.get("category") == "Drug Grades"]
    assert grades
    for grade in grades:
        assert "BTLs" not in (grade.get("required_categories") or [])


NITRO = "d7ec13fa-8601-4f9c-a59c-6a86573b40ee"  # the same at rating 6
HIGH_PAIN_TOLERANCE = "b7866fb4-3747-4caf-9240-69cbdd79ce78"
LOW_PAIN_TOLERANCE = "9ba327d2-38c5-4a25-ae44-25e98f0bbf03"


def test_a_drug_grants_the_quality_it_names() -> None:
    """`<quality>` on a drug: the quality's own bonus, once per rating step."""
    base = compute(_drug_state(False, NOVACOKE))
    dosed = compute(_drug_state(True, NOVACOKE))

    assert base.derived["condition_monitor"]["threshold_offset"] == 0
    assert dosed.derived["condition_monitor"]["threshold_offset"] == 1
    assert dosed.derived["condition_monitor"]["threshold"] == 3
    assert has(dosed.derived["active_drugs"][0]["effect"], "engine.drugEffect.qualityRated")


def test_a_drugs_quality_rating_is_the_drugs_to_give() -> None:
    """Nitro grants six levels though the quality itself caps at three takes:
    the `<limit>` is on buying it, not on what the drug does (CF p.190)."""
    dosed = compute(_drug_state(True, NITRO))
    assert dosed.derived["condition_monitor"]["threshold_offset"] == 6


def test_high_pain_tolerance_pushes_the_first_penalty_out() -> None:
    out = compute(_mundane("hpt", quality_ids=[HIGH_PAIN_TOLERANCE]))
    assert out.derived["condition_monitor"]["threshold_offset"] == 1
    assert out.derived["condition_monitor"]["threshold"] == 3


def test_low_pain_tolerance_tightens_the_penalty_step() -> None:
    out = compute(_mundane("lpt", quality_ids=[LOW_PAIN_TOLERANCE]))
    assert out.derived["condition_monitor"]["threshold"] == 2
    assert out.derived["condition_monitor"]["threshold_offset"] == 0


NARCO = "92a00ca4-7e2b-47ca-ac02-1d58e4932d0a"  # `<drugpositiveattributemodifier>1`
ZEN = "3a946800-be1e-4bbb-899a-c3d1c48a3a31"  # REA −2, the one drug that takes


def test_narco_lifts_what_a_drug_gives() -> None:
    plain = compute(_drug_state(True))
    state = _drug_state(True)
    state.bioware = [CyberwareInstall(ware_id=NARCO, rating=1)]
    dosed = compute(state)

    assert plain.derived["totals"]["REA"] == 5  # Jazz: +1 REA
    assert dosed.derived["totals"]["REA"] == 6
    # the printed line follows the engine, not the book's figure for the drug alone
    assert has(dosed.derived["active_drugs"][0]["effect"], "engine.drugEffect.attribute", name="REA", value="+2")


def test_narco_lifts_a_mixed_drug_too() -> None:
    """Narco names its drug categories one node at a time, and `Custom Drugs`
    is one of them — a drug you cooked yourself is still a drug (CF p.159)."""
    ids = _component_ids()
    parts = [CustomDrugPart(component_id=ids["Tank"], level=0)]

    def bod(*, narco: bool) -> int:
        state = _mundane("mix-narco", custom_drugs=[CustomDrugInstall(name="W", active=True, parts=parts)])
        if narco:
            state.bioware = [CyberwareInstall(ware_id=NARCO, rating=1)]
        return int(compute(state).derived["totals"]["BOD"])

    assert bod(narco=True) - bod(narco=False) == 1  # Tank: BOD +2, and +3 on Narco


def test_narco_leaves_what_a_drug_takes_alone() -> None:
    plain = compute(_drug_state(True, ZEN))
    state = _drug_state(True, ZEN)
    state.bioware = [CyberwareInstall(ware_id=NARCO, rating=1)]
    dosed = compute(state)
    assert dosed.derived["totals"]["REA"] == plain.derived["totals"]["REA"]  # Zen: −2 REA either way


def _component_ids() -> dict[str, str]:
    return {item["name"]: item["id"] for item in catalog()["drug_components"]}


def _mixed(name: str, parts: list[tuple[str, int]], **kwargs: object) -> CharacterState:
    ids = _component_ids()
    drug = CustomDrugInstall(
        name=name,
        parts=[CustomDrugPart(component_id=ids[comp], level=level) for comp, level in parts],
        **kwargs,  # type: ignore[arg-type]
    )
    return _mundane(f"mix-{name}", custom_drugs=[drug])


def test_mixed_drug_sums_its_components() -> None:
    """Tank (Foundation) + Crush at level 2 + a Speed Enhancer, by the book:
    cost / availability / addiction / onset are the components added up, and
    the drug takes effect faster than the 9-second default (CF p.190)."""
    out = compute(_mixed("Wrecker", [("Tank", 0), ("Crush", 1), ("Speed Enhancer", 0)]))
    row = out.derived["custom_drugs"][0]
    assert row["nuyen"] == 145  # 75 + 20 + 50
    assert row["avail"] == "6R"  # +4R + 1 + 1, and R survives
    assert (row["addiction_rating"], row["addiction_threshold"]) == (7, 3)
    assert row["speed"] == 6  # 9 baseline, the enhancer takes 3 off
    assert row["crash_damage"] == 2  # Crush level 2 crashes you; Tank does not
    assert out.derived["nuyen_spent"] == 145
    assert out.derived["errors"] == []


def test_mixed_drug_only_touches_the_character_while_it_is_active() -> None:
    ids = _component_ids()
    parts = [CustomDrugPart(component_id=ids["Tank"], level=0), CustomDrugPart(component_id=ids["Crush"], level=1)]

    def totals(active: bool) -> dict[str, int]:
        state = _mundane("mix-active", custom_drugs=[CustomDrugInstall(name="W", active=active, parts=parts)])
        return compute(state).derived["totals"]

    off, on = totals(False), totals(True)
    # Tank: BOD +2 / WIL +1 / CHA -2 and 3 levels of High Pain Tolerance;
    # Crush at level 2: STR +2 / INT -1.
    assert (on["BOD"] - off["BOD"], on["WIL"] - off["WIL"], on["CHA"] - off["CHA"]) == (2, 1, -2)
    assert (on["STR"] - off["STR"], on["INT"] - off["INT"]) == (2, -1)
    state = _mundane("mix-cm", custom_drugs=[CustomDrugInstall(name="W", active=True, parts=parts)])
    assert compute(state).derived["condition_monitor"]["threshold_offset"] == 3


def test_mixed_drug_grade_moves_the_price_and_the_threshold() -> None:
    """`<grades>` in `drugcomponents.xml`: Street Cooked is half price,
    Pharmaceutical costs double and is a step harder to get hooked on."""
    parts = [("Tank", 0), ("Crush", 1)]
    street = compute(_mixed("W", parts, grade="Street Cooked")).derived["custom_drugs"][0]
    pharma = compute(_mixed("W", parts, grade="Pharmaceutical")).derived["custom_drugs"][0]
    assert (street["nuyen"], pharma["nuyen"]) == (48, 190)  # 95 halved (rounded up), doubled
    assert (street["addiction_threshold"], pharma["addiction_threshold"]) == (2, 1)


def test_mixed_drug_needs_exactly_one_foundation() -> None:
    no_base = compute(_mixed("W", [("Crush", 0)])).derived
    assert has(no_base["errors"], "engine.customDrug.missingFoundation")
    two = compute(_mixed("W", [("Tank", 0), ("Defender", 0)])).derived
    assert has(two["errors"], "engine.customDrug.oneFoundation")
    assert [c["name"] for c in two["custom_drugs"][0]["components"]] == ["Tank"]


def test_mixed_drug_respects_a_components_own_limit() -> None:
    # Speed Enhancer carries `<limit>3</limit>`; the fourth is refused.
    out = compute(_mixed("W", [("Tank", 0)] + [("Speed Enhancer", 0)] * 4)).derived
    assert has(out["errors"], "engine.customDrug.tooMany")
    assert len(out["custom_drugs"][0]["components"]) == 4


def test_a_high_block_may_not_undo_what_its_foundation_lowers() -> None:
    """CF p.191: Tank costs you CHA, so Smoothtalk cannot buy it back at
    level 3 — one level down is still fine."""
    clash = compute(_mixed("W", [("Tank", 0), ("Smoothtalk", 2)])).derived
    assert has(clash["errors"], "engine.customDrug.blockFightsFoundation")
    ok = compute(_mixed("W", [("Tank", 0), ("Smoothtalk", 1)])).derived
    assert ok["errors"] == []


def test_a_component_level_that_does_not_exist_is_dropped_with_a_warning() -> None:
    out = compute(_mixed("W", [("Tank", 0), ("Crush", 5)])).derived
    assert has(out["warnings"], "engine.customDrug.noSuchLevel")
    assert [c["name"] for c in out["custom_drugs"][0]["components"]] == ["Tank"]


def test_a_mixed_drug_is_subject_to_the_chargen_availability_limit() -> None:
    """Five Blocks on top of a Foundation come to 14R — nothing a starting
    character may buy, mixed or not (SR5 p.65)."""
    out = compute(
        _mixed(
            "Nasty",
            [
                ("Tank", 0),
                ("Razor Mind", 0),
                ("Resist", 0),
                ("Shock and Awe", 0),
                ("Speed Demon", 0),
                ("The General", 0),
            ],
        )
    ).derived
    assert out["custom_drugs"][0]["avail"] == "14R"
    assert has(out["errors"], "engine.gear.availOver")
