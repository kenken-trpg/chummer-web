"""First centaur milestone: faithful grant data before chargen exposure.

These test the data boundary only. They do not claim that compute, saving or
character creation already supports centaurs.
"""

import xml.etree.ElementTree as ET

import pytest

from app.catalog_view import public_catalog
from app.data_loader import catalog
from app.data_loader.loaders.magic.spells import load_critter_powers
from app.data_loader.loaders.metatypes import _parse_metatype, load_metatypes
from app.data_loader.loaders.qualities import load_qualities
from app.engine.lookups import critter_power_rows, critter_power_spec

CENTAUR_ID = "8768ec05-4fbb-43ae-b3ba-94ba57610069"
SEARCH_ID = "4f694634-7c91-4534-a9ff-7f8ae3002a1e"
NATURAL_WEAPON_ID = "9fc065db-9d63-4e8b-aba9-e19dfba07652"
KICK_SELECT = "Kick: DV ({STR} + 2)P, AP +1, +1 Reach"
QUALITY_IDS = {
    "Low-Light Vision": "8ec5c9bb-aeb9-42f2-a436-a60f764adfe4",
    "Thermographic Vision": "02e76a38-304e-4a0e-93a3-ad2938306afc",
    "Natural Weapon: Kick (Centaur)": "f9cdcb14-7181-4105-b59a-3628663f3be7",
    "Magic Sense": "912bef16-2f72-45e2-95bb-96ef7eea4811",
}


def test_centaur_grants_are_loaded_without_turning_them_into_purchases() -> None:
    centaur = next(m for m in load_metatypes() if m["id"] == CENTAUR_ID)
    assert centaur["category"] == "Metasapient"
    assert centaur["karma"] == 60
    assert (centaur["source"], centaur["page"]) == ("RF", "98")
    assert centaur["qualities"] == [
        {"name": name, "category": "Positive", "select": "", "rating": "", "removable": False} for name in QUALITY_IDS
    ]
    assert centaur["powers"] == [
        {"name": "Search", "select": "", "rating": "", "removable": False},
        {"name": "Natural Weapon", "select": KICK_SELECT, "rating": "", "removable": False},
    ]
    assert centaur["metavariants"] == []
    assert (centaur["walk"], centaur["run"], centaur["sprint"]) == ("1/1/0", "4/0/0", "4/1/0")


def test_grants_preserve_instances_fixed_picks_ratings_and_removability() -> None:
    metatype = _parse_metatype(
        ET.fromstring("""<metatype><name>Test</name>
        <qualities><negative>
          <quality select="First" removable="True">Repeated</quality>
          <quality select="Second">Repeated</quality>
        </negative></qualities>
        <powers><power rating="{MAG}" select="Self-Only">Concealment</power></powers>
        </metatype>""")
    )
    assert metatype["qualities"] == [
        {"name": "Repeated", "category": "Negative", "select": "First", "rating": "", "removable": True},
        {"name": "Repeated", "category": "Negative", "select": "Second", "rating": "", "removable": False},
    ]
    assert metatype["powers"][0]["rating"] == "{MAG}"
    assert metatype["powers"][0]["select"] == "Self-Only"


def test_hidden_vision_definitions_are_available_only_when_requested() -> None:
    purchase_names = {q["name"] for q in load_qualities()}
    definitions = {q["name"]: q for q in load_qualities(include_hidden=True)}
    for name, expected_id in QUALITY_IDS.items():
        assert definitions[name]["id"] == expected_id
    assert "Low-Light Vision" not in purchase_names
    assert "Thermographic Vision" not in purchase_names
    # The kick's actual weapon comes from the quality, not parsing the power's select.
    assert definitions["Natural Weapon: Kick (Centaur)"]["add_weapon"] == "Kick (Centaur)"


@pytest.mark.parametrize("name, expected_id", [("Search", SEARCH_ID), ("Natural Weapon", NATURAL_WEAPON_ID)])
def test_duplicate_power_names_resolve_the_standard_definition(name: str, expected_id: str) -> None:
    matches = [p for p in catalog()["critter_powers"] if p["name"] == name]
    assert len(matches) > 1  # This fixture must actually exercise the ambiguity.
    spec = critter_power_spec(name)
    assert spec is not None
    assert spec["id"] == expected_id
    assert spec["source"] == "SR5"
    assert critter_power_spec(expected_id) is spec
    assert critter_power_rows([name])[0]["source"] == "SR5"
    # An explicit ID can still select the specialised definition.
    assert critter_power_spec(matches[-1]["id"]) is matches[-1]


def test_power_rules_and_fixed_select_metadata_are_not_lost() -> None:
    definitions = {p["id"]: p for p in load_critter_powers(include_rules=True)}
    weapon = definitions[NATURAL_WEAPON_ID]
    assert [node["tag"] for node in weapon["bonus"]] == ["selecttext"]
    search = definitions[SEARCH_ID]
    assert search["required_tree"] == []
    specialised = next(p for p in definitions.values() if p["name"] == "Search" and p["id"] != SEARCH_ID)
    assert specialised["required_tree"]
    assert critter_power_spec("Unknown power") is None


def test_power_rules_require_explicit_opt_in_until_compute_supports_them() -> None:
    assert all("bonus" not in power for power in catalog()["critter_powers"])


def test_centaur_is_available_without_exposing_other_metasapients() -> None:
    assert "Centaur" in catalog()["all_metatypes"]
    assert {m["name"] for m in public_catalog()["metatypes"]} == {"Human", "Elf", "Dwarf", "Ork", "Troll", "Centaur"}
