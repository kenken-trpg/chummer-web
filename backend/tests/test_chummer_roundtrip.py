"""Chummer5a import ⇄ export is a fixed point on a computed character.

Each scenario builds a Chummer-shaped ``<character>`` document from names that
exist in the live ``catalog()`` and pins the loop:

    xml -> chum5_to_state -> compute -> state_to_chum5 -> chum5_to_state -> compute

The re-imported/re-computed state must equal the first computed state (row ids
stripped), and ``compute`` must land on the same ``derived`` both times. The
builder and the loop live in ``chum5_fixtures``; ``test_chummer_roundtrip_property``
drives the same loop with generated characters.
"""

from __future__ import annotations

from tests.chum5_fixtures import _loop, build_chum5

# --------------------------------------------------------------------------- #
# Scenario A — street samurai: heavy ware / gear / weapons / vehicles          #
# --------------------------------------------------------------------------- #

_SAMURAI_XML = build_chum5(
    name="Chrome",
    metatype="Human",
    talent="Mundane",
    priorities=("D", "A", "E", "B", "C"),
    attributes={"BOD": 5, "AGI": 6, "REA": 4, "STR": 4, "CHA": 2, "INT": 3, "LOG": 3, "WIL": 3},
    notes="街の顔役に借り 2 件。",
    bio={"age": "29", "sex": "女", "concept": "元企業ウェットワーク"},
    skills={"Automatics": 6, "Pistols": 4, "Sneaking": 3},
    skill_specs={"Automatics": "Assault Rifles"},
    groups={"Stealth": 2},
    knowledge=[
        {"name": "Sperethiel", "type": "Language", "native": True},
        {"name": "Corporate Security", "type": "Professional", "rating": 3},
    ],
    cyberware=[
        {"name": "Wired Reflexes", "rating": 2, "grade": "Alphaware"},
        {
            "name": "Obvious Full Arm",
            "grade": "Standard",
            "side": "Left",
            "children": [{"name": "Cyberarm Gyromount", "grade": "Standard"}],
        },
    ],
    bioware=[{"name": "Muscle Toner", "rating": 2, "grade": "Standard"}],
    armor=[{"name": "Armor Jacket", "mods": [{"name": "Fire Resistance", "rating": 3}]}],
    weapons=[
        {"name": "Ares Predator V", "accessories": [{"name": "Silencer/Suppressor", "mount": "Barrel"}]},
        {"name": "AK-97"},
    ],
    gear=[{"name": "Medkit", "rating": 6}, {"name": "Sony Emperor"}],
    vehicles=[{"name": "Dodge Scoot (Scooter)"}],
    lifestyles=[{"name": "Medium", "months": 3}],
    contacts=[{"name": "Fixer Sam", "role": "Fixer", "connection": 4, "loyalty": 3, "group": True}],
)


def test_samurai_sections_import() -> None:
    s1, ch1, _ = _loop(_SAMURAI_XML)
    assert s1["name"] == "Chrome"
    assert s1["priorities"] == {
        "Heritage": "D",
        "Attributes": "A",
        "Talent": "E",
        "Skills": "B",
        "Resources": "C",
    }
    assert s1["attributes"]["AGI"] == 6
    assert s1["skills"]["Automatics"] == 6
    assert s1["skill_specializations"]["Automatics"] == "Assault Rifles"
    assert s1["skill_groups"]["Stealth"] == 2
    assert s1["native_languages"] == ["Sperethiel"]
    assert s1["knowledge_skills"] == {"Corporate Security": 3}
    # two roots + one nested child
    assert len(s1["cyberware"]) == 3
    assert any(w.get("parent_id") for w in s1["cyberware"])
    assert len(s1["bioware"]) == 1
    assert len(s1["armor"]) == 1 and len(s1["armor_mods"]) == 1
    assert len(s1["weapons"]) == 2 and len(s1["weapon_accessories"]) == 1
    assert s1["weapon_accessories"][0]["mount"] == "Barrel"
    assert s1["commlinks"] and len(s1["gear"]) == 1  # Sony Emperor -> commlinks bucket
    assert len(s1["vehicles"]) == 1
    assert s1["lifestyles"][0]["months"] == 3
    assert s1["contacts"][0]["group"] is True
    assert s1["notes"] == "街の顔役に借り 2 件。"
    assert s1["age"] == "29" and s1["sex"] == "女"


def test_samurai_roundtrip_is_a_fixed_point() -> None:
    # _loop already asserts the fixed point + loop-invariant compute; this pins
    # a couple of derived aggregates so a regression names the section.
    _, ch1, ch2 = _loop(_SAMURAI_XML)
    assert ch1.derived["essence"] == ch2.derived["essence"]
    assert ch1.derived["essence"] < 6
    assert len(ch1.derived["weapons"]) >= 2
    assert ch1.derived["totals"]["AGI"] >= 6


# --------------------------------------------------------------------------- #
# Scenario B — full mage: spells / tradition / mentor / initiation             #
# --------------------------------------------------------------------------- #

_MAGE_XML = build_chum5(
    name="Sable",
    metatype="Elf",
    talent="Magician",
    priorities=("C", "B", "A", "D", "E"),
    attributes={"BOD": 2, "AGI": 3, "REA": 3, "STR": 2, "CHA": 4, "INT": 4, "LOG": 5, "WIL": 5, "MAG": 6},
    skills={"Spellcasting": 6, "Counterspelling": 4, "Summoning": 3},
    skill_specs={"Spellcasting": "Combat"},
    knowledge=[{"name": "Sperethiel", "type": "Language", "native": True}],
    qualities=["Focused Concentration"],
    spells=["Manabolt", "Heal", "Increase Reflexes"],
    tradition="Hermetic",
    mentor="Bear",
    initiation=[
        {"grade": 1, "ordeal": True, "metamagic": "Centering"},
        {"grade": 2, "group": True, "metamagic": "Masking"},
    ],
    lifestyles=[{"name": "Low", "months": 4}],
)


def test_mage_magic_sections_import() -> None:
    s1, ch1, _ = _loop(_MAGE_XML)
    assert s1["talent"] == "Magician"
    assert s1["attributes"]["MAG"] == 6
    assert len(s1["spells"]) == 3
    assert s1["tradition_id"] and s1["mentor_id"]
    assert s1["initiate_grade"] == 2
    assert len(s1["initiations"]) == 2
    assert [row["option_id"] for row in s1["initiations"]] == [
        s1["initiations"][0]["option_id"],
        s1["initiations"][1]["option_id"],
    ]
    assert all(row["option_id"] for row in s1["initiations"])  # both metamagics resolved
    assert s1["initiations"][0]["ordeal"] is True
    assert s1["initiations"][1]["group"] is True
    assert "magic" in ch1.derived["enabled_tabs"] or ch1.derived["initiate_grade"] == 2


def test_mage_roundtrip_is_a_fixed_point() -> None:
    _, ch1, ch2 = _loop(_MAGE_XML)
    assert ch1.derived["initiate_grade"] == ch2.derived["initiate_grade"] == 2
    assert len(ch1.derived["spells"]) == 3
    assert ch1.derived["tradition"] == ch2.derived["tradition"]


# --------------------------------------------------------------------------- #
# Scenario C — technomancer: complex forms + submersion                        #
# --------------------------------------------------------------------------- #

_TECHNO_XML = build_chum5(
    name="Echo",
    metatype="Human",
    talent="Technomancer",
    priorities=("D", "B", "A", "C", "E"),
    attributes={"BOD": 3, "AGI": 3, "REA": 3, "STR": 2, "CHA": 3, "INT": 4, "LOG": 5, "WIL": 5, "RES": 6},
    skills={"Software": 6, "Compiling": 4, "Electronic Warfare": 3},
    skill_specs={"Software": "Editing"},
    complex_forms=["Cleaner", "Editor", "Puppeteer"],
    initiation=[
        {"grade": 1, "res": True, "ordeal": True},
        {"grade": 2, "res": True},
        {"grade": 3, "res": True, "group": True},
    ],
    lifestyles=[{"name": "Low", "months": 2}],
)


def test_technomancer_resonance_sections_import() -> None:
    s1, ch1, _ = _loop(_TECHNO_XML)
    assert s1["talent"] == "Technomancer"
    assert s1["attributes"]["RES"] == 6
    assert len(s1["complex_forms"]) == 3
    assert s1["submersion_grade"] == 3
    assert len(s1["submersions"]) == 3
    assert s1["submersions"][0]["ordeal"] is True
    assert s1["submersions"][2]["group"] is True
    assert s1["initiate_grade"] == 0  # res grades are submersion, not initiation
    assert ch1.derived["submersion_grade"] == 3


def test_technomancer_roundtrip_is_a_fixed_point() -> None:
    _, ch1, ch2 = _loop(_TECHNO_XML)
    assert ch1.derived["submersion_grade"] == ch2.derived["submersion_grade"] == 3
    assert len(ch1.derived["complex_forms"]) == 3


# --------------------------------------------------------------------------- #
# Scenario D — career + Sum-to-Ten + martial arts                              #
# --------------------------------------------------------------------------- #

_CAREER_XML = build_chum5(
    name="Veteran",
    metatype="Ork",
    talent="Mundane",
    build_method="SumToTen",
    created=True,
    karma=37,
    nuyen=12000,
    priorities=("A", "B", "E", "C", "D"),  # 4+3+0+2+1 = 10
    attributes={"BOD": 7, "AGI": 4, "REA": 4, "STR": 6, "CHA": 2, "INT": 3, "LOG": 2, "WIL": 4},
    skills={"Unarmed Combat": 5, "Intimidation": 4},
    martial_arts=[{"name": "Aikido", "techniques": ["Counterstrike", "Called Shot (Disarm)"]}],
    contacts=[{"name": "Doc Wu", "role": "Street Doc", "connection": 3, "loyalty": 4}],
    lifestyles=[{"name": "Squatter", "months": 6}],
)


def test_career_and_sum_to_ten_import() -> None:
    s1, ch1, _ = _loop(_CAREER_XML)
    assert s1["build_method"] == "SumToTen"
    assert s1["career"] is True
    assert s1["karma_earned"] == 37
    assert s1["nuyen_earned"] == 12000
    assert s1["metatype"] == "Ork"
    assert len(s1["martial_arts"]) == 1
    assert set(s1["martial_arts"][0]["techniques"]) == {"Counterstrike", "Called Shot (Disarm)"}
    assert ch1.derived["career"] is True


def test_career_roundtrip_is_a_fixed_point() -> None:
    _, ch1, ch2 = _loop(_CAREER_XML)
    assert ch1.derived["career"] is ch2.derived["career"] is True
    assert len(ch1.derived["martial_arts"]) == len(ch2.derived["martial_arts"]) == 1
    assert ch1.derived["karma"] == ch2.derived["karma"]
