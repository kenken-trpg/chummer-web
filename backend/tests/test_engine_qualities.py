"""Qualities: prerequisites, caps, picks and what they grant."""

from app.data_loader import catalog
from app.engine import (
    compute,
    default_attributes,
    find_metatype,
)
from app.models import (
    CharacterState,
    ContactInstall,
    CyberwareInstall,
    GearInstall,
    LifestyleInstall,
    MartialArtInstall,
    Priorities,
    SettingsState,
    WeaponInstall,
)
from tests.engine_support import (
    ARM,
    BLACK_MARKET_PIPELINE,
    BLANDNESS,
    CHANGELING_I,
    CODESLINGER,
    DATAJACK,
    DEAD_SIN,
    DEALER_CONNECTION,
    LIFESTYLE_CRAMPED,
    LIFESTYLE_GYM,
    MADE_MAN,
    MEDIUM_LIFESTYLE,
    MUSCLE,
    SUPRATHYROID,
    TONER,
    WIRED,
    _career_quality,
    _human,
    _into_career,
    _karate_id,
    _mage,
    _mundane,
    _quality_id,
    _quality_row,
    _surge_thirty,
    _ware_named,
)
from tests.notice_asserts import has


def test_gear_a_quality_granted_is_not_written_into_the_character() -> None:
    state = _mundane("dead-sin-state", quality_ids=[DEAD_SIN])
    compute(state)
    assert state.gear == []


QUADRIPLEGIC = "39803e82-d85a-4da1-9637-fdd3249f2f21"
INFECTED_GHOUL_HUMAN = "2d99bbb6-7af0-45c6-a83b-46d9d9f10838"


def test_infected_ghoul_replaces_the_metatype_attribute_ranges() -> None:
    """`replaceattributes`: a ghoul stops being a human where BOD/REA/STR are
    concerned (RF p.136) — the sheet ranges, the chargen cap and the augmented
    max all come from the quality."""
    plain = compute(_mundane("human"))
    out = compute(_mundane("ghoul", quality_ids=[INFECTED_GHOUL_HUMAN]))
    human = plain.derived["metatype_info"]["attributes"]
    ghoul = out.derived["metatype_info"]["attributes"]
    assert human["BOD"] == {"min": 1, "max": 6, "aug": 10}
    assert ghoul["BOD"] == {"min": 1, "max": 10, "aug": 14}
    assert ghoul["STR"]["max"] == 9
    assert ghoul["CHA"]["max"] == 4  # ghouls are not charming
    # An attribute the quality says nothing about keeps the metatype's range.
    assert ghoul["EDG"] == human["EDG"]
    assert out.derived["metatype_info"]["attributes_replaced_by"] == ["Infected: Ghoul (Human)"]
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "replaceattributes" not in tags


def test_quadriplegic_zeroes_agility_reaction_and_strength() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["AGI"] = 5
    attrs["REA"] = 4
    out = compute(
        CharacterState(
            id="quad",
            name="Quad",
            priorities=Priorities(),
            metatype="Human",
            attributes=attrs,
            quality_ids=[QUADRIPLEGIC],
        )
    )
    # The ranges are gone, so a rating bought above them is clamped away.
    assert out.derived["totals"]["AGI"] == 0
    assert out.derived["totals"]["REA"] == 0
    assert out.derived["totals"]["STR"] == 0
    assert out.derived["totals"]["BOD"] >= 1
    assert out.derived["points"]["attributes"]["used"] == 0


ELECTROCEPTION = "67767d53-56f0-4b66-b7ef-5ff6319ea551"  # (Electrosense), RF p.114
LOSS_OF_CONFIDENCE = "c9cd05ad-cd3c-451e-8285-e0fb1d95ebc1"


ALLERGY_MILD = "b7841930-0c7b-4be4-b1cf-86debc41aa95"
ALLERGY_EXTREME = "8a40007a-9876-4998-a7c9-047248cfbc52"
HUMAN_LOOKING = "2844e64e-f271-4ca7-bd58-0860b2db56c9"


def test_allergy_requires_target_text() -> None:
    """An unfilled `<selecttext>` is said, not enforced. What you are allergic
    to is prose: no rule reads it, so an empty one cannot make the build
    illegal, and Chummer saves it empty on three of its own test characters."""
    missing = compute(_human("allergy-empty", quality_ids=[ALLERGY_MILD]))
    assert not has(missing.derived["errors"], "engine.qualities.pickExtra")
    assert has(missing.derived["warnings"], "engine.qualities.pickText")
    filled = compute(_human("allergy-sun", quality_ids=[ALLERGY_MILD], quality_extras={ALLERGY_MILD: "Sunlight"}))
    assert filled.derived["errors"] == []
    assert filled.derived["karma"]["negative"] == {"used": 5, "max": 25}
    assert filled.derived["karma"]["remaining"] == 30


def test_a_quality_outside_the_limit_does_not_fill_the_positive_cap() -> None:
    """`<contributetolimit>False` (Chummer's `PositiveQualityLimitKarma`):
    Infected: Ghoul costs 29 but sits outside the 25-karma limit."""
    ghoul = next(q for q in catalog()["qualities"] if q["name"] == "Infected: Ghoul (Human)")
    assert ghoul["karma"] > 25
    out = compute(_human("ghoul-limit", quality_ids=[ghoul["id"]]))
    assert not has(out.derived["errors"], "engine.qualities.positiveCap")
    # still paid for, just not counted against the limit
    assert out.derived["karma"]["remaining"] == 25 - ghoul["karma"]


def test_negative_quality_karma_is_capped_at_25() -> None:
    out = compute(
        _human(
            "neg-cap",
            quality_ids=[ALLERGY_EXTREME, ALLERGY_MILD],
            quality_extras={ALLERGY_EXTREME: "Bees", ALLERGY_MILD: "Sunlight"},
        )
    )
    assert out.derived["karma"]["negative"]["used"] == 30
    assert has(out.derived["errors"], "engine.qualities.negativeCap")


def _over_the_negative_cap(cid: str, settings: SettingsState) -> CharacterState:
    return _human(
        cid,
        quality_ids=[ALLERGY_EXTREME, ALLERGY_MILD],
        quality_extras={ALLERGY_EXTREME: "Bees", ALLERGY_MILD: "Sunlight"},
        settings=settings,
    )


def test_a_settings_file_may_let_negative_qualities_pass_the_cap() -> None:
    """`<exceednegativequalities>` (the Missions presets): 30 karma of
    negatives is legal and all 30 is paid out."""
    capped = compute(_over_the_negative_cap("neg-strict", SettingsState()))
    loose = compute(_over_the_negative_cap("neg-loose", SettingsState(exceed_negative_qualities=True)))
    assert not has(loose.derived["errors"], "engine.qualities.negativeCap")
    assert loose.derived["karma"]["negative"]["used"] == 30
    assert loose.derived["karma"]["remaining"] == capped.derived["karma"]["remaining"]


def test_past_the_cap_a_no_bonus_file_pays_no_karma() -> None:
    """`<exceednegativequalitiesnobonus>`: the qualities stay, but only 25 of
    the 30 karma is handed out (Chummer's `NegativeQualityKarma`)."""
    loose = compute(_over_the_negative_cap("neg-loose2", SettingsState(exceed_negative_qualities=True)))
    no_bonus = compute(
        _over_the_negative_cap(
            "neg-nobonus",
            SettingsState(exceed_negative_qualities=True, exceed_negative_qualities_no_bonus=True),
        )
    )
    assert not has(no_bonus.derived["errors"], "engine.qualities.negativeCap")
    assert no_bonus.derived["karma"]["remaining"] == loose.derived["karma"]["remaining"] - 5
    assert has(no_bonus.derived["warnings"], "engine.qualities.negativeNoBonus", karma=5, limit=25)


def test_human_looking_requires_nonhuman_metatype() -> None:
    human = compute(_human("looking-human", quality_ids=[HUMAN_LOOKING]))
    assert has(human.derived["errors"], "engine.qualities.prereq", name="Human-Looking")
    elf = compute(
        CharacterState(
            id="looking-elf",
            name="looking-elf",
            priorities=Priorities(),
            metatype="Elf",
            attributes=default_attributes(find_metatype("Elf", None)),
            quality_ids=[HUMAN_LOOKING],
        )
    )
    assert elf.derived["errors"] == []


def test_loss_of_confidence_requires_rating_four() -> None:
    out = compute(
        _human(
            "confidence",
            quality_ids=[LOSS_OF_CONFIDENCE],
            skills={"Gymnastics": 4},
            skill_picks={"quality:c9cd05ad-cd3c-451e-8285-e0fb1d95ebc1:0": "Gymnastics"},
        )
    )
    assert out.derived["skill_bonus"]["Gymnastics"] == -2
    blocked = compute(
        _human(
            "confidence-low",
            quality_ids=[LOSS_OF_CONFIDENCE],
            skills={"Gymnastics": 3},
            skill_picks={"quality:c9cd05ad-cd3c-451e-8285-e0fb1d95ebc1:0": "Gymnastics"},
        )
    )
    assert has(blocked.derived["warnings"], "engine.skills.pickInvalid")


def test_a_quality_can_widen_a_skills_specialization_list() -> None:
    """Electroception (RF p.114) offers Perception a specialization no style
    does — the same `<addskillspecializationoption>` a martial art carries, in
    upstream's nested `<skills>` shape."""
    out = compute(_human("electro", quality_ids=[CHANGELING_I, ELECTROCEPTION]))
    assert out.derived["skill_spec_options"]["Perception"] == ["Electroception"]
    assert out.derived["unimplemented_bonuses"] == []


ONE_TRICK_PONY = "98644894-e3a4-41f2-9b7e-91feb74d0334"
ONE_TRICK_PONY_ART = "0325b2c8-0a48-497f-92b1-2830a5ac467f"


def test_one_trick_pony_grants_free_quality_art() -> None:
    out = compute(_mundane("otp", quality_ids=[ONE_TRICK_PONY]))
    row = next(a for a in out.derived["martial_arts"] if a.get("art_id") == ONE_TRICK_PONY_ART)
    assert row["free"] is True
    assert row["locked"] is True
    assert row["karma"] == 0
    assert row["style_karma"] == 0
    assert row["technique_max"] == 1
    assert out.derived["martial_art_points"]["styles"] == 0
    assert out.derived["martial_art_points"]["karma"] == 0
    assert has(out.derived["warnings"], "engine.martial.pickTechnique")
    assert "martialart" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    # quality karma only
    assert out.derived["karma"]["spent"] == 7


def test_one_trick_pony_technique_is_free_and_single() -> None:
    out = compute(
        _mundane(
            "otp-kick",
            quality_ids=[ONE_TRICK_PONY],
            martial_arts=[
                MartialArtInstall(
                    art_id=ONE_TRICK_PONY_ART,
                    techniques=["Kick Attack", "Counterstrike"],
                    free=True,
                    source_quality_id=ONE_TRICK_PONY,
                )
            ],
        )
    )
    row = next(a for a in out.derived["martial_arts"] if a.get("art_id") == ONE_TRICK_PONY_ART)
    assert len(row["techniques"]) == 1
    assert row["techniques"][0]["name"] == "Kick Attack"
    assert row["techniques"][0]["free"] is True
    assert row["karma"] == 0
    assert out.derived["unarmed_reach"] == 1
    assert out.derived["martial_art_points"]["techniques"] == 1
    assert has(out.derived["warnings"], "engine.martial.oneTechniqueOnly")


def test_one_trick_pony_does_not_block_paid_style() -> None:
    out = compute(
        _mundane(
            "otp-karate",
            quality_ids=[ONE_TRICK_PONY],
            martial_arts=[
                MartialArtInstall(
                    art_id=ONE_TRICK_PONY_ART,
                    techniques=["Counterstrike"],
                    free=True,
                    source_quality_id=ONE_TRICK_PONY,
                ),
                MartialArtInstall(art_id=_karate_id(), techniques=["Kick Attack"]),
            ],
        )
    )
    assert out.derived["martial_art_points"]["styles"] == 1
    assert len(out.derived["martial_arts"]) == 2
    assert out.derived["errors"] == []
    # quality 7 + karate style 7
    assert out.derived["karma"]["spent"] == 14


EX_CON = "4fe8fa5e-e31b-4126-a880-3e719a0a5820"
PHOTOGRAPHIC_MEMORY = "9d3be1d9-1309-45e7-8bd9-1f5a3ede3522"
QUICK_HEALER = "291efdb6-a8b8-49ce-b2be-72f9d3f8a243"
UNCANNY_HEALER = "0ebdfce5-c613-4fd9-9763-cae2d21c2153"
HOME_GROUND = "823eb204-c155-45a9-bb9a-98dcbe17a707"
SPIRIT_AFFINITY = "c067baa6-0dfa-4783-a0c8-0873564f0308"
CRYSTAL_BREATH = "c2b4f018-7b14-4e04-aab9-71c891dd0a18"
SINNER_CRIMINAL = "d9479e5c-d44a-45b9-8fb4-d1e08a9487b2"


def test_blandness_notoriety() -> None:
    out = compute(_human("bland", quality_ids=[BLANDNESS]))
    assert out.derived["notoriety"] == -1
    assert "notoriety" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_ex_con_adds_sinner_quality() -> None:
    out = compute(_human("excon", quality_ids=[EX_CON]))
    names = {q["name"] for q in out.derived["qualities"]}
    assert "Ex-Con" in names
    assert "SINner (Criminal)" in names
    assert SINNER_CRIMINAL in out.quality_ids or any(q["id"] == SINNER_CRIMINAL for q in out.derived["qualities"])
    assert out.derived["excon"] is True
    assert "excon" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


ERASED = "07f1833e-e5e0-41e1-91de-9044b2f48367"
FAME_LOCAL = "51e9e615-e3ba-4b25-b7b0-ffa8acf076f8"
LIFESTYLE_HIGH = "4a37d519-c9be-4ecc-97bb-e9d78708c374"
LIFESTYLE_MEDIUM = "9cb0222c-14c1-4bea-bf83-055513a1f33e"


def test_erased_caps_public_awareness() -> None:
    out = compute(
        _human(
            "erased-pa",
            quality_ids=[ERASED, FAME_LOCAL],
            street_cred=9,
        )
    )
    assert out.derived["erased"] is True
    assert out.derived["public_awareness"] == 1
    assert "erased" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_erased_blocks_high_lifestyle() -> None:
    out = compute(
        _human(
            "erased-high",
            quality_ids=[ERASED],
            lifestyles=[LifestyleInstall(lifestyle_id=LIFESTYLE_HIGH)],
        )
    )
    assert has(out.derived["warnings"], "engine.gear.erasedLifestyle")
    ok = compute(
        _human(
            "erased-med",
            quality_ids=[ERASED],
            lifestyles=[LifestyleInstall(lifestyle_id=LIFESTYLE_MEDIUM)],
        )
    )
    assert not has(ok.derived["warnings"], "engine.gear.erasedLifestyle")


def test_ex_con_bans_restricted_ware() -> None:
    out = compute(
        _human(
            "excon-ware",
            quality_ids=[EX_CON],
            cyberware=[CyberwareInstall(ware_id=MUSCLE, rating=1)],
        )
    )
    assert has(out.derived["errors"], "engine.ware.exconRestricted")


def test_ex_con_raises_corp_and_law_loyalty() -> None:
    corp = compute(
        _human(
            "excon-corp",
            quality_ids=[EX_CON],
            contacts=[ContactInstall(name="Boss", role="Mr. Johnson", connection=2, loyalty=2)],
        )
    )
    row = corp.derived["contacts"][0]
    assert row["loyalty"] == 4
    assert row["loyalty_min"] == 4
    law = compute(
        _human(
            "excon-law",
            quality_ids=[EX_CON],
            contacts=[ContactInstall(name="Buddy", role="Cop", connection=1, loyalty=2)],
        )
    )
    assert law.derived["contacts"][0]["loyalty"] == 5
    assert law.derived["contacts"][0]["loyalty_min"] == 5


INSPIRED_SASS = "fd9b9b6d-c969-40f1-8dc7-61f8e5d9cd4d"


def test_inspired_grants_free_artisan_expertise() -> None:
    out = compute(
        _human(
            "inspired",
            quality_ids=[INSPIRED_SASS],
            skills={"Artisan": 3},
            quality_extras={INSPIRED_SASS: "Cooking"},
        )
    )
    assert out.derived["skill_specializations"]["Artisan"] == "Cooking"
    row = out.derived["skill_expertises"][0]
    assert row["skill"] == "Artisan"
    assert row["spec"] == "Cooking"
    assert row["bonus"] == 3
    assert row["free"] is True
    assert out.derived["points"]["skills"]["used"] == 3  # rating only; expertise is free
    assert "selectexpertise" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_inspired_requires_choice_and_skill() -> None:
    missing = compute(_human("insp-empty", quality_ids=[INSPIRED_SASS], skills={"Artisan": 2}))
    assert has(missing.derived["warnings"], "engine.skills.pickExpertise")
    no_skill = compute(
        _human(
            "insp-noskill",
            quality_ids=[INSPIRED_SASS],
            skills={"Artisan": 0},
            quality_extras={INSPIRED_SASS: "Cooking"},
        )
    )
    assert has(no_skill.derived["warnings"], "engine.skills.expertiseNeedsSkill", skill="Artisan")


def test_photographic_memory_and_quick_healer() -> None:
    out = compute(_human("mem-heal", quality_ids=[PHOTOGRAPHIC_MEMORY, QUICK_HEALER]))
    assert out.derived["test_mods"]["memory"] == 2
    assert out.derived["cm_recovery"]["physical"] == 2
    assert out.derived["cm_recovery"]["stun"] == 2
    assert any(row["name"] == "Heal" and row["bonus"] == 2 for row in out.derived["spell_dice_pool"])
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "memory" not in tags
    assert "spelldicepool" not in tags
    assert "physicalcmrecovery" not in tags


def test_uncanny_healer_cm_recovery() -> None:
    out = compute(_human("uncanny", quality_ids=[UNCANNY_HEALER]))
    assert out.derived["essence"] == 6.0
    assert out.derived["cm_recovery"]["physical"] == 6
    assert out.derived["cm_recovery"]["stun"] == 6
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "addesstophysicalcmrecovery" not in tags
    assert "addesstostuncmrecovery" not in tags


def test_home_ground_selecttext() -> None:
    missing = compute(_human("hg-missing", quality_ids=[HOME_GROUND]))
    tags = [item["tag"] for item in missing.derived["unimplemented_bonuses"]]
    assert "selecttext" not in tags
    # prose, so a warning rather than an error — see test_allergy_requires_target_text
    assert has(missing.derived["warnings"], "engine.qualities.pickText")
    out = compute(_human("hg", quality_ids=[HOME_GROUND], quality_extras={HOME_GROUND: "Barrens"}))
    row = next(item for item in out.derived["qualities"] if item["id"] == HOME_GROUND)
    assert row["extra"] == "Barrens"
    assert not has(out.derived["errors"], "engine.qualities.pickExtra")


def test_selecttext_quality_populates_catalog_options() -> None:
    from app.data_loader import catalog

    spirit_affinity = next(q for q in catalog()["qualities"] if q["id"] == SPIRIT_AFFINITY)
    assert spirit_affinity["extra_kind"] == "text"
    assert spirit_affinity["select_options"]
    assert "Spirit of Man" in spirit_affinity["select_options"]


def test_crystal_breath_essence_penalty() -> None:
    out = compute(_human("crystal", quality_ids=[CRYSTAL_BREATH]))
    assert out.derived["essence_penalty"] == 1.0
    assert out.derived["essence"] == 5.0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "essencepenaltyt100" not in tags
    assert "fatigueresist" not in tags
    assert out.derived["fatigue_resist"] == 1


def test_medium_lifestyle_freegrids_and_quality() -> None:
    """The built-in Grid Subscriptions cost nothing; Gym, `<allowed>` on
    Medium, takes no LP there but is still paid for (Chummer's `LPFree`)."""
    out = compute(
        _mundane(
            "medium-gym",
            lifestyles=[
                LifestyleInstall(
                    lifestyle_id=MEDIUM_LIFESTYLE,
                    months=1,
                    quality_ids=[LIFESTYLE_GYM],
                )
            ],
        )
    )
    ls = out.derived["lifestyle"]
    assert ls["name"] == "Medium"
    assert ls["base_monthly"] == 5000
    assert ls["monthly"] == 5300  # Gym's 300 on top
    assert ls["lp_used"] == 0
    assert ls["lp_max"] == 4
    grids = [q for q in ls["qualities"] if q["name"] == "Grid Subscription"]
    assert len(grids) == 2
    assert {q["extra"] for q in grids} == {"Local Grid", "Public Grid"}
    assert all(q.get("from_freegrid") for q in grids)
    gym = next(q for q in ls["qualities"] if q["name"] == "Gym")
    assert gym["free"] is False
    assert (gym["cost"], gym["lp"]) == (300, 0)
    assert out.derived["nuyen_spent"] == 5300
    assert out.derived["errors"] == []


def test_lifestyle_quality_multiplier_cramped() -> None:
    out = compute(
        _mundane(
            "cramped",
            lifestyles=[
                LifestyleInstall(
                    lifestyle_id=MEDIUM_LIFESTYLE,
                    months=1,
                    quality_ids=[LIFESTYLE_CRAMPED],
                )
            ],
        )
    )
    ls = out.derived["lifestyle"]
    assert ls["multiplier_pct"] == -10
    assert ls["monthly"] == 4500
    assert ls["nuyen"] == 4500


BORN_RICH = "8f232e71-d4bf-4bea-b1b2-b88c7e652073"
IN_DEBT = "2b4dd1b1-b806-44e3-9067-65dc39c82d13"
TRUST_FUND_I = "2656bcd7-3fe1-4c34-a4fb-89ebebfbf016"
SINNER_NATIONAL = "9ac85feb-ae1e-4996-8514-3570d411e1d5"
BIOCOMPAT_CYBER = "23bfa65d-9241-4183-b7ea-0e2935e42f29"
SENSITIVE_SYSTEM = "13fd45c3-e031-4452-8bf8-31829d2401f9"
COLLEGE_EDUCATION_RF = "604aea10-3f13-4f28-a87b-25b8bf677276"
UNCOUTH = "f0873c37-4f09-41cd-be81-88e8df5b42ae"
AMBIDEXTROUS = "68cfe94a-fa7e-4129-a9b9-b5d73e3ced99"


def test_born_rich_raises_priority_karma_nuyen_cap() -> None:
    out = compute(_mundane("born-rich", quality_ids=[BORN_RICH], karma_nuyen=40))
    assert out.derived["karma_chargen"]["nuyen_karma_max"] == 40
    assert out.derived["nuyen_pool"] == 50_000 + 80_000
    assert out.derived["karma"]["spent"] == 5 + 40


def test_unrestricted_nuyen_lifts_the_karma_for_nuyen_cap() -> None:
    out = compute(_mundane("unrestricted", karma_nuyen=30, settings=SettingsState(unrestricted_nuyen=True)))
    assert out.derived["karma_chargen"]["nuyen_karma_max"] > 30
    assert out.derived["nuyen_pool"] == 50_000 + 60_000
    assert out.derived["karma"]["spent"] == 30


def test_in_debt_adds_nuyen_and_lowers_cap() -> None:
    out = compute(_mundane("in-debt", quality_ids=[IN_DEBT]))
    assert out.derived["nuyen_amt"] == 5000
    assert out.derived["karma_chargen"]["nuyen_karma_max"] == 9
    assert out.derived["nuyen_pool"] == 55_000


def test_trust_fund_covers_medium_lifestyle() -> None:
    out = compute(
        _mundane(
            "trust-fund",
            quality_ids=[TRUST_FUND_I, SINNER_NATIONAL],
            lifestyles=[LifestyleInstall(lifestyle_id=MEDIUM_LIFESTYLE, months=1)],
        )
    )
    assert out.derived["trustfund"] == 1
    assert out.derived["lifestyles"][0]["nuyen"] == 0
    assert out.derived["lifestyles"][0].get("trustfund") is True


def test_biocompatibility_and_sensitive_system_essence() -> None:
    base = compute(_mundane("ess0", cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)]))
    compat = compute(
        _mundane(
            "ess1",
            quality_ids=[BIOCOMPAT_CYBER],
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)],
        )
    )
    sens = compute(
        _mundane(
            "ess2",
            quality_ids=[SENSITIVE_SYSTEM],
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)],
        )
    )
    assert compat.derived["cyberware_ess_multiplier"] == 90
    assert compat.derived["essence_lost_cyber"] == 1.8
    assert sens.derived["essence_lost_cyber"] == 4.0
    assert base.derived["essence_lost_cyber"] == 2.0


def test_dealer_connection_discounts_groundcraft() -> None:
    car = next(v for v in catalog()["vehicles"] if v.get("category") == "Cars")
    base = compute(_mundane("dealer0", vehicles=[GearInstall(gear_id=car["id"])]))
    deal = compute(_mundane("dealer1", quality_ids=[DEALER_CONNECTION], vehicles=[GearInstall(gear_id=car["id"])]))
    assert base.derived["nuyen_spent"] > 0
    assert deal.derived["nuyen_spent"] == int(round(base.derived["nuyen_spent"] * 0.9))
    assert deal.derived["vehicles"][0]["discount_pct"] == 10


BIOCOMPAT_BIO = "dcecd7e5-8cf1-4f83-89fa-177e28cfba03"


def test_biocompatibility_bioware_scales_bioware_essence() -> None:
    base = compute(_mundane("bio-ess0", bioware=[CyberwareInstall(ware_id=TONER, rating=2)]))
    compat = compute(
        _mundane(
            "bio-ess1",
            quality_ids=[BIOCOMPAT_BIO],
            bioware=[CyberwareInstall(ware_id=TONER, rating=2)],
        )
    )
    assert compat.derived["bioware_ess_multiplier"] == 90
    assert base.derived["essence_lost_bio"] == 0.4
    assert compat.derived["essence_lost_bio"] == 0.3  # 0.4 * 0.9, floored to the tenth


def test_made_man_does_not_discount_gear() -> None:
    """Chummer's Made Man adds a contact and nothing else — its `mademan`
    improvement never touches a price, so a Restricted weapon costs the same."""
    weapon = next(w for w in catalog()["weapons"] if w.get("name") == "Ares Predator V")  # 5R
    base = compute(_mundane("mm-disc0", weapons=[WeaponInstall(weapon_id=weapon["id"])]))
    made = compute(_mundane("mm-disc1", quality_ids=[MADE_MAN], weapons=[WeaponInstall(weapon_id=weapon["id"])]))
    assert made.derived["nuyen_spent"] == base.derived["nuyen_spent"]
    assert not made.derived["weapons"][0].get("discount_pct")


def test_black_market_pipeline_discounts_and_lowers_cyberware_avail() -> None:
    contact = ContactInstall(name="Street Doc", connection=4, loyalty=2)
    base = compute(_mundane("bmp-cw0", cyberware=[CyberwareInstall(ware_id=WIRED, rating=2)]))
    bmp = compute(
        _mundane(
            "bmp-cw1",
            quality_ids=[BLACK_MARKET_PIPELINE],
            quality_extras={
                BLACK_MARKET_PIPELINE: "Cyberware",
                f"{BLACK_MARKET_PIPELINE}:contact": contact.id,
            },
            contacts=[contact],
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=2, discounted=True)],
        )
    )
    assert bmp.derived["nuyen_spent"] == int(round(base.derived["nuyen_spent"] * 0.9))
    assert bmp.derived["cyberware"][0]["nuyen"] == int(round(base.derived["cyberware"][0]["nuyen"] * 0.9))
    assert base.derived["cyberware"][0]["avail"] == "12R"
    assert bmp.derived["cyberware"][0]["avail"] == "10R"  # -2 from BMP


def test_black_market_pipeline_discounts_and_lowers_bioware_avail() -> None:
    contact = ContactInstall(name="Bio Fixer", connection=4, loyalty=2)
    base = compute(_mundane("bmp-bw0", bioware=[CyberwareInstall(ware_id=SUPRATHYROID)]))
    bmp = compute(
        _mundane(
            "bmp-bw1",
            quality_ids=[BLACK_MARKET_PIPELINE],
            quality_extras={
                BLACK_MARKET_PIPELINE: "Bioware",
                f"{BLACK_MARKET_PIPELINE}:contact": contact.id,
            },
            contacts=[contact],
            bioware=[CyberwareInstall(ware_id=SUPRATHYROID, discounted=True)],
        )
    )
    assert bmp.derived["nuyen_spent"] == int(round(base.derived["nuyen_spent"] * 0.9))
    assert bmp.derived["bioware"][0]["nuyen"] == int(round(base.derived["bioware"][0]["nuyen"] * 0.9))
    base_avail = int(base.derived["bioware"][0]["avail_value"])
    assert int(bmp.derived["bioware"][0]["avail_value"]) == max(0, base_avail - 2)


def test_college_education_halves_academic_knowledge_points() -> None:
    out = compute(
        _mundane(
            "college",
            quality_ids=[COLLEGE_EDUCATION_RF],
            knowledge_skills={"History": 4},
            knowledge_categories={"History": "Academic"},
        )
    )
    assert out.derived["points"]["knowledge"]["used"] == 2


def test_a_point_multiplier_prices_a_skill_and_its_specialization_together() -> None:
    """Chummer's `CurrentSpCost`: (points + specialization) × multiplier, rounded
    up once. Halving the 3 points and adding the specialization at full price
    made it 2 + 1 = 3; Chummer charges ceil(4 × 0.5) = 2."""
    out = compute(
        _mundane(
            "college-spec",
            quality_ids=[COLLEGE_EDUCATION_RF],
            knowledge_skills={"History": 3},
            knowledge_categories={"History": "Academic"},
            skill_specializations={"History": "Ancient"},
        )
    )
    assert out.derived["points"]["knowledge"]["used"] == 2


def test_a_multiplier_that_raises_the_cost_raises_the_specialization_too() -> None:
    out = compute(
        _mundane(
            "uncouth-spec",
            quality_ids=[UNCOUTH],
            skills={"Negotiation": 2},
            skill_specializations={"Negotiation": "Bargaining"},
        )
    )
    assert out.derived["points"]["skills"]["used"] == 6


def test_a_listed_knowledge_skill_can_change_its_type_and_the_cost_follows() -> None:
    """Chummer lets any non-native knowledge skill change type during creation
    (`KnowledgeSkill.AllowTypeChange`), listed ones too, and the new type brings
    its default attribute. Alcohol is listed as Interest; filed as Academic it
    is halved by College Education and rolls LOG."""
    out = compute(
        _mundane(
            "college-retyped",
            quality_ids=[COLLEGE_EDUCATION_RF],
            knowledge_skills={"Alcohol": 4},
            knowledge_categories={"Alcohol": "Academic"},
        )
    )
    assert out.derived["points"]["knowledge"]["used"] == 2
    row = next(r for r in out.derived["knowledge_skills"] if r["name"] == "Alcohol")
    assert (row["category"], row["attribute"]) == ("Academic", "LOG")


def test_a_listed_knowledge_skill_keeps_its_type_when_none_was_chosen() -> None:
    out = compute(_mundane("alcohol-listed", knowledge_skills={"Alcohol": 2}))
    row = next(r for r in out.derived["knowledge_skills"] if r["name"] == "Alcohol")
    assert (row["category"], row["attribute"]) == ("Interest", "INT")


def test_uncouth_doubles_social_active_skill_points() -> None:
    out = compute(_mundane("uncouth", quality_ids=[UNCOUTH], skills={"Negotiation": 2}))
    assert out.derived["points"]["skills"]["used"] == 4


def test_black_market_pipeline_warns_without_contact() -> None:
    out = compute(
        _mundane(
            "bmp-nocontact",
            quality_ids=[BLACK_MARKET_PIPELINE],
            quality_extras={BLACK_MARKET_PIPELINE: "Weapons"},
        )
    )
    assert has(out.derived["warnings"], "engine.gear.bmpContact")
    assert out.derived["black_market_avail_bonus"] == 0


def test_ambidextrous_flag() -> None:
    out = compute(_mundane("ambi", quality_ids=[AMBIDEXTROUS]))
    assert out.derived["ambidextrous"] is True


CYBER_SNOB = "aaac8dfd-dee6-4277-b967-9ec9089260a7"


def test_cyber_snob_disables_low_grades() -> None:
    out = compute(_mundane("cyber-snob", quality_ids=[CYBER_SNOB]))
    assert "Standard" in out.derived["disabled_cyberware_grades"]
    assert "Alphaware" in out.derived["disabled_cyberware_grades"]
    assert "Used" in out.derived["disabled_bioware_grades"]
    assert "Betaware" not in out.derived["disabled_cyberware_grades"]
    assert "disablecyberwaregrade" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "disablebiowaregrade" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_cyber_snob_clamps_standard_to_betaware() -> None:
    out = compute(
        _mundane(
            "snob-clamp",
            quality_ids=[CYBER_SNOB],
            cyberware=[CyberwareInstall(ware_id=DATAJACK, grade="Standard")],
        )
    )
    row = out.derived["cyberware"][0]
    assert row["grade"] == "Betaware"
    assert has(out.derived["warnings"], "engine.ware.gradeBanned", fallback="Betaware")
    # Datajack 0.1 × Betaware 0.7
    assert out.derived["essence"] == 5.93
    assert out.derived["nuyen_spent"] == 1500


def test_cyber_snob_allows_betaware() -> None:
    out = compute(
        _mundane(
            "snob-beta",
            quality_ids=[CYBER_SNOB],
            cyberware=[CyberwareInstall(ware_id=DATAJACK, grade="Betaware")],
        )
    )
    assert out.derived["cyberware"][0]["grade"] == "Betaware"
    assert not has(out.derived["warnings"], "engine.ware.gradeBanned")


def test_made_man_adds_free_group_contact() -> None:
    out = compute(_mundane("made-man", quality_ids=[MADE_MAN]))
    row = next(c for c in out.derived["contacts"] if c.get("source_quality_id") == MADE_MAN)
    assert row["connection"] == 1
    assert row["loyalty"] == 3
    assert row["free"] is True
    assert row["group"] is True
    assert row["locked"] is True
    assert row["billable"] == 0
    assert out.derived["made_man"] is True
    assert out.derived["contact_points"]["used"] == 0
    assert "addcontact" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_quality_contact_removed_when_quality_dropped() -> None:
    with_q = compute(_mundane("mm-on", quality_ids=[MADE_MAN]))
    assert any(c.get("source_quality_id") == MADE_MAN for c in with_q.derived["contacts"])
    # Persist quality-linked contact then drop the quality
    state = _mundane("mm-off", contacts=list(with_q.contacts or []))
    out = compute(state)
    assert not any(c.get("source_quality_id") == MADE_MAN for c in out.derived["contacts"])


def test_made_man_contact_excess_connection_costs_points() -> None:
    base = compute(_mundane("mm-base", quality_ids=[MADE_MAN]))
    contact = next(c for c in (base.contacts or []) if c.source_quality_id == MADE_MAN)
    contact.connection = 4  # free baseline 1+3=4; excess 3
    out = compute(
        _mundane(
            "mm-excess",
            quality_ids=[MADE_MAN],
            contacts=[contact],
        )
    )
    row = next(c for c in out.derived["contacts"] if c.get("source_quality_id") == MADE_MAN)
    assert row["billable"] == 3
    assert out.derived["contact_points"]["used"] == 3


def test_codeslinger_adds_action_dice_pool() -> None:
    out = compute(
        _mundane(
            "code-hack",
            quality_ids=[CODESLINGER],
            quality_extras={CODESLINGER: "Hack on the Fly"},
        )
    )
    assert out.derived["action_dice_pools"] == [
        {"category": "Matrix", "name": "Hack on the Fly", "bonus": 2, "source": "Codeslinger"}
    ]
    assert "actiondicepool" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert out.derived["karma"]["spent"] == 10


CRYSTAL_LIMB_ARM = "350844b9-db9f-4cce-83c3-e8965511e928"


def test_crystal_limb_requires_side() -> None:
    out = compute(_mage("crystal-empty", quality_ids=[CRYSTAL_LIMB_ARM]))
    assert has(out.derived["errors"], "engine.qualities.pickSide")


def test_crystal_limb_arm_selects_side() -> None:
    out = compute(
        _mage(
            "crystal-left",
            quality_ids=[CRYSTAL_LIMB_ARM],
            quality_extras={CRYSTAL_LIMB_ARM: "Left"},
        )
    )
    row = next(q for q in out.derived["qualities"] if q["id"] == CRYSTAL_LIMB_ARM)
    assert row["selectside"] is True
    assert row["side"] == "Left"
    assert not has(out.derived["errors"], "engine.qualities.pickSide")
    assert not has(out.derived["errors"], "engine.qualities.sideInvalid")


def test_crystal_limb_conflicts_with_cyberarm_same_side() -> None:
    out = compute(
        _mage(
            "crystal-dup",
            quality_ids=[CRYSTAL_LIMB_ARM],
            quality_extras={CRYSTAL_LIMB_ARM: "Left"},
            cyberware=[CyberwareInstall(id="arm1", ware_id=ARM, side="Left")],
        )
    )
    assert has(out.derived["errors"], "engine.qualities.sideDuplicate")


def test_crystal_limb_allows_opposite_cyberarm() -> None:
    out = compute(
        _mage(
            "crystal-ok",
            quality_ids=[CRYSTAL_LIMB_ARM],
            quality_extras={CRYSTAL_LIMB_ARM: "Left"},
            cyberware=[CyberwareInstall(id="arm1", ware_id=ARM, side="Right")],
        )
    )
    assert not has(out.derived["errors"], "engine.qualities.sideDuplicate")


INCOMPETENT = "216290b9-053d-4f6d-81c9-d1fe8ae346be"
AGED = "97e9b186-8924-4885-a948-3c781244a5cb"
UNEDUCATED = "d8362a78-54e9-4dbe-8388-6ba0a7b9df31"


def test_uncouth_disables_social_skill_groups() -> None:
    out = compute(_mundane("uncouth-groups", quality_ids=[UNCOUTH], skill_groups={"Acting": 1}))
    assert set(out.derived["disabled_skill_groups"]) >= {"Acting", "Influence"}
    assert has(out.derived["warnings"], "engine.skills.groupDisabled", name="Acting")


def test_incompetent_disables_chosen_skill_group() -> None:
    out = compute(
        _mundane(
            "incomp",
            quality_ids=[INCOMPETENT],
            quality_extras={INCOMPETENT: "Athletics"},
            skill_groups={"Athletics": 2},
        )
    )
    assert "Athletics" in out.derived["disabled_skill_groups"]
    assert has(out.derived["warnings"], "engine.skills.groupDisabled", name="Athletics")


def test_aged_adds_knowledge_points_and_lowers_physical_max() -> None:
    out = compute(_mundane("aged", quality_ids=[AGED]))
    assert out.derived["points"]["knowledge"]["max"] == 9
    assert out.derived["metatype_info"]["attributes"]["BOD"]["max"] == 5
    assert out.derived["metatype_info"]["attributes"]["AGI"]["max"] == 5


def test_uneducated_blocks_defaulting_and_doubles_tech_group_karma() -> None:
    from app.engine import snapshot_career_baseline

    out = compute(_mundane("uned", quality_ids=[UNEDUCATED]))
    assert set(out.derived["blocked_default_categories"]) >= {
        "Professional",
        "Academic",
        "Technical Active",
    }
    assert has(out.derived["warnings"], "engine.skills.noDefaulting")

    st = compute(_mundane("uned-g", quality_ids=[UNEDUCATED], skill_groups={"Electronics": 1}))
    st.career = True
    st.career_baseline = snapshot_career_baseline(st)
    st.skill_groups = {**dict(st.skill_groups), "Electronics": 2}
    raised = compute(st)
    # group rating 2 normally costs 10; Uneducated Technical Active groups ×2 → 20
    assert raised.derived["career_advancement_karma"] == 20


# --- chargen rule-parity checks -------------------------------------------

LIGHTNING_REFLEXES = "3564b678-7721-4a8d-ac79-1600cf92dc14"
ADRENALINE_SURGE = "f446f88c-26aa-496a-aa78-ed478bf0875f"


def test_positive_quality_karma_cap_at_chargen() -> None:
    out = compute(
        CharacterState(
            id="posq-cap",
            name="PosQCap",
            build_method="Karma",
            priorities=Priorities(),
            metatype="Human",
            attributes=default_attributes(find_metatype("Human", None)),
            quality_ids=[LIGHTNING_REFLEXES, ADRENALINE_SURGE],  # 20 + 12 karma
        )
    )
    assert has(out.derived["errors"], "engine.qualities.positiveCap")
    # career growth is not bound by the chargen cap
    career = compute(
        CharacterState(
            id="posq-cap-career",
            name="PosQCap",
            build_method="Karma",
            career=True,
            priorities=Priorities(),
            metatype="Human",
            attributes=default_attributes(find_metatype("Human", None)),
            quality_ids=[LIGHTNING_REFLEXES, ADRENALINE_SURGE],
        )
    )
    assert not has(career.derived["errors"], "engine.qualities.positiveCap")


def test_the_house_rule_lets_positive_qualities_pass_the_cap() -> None:
    """`<exceedpositivequalities>`: Chummer skips its positive limit check."""
    state = CharacterState(
        id="posq-exceed",
        name="PosQExceed",
        build_method="Karma",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        quality_ids=[LIGHTNING_REFLEXES, ADRENALINE_SURGE],
    )
    state.settings = SettingsState(exceed_positive_qualities=True)
    assert not has(compute(state).derived["errors"], "engine.qualities.positiveCap")


THERMO_SURGE = "fd346177-3791-44c0-af8c-7cf176fc9aa3"  # +3 positive metagenic
FEATHERS = "35279341-3611-439a-9550-8227b306198f"  # -3 negative metagenic


def test_metagenic_requires_changeling() -> None:
    """RF p.106 sells these to Changelings alone, but Chummer enforces it by
    filtering its purchase list and runs the metagenic validity block only
    `if (intMetagenicLimit > 0)`. A save holding one without SURGE is legal to
    Chummer, so this is said and not enforced."""
    out = compute(_mundane("mg-nochangeling", quality_ids=[THERMO_SURGE, FEATHERS]))
    assert not has(out.derived["errors"], "engine.qualities.metagenicNeedsChangeling")
    assert has(out.derived["warnings"], "engine.qualities.metagenicNeedsChangeling")


def test_metagenic_karma_must_balance() -> None:
    unbalanced = compute(_mundane("mg-unbalanced", quality_ids=[CHANGELING_I, THERMO_SURGE]))
    assert has(unbalanced.derived["errors"], "engine.qualities.metagenicUnbalanced")
    mg = unbalanced.derived["metagenic"]
    assert mg["limit"] == 30 and mg["positive"] == 3 and mg["negative"] == 0

    balanced = compute(_mundane("mg-balanced", quality_ids=[CHANGELING_I, THERMO_SURGE, FEATHERS]))
    assert not has(balanced.derived["errors"], "engine.qualities.metagenicUnbalanced")
    assert not any("Changeling" in e for e in balanced.derived["errors"])
    assert balanced.derived["metagenic"]["balanced"] is True


def test_a_changelings_metagenic_qualities_answer_to_the_surge_limit_not_the_25() -> None:
    """Chummer's `ContributeToLimit`: metagenic qualities on a SURGE Changeling
    are out of the 25-karma quality limits both ways. A legal Class I build
    with 30 each way used to be told it was over the positive and negative 25."""
    out = compute(_surge_thirty("mg-thirty"))
    keys = {e["key"] for e in out.derived["errors"]}
    assert "engine.qualities.positiveCap" not in keys
    assert "engine.qualities.negativeCap" not in keys
    assert not any(k.startswith("engine.qualities.metagenic") for k in keys)
    mg = out.derived["metagenic"]
    assert (mg["positive"], mg["negative"]) == (30, 30)


def test_gremlins_notoriety_comes_with_the_first_level_only() -> None:
    """`<firstlevelbonus><notoriety>1` (Gremlins, SR5 p.81): one point of
    Notoriety for taking the quality, not one per level."""
    gremlins = _quality_id("Gremlins")
    for levels, expected in ((0, 0), (1, 1), (3, 1)):
        out = compute(_human("gremlins", quality_ids=[gremlins] * levels)).derived
        assert out["notoriety"] == expected, levels


def test_infirm_first_level_clamp_is_not_left_unimplemented() -> None:
    """Infirm's `<attributemaxclamp>` (RF p.156) is what the attribute pass
    does anyway: a BOD above the lowered maximum comes down to it."""
    ch = _human("infirm", quality_ids=[_quality_id("Infirm")])
    ch.attributes["BOD"] = 6
    out = compute(ch).derived
    assert out["totals"]["BOD"] == 5
    assert not any("attributemaxclamp" in str(row) for row in out.get("unimplemented_bonuses") or [])


def _limit_quality(name: str) -> str:
    return next(str(q["id"]) for q in catalog()["qualities"] if q["name"] == name)


def _taken(ids: list[str]) -> dict[str, int]:
    out = compute(_human("limits", career=True, quality_ids=ids)).derived
    counts: dict[str, int] = {}
    for row in out["qualities"]:
        counts[row["name"]] = counts.get(row["name"], 0) + 1
    return counts


def test_indomitable_kinds_share_one_limit() -> None:
    """`<includeinlimit>` (Indomitable, SR5 p.75): Physical, Mental and Social
    count together toward the limit of 3."""
    physical = _limit_quality("Indomitable (Physical)")
    mental = _limit_quality("Indomitable (Mental)")
    counts = _taken([physical, physical, mental, mental])
    assert counts["Indomitable (Physical)"] + counts["Indomitable (Mental)"] == 3
    assert _taken([physical] * 3)["Indomitable (Physical)"] == 3


def test_tough_as_nails_has_its_own_shared_cap() -> None:
    """`<limitwithinclusions>4` (Tough as Nails, RF p.150): up to 3 of either
    kind, 4 across both."""
    physical = _limit_quality("Tough as Nails (Physical)")
    stun = _limit_quality("Tough as Nails (Stun)")
    counts = _taken([physical] * 3 + [stun] * 3)
    assert counts == {"Tough as Nails (Physical)": 3, "Tough as Nails (Stun)": 1}
    assert _taken([physical, physical, stun, stun]) == {"Tough as Nails (Physical)": 2, "Tough as Nails (Stun)": 2}


def test_buying_off_a_chargen_negative_costs_twice_what_it_gave() -> None:
    bad = _career_quality("Bad Luck")
    st = _into_career("career-buyoff", [bad["id"]])
    held = compute(st).derived
    assert "career_cost" not in _quality_row(held, "Bad Luck")
    st.quality_ids = []
    out = compute(st).derived
    assert out["qualities_removed"] == [
        {"id": bad["id"], "name": "Bad Luck", "category": "Negative", "karma": -bad["karma"] * 2}
    ]
    assert held["karma"]["remaining"] - out["karma"]["remaining"] == -bad["karma"] * 2


def test_infirm_caps_augmentation_at_the_natural_maximum() -> None:
    """`<attributemaxclamp>` (RF p.156): an Infirm character's augmented
    maximum for BOD/AGI/REA/STR is the lowered natural one, so Muscle
    Replacement cannot push STR past it. Attributes Infirm leaves alone keep
    their +4 headroom."""
    infirm = _career_quality("Infirm")["id"]
    muscle = CyberwareInstall(ware_id=_ware_named("Muscle Replacement"), rating=2)
    healthy_st = _mundane("mr", cyberware=[muscle])
    frail_st = _mundane("mr-infirm", cyberware=[muscle], quality_ids=[infirm])
    for st in (healthy_st, frail_st):
        st.attributes.update({"STR": 5, "AGI": 3})
    healthy = compute(healthy_st).derived
    frail = compute(frail_st).derived
    assert healthy["totals"]["STR"] == 7
    # Infirm lowers the STR maximum to 5, and STR is already there
    assert frail["totals"]["STR"] == 5
    # AGI 3 has room up to 5 — the +2 still fits
    assert frail["totals"]["AGI"] == 5
    spec = frail["metatype_info"]["attributes"]
    assert (spec["STR"]["max"], spec["STR"]["aug"]) == (5, 5)
    assert spec["INT"]["aug"] == healthy["metatype_info"]["attributes"]["INT"]["aug"]


def _elf_banshee(extras: dict[str, str] | None = None) -> dict:
    banshee = _career_quality("Infected: Banshee")["id"]
    st = CharacterState(
        id="banshee",
        name="banshee",
        metatype="Elf",
        attributes=default_attributes(find_metatype("Elf", None)),
        priorities=Priorities(),
        quality_ids=[banshee],
        quality_extras=extras or {},
    )
    out = compute(st).derived
    return {"out": out, "row": _quality_row(out, "Infected: Banshee"), "id": banshee}


def test_infected_quality_lists_the_critter_powers_it_grants() -> None:
    """`<critterpowers>` (RF p.126): every power the Infected quality names,
    each with its own `select` — the two Vulnerabilities stay apart."""
    row = _elf_banshee()["row"]
    names = [p["name"] for p in row["critter_powers"]]
    assert names == [
        "Dual Natured",
        "Essence Drain",
        "Immunity (Age)",
        "Essence Loss",
        "Allergy (Sunlight, Severe)",
        "Dietary Requirement (Metahuman Blood)",
        "Vulnerability (Silver)",
        "Vulnerability (Wood)",
    ]
    # looked up in critterpowers.xml like a spirit's powers
    assert next(p for p in row["critter_powers"] if p["name"] == "Dual Natured")["type"]


def test_infected_optional_power_is_a_required_pick_from_its_list() -> None:
    """`<optionalpowers>`: one power, chosen from the quality's own list."""
    first = _elf_banshee()
    assert first["row"]["optional_powers"] == [
        "Enhanced Senses (Hearing)",
        "Immunity (Toxins)",
        "Enhanced Senses (Smell)",
        "Immunity (Pathogens)",
    ]
    assert first["row"]["optional_power"] == ""
    assert has(first["out"]["errors"], "engine.qualities.pickOptionalPower")

    key = f"{first['id']}:optionalpower"
    picked = _elf_banshee({key: "Immunity (Toxins)"})
    assert not has(picked["out"]["errors"], "engine.qualities.pickOptionalPower")
    assert picked["row"]["optional_power"] == "Immunity (Toxins)"
    assert picked["row"]["critter_powers"][-1]["name"] == "Immunity (Toxins)"

    wrong = _elf_banshee({key: "Armor"})
    assert has(wrong["out"]["errors"], "engine.qualities.extraInvalid")
    assert "Armor" not in [p["name"] for p in wrong["row"]["critter_powers"]]


def test_qualities_without_critter_powers_carry_no_power_fields() -> None:
    row = compute(_mundane("plain", quality_ids=[ALLERGY_MILD])).derived["qualities"][0]
    assert "critter_powers" not in row and "optional_powers" not in row


def test_a_career_character_keeps_a_quality_whose_prerequisite_moved() -> None:
    """`<required>` is a purchase-time gate: Chummer calls `RequirementsMetAsync`
    when a quality is *added* and its validity sweep never re-checks. So a career
    character who bought Apt Pupil at Arcana 6 keeps it after moving those points
    — two of Chummer's own career saves depend on this."""
    apt_pupil = next(q for q in catalog()["qualities"] if q["name"] == "Apt Pupil")
    assert apt_pupil["required_tree"]  # it does have prerequisites to miss

    chargen = compute(_mundane("apt-chargen", quality_ids=[apt_pupil["id"]]))
    assert has(chargen.derived["errors"], "engine.qualities.prereq")

    state = _mundane("apt-career", quality_ids=[apt_pupil["id"]])
    state.career = True
    assert not has(compute(state).derived["errors"], "engine.qualities.prereq")


def test_a_spirit_pick_saved_the_short_way_is_still_valid() -> None:
    """Chummer stores Spirit Bane's pick as `Man`; the option list this app
    builds from the critter data spells it `Spirit of Man`. Left alone the pick
    matches nothing and the quality is reported as holding an invalid choice."""
    from app.chummer_import import chum5_to_state

    bane = next(q for q in catalog()["qualities"] if q["name"] == "Spirit Bane")
    assert "Spirit of Man" in bane["select_options"] and "Man" not in bane["select_options"]

    raw = f"""<?xml version="1.0" encoding="utf-8"?><character>
      <metatype>Human</metatype>
      <qualities><quality>
        <name>Spirit Bane</name><extra>Man</extra>
        <sourceid>{bane["id"]}</sourceid><qualitytype>Negative</qualitytype>
      </quality></qualities>
    </character>""".encode()
    state = chum5_to_state(raw)[0]
    assert state["quality_extras"][bane["id"]] == "Spirit of Man"


def test_free_grids_follow_hard_targets_or_the_setting() -> None:
    def grids(settings: SettingsState) -> int:
        out = compute(
            _mundane(
                "grids",
                lifestyles=[LifestyleInstall(lifestyle_id=MEDIUM_LIFESTYLE, months=1)],
                settings=settings,
            )
        )
        return sum(1 for q in out.derived["lifestyle"]["qualities"] if q.get("from_freegrid"))

    assert grids(SettingsState()) == 2
    assert grids(SettingsState(books=["SR5", "HT"])) == 2
    assert grids(SettingsState(books=["SR5"])) == 0
    assert grids(SettingsState(books=["SR5"], allow_free_grids=True)) == 2
