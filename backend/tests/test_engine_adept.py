"""Adepts: power points, powers, ways, qi foci and mentor powers."""

from app.engine import (
    compute,
    default_attributes,
    find_metatype,
)
from app.models import (
    AdeptPowerInstall,
    CharacterState,
    CyberwareInstall,
    InitiationChoice,
    Priorities,
    QiFocusInstall,
    SpellInstall,
    WeaponInstall,
)
from tests.engine_support import (
    CHAOS,
    DATAJACK,
    HERMETIC,
    IMPROVED_REFLEXES,
    MANABOLT,
    MASTER_ARCHER,
    MENTOR_SPIRIT,
    MISSILE_MASTERY,
    POWER_POINT_META,
    STUNBOLT,
    _adept,
    _mage,
)
from tests.notice_asserts import has

IMPROVED_ABILITY = "75821fb7-a180-4012-aa16-daa92ac3bb63"
IMPROVED_PHYS = "901d2af5-246a-447a-a8e2-b2e8c10593df"


def test_adept_b_has_six_power_points() -> None:
    out = compute(_adept("adept-b"))
    assert out.derived["totals"]["MAG"] == 6
    assert out.derived["power_points"]["max"] == 6
    assert out.derived["power_points"]["used"] == 0
    assert "adept" in out.derived["enabled_tabs"]


def test_adept_essence_loss_reduces_power_points() -> None:
    out = compute(_adept("adept-ess", cyberware=[CyberwareInstall(ware_id=DATAJACK)]))
    assert out.derived["totals"]["MAG"] == 5
    assert out.derived["power_points"]["max"] == 5


def test_improved_reflexes_rating_two_costs_two_point_five() -> None:
    out = compute(
        _adept(
            "reflexes",
            adept_powers=[AdeptPowerInstall(power_id=IMPROVED_REFLEXES, rating=2)],
        )
    )
    assert out.derived["power_points"]["used"] == 2.5
    assert out.derived["totals"]["REA"] == 3
    assert out.derived["initiative"]["dice"] == 3


def test_improved_physical_attribute_raises_agility() -> None:
    out = compute(
        _adept(
            "ipa",
            adept_powers=[AdeptPowerInstall(power_id=IMPROVED_PHYS, rating=2, extra="AGI")],
        )
    )
    assert out.derived["totals"]["AGI"] == 3
    assert out.derived["power_points"]["used"] == 2


def test_improved_ability_adds_dice_not_rating() -> None:
    out = compute(
        _adept(
            "ability",
            adept_powers=[AdeptPowerInstall(power_id=IMPROVED_ABILITY, rating=2, extra="Gymnastics")],
        )
    )
    assert out.derived["skill_bonus"]["Gymnastics"] == 2
    assert out.derived["skill_totals"].get("Gymnastics", 0) == 0
    assert out.derived["power_points"]["used"] == 1


PRECISION_THROWING = "18da4f2f-f813-4d17-8b7b-29b2751e9cfa"  # levels, max 3, throwrangestr = Rating*2
BOW_RATING_4 = "b6bf94d9-3513-409f-b5aa-29f415fe9fd7"


def test_missile_mastery_grants_throw_str() -> None:
    out = compute(_adept("missile-mastery", adept_powers=[AdeptPowerInstall(power_id=MISSILE_MASTERY)]))
    assert out.derived["throw_str"] == 1
    assert out.derived["skill_bonus"].get("Throwing Weapons") == 1
    assert out.derived["errors"] == []


def test_precision_throwing_evaluates_rating_times_two() -> None:
    base = compute(_adept("pt-none"))
    assert base.derived["throw_range_str"] == 0

    out = compute(_adept("pt-2", adept_powers=[AdeptPowerInstall(power_id=PRECISION_THROWING, rating=2)]))
    assert out.derived["throw_range_str"] == 4  # "Rating*2" -> 2*2
    assert out.derived["throw_str"] == 0


def test_master_archer_adds_category_dice_to_bows() -> None:
    out = compute(
        _adept(
            "master-archer",
            adept_powers=[AdeptPowerInstall(power_id=MASTER_ARCHER)],
            weapons=[WeaponInstall(weapon_id=BOW_RATING_4)],
        )
    )
    bow = out.derived["weapons"][0]
    assert bow["category"] == "Bows"
    assert bow["category_dice"] == 1
    assert out.derived["errors"] == []


def test_adept_power_overspend_is_an_error() -> None:
    out = compute(
        _adept(
            "overspend",
            letter="D",
            adept_powers=[AdeptPowerInstall(power_id=IMPROVED_REFLEXES, rating=2)],
        )
    )
    assert out.derived["totals"]["MAG"] == 2
    assert has(out.derived["errors"], "engine.adept.powerPointsOver")


def test_mystic_adept_buys_power_points_with_karma() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    out = compute(
        CharacterState(
            id="mystic",
            name="mystic",
            priorities=Priorities(Heritage="C", Attributes="A", Talent="C", Skills="B", Resources="E"),
            metatype="Human",
            talent="Mystic Adept",
            attributes=attrs,
            mystic_pp=2,
        )
    )
    assert out.derived["power_points"]["max"] == 2
    assert out.derived["karma"]["spent"] == 10
    assert out.derived["karma"]["remaining"] == 15
    assert "adept" in out.derived["enabled_tabs"]


COMBAT_SENSE = "76337564-7688-497f-84f9-302c6ece10fe"
WARRIOR_WAY = "32d0d753-9dad-4074-ab38-2d1ff5069a6a"
MAGICIAN_WAY = "64165b48-d67e-4bb8-b662-ca45fbf5b3c0"
ATHLETE_WAY = "3f536570-2f0c-40b1-a056-d310e29e983d"
BEAST_WAY = "2e7424d3-5d11-4c9d-ba92-f0431bb86786"
BEAR = "136a3dc5-d9c4-45ad-bc24-705f54692590"
HEINZELMANNCHEN = "62188234-323a-4c8e-96c4-b8b8a750e272"
NORSE_BERSERKER = "52668f12-2895-48e1-8b84-2382ef0fcee0"
BERSERKER_TEMPER = "ad6f8984-f0c2-41e9-a2d1-73a719d21a06"
CHAOS_POWER_CHOICE = "Adept: 2 free levels of Improved Potential"
IMPROVED_POTENTIAL_PHYSICAL = "Improved Potential (Physical)"
CHAOS_POTENTIAL = "Improved Potential (Chaos Mentor)"
# `<selectlimit>`'s only carrier is granted by that choice, so its own pick
# lives beside the choice's under a key naming the power.
CHAOS_LIMIT_KEY = f"{CHAOS_POWER_CHOICE} / {CHAOS_POTENTIAL}"
LIGHT_BODY = "ce7df757-792e-4fac-a86e-6b587586deb2"
AIR_WALKING = "8dc0a8e3-535a-4935-8c90-2079666e6a01"
ADEPT_SPELL = "87f0f97d-cbcf-4427-9259-baf376c9f55a"


def test_warrior_way_discounts_combat_sense() -> None:
    out = compute(
        _adept(
            "way-cs",
            quality_ids=[WARRIOR_WAY],
            adept_powers=[AdeptPowerInstall(power_id=COMBAT_SENSE, rating=1, discounted=True)],
        )
    )
    assert out.derived["power_points"]["used"] == 0.25
    assert out.derived["way_discount"]["used"] == 0.25
    assert out.derived["way_discount"]["max"] == 2
    assert out.derived["karma"]["spent"] == 20


def test_combat_sense_without_discount_is_half_point() -> None:
    out = compute(
        _adept(
            "cs-full",
            quality_ids=[WARRIOR_WAY],
            adept_powers=[AdeptPowerInstall(power_id=COMBAT_SENSE, rating=1, discounted=False)],
        )
    )
    assert out.derived["power_points"]["used"] == 0.5


def test_magician_way_can_discount_combat_sense() -> None:
    out = compute(
        _adept(
            "mage-way",
            quality_ids=[MAGICIAN_WAY],
            adept_powers=[AdeptPowerInstall(power_id=COMBAT_SENSE, rating=1, discounted=True)],
        )
    )
    assert out.derived["power_points"]["used"] == 0.25


def test_heinzelmannchen_adds_a_die_to_artisan_and_the_engineering_group() -> None:
    """`skillgrouplevel` is Chummer's free-level flavour, but the mentor reads
    "+1 dice pool modifier ... the Engineering skill group" (SAG p.121), so it
    is dice — the same +1 the sibling `specificskill` gives Artisan."""
    out = compute(
        _mage(
            "heinzel",
            quality_ids=[MENTOR_SPIRIT],
            mentor_id=HEINZELMANNCHEN,
            skills={"Artisan": 2, "Automotive Mechanic": 3},
        )
    )
    assert out.derived["skill_group_bonus"]["Engineering"] == 1
    assert out.derived["skill_bonus"]["Automotive Mechanic"] == 1
    assert out.derived["skill_bonus"]["Artisan"] == 1
    # A level would have shown up as a rating nobody paid for.
    assert out.derived["skill_totals"]["Automotive Mechanic"] == 3
    assert out.derived["skill_totals"].get("Nautical Mechanic", 0) == 0
    assert out.derived["points"]["skill_groups"]["used"] == 0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "skillgrouplevel" not in tags


def test_bear_mentor_gives_free_rapid_healing() -> None:
    out = compute(
        _adept(
            "bear",
            quality_ids=[MENTOR_SPIRIT],
            mentor_id=BEAR,
        )
    )
    assert out.derived["needs_mentor"] is True
    assert out.derived["mentor"]["name"] == "Bear"
    assert out.derived["damage_resistance"] == 2
    assert out.derived["power_points"]["used"] == 0
    names = {item["name"]: item for item in out.derived["adept_powers"]}
    assert names["Rapid Healing"]["free_levels"] == 1
    assert names["Rapid Healing"]["cost"] == 0
    assert out.derived["karma"]["spent"] == 5


def test_norse_berserker_tradition_grants_berserker_temper() -> None:
    out = compute(_adept("norse-berserker", tradition_id=NORSE_BERSERKER))
    names = {item["name"]: item for item in out.derived["adept_powers"]}
    assert names["Berserker Temper"]["power_id"] == BERSERKER_TEMPER
    assert names["Berserker Temper"]["free_levels"] == 1
    assert names["Berserker Temper"]["cost"] == 0
    assert out.derived["power_points"]["used"] == 0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "specificpower" not in tags


def _chaos(extras: dict[str, str]) -> object:
    return compute(
        _adept(
            "chaos",
            quality_ids=[MENTOR_SPIRIT],
            mentor_id=CHAOS,
            mentor_choices=[CHAOS_POWER_CHOICE],
            mentor_extras={CHAOS_POWER_CHOICE: IMPROVED_POTENTIAL_PHYSICAL, **extras},
        )
    )


def test_a_selectlimit_power_offers_the_three_limits() -> None:
    out = _chaos({})
    power = next(row for row in out.derived["adept_powers"] if row["name"] == CHAOS_POTENTIAL)
    assert power["select"] == "limit"
    assert power["options"] == ["Physical", "Mental", "Social"]
    assert power["extra"] == ""
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "selectlimit" not in tags


def test_an_unpicked_selectlimit_raises_no_limit() -> None:
    picked = _chaos({CHAOS_LIMIT_KEY: "Social"}).derived["limits"]
    unpicked = _chaos({}).derived["limits"]
    assert picked["social"] == unpicked["social"] + 1
    assert picked["physical"] == unpicked["physical"]
    assert picked["mental"] == unpicked["mental"]


def test_the_selectlimit_pick_chooses_which_limit_gains() -> None:
    mental = _chaos({CHAOS_LIMIT_KEY: "Mental"}).derived["limits"]
    social = _chaos({CHAOS_LIMIT_KEY: "Social"}).derived["limits"]
    assert mental["mental"] == social["mental"] + 1
    assert social["social"] == mental["social"] + 1


def test_the_chaos_limit_pick_is_offered_beside_the_power_pick() -> None:
    # The choice's own `extra` is spent on *which* Improved Potential it grants,
    # so the limit needs a select of its own.
    out = _chaos({CHAOS_LIMIT_KEY: "Mental"})
    choice = next(row for row in out.derived["mentor"]["choices"] if row["name"] == CHAOS_POWER_CHOICE)
    assert choice["extra"] == IMPROVED_POTENTIAL_PHYSICAL
    assert choice["power_targets"] == [
        {
            "power": CHAOS_POTENTIAL,
            "key": CHAOS_LIMIT_KEY,
            "kind": "limit",
            "extra": "Mental",
            "options": ["Physical", "Mental", "Social"],
        }
    ]


def test_beasts_way_grants_free_mentor_spirit() -> None:
    out = compute(
        _adept(
            "beast-way",
            quality_ids=[BEAST_WAY],
            mentor_id=BEAR,
        )
    )
    assert out.derived["needs_mentor"] is True
    assert out.derived["karma"]["spent"] == 20
    assert any(q["id"] == MENTOR_SPIRIT for q in out.derived["qualities"])


def test_air_walking_costs_two_karma() -> None:
    out = compute(
        _adept(
            "air-walk",
            quality_ids=[ATHLETE_WAY],
            adept_powers=[AdeptPowerInstall(power_id=LIGHT_BODY, rating=1)],
            adept_enhancements=[AIR_WALKING],
        )
    )
    assert out.derived["karma"]["spent"] == 22
    assert any(item["name"] == "Air Walking" for item in out.derived["enhancements"])
    assert not any("Air Walking" in warn for warn in out.derived["warnings"])


def test_adept_spell_selects_stunbolt() -> None:
    out = compute(
        _adept(
            "spell",
            adept_powers=[AdeptPowerInstall(power_id=ADEPT_SPELL, extra="Stunbolt")],
        )
    )
    assert out.derived["power_points"]["used"] == 1
    row = next(item for item in out.derived["adept_powers"] if item["name"] == "Adept Spell")
    assert row["extra"] == "Stunbolt"
    assert row["select"] == "spell"
    assert "Spellcasting" in out.derived["unlock_skills"]
    assert row["spell"]["dv"] == "F-3"
    assert row["spell"]["force"] == 6
    assert row["spell"]["drain"] == 3
    assert row["spell"]["drain_code"] == "S"
    assert row["spell"]["resist_attrs"] == "WIL+INT"


def test_qi_focus_binds_combat_sense() -> None:
    out = compute(
        _adept(
            "qi-cs",
            qi_foci=[QiFocusInstall(power_id=COMBAT_SENSE, rating=2, power_rating=1)],
        )
    )
    focus = out.derived["qi_foci"][0]
    assert focus["rating"] == 2
    assert focus["nuyen"] == 6000
    assert focus["karma"] == 2
    assert out.derived["nuyen_spent"] == 6000
    assert out.derived["karma"]["spent"] == 2
    assert out.derived["power_points"]["used"] == 0
    names = {item["name"]: item for item in out.derived["adept_powers"]}
    assert names["Combat Sense"]["free_levels"] == 1


def test_athlete_way_reduces_qi_binding_karma() -> None:
    out = compute(
        _adept(
            "qi-way",
            quality_ids=[ATHLETE_WAY],
            qi_foci=[QiFocusInstall(power_id=IMPROVED_ABILITY, rating=2, power_rating=1, extra="Gymnastics")],
        )
    )
    focus = out.derived["qi_foci"][0]
    assert focus["karma"] == 0
    assert out.derived["skill_bonus"]["Gymnastics"] == 1


def test_qi_focus_selectpowers_metadata_loaded() -> None:
    from app.data_loader import catalog

    cfg = catalog()["qi_focus"]
    assert cfg is not None
    slot = cfg["select_power"]
    assert slot["open_select"] is True
    assert slot["ignore_rating"] is True
    assert slot["points_per_level"] == 0.25
    assert slot["rating_expr"] == "Rating"
    assert slot["limit_expr"] == "Rating"


def test_qi_focus_selectpowers_grants_multiple_levels_from_force() -> None:
    out = compute(
        _adept(
            "qi-ia",
            qi_foci=[QiFocusInstall(power_id=IMPROVED_ABILITY, rating=4, power_rating=2, extra="Gymnastics")],
        )
    )
    focus = out.derived["qi_foci"][0]
    assert focus["rating"] == 4
    assert focus["power_rating"] == 2
    row = next(item for item in out.derived["adept_powers"] if item["power_id"] == IMPROVED_ABILITY)
    assert row["free_levels"] == 2
    assert out.derived["skill_bonus"]["Gymnastics"] == 2


def test_later_way_replaces_earlier_way() -> None:
    out = compute(
        _adept(
            "swap-way",
            quality_ids=[BEAST_WAY, WARRIOR_WAY],
            mentor_id=BEAR,
            adept_enhancements=[AIR_WALKING],
        )
    )
    names = {q["name"] for q in out.derived["qualities"]}
    assert "The Warrior's Way" in names
    assert "The Beast's Way" not in names
    assert not out.derived["needs_mentor"]
    assert out.derived["karma"]["spent"] == 20
    assert has(out.derived["warnings"], "engine.qualities.droppedIncompatible", name="The Beast's Way")


def test_way_swap_drops_old_enhancement() -> None:
    out = compute(
        _adept(
            "swap-enh",
            quality_ids=[ATHLETE_WAY, WARRIOR_WAY],
            adept_powers=[AdeptPowerInstall(power_id=LIGHT_BODY, rating=1)],
            adept_enhancements=[AIR_WALKING],
        )
    )
    assert "The Warrior's Way" in {q["name"] for q in out.derived["qualities"]}
    assert out.adept_enhancements == []
    assert has(out.derived["warnings"], "engine.adept.droppedWithQuality", name="Air Walking")


def test_adept_spell_overcast_is_physical() -> None:
    out = compute(
        _adept(
            "overcast",
            adept_powers=[AdeptPowerInstall(power_id=ADEPT_SPELL, extra="Stunbolt", force=7)],
        )
    )
    row = next(item for item in out.derived["adept_powers"] if item["name"] == "Adept Spell")
    assert row["spell"]["force"] == 7
    assert row["spell"]["drain"] == 4
    assert row["spell"]["drain_code"] == "P"


def test_adept_has_no_spell_tab() -> None:
    out = compute(_adept("no-spells"))
    assert "spells" not in out.derived["enabled_tabs"]
    assert out.derived["spell_points"]["free"] == 0


def test_mystic_adept_spell_uses_tradition() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["WIL"] = 4
    attrs["LOG"] = 5
    out = compute(
        CharacterState(
            id="mystic",
            name="mystic",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
            metatype="Human",
            talent="Mystic Adept",
            attributes=attrs,
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT)],
            adept_powers=[AdeptPowerInstall(power_id=ADEPT_SPELL, extra="Stunbolt")],
        )
    )
    assert "spells" in out.derived["enabled_tabs"]
    assert "adept" in out.derived["enabled_tabs"]
    assert out.derived["spells"][0]["spell"]["resist_attrs"] == "WIL+LOG"
    adept_row = next(item for item in out.derived["adept_powers"] if item["name"] == "Adept Spell")
    assert adept_row["spell"]["resist_attrs"] == "WIL+LOG"
    assert adept_row["spell"]["resist"] == 9


def test_power_point_metamagic_adds_pp() -> None:
    base = compute(_adept("pp-base"))
    out = compute(
        _adept(
            "pp-meta",
            initiate_grade=1,
            initiations=[InitiationChoice(grade=1, kind="metamagic", option_id=POWER_POINT_META)],
        )
    )
    assert out.derived["initiation"]["metamagics"][0]["name"] == "Power Point"
    assert out.derived["power_points"]["max"] == float(base.derived["power_points"]["max"]) + 1
    assert out.derived["karma"]["spent"] == 13


def test_adept_spell_rejects_ritual() -> None:
    out = compute(
        _adept(
            "no-ritual",
            adept_powers=[AdeptPowerInstall(power_id=ADEPT_SPELL, extra="Ward")],
        )
    )
    row = next(item for item in out.derived["adept_powers"] if item["name"] == "Adept Spell")
    assert row["extra"] != "Ward"
    assert has(out.derived["warnings"], "engine.adept.selectInvalid", name="Adept Spell", picked="Ward")


BAREHANDED_ADEPT = "742caf46-a10b-4aa1-a6bc-a53feb99748c"
DEATH_TOUCH = "9baed162-5e84-4f19-9b94-d543a560c067"
BUDDHISM = "a283220f-2197-4526-b15a-331b9185b326"


def test_barehanded_adept_touch_spells_and_doubled_drain() -> None:
    out = compute(
        _adept(
            "bha",
            quality_ids=[BAREHANDED_ADEPT],
            tradition_id=BUDDHISM,
            skills={"Unarmed Combat": 6},
            spells=[
                SpellInstall(spell_id=DEATH_TOUCH, force=6),
                SpellInstall(spell_id=MANABOLT, force=6),
            ],
        )
    )
    assert "spells" in out.derived["enabled_tabs"]
    assert set(out.derived["allow_spell_ranges"] or []) >= {"T", "T (A)"}
    assert out.derived["spell_range_gated"] is True
    # MAG 6 → half touch-only free spells = 3
    assert out.derived["spell_points"]["free"] == 3
    assert [s["name"] for s in out.derived["spells"]] == ["Death Touch"]
    assert has(out.derived["warnings"], "engine.spells.blockedByLimit", name="Manabolt")
    touch = out.derived["spells"][0]
    assert touch["free"] is True
    assert touch["barehanded_adept"] is True
    assert touch["useskill"] == "Unarmed Combat"
    assert touch["spell"]["force_max"] == 2  # MAG/3 rounded up
    assert touch["spell"]["force"] == 2
    # F-6 @2 → base 2, ×2 → 4
    assert touch["spell"]["drain"] == 4
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "allowspellrange" not in tags
    assert "freespells" not in tags
