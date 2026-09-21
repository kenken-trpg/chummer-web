"""Magicians: spells, traditions, drain, initiation, spirits and foci."""

from app.data_loader import catalog
from app.data_loader.loaders.magic.spells import load_spirits
from app.engine import (
    compute,
    default_attributes,
    find_metatype,
    spell_drain_value,
    tradition_resist,
)
from app.engine.lookups import critter_power_rows
from app.improvements import collect_effects
from app.models import (
    CharacterState,
    CyberwareInstall,
    FocusInstall,
    InitiationChoice,
    LifestyleInstall,
    Priorities,
    SettingsState,
    SpellInstall,
    SpiritInstall,
)
from tests.engine_support import (
    DATAJACK,
    EYES,
    HEAL,
    HERMETIC,
    HOLY_TEXT,
    HOLY_TEXT_POWER_CHOICE,
    LOW_LIFESTYLE,
    MANABOLT,
    MENTOR_SPIRIT,
    POWER_POINT_META,
    SPIRIT_FIRE,
    STUNBOLT,
    WEAPON_FOCUS,
    _adept,
    _human,
    _mage,
    _mage_rich,
    _mundane,
    _quality_row,
)
from tests.notice_asserts import has


def test_karma_chargen_magician_starts_at_magic_one_without_free_spells() -> None:
    out = compute(
        CharacterState(
            id="karma-mage",
            name="Karma Mage",
            build_method="Karma",
            priorities=Priorities(),
            metatype="Human",
            talent="Magician",
            attributes=default_attributes(find_metatype("Human", None)),
            tradition_id="19320625-bc1a-492f-8904-da6a847e5700",
        )
    )
    assert out.derived["totals"]["MAG"] == 1
    assert out.derived["spell_points"]["free"] == 0
    assert "spells" in out.derived["enabled_tabs"]
    assert out.attributes["MAG"] == 1


def test_magician_a_starts_at_magic_six_without_special_cost() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["MAG"] = 0
    state = CharacterState(
        id="mage",
        name="Mage",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
        metatype="Human",
        talent="Magician",
        attributes=attrs,
    )
    out = compute(state)
    assert out.derived["totals"]["MAG"] == 6
    assert out.derived["totals"]["RES"] == 0
    assert out.derived["points"]["special"]["used"] == 0
    assert "MAG" in out.derived["enabled_tabs"]
    assert "spells" in out.derived["enabled_tabs"]
    assert out.derived["spell_points"]["free"] == 10
    assert has(out.derived["warnings"], "engine.spells.pickTradition")
    assert out.derived["errors"] == []


def test_essence_loss_reduces_magic() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="mageware",
        name="Mageware",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
        metatype="Human",
        talent="Magician",
        attributes=attrs,
        cyberware=[CyberwareInstall(ware_id=DATAJACK)],
    )
    out = compute(state)
    assert out.derived["totals"]["MAG"] == 5
    assert out.derived["essence"] == 5.9


def test_unknown_bonus_does_not_crash() -> None:
    effects = collect_effects(
        [
            (
                "Dummy",
                [
                    {"tag": "notarealbonus", "value": "1"},
                    {"tag": "armor", "value": "2"},
                ],
            )
        ]
    )
    assert effects["armor"] == 2
    assert effects["unimplemented"][0]["tag"] == "notarealbonus"


def test_cybereyes_include_image_link() -> None:
    state = CharacterState(
        id="eyes",
        name="Eyes",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[CyberwareInstall(ware_id=EYES, rating=1)],
    )
    out = compute(state)
    names = {item["name"] for item in out.derived["cyberware"]}
    assert "Image Link" in names
    assert out.derived["essence"] == 5.8
    assert out.derived["nuyen_spent"] == 4000
    eyes = next(item for item in out.derived["cyberware"] if item["ware_id"] == EYES)
    assert eyes["capacity_used"] == 0
    assert eyes["capacity_max"] == 4
    link = next(item for item in out.derived["cyberware"] if item["name"] == "Image Link")
    assert link["included"]
    assert link["essence"] == 0
    assert link["nuyen"] == 0


ASTRAL_CHAMELEON = "7d81f676-e523-4ec6-ae98-8d801f90b031"


def test_astral_chameleon_requires_magic() -> None:
    mundane = compute(_human("astral-mundane", quality_ids=[ASTRAL_CHAMELEON]))
    assert has(mundane.derived["errors"], "engine.qualities.prereq", name="Astral Chameleon")
    attrs = default_attributes(find_metatype("Human", None))
    mage = compute(
        CharacterState(
            id="astral-mage",
            name="astral-mage",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
            metatype="Human",
            talent="Magician",
            attributes=attrs,
            quality_ids=[ASTRAL_CHAMELEON],
        )
    )
    assert not has(mage.derived["errors"], "engine.qualities.prereq")


def test_a_mentor_power_target_still_reads_the_plain_choice_key() -> None:
    # Holy Text has no `<selectpowers>`, so its granted power's target stays
    # under the choice name — where every character saved so far keeps it.
    out = compute(
        _adept(
            "holy-text-target",
            quality_ids=[MENTOR_SPIRIT],
            mentor_id=HOLY_TEXT,
            mentor_choices=[HOLY_TEXT_POWER_CHOICE],
            mentor_extras={HOLY_TEXT_POWER_CHOICE: "Mystic Armor"},
        )
    )
    choice = next(row for row in out.derived["mentor"]["choices"] if row["name"] == HOLY_TEXT_POWER_CHOICE)
    assert choice["power_targets"] == []


def test_spell_drain_formulas() -> None:
    assert spell_drain_value("F-3", 6) == 3
    assert spell_drain_value("F", 5) == 5
    assert spell_drain_value("F-6", 6) == 2
    assert spell_drain_value("F+1", 4) == 5
    assert spell_drain_value("Special", 6) is None
    assert spell_drain_value("0", 6) == 0


ELDER_GOD = "4bbe470b-51a7-494b-8ccf-5c638e141049"
AGONY = "46b12a6a-9d9d-4176-bfd6-80e8e21cb0e4"
SHAMANIC = "8d185e0e-5f49-4992-babd-d1ac9c848f68"


def _learnable_ids(count: int) -> list[str]:
    return [item["id"] for item in catalog()["spells"] if item.get("learnable")][:count]


TRADITIONALIST_SHAMAN = "9d0cec5d-4350-47da-9ced-6619bbcb1936"  # a lone `<addquality>`
VIGILA_EVANGELICA = "ca673acd-961e-4491-8a8d-ddf0c577441b"  # the same inside `<addqualities>`
DRUID_TRADITIONAL = "77288f4d-e262-47b6-aad8-2edff23859cb"
CODE_OF_HONOR_CODE = "Harmony with Nature, the Shaman\u2019s Code"


def test_a_tradition_grants_the_quality_it_names() -> None:
    """`<addquality select="...">` — the tradition demands it and names the pick."""
    out = compute(_mage("shaman-code", tradition_id=TRADITIONALIST_SHAMAN))
    row = next(q for q in out.derived["qualities"] if q["name"] == "Code of Honor")
    assert row["extra"] == CODE_OF_HONOR_CODE
    assert row["free"] is True
    assert "addquality" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_a_tradition_grant_costs_nothing_either_way() -> None:
    """The follower never chose it, so the karma a negative quality pays back
    is not theirs to collect (nor a positive one's cost theirs to pay)."""
    granted = compute(_mage("shaman-karma", tradition_id=TRADITIONALIST_SHAMAN))
    plain = compute(_mage("hermetic-karma", tradition_id=HERMETIC))
    assert granted.derived["karma"] == plain.derived["karma"]


def test_a_tradition_grants_from_the_plural_container_too() -> None:
    out = compute(_mage("theurgy", tradition_id=VIGILA_EVANGELICA))
    assert "Pacifist I" in [q["name"] for q in out.derived["qualities"]]


def test_a_granted_mentor_spirit_still_asks_for_the_mentor() -> None:
    """Druid [Traditional] grants Mentor Spirit — the pick stays the player's."""
    out = compute(_mage("druid", tradition_id=DRUID_TRADITIONAL))
    assert "Mentor Spirit" in [q["name"] for q in out.derived["qualities"]]
    assert out.derived["needs_mentor"] is True
    assert has(out.derived["warnings"], "engine.qualities.mentorMissing")


def test_a_mundane_is_handed_nothing_by_a_tradition() -> None:
    out = compute(_mundane("mundane-trad", tradition_id=TRADITIONALIST_SHAMAN))
    assert [q["name"] for q in out.derived["qualities"]] == []


def test_tradition_resist_hermetic() -> None:
    spec = next(item for item in catalog()["traditions"] if item["id"] == HERMETIC)
    pool, label = tradition_resist(spec, {"WIL": 5, "LOG": 6, "INT": 2, "CHA": 1})
    assert pool == 11
    assert label == "WIL+LOG"


def test_mage_stunbolt_uses_hermetic_drain() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["WIL"] = 5
    attrs["LOG"] = 4
    attrs["INT"] = 2
    out = compute(
        _mage(
            "hermetic-drain",
            attributes=attrs,
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT)],
        )
    )
    row = out.derived["spells"][0]
    assert row["name"] == "Stunbolt"
    assert row["free"] is True
    assert row["karma"] == 0
    assert row["spell"]["dv"] == "F-3"
    assert row["spell"]["force"] == 6
    assert row["spell"]["drain"] == 3
    assert row["spell"]["drain_code"] == "S"
    assert row["spell"]["resist"] == 9
    assert row["spell"]["resist_attrs"] == "WIL+LOG"
    assert out.derived["tradition"]["name"] == "Hermetic"
    assert out.derived["karma"]["spent"] == 0
    assert not has(out.derived["warnings"], "engine.kind.tradition")


def test_mage_overcast_is_physical() -> None:
    out = compute(
        _mage(
            "mage-overcast",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT, force=7)],
        )
    )
    row = out.derived["spells"][0]
    assert row["spell"]["force"] == 7
    assert row["spell"]["drain"] == 4
    assert row["spell"]["drain_code"] == "P"


def test_eleventh_spell_costs_five_karma() -> None:
    ids = _learnable_ids(11)
    assert len(ids) == 11
    out = compute(
        _mage(
            "eleven",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=sid) for sid in ids],
        )
    )
    assert out.derived["spell_points"]["used"] == 11
    assert out.derived["spell_points"]["paid"] == 1
    assert out.derived["spells"][-1]["free"] is False
    assert out.derived["spells"][-1]["karma"] == 5
    assert out.derived["karma"]["spent"] == 5
    assert out.derived["errors"] == []


def test_duplicate_spell_is_dropped() -> None:
    out = compute(
        _mage(
            "dup",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT), SpellInstall(spell_id=STUNBOLT)],
        )
    )
    assert len(out.derived["spells"]) == 1
    assert has(out.derived["warnings"], "engine.spells.duplicateDropped")


def test_aspected_magician_buys_spells() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    out = compute(
        CharacterState(
            id="aspected",
            name="aspected",
            priorities=Priorities(Heritage="C", Attributes="A", Talent="B", Skills="D", Resources="E"),
            metatype="Human",
            talent="Aspected Magician",
            attributes=attrs,
            tradition_id=SHAMANIC,
            spells=[SpellInstall(spell_id=STUNBOLT)],
        )
    )
    assert out.derived["spell_points"]["free"] == 0
    assert out.derived["spells"][0]["karma"] == 5
    assert out.derived["karma"]["spent"] == 5
    assert out.derived["spells"][0]["spell"]["resist_attrs"] == "WIL+CHA"


WARD = "3cea53a2-7628-4009-9bc4-af2f141fc28d"
RECHARGE_REAGENTS = "e45f4b5d-8969-4e03-ae55-583beee464fc"


def test_ward_ritual_uses_free_slot() -> None:
    out = compute(
        _mage(
            "ward",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=WARD)],
        )
    )
    row = out.derived["spells"][0]
    assert row["name"] == "Ward"
    assert row["kind"] == "ritual"
    assert row["useskill"] == "Ritual Spellcasting"
    assert row["has_force"] is True
    assert row["free"] is True
    assert row["spell"]["drain"] is None
    assert row["spell"]["dv"] == "Special"
    assert out.derived["spell_points"]["used"] == 1
    assert out.derived["karma"]["spent"] == 0


def test_enchantment_warns_for_metamagic() -> None:
    out = compute(
        _mage(
            "reagents",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=RECHARGE_REAGENTS)],
        )
    )
    row = out.derived["spells"][0]
    assert row["name"] == "Recharge Reagents"
    assert row["kind"] == "enchantment"
    assert row["useskill"] == "Artificing"
    assert row["has_force"] is False
    assert row["spell"] is None
    assert row["free"] is True
    assert has(out.derived["warnings"], "engine.spells.requires", needed=["Geomancy"])


GEOMANCY_ART = "5b922bcf-4114-4c49-a4f3-0f3dcb45dd2f"
QUICKENING_META = "4ea558ed-0fe8-4b9e-b2fa-afffb3eb2476"


def test_initiation_grade_one_costs_thirteen_karma() -> None:
    out = compute(
        _mage(
            "init1",
            initiate_grade=1,
            initiations=[InitiationChoice(grade=1, kind="metamagic", option_id=QUICKENING_META)],
        )
    )
    assert "initiation" in out.derived["enabled_tabs"]
    assert out.derived["initiation"]["grade"] == 1
    assert out.derived["initiation"]["karma"] == 13
    assert out.derived["karma"]["spent"] == 13
    assert out.derived["initiation"]["metamagics"][0]["name"] == "Quickening"


def test_quickening_metamagic_is_reported_on_the_sheet() -> None:
    """`quickeningmetamagic` grants no dice — it is the permission to lock a
    sustained spell in with karma (SR5 p.326), so the sheet just says so."""
    out = compute(
        _mage(
            "quicken",
            initiate_grade=1,
            initiations=[InitiationChoice(grade=1, kind="metamagic", option_id=QUICKENING_META)],
        )
    )
    assert out.derived["initiation"]["quickening"] is True
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "quickeningmetamagic" not in tags


def test_a_mage_without_quickening_says_nothing() -> None:
    out = compute(
        _mage(
            "no-quicken",
            initiate_grade=1,
            initiations=[InitiationChoice(grade=1, kind="metamagic", option_id=POWER_POINT_META)],
        )
    )
    assert out.derived["initiation"]["quickening"] is False


def test_initiation_ordeal_and_group_discount_karma() -> None:
    ordeal = compute(
        _mage(
            "init-ordeal",
            initiate_grade=1,
            initiations=[InitiationChoice(grade=1, kind="metamagic", option_id=QUICKENING_META, ordeal=True)],
        )
    )
    # grade 1 base 13 × 0.9 = 11.7 → 12
    assert ordeal.derived["initiation"]["karma"] == 12
    assert ordeal.derived["initiation"]["choices"][0]["ordeal"] is True

    both = compute(
        _mage(
            "init-both",
            initiate_grade=1,
            initiations=[
                InitiationChoice(grade=1, kind="metamagic", option_id=QUICKENING_META, group=True, ordeal=True)
            ],
        )
    )
    # 13 × 0.8 = 10.4 → 10
    assert both.derived["initiation"]["karma"] == 10


def test_initiation_raises_mag_max() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["MAG"] = 7
    out = compute(
        _mage(
            "init-mag",
            attributes=attrs,
            initiate_grade=1,
            initiations=[InitiationChoice(grade=1, kind="metamagic", option_id=QUICKENING_META)],
        )
    )
    assert out.derived["metatype_info"]["attributes"]["MAG"]["max"] == 7
    assert out.attributes["MAG"] == 7
    assert out.derived["totals"]["MAG"] == 7


def test_geomancy_art_clears_recharge_warning() -> None:
    out = compute(
        _mage(
            "geomancy",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=RECHARGE_REAGENTS)],
            initiate_grade=1,
            initiations=[InitiationChoice(grade=1, kind="art", option_id=GEOMANCY_ART)],
        )
    )
    assert out.derived["initiation"]["arts"][0]["name"] == "Geomancy"
    assert not any("Geomancy" in warn for warn in out.derived["warnings"])


def test_initiation_grade_above_mag_errors() -> None:
    out = compute(_mage("init-over", initiate_grade=7))
    assert has(out.derived["errors"], "engine.initiation.gradeOverMagic")


def test_ritual_and_spell_share_free_pool() -> None:
    out = compute(
        _mage(
            "mix",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT), SpellInstall(spell_id=WARD)],
        )
    )
    kinds = {item["name"]: item["kind"] for item in out.derived["spells"]}
    assert kinds["Stunbolt"] == "spell"
    assert kinds["Ward"] == "ritual"
    assert out.derived["spell_points"]["used"] == 2
    assert out.derived["karma"]["spent"] == 0


def test_enchanter_can_buy_enchantments() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    out = compute(
        CharacterState(
            id="enchanter",
            name="enchanter",
            priorities=Priorities(Heritage="C", Attributes="A", Talent="C", Skills="B", Resources="E"),
            metatype="Human",
            talent="Enchanter",
            attributes=attrs,
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=RECHARGE_REAGENTS)],
        )
    )
    assert "spells" in out.derived["enabled_tabs"]
    assert out.derived["spell_points"]["free"] == 0
    assert out.derived["spells"][0]["karma"] == 5
    assert out.derived["karma"]["spent"] == 5


POWER_FOCUS = "62bfb38d-5515-440b-83ed-289ed926d27e"
SPELLCASTING_COMBAT = "2f485376-54c1-41be-8678-79cc98e04ebc"


def test_hermetic_binds_fire_spirit() -> None:
    out = compute(
        _mage(
            "bind-fire",
            tradition_id=HERMETIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, services=2)],
        )
    )
    row = out.derived["spirits"][0]
    assert row["name"] == "Spirit of Fire"
    assert row["role"] == "combat"
    assert row["force"] == 3
    assert row["services"] == 2
    assert row["nuyen"] == 60
    assert row["attributes"]["BOD"] == 4
    assert row["attributes"]["AGI"] == 5
    assert row["attributes"]["REA"] == 6
    assert row["attributes"]["STR"] == 1
    assert row["attributes"]["INI"] == 9
    # Each power carries what the table gives it (SR5 p.394), not just a name
    assert {"name": "Elemental Attack", "type": "P", "action": "Complex"}.items() <= next(
        p for p in row["powers"] if p["name"] == "Elemental Attack"
    ).items()
    assert out.derived["nuyen_spent"] == 60
    assert "spirits" in out.derived["enabled_tabs"]


def test_a_spirit_power_carries_what_the_table_gives_it() -> None:
    """`traditions.xml` names a spirit's powers and nothing else, so each name
    is filled in from `critterpowers.xml`: Engulf is a Complex Action at Touch
    that you sustain (SR5 p.396)."""
    out = compute(
        _mage(
            "spirit-powers",
            tradition_id=HERMETIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, services=1, bound=True)],
        )
    )
    engulf = next(p for p in out.derived["spirits"][0]["powers"] if p["name"] == "Engulf")
    assert (engulf["type"], engulf["action"], engulf["range"], engulf["duration"]) == (
        "P",
        "Complex",
        "Touch",
        "Sustained",
    )


def test_a_power_names_the_flavour_it_comes_in() -> None:
    """A toxic spirit's `Engulf (Fire)` is Engulf, in fire: the bracket says
    what it engulfs you with, and the power before it is what holds the
    action and the duration."""
    assert critter_power_rows(["Engulf (Fire)"])[0] == {
        "name": "Engulf (Fire)",
        "type": "P",
        "action": "Complex",
        "range": "Touch",
        "duration": "Sustained",
        "source": "SR5",
        "page": "396",
    }


def test_a_power_the_data_does_not_describe_is_still_listed() -> None:
    """Three names in `traditions.xml` have no entry of their own — one of
    them is a typo upstream. The name is what the sheet prints, so the row
    comes back with the name and nothing else rather than going missing."""
    assert critter_power_rows(["Natural Weaponry"]) == [
        {"name": "Natural Weaponry", "type": "", "action": "", "range": "", "duration": "", "source": "", "page": ""}
    ]


def test_shaman_rejects_fire_spirit() -> None:
    out = compute(
        _mage(
            "wrong-spirit",
            tradition_id=SHAMANIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, services=1)],
        )
    )
    assert out.derived["spirits"] == []
    assert has(out.derived["warnings"], "engine.spirits.notInTradition")


def test_spirit_force_clamps_to_magic() -> None:
    out = compute(
        _mage(
            "spirit-cap",
            tradition_id=HERMETIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=12, services=9)],
        )
    )
    row = out.derived["spirits"][0]
    assert row["force"] == 6
    assert row["services"] == 6
    assert row["nuyen"] == 120


def test_enchanter_cannot_bind_spirits() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    out = compute(
        CharacterState(
            id="no-summon",
            name="no-summon",
            priorities=Priorities(Heritage="C", Attributes="A", Talent="C", Skills="B", Resources="E"),
            metatype="Human",
            talent="Enchanter",
            attributes=attrs,
            tradition_id=HERMETIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=2, services=1)],
        )
    )
    assert out.derived["spirits"] == []
    assert "spirits" not in out.derived["enabled_tabs"]
    assert "foci" in out.derived["enabled_tabs"]


def test_power_focus_costs_and_boosts_magic_skills() -> None:
    out = compute(
        _mage_rich(
            "power-focus",
            tradition_id=HERMETIC,
            foci=[FocusInstall(gear_id=POWER_FOCUS, force=2)],
        )
    )
    row = out.derived["foci"][0]
    assert row["name"] == "Power Focus"
    assert row["force"] == 2
    assert row["nuyen"] == 36000
    # Force x `<karmapowerfocus>` (6): a power focus is the dearest to bond
    assert row["karma"] == 12
    assert out.derived["nuyen_spent"] == 36000
    assert out.derived["karma"]["spent"] == 12
    assert out.derived["skill_bonus"]["Spellcasting"] == 2
    assert out.derived["skill_bonus"]["Summoning"] == 2
    assert out.derived["focus_limits"]["count"] == 1
    assert out.derived["focus_limits"]["force"] == 2


def test_spellcasting_focus_marks_combat_spells() -> None:
    out = compute(
        _mage_rich(
            "spell-focus",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT)],
            foci=[FocusInstall(gear_id=SPELLCASTING_COMBAT, force=3)],
        )
    )
    assert out.derived["foci"][0]["nuyen"] == 12000
    # Force 3 x `<karmaspellcastingfocus>` (2)
    assert out.derived["foci"][0]["karma"] == 6
    assert out.derived["spells"][0]["focus_bonus"] == 3


def test_bound_focus_count_cannot_exceed_magic() -> None:
    out = compute(
        _mage_rich(
            "too-many-foci",
            foci=[FocusInstall(gear_id=WEAPON_FOCUS, force=1) for _ in range(7)],
        )
    )
    assert out.derived["focus_limits"]["count"] == 7
    assert has(out.derived["errors"], "engine.foci.countOverMagic")


def test_bound_focus_force_total_cannot_exceed_magic_times_five() -> None:
    out = compute(
        _mage_rich(
            "too-much-force",
            foci=[FocusInstall(gear_id=WEAPON_FOCUS, force=6) for _ in range(6)],
        )
    )
    assert out.derived["focus_limits"]["force"] == 36
    assert has(out.derived["errors"], "engine.foci.forceOverLimit")


def test_summoned_spirit_uses_summoning_test() -> None:
    out = compute(
        _mage(
            "summon-fire",
            tradition_id=HERMETIC,
            skills={"Summoning": 4},
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, bound=False, hits=5, opposed_hits=2)],
        )
    )
    row = out.derived["spirits"][0]
    assert row["bound"] is False
    assert row["nuyen"] == 0
    assert row["services"] == 3
    assert row["force"] == 3
    assert out.derived["nuyen_spent"] == 0
    test = row["test"]
    assert test["skill"] == "Summoning"
    assert test["pool"] == 10
    assert test["vs"] == 3
    assert test["limit"] == 3
    assert test["drain"] == 4
    assert test["drain_code"] == "S"
    assert test["net"] == 3
    assert test["missing"] is False


def test_summoned_overcast_is_physical() -> None:
    out = compute(
        _mage(
            "summon-over",
            tradition_id=HERMETIC,
            skills={"Summoning": 6},
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=7, bound=False, hits=4, opposed_hits=3)],
        )
    )
    row = out.derived["spirits"][0]
    assert row["force"] == 7
    assert row["test"]["vs"] == 7
    assert row["test"]["physical"] is True
    assert row["test"]["drain"] == 6
    assert row["test"]["drain_code"] == "P"
    assert row["services"] == 1


def test_bound_spirit_uses_binding_test() -> None:
    out = compute(
        _mage(
            "bind-test",
            tradition_id=HERMETIC,
            skills={"Binding": 3},
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, bound=True, hits=6, opposed_hits=2)],
        )
    )
    row = out.derived["spirits"][0]
    assert row["bound"] is True
    assert row["nuyen"] == 60
    assert row["services"] == 4
    assert row["test"]["skill"] == "Binding"
    assert row["test"]["pool"] == 9
    assert row["test"]["vs"] == 6
    assert row["test"]["drain"] == 4


def test_summon_without_skill_warns() -> None:
    out = compute(
        _mage(
            "no-summon-skill",
            tradition_id=HERMETIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=1, bound=False)],
        )
    )
    assert out.derived["spirits"][0]["test"]["missing"] is True
    assert has(out.derived["warnings"], "engine.spirits.summonNeedsSkill", skill="Summoning")


def test_crafted_power_focus_uses_formula_and_artificing() -> None:
    out = compute(
        _mage_rich(
            "craft-power",
            skills={"Artificing": 5},
            foci=[
                FocusInstall(gear_id=POWER_FOCUS, force=2, crafted=True, formula_bought=True, hits=5, opposed_hits=2)
            ],
        )
    )
    row = out.derived["foci"][0]
    assert row["crafted"] is True
    assert row["formula_nuyen"] == 9000
    assert row["reagent_nuyen"] == 40
    assert row["nuyen"] == 9040
    assert row["retail_nuyen"] == 36000
    # crafting changes what it costs in nuyen, not what bonding costs in karma
    assert row["karma"] == 12
    test = row["test"]
    assert test["skill"] == "Artificing"
    assert test["pool"] == 11
    assert test["vs"] == 4
    assert test["days"] == 2
    assert test["drain"] == 4
    assert test["net"] == 3
    assert test["missing"] is False


def test_designed_formula_skips_formula_price() -> None:
    out = compute(
        _mage_rich(
            "design-formula",
            skills={"Artificing": 4, "Arcana": 3},
            foci=[FocusInstall(gear_id=POWER_FOCUS, force=1, crafted=True, formula_bought=False)],
        )
    )
    row = out.derived["foci"][0]
    assert row["nuyen"] == 20
    assert row["formula_nuyen"] == 0
    assert row["formula_test"]["skill"] == "Arcana"
    assert row["formula_test"]["vs"] == 2
    assert row["formula_test"]["limit_name"] == "Mental"
    assert row["formula_test"]["missing"] is False


def test_craft_without_artificing_warns() -> None:
    out = compute(
        _mage_rich(
            "no-artifice",
            foci=[FocusInstall(gear_id=POWER_FOCUS, force=1, crafted=True, hits=1, opposed_hits=1)],
        )
    )
    assert out.derived["foci"][0]["test"]["missing"] is True
    assert has(out.derived["warnings"], "engine.foci.needsArtificing")
    assert has(out.derived["warnings"], "engine.foci.craftFailed")


DAREADRENALINE = "6a62e21f-f291-4e93-b109-df9c56c938f9"
DIMMER_BULB = "7706ce23-77c2-470f-bb7e-6a4e56fa78fe"


def test_dareadrenaline_drain_resist() -> None:
    base = compute(_mage("drain-base", tradition_id=HERMETIC))
    out = compute(
        _mage(
            "drain",
            tradition_id=HERMETIC,
            bioware=[CyberwareInstall(ware_id=DAREADRENALINE)],
        )
    )
    assert base.derived["drain_resist"]["pool"] == 2
    assert out.derived["drain_resist"]["pool"] == 3
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "drainresist" not in tags


def test_elder_god_tradition_bonus() -> None:
    base = compute(_mage("elder-base", tradition_id=HERMETIC))
    out = compute(
        _mage(
            "elder",
            tradition_id=ELDER_GOD,
            spells=[SpellInstall(spell_id=AGONY, force=6)],
        )
    )
    assert base.derived["drain_resist"]["pool"] == 2
    assert out.derived["drain_resist"]["pool"] == 0
    assert out.derived["drain_resist"]["attrs"] == "WIL+INT"
    row = next(spell for spell in out.derived["spells"] if spell["name"] == "Agony")
    assert row["focus_bonus"] == 3


def test_dareadrenaline_spell_defense_resists() -> None:
    out = compute(_human("dd", bioware=[CyberwareInstall(ware_id=DAREADRENALINE)]))
    sd = out.derived["spell_defense"]
    assert sd["general"] == 0
    assert sd["direct_mana"] == 1
    assert sd["detection"] == 1
    assert sd["mental_manipulation"] == 1
    assert sd["mana_illusion"] == 1
    assert sd["decrease"]["BOD"] == 1
    assert sd["decrease"]["WIL"] == 1
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    for tag in (
        "directmanaspellresist",
        "detectionspellresist",
        "mentalmanipulationresist",
        "manaillusionresist",
        "decreasebodresist",
        "decreasewilresist",
    ):
        assert tag not in tags


def test_magic_resistance_stacks_with_spell_defense() -> None:
    out = compute(_mundane("mr", quality_ids=[MAGIC_RESISTANCE]))
    assert out.derived["spell_defense"]["general"] == 1
    assert out.derived["spell_defense"]["detection"] == 1
    out2 = compute(_human("mr-dd", quality_ids=[MAGIC_RESISTANCE], bioware=[CyberwareInstall(ware_id=DAREADRENALINE)]))
    assert out2.derived["spell_defense"]["detection"] == 2
    assert out2.derived["spell_defense"]["mental_manipulation"] == 2


def test_dimmer_bulb_spell_defense_penalty() -> None:
    out = compute(_human("dim", quality_ids=[DIMMER_BULB]))
    sd = out.derived["spell_defense"]
    assert sd["mana_illusion"] == -1
    assert sd["detection"] == -1
    assert sd["decrease"]["LOG"] == -1
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "manaillusionresist" not in tags


MAGIC_RESISTANCE = "f80ef6fc-e844-441c-81e3-b1264b34a4e7"
DEPENDENT_NUISANCE = "2b9a495d-b735-416b-a000-f648c3b4191a"


def test_mage_enableattribute_not_unimplemented() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["MAG"] = 6
    out = compute(
        CharacterState(
            id="mage-enable",
            name="Mage",
            priorities=Priorities(Heritage="E", Attributes="B", Talent="A", Skills="C", Resources="D"),
            metatype="Human",
            talent="Magician",
            attributes=attrs,
        )
    )
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "enableattribute" not in tags


def test_magic_resistance_and_dependent_lifestyle() -> None:
    out = compute(
        _mundane(
            "resist-dep",
            quality_ids=[MAGIC_RESISTANCE, DEPENDENT_NUISANCE],
            lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, months=1)],
        )
    )
    assert out.derived["spell_resistance"] == 1
    assert out.derived["lifestyle_cost_mod"] == 10
    assert out.derived["lifestyle"]["nuyen"] == 2200


ELEMENTALIST_AIR = "4d5e0fd2-dab3-4de0-9756-096a748bb3cc"
HEDGE_WITCH = "d03a9696-2341-4894-8cf2-0537c4e74af2"
SPIRIT_AIR = "380a4860-e5b7-4d07-9b8f-24951c1d656a"


def test_elementalist_requires_spell_category() -> None:
    out = compute(_mage("elem-empty", quality_ids=[ELEMENTALIST_AIR]))
    assert has(out.derived["errors"], "engine.qualities.pickSpellCategory")
    assert "limitspellcategory" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_elementalist_limits_spells_and_spirits() -> None:
    out = compute(
        _mage(
            "elem-air",
            quality_ids=[ELEMENTALIST_AIR],
            quality_extras={ELEMENTALIST_AIR: "Combat"},
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=MANABOLT), SpellInstall(spell_id=HEAL)],
            spirits=[
                SpiritInstall(spirit_id=SPIRIT_AIR, force=1, services=1, bound=False),
                SpiritInstall(spirit_id=SPIRIT_FIRE, force=1, services=1, bound=False),
            ],
        )
    )
    assert out.derived["limit_spell_categories"] == ["Combat"]
    assert out.derived["limit_spirit_categories"] == ["Spirit of Air"]
    assert [s["name"] for s in out.derived["spells"]] == ["Manabolt"]
    assert has(out.derived["warnings"], "engine.spells.blockedByLimit")
    assert [s["name"] for s in out.derived["spirits"]] == ["Spirit of Air"]
    assert has(out.derived["warnings"], "engine.spirits.blockedByLimit", name="Spirit of Fire")
    assert "Enchanting" in (out.derived["disabled_skill_groups"] or [])


def test_hedge_witch_allows_rituals_plus_selected_category() -> None:
    out = compute(
        _mage(
            "hedge",
            quality_ids=[HEDGE_WITCH],
            quality_extras={HEDGE_WITCH: "Health"},
        )
    )
    assert out.derived["limit_spell_categories"] == ["Health"]
    assert out.derived["allow_spell_categories"] == ["Rituals"]
    assert "Conjuring" in (out.derived["disabled_skill_groups"] or [])


def test_hedge_witch_reduces_selected_category_drain() -> None:
    heal_id = "c09e8bb5-4bed-44f9-a41c-bed6a4deb871"
    out = compute(
        _mage(
            "hedge-drain",
            quality_ids=[HEDGE_WITCH],
            quality_extras={HEDGE_WITCH: "Health"},
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=heal_id, force=8)],
        )
    )
    heal = next(s for s in out.derived["spells"] if s["name"] == "Heal")
    assert heal["spell"]["drain_mod"] == -2
    # F-4 @8 = 4, with -2 = 2
    assert heal["spell"]["drain"] == 2
    assert "spellcategorydrain" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


DEATH_DEALER = "36e76b70-bf6a-4e66-8dac-13cd529b9274"


def test_death_dealer_combat_spell_drain_and_damage() -> None:
    heal_id = "c09e8bb5-4bed-44f9-a41c-bed6a4deb871"
    out = compute(
        _mage(
            "death-dealer",
            quality_ids=[DEATH_DEALER],
            tradition_id=HERMETIC,
            skills={"Spellcasting": 6},
            spells=[SpellInstall(spell_id=MANABOLT, force=6), SpellInstall(spell_id=heal_id, force=6)],
        )
    )
    bolt = next(s for s in out.derived["spells"] if s["name"] == "Manabolt")
    heal = next(s for s in out.derived["spells"] if s["name"] == "Heal")
    assert bolt["spell"]["drain_mod"] == 1
    assert bolt["damage_mod"] == 1
    # F-3 @6 = 3, with +1 = 4
    assert bolt["spell"]["drain"] == 4
    assert heal["spell"]["drain_mod"] == 0
    assert heal["damage_mod"] == 0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "spellcategorydrain" not in tags
    assert "spellcategorydamage" not in tags


WITNESS_MY_HATE = "f8af38e2-e79a-44f9-8e72-57aba35b7056"
MANABALL = "d866f612-7160-41d2-8ce9-b64262327559"


def test_witness_my_hate_direct_non_area_drain_and_damage() -> None:
    heal_id = "c09e8bb5-4bed-44f9-a41c-bed6a4deb871"
    out = compute(
        _mage(
            "wmh",
            quality_ids=[WITNESS_MY_HATE],
            tradition_id=HERMETIC,
            spells=[
                SpellInstall(spell_id=MANABOLT, force=6),
                SpellInstall(spell_id=MANABALL, force=6),
                SpellInstall(spell_id=heal_id, force=6),
            ],
        )
    )
    bolt = next(s for s in out.derived["spells"] if s["name"] == "Manabolt")
    ball = next(s for s in out.derived["spells"] if s["name"] == "Manaball")
    heal = next(s for s in out.derived["spells"] if s["name"] == "Heal")
    # Direct,NOT(Area): Manabolt gets +2 drain / +2 damage
    assert bolt["spell"]["drain_mod"] == 2
    assert bolt["damage_mod"] == 2
    # F-3 @6 = 3, with +2 = 5
    assert bolt["spell"]["drain"] == 5
    # Direct+Area excluded
    assert ball["spell"]["drain_mod"] == 0
    assert ball["damage_mod"] == 0
    # Non-Direct unaffected
    assert heal["spell"]["drain_mod"] == 0
    assert heal["damage_mod"] == 0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "spelldescriptordrain" not in tags
    assert "spelldescriptordamage" not in tags


CHAIN_BREAKER = "8c49fcfb-54fa-43ce-b2af-51780dabf40f"
DEDICATED_CONJURER = "2a599984-62e4-4110-9784-dc1922df395d"
SEER = "90691f29-5b81-4a81-9ebc-21f2f5da1d55"
NULL_WIZARD = "ecb5ab50-68c9-45ee-9fb4-c2f0b3051096"
GUARDIAN_SPIRIT = next(s["id"] for s in catalog()["spirits"] if s["name"] == "Guardian Spirit")
TASK_SPIRIT = next(s["id"] for s in catalog()["spirits"] if s["name"] == "Task Spirit")


def test_chain_breaker_adds_extra_spirit_types() -> None:
    from app.engine import quality_addspirit_extra_key

    missing = compute(_mage("cb-empty", quality_ids=[CHAIN_BREAKER], tradition_id=HERMETIC))
    assert has(missing.derived["errors"], "engine.qualities.pickAddSpirit")
    assert "addspirit" not in [item["tag"] for item in missing.derived["unimplemented_bonuses"]]
    out = compute(
        _mage(
            "cb",
            quality_ids=[CHAIN_BREAKER],
            tradition_id=HERMETIC,
            quality_extras={
                quality_addspirit_extra_key(CHAIN_BREAKER, 0): "Guardian Spirit",
                quality_addspirit_extra_key(CHAIN_BREAKER, 1): "Plant Spirit",
            },
            spirits=[
                SpiritInstall(spirit_id=GUARDIAN_SPIRIT, force=1, services=1, bound=False),
                SpiritInstall(
                    spirit_id=next(s["id"] for s in catalog()["spirits"] if s["name"] == "Spirit of Fire"),
                    force=1,
                    services=1,
                    bound=False,
                ),
            ],
        )
    )
    assert set(out.derived["extra_spirits"]) == {"Guardian Spirit", "Plant Spirit"}
    names = {s["name"] for s in out.derived["spirits"]}
    assert "Guardian Spirit" in names
    assert "Spirit of Fire" in names
    assert "Binding" in (out.derived["disabled_skills"] or [])


def test_dedicated_conjurer_spirit_slots_scale_with_summoning() -> None:
    from app.engine import quality_addspirit_extra_key

    low = compute(
        _mage(
            "dc-low",
            quality_ids=[DEDICATED_CONJURER],
            tradition_id=HERMETIC,
            skills={"Summoning": 1},
        )
    )
    assert low.derived["add_spirit_picks"] == []
    assert "Spellcasting" in (low.derived["disabled_skills"] or [])
    mid = compute(
        _mage(
            "dc-mid",
            quality_ids=[DEDICATED_CONJURER],
            tradition_id=HERMETIC,
            skills={"Summoning": 4},
            quality_extras={
                quality_addspirit_extra_key(DEDICATED_CONJURER, 0): "Guardian Spirit",
                quality_addspirit_extra_key(DEDICATED_CONJURER, 1): "Task Spirit",
            },
            spirits=[SpiritInstall(spirit_id=TASK_SPIRIT, force=1, services=1, bound=False)],
        )
    )
    assert len(mid.derived["add_spirit_picks"]) == 2
    assert set(mid.derived["extra_spirits"]) == {"Guardian Spirit", "Task Spirit"}
    assert any(s["name"] == "Task Spirit" for s in mid.derived["spirits"])


def test_seer_and_null_wizard_grant_free_metamagics() -> None:
    seer = compute(_mage("seer", quality_ids=[SEER], tradition_id=HERMETIC))
    free_names = {m["name"] for m in seer.derived["initiation"]["metamagics"] if m.get("free")}
    assert free_names == {"Psychometry", "Sensing"}
    assert set(seer.derived["disabled_skill_groups"]) >= {"Sorcery", "Conjuring", "Enchanting"}
    assert "addmetamagic" not in [item["tag"] for item in seer.derived["unimplemented_bonuses"]]

    null = compute(_mage("null", quality_ids=[NULL_WIZARD], tradition_id=HERMETIC))
    free_names = {m["name"] for m in null.derived["initiation"]["metamagics"] if m.get("free")}
    assert free_names == {"Reflection"}
    assert any(q["name"] == "Magic Resistance" and q.get("free") for q in null.derived["qualities"])
    assert set(null.derived["disabled_skills"] or []) >= {
        "Binding",
        "Spellcasting",
        "Ritual Spellcasting",
        "Alchemy",
        "Artificing",
    }
    assert null.derived["spell_resistance"] >= 1


MENTORS_MASK = "bf68095e-35b9-49dc-a008-f67bbac9b83b"


def test_mentors_mask_reduces_spell_drain() -> None:
    base = compute(_mage("mm-base", tradition_id=HERMETIC, spells=[SpellInstall(spell_id=STUNBOLT, force=6)]))
    out = compute(
        _mage(
            "mm",
            tradition_id=HERMETIC,
            quality_ids=[MENTORS_MASK],
            spells=[SpellInstall(spell_id=STUNBOLT, force=6)],
        )
    )
    base_row = base.derived["spells"][0]
    row = out.derived["spells"][0]
    assert base_row["spell"]["drain_mod"] == 0
    assert row["spell"]["drain_mod"] == -1
    # F-3 @6 = 3, with -1 = 2
    assert base_row["spell"]["drain"] == 3
    assert row["spell"]["drain"] == 2
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "drainvalue" not in tags


DEDICATED_SPELLSLINGER = "bbc6879e-b50d-4862-b85c-a86c5b9e5d67"


def test_dedicated_spellslinger_free_spells_and_karma_discount() -> None:
    # Magician A: priority free spells + Spellcasting rating from freespells
    base = compute(_mage("dss0", tradition_id=HERMETIC, skills={"Spellcasting": 4}))
    priority_free = int(base.derived["spell_points"]["free"])
    ids = _learnable_ids(priority_free + 5)
    assert len(ids) == priority_free + 5
    out = compute(
        _mage(
            "dss",
            tradition_id=HERMETIC,
            quality_ids=[DEDICATED_SPELLSLINGER],
            skills={"Spellcasting": 4},
            spells=[SpellInstall(spell_id=sid) for sid in ids],
        )
    )
    assert out.derived["spell_points"]["free"] == priority_free + 4
    assert out.derived["spell_points"]["spell_karma"] == 4
    assert "Summoning" in (out.derived["disabled_skills"] or [])
    assert "Binding" in (out.derived["disabled_skills"] or [])
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "freespells" not in tags
    assert "newspellkarmacost" not in tags
    # First priority_free+4 are free; remaining 1 paid at 4 karma
    assert out.derived["spell_points"]["used"] == priority_free + 5
    assert out.derived["spell_points"]["paid"] == 1
    assert out.derived["spell_points"]["karma"] == 4
    paid_row = next(s for s in out.derived["spells"] if not s["free"])
    assert paid_row["karma"] == 4


def _discount_quality(name: str) -> str:
    return next(str(q["id"]) for q in catalog()["qualities"] if q["name"] == name)


def test_blind_is_worth_less_to_someone_who_sees_astrally() -> None:
    """`<costdiscount>` (Blind, RF p.153): −15 karma, but −5 for a character
    with astral perception (a Magician here)."""
    blind = _discount_quality("Blind")
    mundane = compute(_human("blind", quality_ids=[blind])).derived
    assert _quality_row(mundane, "Blind")["karma"] == -15
    assert "karma_base" not in _quality_row(mundane, "Blind")
    assert mundane["karma"]["negative"]["used"] == 15

    magician = compute(_human("blind-mage", quality_ids=[blind, _discount_quality("Magician")])).derived
    row = _quality_row(magician, "Blind")
    assert (row["karma"], row["karma_base"]) == (-5, -15)
    assert magician["karma"]["negative"]["used"] == 5


def test_a_positive_discount_lowers_the_cost() -> None:
    """The Beast's Way (SG p.176): 20 karma, 17 with an Animal Familiar."""
    way = _discount_quality("The Beast's Way")
    alone = compute(_human("way", quality_ids=[way])).derived
    paired = compute(_human("way-fam", quality_ids=[way, _discount_quality("Animal Familiar")])).derived
    assert _quality_row(alone, "The Beast's Way")["karma"] == 20
    assert _quality_row(paired, "The Beast's Way")["karma"] == 17
    assert paired["karma"]["spent"] - alone["karma"]["spent"] == 5 - 3  # the familiar's 5, less the 3 off


def test_bound_spirits_are_capped_by_charisma() -> None:
    """Chummer's Standard `<boundspiritexpression>` is `{CHA}`; an unbound
    spirit does not count."""

    def run(cid: str, cha: int, *, second_bound: bool = True) -> list:
        state = _mage(
            cid,
            tradition_id=HERMETIC,
            spirits=[
                SpiritInstall(spirit_id=SPIRIT_FIRE, force=2, services=1),
                SpiritInstall(spirit_id=SPIRIT_FIRE, force=2, services=1, bound=second_bound),
            ],
        )
        state.attributes["CHA"] = cha
        return compute(state).derived["errors"]

    assert has(run("bound-cha1", 1), "engine.spirits.boundOverLimit", attr="CHA", count=2, max=1)
    assert not has(run("bound-cha2", 2), "engine.spirits.boundOverLimit")
    assert not has(run("unbound", 1, second_bound=False), "engine.spirits.boundOverLimit")


def test_homunculi_and_watchers_sit_outside_the_bound_limit() -> None:
    flagged = {row["name"] for row in load_spirits() if row["ignore_bound_limit"]}
    assert "Watcher" in flagged
    assert "Homunculus (Fragile)" in flagged
    assert "Spirit of Fire" not in flagged


def test_a_magician_has_an_astral_initiative() -> None:
    """Chummer's `AstralInitiativeValue` (INT×2) + `AstralInitiativeDice`
    (the settings' minimum, 3 in Standard); a mundane has none."""
    state = _mage("astral-init")
    state.attributes["INT"] = 4
    out = compute(state)
    assert out.derived["astral_initiative"] == {"value": 8, "dice": 3}
    assert compute(_human("mundane-astral")).derived["astral_initiative"] is None

    german = _mage("astral-init-de", settings=SettingsState(min_astral_initiative_dice=2))
    assert compute(german).derived["astral_initiative"]["dice"] == 2


def _magician_with_datajacks(grades: list[str], settings: SettingsState | None = None) -> dict:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["MAG"] = 4
    state = CharacterState(
        id="ess-rule",
        name="Ess Rule",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="B", Skills="D", Resources="E"),
        metatype="Human",
        talent="Magician",
        attributes=attrs,
        cyberware=[CyberwareInstall(ware_id=DATAJACK, grade=grade) for grade in grades],
    )
    if settings is not None:
        state.settings = settings
    return compute(state).derived


#: Five Used, four Betaware and one Standard datajack: 1.005 Essence gone.
_ESS_1005 = ["Used"] * 5 + ["Betaware"] * 4 + ["Standard"]


def test_magic_loss_rounds_the_essence_left_first() -> None:
    """Chummer rounds 4.995 Essence to 5.00 before taking MAG off it."""
    assert _magician_with_datajacks(_ESS_1005)["totals"]["MAG"] == 3


def test_the_house_rule_keeps_essence_unrounded() -> None:
    """`<donotroundessenceinternally>`: 4.995 stays 4.995, so two points go."""
    out = _magician_with_datajacks(_ESS_1005, SettingsState(dont_round_essence_internally=True))
    assert out["totals"]["MAG"] == 2
    assert out["essence"] == 4.995


def test_the_house_rule_lowers_only_the_magic_maximum() -> None:
    """`<esslossreducesmaximumonly>`: 1.25 Essence gone takes the maximum to
    4, so a Magic of 4 bought keeps its 4 instead of dropping two."""
    grades = ["Used"] * 10
    assert _magician_with_datajacks(grades)["totals"]["MAG"] == 2
    out = _magician_with_datajacks(grades, SettingsState(ess_loss_reduces_maximum_only=True))
    assert out["totals"]["MAG"] == 4
