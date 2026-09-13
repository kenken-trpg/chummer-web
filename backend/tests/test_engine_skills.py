"""Active, knowledge, exotic skills; groups and specializations."""

from app.data_loader import catalog
from app.engine import (
    compute,
    resolve_skill_mods,
    selectskill_options,
)
from app.improvements import collect_effects
from app.models import (
    CyberwareInstall,
    ExoticSkillInstall,
    GearInstall,
    MartialArtInstall,
    SettingsState,
)
from tests.engine_support import (
    QUALIA,
    _human,
    _karate_id,
    _karma_human,
    _mundane,
)
from tests.notice_asserts import has

EMPATHIC_LISTENER = "919cc565-a5b6-4eda-addb-afa2e293af24"
MASTER_DEBATER = "41416949-62eb-4638-9457-fd7e833cea58"


def test_knowledge_points_are_intuition_plus_logic_times_two() -> None:
    out = compute(_human("know-pool"))
    assert out.derived["points"]["knowledge"] == {"used": 0, "max": 4}
    high_state = _human("know-pool-high")
    high_state.attributes["INT"] = 5
    high_state.attributes["LOG"] = 4
    high = compute(high_state)
    assert high.derived["points"]["knowledge"] == {"used": 0, "max": 18}


def test_knowledge_skills_spend_free_points_and_keep_native_free() -> None:
    state = _human(
        "know-spend",
        knowledge_skills={"Alcohol": 3, "English": 2},
        native_languages=["Japanese"],
    )
    state.attributes["INT"] = 3
    state.attributes["LOG"] = 3
    out = compute(state)
    points = out.derived["points"]["knowledge"]
    assert points == {"used": 5, "max": 12}
    assert out.derived["errors"] == []
    public = {row["name"]: row for row in out.derived["knowledge_skills"]}
    assert public["Japanese"] == {
        "name": "Japanese",
        "category": "Language",
        "attribute": "INT",
        "rating": 0,
        "native": True,
    }
    assert public["Alcohol"]["category"] == "Interest"
    assert public["Alcohol"]["rating"] == 3
    assert public["English"]["native"] is False
    assert "Japanese" not in out.knowledge_skills
    assert out.native_languages == ["Japanese"]


def test_knowledge_overspend_is_an_error() -> None:
    out = compute(_human("know-over", knowledge_skills={"Alcohol": 6, "Biology": 6, "Chemistry": 1}))
    assert out.derived["points"]["knowledge"]["used"] == 13
    assert has(out.derived["errors"], "engine.skills.knowledgePointsOver")


def test_second_native_language_is_warned() -> None:
    out = compute(_human("know-natives", native_languages=["Japanese", "English"]))
    assert out.native_languages == ["Japanese"]
    assert has(out.derived["warnings"], "engine.skills.nativeLimit")
    assert out.derived["points"]["knowledge"]["used"] == 0


def test_skill_specialization_costs_one_skill_point() -> None:
    out = compute(_human("spec-pistols", skills={"Pistols": 4}, skill_specializations={"Pistols": "Semi-Automatics"}))
    assert out.derived["skill_totals"]["Pistols"] == 4
    assert out.skill_specializations["Pistols"] == "Semi-Automatics"
    assert out.derived["skill_specializations"]["Pistols"] == "Semi-Automatics"
    assert out.derived["points"]["skills"]["used"] == 5
    assert out.derived["errors"] == []
    pistols = next(item for item in catalog()["skills"]["skills"] if item["name"] == "Pistols")
    assert "Semi-Automatics" in pistols["specs"]


def test_skill_specialization_requires_the_skill() -> None:
    out = compute(_human("spec-none", skill_specializations={"Pistols": "Semi-Automatics"}))
    assert "Pistols" not in out.skill_specializations
    assert has(out.derived["warnings"], "engine.skills.specNeedsSkill", name="Pistols")
    assert out.derived["points"]["skills"]["used"] == 0


def test_skill_specialization_works_with_skill_group() -> None:
    out = compute(_human("spec-group", skill_groups={"Firearms": 2}, skill_specializations={"Pistols": "Revolvers"}))
    assert out.derived["skill_totals"]["Pistols"] == 2
    assert out.skill_specializations["Pistols"] == "Revolvers"
    assert out.derived["points"]["skill_groups"]["used"] == 2
    assert out.derived["points"]["skills"]["used"] == 1


def test_knowledge_specialization_costs_one_knowledge_point() -> None:
    state = _human(
        "spec-know",
        knowledge_skills={"Alcohol": 2},
        skill_specializations={"Alcohol": "Wines"},
    )
    state.attributes["INT"] = 3
    state.attributes["LOG"] = 3
    out = compute(state)
    assert out.derived["points"]["knowledge"] == {"used": 3, "max": 12}
    row = next(item for item in out.derived["knowledge_skills"] if item["name"] == "Alcohol")
    assert row["spec"] == "Wines"
    assert row["rating"] == 2
    assert out.derived["errors"] == []


def test_native_language_specialization_costs_knowledge_point() -> None:
    state = _human(
        "spec-native",
        native_languages=["Japanese"],
        skill_specializations={"Japanese": "Speak"},
    )
    state.attributes["INT"] = 3
    state.attributes["LOG"] = 3
    out = compute(state)
    assert out.derived["points"]["knowledge"] == {"used": 1, "max": 12}
    row = next(item for item in out.derived["knowledge_skills"] if item["name"] == "Japanese")
    assert row["native"] is True
    assert row["spec"] == "Speak"


def test_custom_knowledge_specialization_is_kept() -> None:
    out = compute(
        _human(
            "spec-custom",
            knowledge_skills={"Seattle Gangs": 1},
            knowledge_categories={"Seattle Gangs": "Street"},
            skill_specializations={"Seattle Gangs": "Halloweeners"},
        )
    )
    row = next(item for item in out.derived["knowledge_skills"] if item["name"] == "Seattle Gangs")
    assert row["spec"] == "Halloweeners"
    assert out.derived["points"]["knowledge"]["used"] == 2


SKILLWIRES = "60485c4e-042f-44f6-ad89-324003223f73"
ACTIVESOFT = "c4da5448-0069-447c-b3e4-4147e6bf4ca7"


def test_activesoft_can_take_a_specialization() -> None:
    out = compute(
        _mundane(
            "soft-spec",
            cyberware=[CyberwareInstall(ware_id=SKILLWIRES, rating=1)],
            gear=[GearInstall(gear_id=ACTIVESOFT, rating=1, extra="Pistols")],
            skill_specializations={"Pistols": "Semi-Automatics"},
        )
    )
    assert out.derived["skill_totals"].get("Pistols", 0) == 0
    assert out.derived["skillsoft"]["Pistols"] == 1
    assert out.skill_specializations["Pistols"] == "Semi-Automatics"
    assert out.derived["points"]["skills"]["used"] == 1
    assert out.derived["errors"] == []


def test_exotic_ranged_costs_rating_points() -> None:
    out = compute(
        _human(
            "exotic-lasers",
            exotic_skills=[ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=4)],
        )
    )
    assert out.derived["skill_totals"]["Exotic Ranged Weapon (Lasers)"] == 4
    assert "Exotic Ranged Weapon" not in out.derived["skill_totals"]
    assert out.derived["points"]["skills"]["used"] == 4
    assert out.derived["errors"] == []
    row = out.derived["exotic_skills"][0]
    assert row["label"] == "Exotic Ranged Weapon (Lasers)"
    assert row["rating"] == 4
    assert "Lasers" in row["options"]


def test_exotic_skill_requires_target() -> None:
    out = compute(
        _human(
            "exotic-empty",
            exotic_skills=[ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="", rating=2)],
        )
    )
    assert has(out.derived["warnings"], "engine.skills.pickExoticTarget", name="Exotic Ranged Weapon")
    assert "Exotic Ranged Weapon" not in out.derived["skill_totals"]
    assert out.derived["points"]["skills"]["used"] == 2


def test_exotic_skill_allows_multiple_targets() -> None:
    out = compute(
        _human(
            "exotic-two",
            exotic_skills=[
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=4),
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Flamethrowers", rating=2),
            ],
        )
    )
    totals = out.derived["skill_totals"]
    assert totals["Exotic Ranged Weapon (Lasers)"] == 4
    assert totals["Exotic Ranged Weapon (Flamethrowers)"] == 2
    assert out.derived["points"]["skills"]["used"] == 6
    assert out.derived["errors"] == []


def test_exotic_skill_duplicate_target_is_dropped() -> None:
    out = compute(
        _human(
            "exotic-dup",
            exotic_skills=[
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=4),
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=2),
            ],
        )
    )
    assert has(out.derived["warnings"], "engine.skills.exoticDuplicate", name="Exotic Ranged Weapon (Lasers)")
    assert out.derived["skill_totals"]["Exotic Ranged Weapon (Lasers)"] == 4
    assert len(out.derived["exotic_skills"]) == 1
    assert out.derived["points"]["skills"]["used"] == 4


def test_exotic_and_normal_skill_share_rating_six_limit() -> None:
    out = compute(
        _human(
            "exotic-six",
            skills={"Pistols": 6},
            exotic_skills=[ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=6)],
        )
    )
    assert has(out.derived["errors"], "engine.skills.oneAtSix")


def test_exotic_does_not_charge_specialization_point() -> None:
    out = compute(
        _human(
            "exotic-spec-mix",
            skills={"Pistols": 4},
            skill_specializations={"Pistols": "Semi-Automatics"},
            exotic_skills=[ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=3)],
        )
    )
    assert out.derived["points"]["skills"]["used"] == 8
    assert out.derived["skill_totals"]["Pistols"] == 4
    assert out.derived["skill_totals"]["Exotic Ranged Weapon (Lasers)"] == 3
    assert out.skill_specializations["Pistols"] == "Semi-Automatics"
    assert out.derived["errors"] == []


def test_skill_group_exclude_is_honored() -> None:
    effects = collect_effects(
        [
            (
                "Dummy",
                [{"tag": "skillgroup", "fields": {"name": "Athletics", "bonus": "2", "exclude": "Running"}}],
            )
        ]
    )
    mods = resolve_skill_mods(catalog()["skills"], effects, {})
    assert mods["skill_bonus"]["Gymnastics"] == 2
    assert "Running" not in mods["skill_bonus"]


APTITUDE = "58e3d62a-2073-4af5-b8e0-00c446b3a5ab"


def test_aptitude_raises_skill_max() -> None:
    out = compute(
        _human(
            "aptitude",
            quality_ids=[APTITUDE],
            skills={"Pistols": 7},
            skill_picks={"quality:58e3d62a-2073-4af5-b8e0-00c446b3a5ab:0": "Pistols"},
        )
    )
    assert out.derived["skill_max_bonus"]["Pistols"] == 1
    assert out.derived["skill_totals"]["Pistols"] == 7
    assert out.derived["skill_bonus"].get("Pistols", 0) == 0


def test_selectskill_options_limit_to_physical_attributes() -> None:
    spec = {
        "limittoattribute": "BOD,AGI,REA,STR",
        "knowledgeskills": False,
        "minimumrating": 0,
    }
    options = selectskill_options(spec, catalog()["skills"], {})
    assert "Gymnastics" in options
    assert "Pistols" in options
    assert "Software" not in options
    assert "Negotiation" not in options


def test_empathic_listener_moves_etiquette_onto_intuition() -> None:
    """`swapskillattribute` changes the skill's linked attribute for good
    (Empathic Listener reads the room rather than works it, RF p.153)."""
    out = compute(_mundane("empath", quality_ids=[EMPATHIC_LISTENER]))
    assert out.derived["skill_attribute_swaps"] == [
        {"skill": "Etiquette", "attribute": "INT", "spec": "", "source": "Empathic Listener"}
    ]
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "swapskillattribute" not in tags


def test_a_swapped_skill_keeps_taking_bonuses_by_its_printed_attribute() -> None:
    """Chummer tells `skillattribute` and `skilllinkedattribute` apart only
    once something swapped: the linked one stays on the printed attribute, so
    Qualia's INT dice miss the Etiquette that moved onto INT."""
    out = compute(
        _mundane(
            "empath-qualia",
            quality_ids=[EMPATHIC_LISTENER],
            bioware=[CyberwareInstall(ware_id=QUALIA)],
        )
    )
    bonus = out.derived["skill_bonus"]
    assert bonus["Perception"] == 1  # printed INT
    assert bonus.get("Etiquette", 0) == 0  # printed CHA, swapped to INT


def test_master_debater_swaps_only_the_specialized_tests() -> None:
    out = compute(_mundane("debater", quality_ids=[MASTER_DEBATER]))
    assert out.derived["skill_attribute_swaps"] == [
        {
            "skill": "Negotiation",
            "attribute": "LOG",
            "spec": "Diplomacy",
            "source": "Master Debater",
        }
    ]


def test_martial_art_style_includes_one_technique() -> None:
    out = compute(
        _human(
            "karate-basic",
            martial_arts=[MartialArtInstall(art_id=_karate_id(), techniques=["Counterstrike"])],
        )
    )
    row = out.derived["martial_arts"][0]
    assert row["name"] == "Karate"
    assert row["karma"] == 7
    assert row["techniques"][0]["free"] is True
    assert out.derived["martial_art_points"]["karma"] == 7
    assert out.derived["skill_spec_options"]["Unarmed Combat"] == ["Karate"]
    assert out.derived["karma"]["spent"] == 7
    assert out.derived["errors"] == []


def test_martial_art_chargen_limits() -> None:
    aikido = next(item["id"] for item in catalog()["martial_arts"] if item["name"] == "Aikido")
    out = compute(
        _human(
            "too-many-arts",
            martial_arts=[
                MartialArtInstall(art_id=_karate_id(), techniques=["Counterstrike"]),
                MartialArtInstall(art_id=aikido, techniques=["Counterstrike"]),
            ],
        )
    )
    assert has(out.derived["errors"], "engine.martial.styleMax")

    techs = [
        "Counterstrike",
        "Kick Attack",
        "Kip-Up",
        "Opposing Force (Block)",
        "Sweep",
        "Yielding Force (Counterstrike)",
    ]
    out2 = compute(
        _human(
            "too-many-techs",
            martial_arts=[MartialArtInstall(art_id=_karate_id(), techniques=techs)],
        )
    )
    assert has(out2.derived["errors"], "engine.martial.techniqueMax")


BILINGUAL = "c734e46a-d391-45a6-b022-6f18db5019f1"


def test_bilingual_allows_two_native_languages() -> None:
    out = compute(
        _mundane(
            "bilingual",
            quality_ids=[BILINGUAL],
            native_languages=["Japanese", "English"],
        )
    )
    assert out.native_languages == ["Japanese", "English"]
    assert out.derived["native_language_limit"] == 2
    assert not has(out.derived["warnings"], "engine.skills.nativeLimit")


def test_a_knowledge_specialization_has_its_own_karma_price() -> None:
    """`<karmaknospecialization>`: Neon Anarchy prices a knowledge skill's
    specialization at 3 while an active skill's stays at 7."""

    def spec_karma(settings: SettingsState) -> int:
        state = _karma_human("kno-spec")
        state.skills = {"Pistols": 2}
        state.knowledge_skills = {"Seattle Gangs": 2}
        state.knowledge_categories = {"Seattle Gangs": "Street"}
        state.skill_specializations = {"Pistols": "Revolvers", "Seattle Gangs": "Halloweeners"}
        state.settings = settings
        return int(compute(state).derived["karma_chargen"]["specializations"])

    assert spec_karma(SettingsState()) == 14
    assert spec_karma(SettingsState(karma_knowledge_specialization=3)) == 10
