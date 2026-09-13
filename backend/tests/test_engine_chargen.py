"""Build methods, priorities, karma build, attribute limits and chargen checks."""

from app.data_loader import parse_avail
from app.engine import (
    compute,
    default_attributes,
    find_metatype,
)
from app.engine.compute.finalize import resolve_movement
from app.improvements import collect_effects
from app.models import (
    CharacterState,
    CyberwareInstall,
    Priorities,
)
from tests.engine_support import (
    RESTRICTED_GEAR,
    WIRED,
    _human,
    _karma_human,
    _mundane,
)
from tests.notice_asserts import has

MYOSTATIN = "1b6713f7-f5b6-49fb-a89a-68322c06f38d"


def test_human_derived_stats() -> None:
    state = CharacterState(
        id="test",
        name="Test",
        priorities=Priorities(Heritage="C", Attributes="A", Talent="E", Skills="B", Resources="D"),
        metatype="Human",
        attributes={
            "BOD": 3,
            "AGI": 5,
            "REA": 4,
            "STR": 3,
            "WIL": 3,
            "LOG": 3,
            "INT": 5,
            "CHA": 3,
            "EDG": 3,
            "MAG": 0,
            "RES": 0,
            "ESS": 6,
        },
    )
    out = compute(state)
    totals = out.derived["totals"]
    assert totals["BOD"] == 3
    assert out.derived["limits"]["physical"] == 6
    assert out.derived["condition_monitor"]["physical"] == 10
    assert out.derived["condition_monitor"]["stun"] == 10
    assert out.derived["initiative"]["value"] == 9
    assert out.derived["essence"] == 6
    assert out.derived["karma"]["remaining"] == 25


def test_elf_priority_does_not_charge_xml_karma() -> None:
    state = CharacterState(
        id="elf",
        name="Elf",
        priorities=Priorities(Heritage="C", Attributes="A", Talent="E", Skills="B", Resources="D"),
        metatype="Elf",
        attributes=default_attributes(find_metatype("Elf", None)),
    )
    out = compute(state)
    assert out.derived["karma"]["remaining"] == 25
    assert out.derived["errors"] == []


def test_priority_rejects_duplicate_letters() -> None:
    state = CharacterState(
        id="dup-pri",
        name="Dup",
        build_method="Priority",
        priorities=Priorities(Heritage="A", Attributes="A", Talent="E", Skills="B", Resources="D"),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
    )
    out = compute(state)
    assert has(out.derived["errors"], "engine.priority.oneEach")


def test_sum_to_ten_allows_duplicate_a() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="sum10-aa",
        name="Rich Mage",
        build_method="SumToTen",
        priorities=Priorities(Heritage="E", Attributes="C", Talent="A", Skills="E", Resources="A"),
        metatype="Human",
        talent="Magician",
        attributes=attrs,
        tradition_id="19320625-bc1a-492f-8904-da6a847e5700",
    )
    out = compute(state)
    assert out.build_method == "SumToTen"
    assert out.derived["sum_to_ten"]["used"] == 10
    assert out.derived["totals"]["MAG"] == 6
    assert out.derived["nuyen"] == 450_000
    assert not any("Sum to Ten" in err for err in out.derived["errors"])
    assert not has(out.derived["errors"], "engine.priority.oneEach")


def test_sum_to_ten_requires_exact_budget() -> None:
    state = CharacterState(
        id="sum10-low",
        name="Under",
        build_method="SumToTen",
        priorities=Priorities(Heritage="E", Attributes="E", Talent="E", Skills="E", Resources="E"),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
    )
    out = compute(state)
    assert out.derived["sum_to_ten"]["used"] == 0
    assert has(out.derived["errors"], "engine.priority.sumToTen", spent=0)


def test_karma_chargen_human_baseline_is_800() -> None:
    out = compute(
        CharacterState(
            id="karma-base",
            name="Karma Base",
            build_method="Karma",
            priorities=Priorities(),
            metatype="Human",
            attributes=default_attributes(find_metatype("Human", None)),
        )
    )
    assert out.build_method == "Karma"
    assert out.derived["karma"]["pool"] == 800
    assert out.derived["karma"]["spent"] == 0
    assert out.derived["karma_chargen"]["enabled"] is True
    assert out.derived["points"]["attributes"]["max"] == 0
    assert out.derived["errors"] == []


def test_karma_chargen_attributes_and_metatype_cost() -> None:
    attrs = default_attributes(find_metatype("Elf", None))
    attrs["BOD"] = 3  # racial min 1 → 2*5 + 3*5 = 25
    out = compute(
        CharacterState(
            id="karma-elf",
            name="Karma Elf",
            build_method="Karma",
            priorities=Priorities(),
            metatype="Elf",
            attributes=attrs,
        )
    )
    assert out.derived["karma_chargen"]["metatype"] == 40
    assert out.derived["karma_chargen"]["attributes"] == 25
    assert out.derived["karma"]["spent"] == 65


def test_myostatin_inhibitor_makes_strength_cheaper_at_chargen() -> None:
    plain = compute(_karma_human("myo-off", STR=4))
    st = _karma_human("myo-on", STR=4)
    st.bioware = [CyberwareInstall(ware_id=MYOSTATIN)]
    with_ware = compute(st)
    # Levels 2/3/4 cost 10+15+20 = 45; the inhibitor takes 2 off each.
    assert plain.derived["karma_chargen"]["attributes"] == 45
    assert with_ware.derived["karma_chargen"]["attributes"] == 39


def test_myostatin_inhibitor_discount_is_strength_only() -> None:
    from app.engine import snapshot_career_baseline

    def raise_both(cid: str, ware: bool) -> int:
        st = _karma_human(cid, STR=3, BOD=3)
        st.build_method = "Priority"
        if ware:
            st.bioware = [CyberwareInstall(ware_id=MYOSTATIN)]
        st = compute(st)
        st.career = True
        st.career_baseline = snapshot_career_baseline(st)
        st.attributes = {**dict(st.attributes), "STR": 4, "BOD": 4}
        return int(compute(st).derived["career_advancement_karma"])

    # STR 3→4 and BOD 3→4 are 20 karma each; only STR is discounted.
    assert raise_both("myo-career-off", False) == 40
    assert raise_both("myo-career-on", True) == 38


def test_karma_chargen_nuyen_conversion() -> None:
    out = compute(
        CharacterState(
            id="karma-yen",
            name="Karma Yen",
            build_method="Karma",
            priorities=Priorities(),
            metatype="Human",
            attributes=default_attributes(find_metatype("Human", None)),
            karma_nuyen=10,
        )
    )
    assert out.derived["nuyen"] == 20_000
    assert out.derived["karma_chargen"]["nuyen_karma"] == 10
    assert out.derived["karma"]["spent"] == 10


def test_parse_avail_reads_rating_suffix_and_additive() -> None:
    assert parse_avail("12R") == (12, "R", False)
    assert parse_avail("+4") == (4, "", True)
    assert parse_avail("+2R") == (2, "R", True)
    assert parse_avail("FixedValues(8R,12R,20R)", 1) == (8, "R", False)
    assert parse_avail("FixedValues(8R,12R,20R)", 2) == (12, "R", False)
    assert parse_avail("FixedValues(8R,12R,20R)", 3) == (20, "R", False)
    assert parse_avail("(Rating * 5)R", 2) == (10, "R", False)
    assert parse_avail("+Rating - MinRating + 1", 3, {"MinRating": 1}) == (3, "", True)


def test_restricted_gear_allows_one_item_over_avail_twelve() -> None:
    out = compute(
        _mundane(
            "avail-restricted",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
            quality_ids=[RESTRICTED_GEAR],
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=3)],
        )
    )
    assert out.derived["cyberware"][0]["avail"] == "20R"
    assert out.derived["cyberware"][0].get("restricted_gear") is True
    assert not has(out.derived["errors"], "engine.gear.availOver")
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "restrictedgear" not in tags


EXCEPTIONAL_ATTRIBUTE = "2ac8a95a-a4d0-4bef-a2f2-dcde020258cf"
CELERITY = "bd2cf8ea-4eb3-458c-aa04-2de47067f3ad"


def test_exceptional_attribute_raises_max() -> None:
    missing = compute(_human("ea-miss", quality_ids=[EXCEPTIONAL_ATTRIBUTE]))
    assert has(missing.derived["warnings"], "engine.attrs.pickAttribute")
    attrs = default_attributes(find_metatype("Human", None))
    attrs["BOD"] = 6
    out = compute(
        CharacterState(
            id="ea-bod",
            name="ea-bod",
            priorities=Priorities(),
            metatype="Human",
            attributes=attrs,
            quality_ids=[EXCEPTIONAL_ATTRIBUTE],
            quality_extras={EXCEPTIONAL_ATTRIBUTE: "BOD"},
        )
    )
    assert out.derived["attribute_max_bonus"]["BOD"] == 1
    assert out.derived["metatype_info"]["attributes"]["BOD"]["max"] == 7
    assert out.derived["totals"]["BOD"] == 6
    assert "selectattributes" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_celerity_replaces_movement() -> None:
    """Celerity sets the Ground rates to 3/6 and adds 1 m per sprint hit;
    at AGI 1 that is 3 m walking, 6 m running, 3 m per hit."""
    out = compute(_human("celerity", quality_ids=[CELERITY]))
    assert out.derived["totals"]["AGI"] == 1
    assert out.derived["movement"]["walk"] == "3"
    assert out.derived["movement"]["run"] == "6"
    assert out.derived["movement"]["sprint"] == "3"
    assert out.derived["movement"]["sprint_bonus"] == 100
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "movementreplace" not in tags
    assert "sprintbonus" not in tags


def test_movement_is_metres_off_agility() -> None:
    """Chummer's `CalculatedMovement("Ground")`: a human walks 2×AGI and
    runs 4×AGI metres, and sprints +2 m per hit."""
    state = _human("move-agi")
    state.attributes["AGI"] = 4
    move = compute(state).derived["movement"]
    assert (move["walk"], move["run"], move["sprint"]) == ("8", "16", "2")


def test_a_percent_movement_bonus_scales_the_rate() -> None:
    """`<walkmultiplier><percent>` was read as `+0` before; it scales the
    Ground rate, so +50% on a 2× walk at AGI 2 is 6 m."""
    effects = collect_effects([("t", [{"tag": "walkmultiplier", "fields": {"category": "Ground", "percent": "50"}}])])
    assert effects["walk_multiplier_percent"] == {"Ground": 50}
    assert effects["walk_multiplier"] == {}
    move = resolve_movement({"walk": "2/1/0", "run": "4/0/0", "sprint": "2/1/0"}, effects, 2)
    assert move["walk"] == "6"
    assert move["run"] == "8"


def test_only_one_attribute_at_natural_max_for_priority_build() -> None:
    prio = Priorities(Heritage="C", Attributes="A", Talent="E", Skills="D", Resources="B")

    two = default_attributes(find_metatype("Human", None))
    two["BOD"] = 6
    two["AGI"] = 6
    flagged = compute(
        CharacterState(
            id="natmax-two",
            name="NatMax",
            build_method="Priority",
            priorities=prio,
            metatype="Human",
            attributes=two,
        )
    )
    assert has(flagged.derived["errors"], "engine.attrs.oneAtNaturalMax")

    one = default_attributes(find_metatype("Human", None))
    one["BOD"] = 6
    ok = compute(
        CharacterState(
            id="natmax-one",
            name="NatMax",
            build_method="Priority",
            priorities=prio,
            metatype="Human",
            attributes=one,
        )
    )
    assert not has(ok.derived["errors"], "engine.attrs.oneAtNaturalMax")


def _adept_at_mag_six(cid: str, **attrs: int) -> CharacterState:
    base = default_attributes(find_metatype("Human", None))
    base.update(attrs)
    return CharacterState(
        id=cid,
        name=cid,
        build_method="Priority",
        priorities=Priorities(Heritage="E", Attributes="A", Talent="B", Skills="C", Resources="D"),
        metatype="Human",
        talent="Adept",
        attributes={**base, "MAG": 6},
    )


def test_a_special_attribute_at_its_maximum_is_not_counted() -> None:
    """Chummer counts its `AttributeList` — BOD to WIL. MAG 6 plus AGI 6 on a
    human Adept is one attribute at the maximum, not two."""
    out = compute(_adept_at_mag_six("natmax-mag", AGI=6))
    assert out.attributes["MAG"] == 6
    assert not has(out.derived["errors"], "engine.attrs.oneAtNaturalMax")


def test_the_settings_file_can_allow_more_attributes_at_maximum() -> None:
    state = _adept_at_mag_six("natmax-two", AGI=6, BOD=6)
    assert has(compute(state.model_copy(deep=True)).derived["errors"], "engine.attrs.oneAtNaturalMax")
    state.settings.chargen_attributes_at_max = 2
    assert not has(compute(state).derived["errors"], "engine.attrs.oneAtNaturalMax")


def test_leftover_nuyen_carryover_notice() -> None:
    prio = Priorities(Heritage="C", Attributes="D", Talent="E", Skills="B", Resources="A")
    chargen = compute(_mundane("carry-cg", priorities=prio))
    assert has(chargen.derived["warnings"], "engine.nuyen.chargenCarryOver")
    # the notice is a chargen-only reminder; career mode omits it
    career = compute(_mundane("carry-career", career=True, priorities=prio))
    assert not has(career.derived["warnings"], "engine.nuyen.chargenCarryOver")
