"""Natural weapons in the .chum5: the weapon Chummer's
`AddImprovementCollection.naturalweapon` builds and the `Weapon` improvement
that ties it to its owner (app/chummer_export/natural_weapons.py)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute, default_attributes, find_metatype
from app.models import CharacterState, CritterPowerInstall, Priorities
from tests.test_quality_natural_weapons import _infected

EMPTY = "00000000-0000-0000-0000-000000000000"


def _root(state: CharacterState) -> ET.Element:
    return ET.fromstring(state_to_chum5(state))


def _natural(root: ET.Element) -> list[ET.Element]:
    return [w for w in root.findall("./weapons/weapon") if w.findtext("sourceid") == EMPTY]


def _weapon_improvements(root: ET.Element) -> dict[str, ET.Element]:
    return {
        imp.findtext("improvedname") or "": imp
        for imp in root.findall("./improvements/improvement")
        if imp.findtext("improvementttype") == "Weapon"
    }


def _fields(weapon: ET.Element, *keys: str) -> tuple[str, ...]:
    return tuple(weapon.findtext(key) or "" for key in keys)


def test_a_vampire_bite_is_saved_with_its_improvement() -> None:
    root = _root(_infected("Infected: Vampire (Non-Human)"))
    [bite] = _natural(root)
    # the node's own figures, unworked, as Chummer's builder copies them
    assert _fields(bite, "name", "category", "type", "damage", "ap", "reach", "accuracy", "useskill") == (
        "Infected Bite",
        "Critter Powers",
        "Melee",
        "({STR}+1)P",
        "-1",
        "-1",
        "Physical",
        "Unarmed Combat",
    )
    quality = next(q for q in root.iter("quality") if q.findtext("name") == "Infected: Vampire (Non-Human)")
    owner = quality.findtext("guid")
    assert owner and bite.findtext("parentid") == owner
    assert quality.find("./naturalweapons/naturalweapon") is not None
    imp = _weapon_improvements(root)[bite.findtext("guid") or ""]
    assert (imp.findtext("sourcename"), imp.findtext("improvementsource")) == (owner, "Quality")


def test_a_ghoul_saves_both_attacks_with_their_own_guids() -> None:
    root = _root(_infected("Infected: Ghoul (Dwarf)"))
    weapons = _natural(root)
    assert [w.findtext("name") for w in weapons] == ["Infected Claws", "Infected Bite"]
    guids = {w.findtext("guid") for w in weapons}
    assert len(guids) == 2 and guids <= set(_weapon_improvements(root))


def test_a_shapeshifter_bite_belongs_to_the_metatype() -> None:
    meta = find_metatype("Shapeshifter: Vulpine", None)
    state = compute(
        CharacterState(
            id="shapeshifter",
            name="Mittens",
            metatype="Shapeshifter: Vulpine",
            priorities=Priorities(Heritage="C", Attributes="A", Talent="E", Skills="B", Resources="D"),
            attributes=default_attributes(meta),
        )
    )
    root = _root(state)
    [bite] = _natural(root)
    assert bite.findtext("name") == "Bite (Vulpine Form)"
    imp = _weapon_improvements(root)[bite.findtext("guid") or ""]
    assert imp.findtext("improvementsource") == "Metatype"
    assert imp.findtext("sourcename") == bite.findtext("parentid") == meta["id"]


def test_a_bought_power_saves_its_weapon() -> None:
    stock = {str(p["name"]): p for p in catalog()["buyable_critter_powers"]}
    state = _infected("Infected: Ghoul (Dwarf)")
    state.critter_powers = [CritterPowerInstall(id="claws-power", power_id=stock["Tunneling Claws"]["id"])]
    state = compute(state)
    root = _root(state)
    claws = [w for w in _natural(root) if w.findtext("parentid") == "claws-power"]
    assert [w.findtext("name") for w in claws] == ["Tunneling Claws"]
    imp = _weapon_improvements(root)[claws[0].findtext("guid") or ""]
    assert (imp.findtext("sourcename"), imp.findtext("improvementsource")) == ("claws-power", "CritterPower")


def test_one_weapons_section_and_a_round_trip_keeps_one_bite() -> None:
    first = _infected("Infected: Vampire (Non-Human)")
    xml = state_to_chum5(first)
    assert len(ET.fromstring(xml).findall("weapons")) == 1
    st, warnings = chum5_to_state(xml)
    assert st["weapons"] == []
    assert not [w for w in warnings if "Infected Bite" in str(w)]
    back = compute(CharacterState(**st))
    assert [w["name"] for w in back.derived["weapons"] if w.get("natural")] == ["Infected Bite"]


def test_no_natural_weapon_no_section_entry() -> None:
    root = _root(_infected("Infected: Vampire (Non-Human)").model_copy(update={"quality_ids": []}))
    assert _natural(root) == []
    assert _weapon_improvements(root) == {}
