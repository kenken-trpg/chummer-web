"""Innate grants for every metatype, not only the one that needed them first.

`tests/test_centaur_grants.py` covers the mechanics of the grant path — free,
not removable, not a career purchase. This file is about its reach: an elf's
low-light vision comes from the same `<qualities>` block a centaur's does, and
for a long while only the centaur's was read.
"""

from __future__ import annotations

import pytest

from app.data_loader import catalog
from app.engine import compute, default_attributes, find_metatype
from app.models import CharacterState, Priorities

#: What SR5 p.65 grants each playable metatype, as `metatypes.xml` names it.
INNATE = {
    "Human": set(),
    "Elf": {"Low-Light Vision"},
    "Dwarf": {"Thermographic Vision", "Resistance to Pathogens/Toxins"},
    "Ork": {"Low-Light Vision"},
    "Troll": {"Thermographic Vision"},
}


def _state(metatype: str) -> CharacterState:
    return CharacterState(
        id=metatype,
        name=metatype,
        metatype=metatype,
        priorities=Priorities(),
        attributes=default_attributes(find_metatype(metatype, None)),
    )


@pytest.mark.parametrize("metatype,names", sorted(INNATE.items()))
def test_each_metatype_owns_the_qualities_its_species_grants(metatype: str, names: set[str]) -> None:
    rows = compute(_state(metatype)).derived["qualities"]
    assert {row["name"] for row in rows} == names
    for row in rows:
        assert row["origin"] == "Metatype"
        assert row["origin_name"] == metatype
        assert row["free"] and row["karma"] == 0
        assert row["removable"] is False


def test_the_dwarf_resistance_reaches_the_dice_and_not_only_the_list() -> None:
    """A grant that is only printed is a grant that was not applied. This one
    is the visible half of the metatype's `<bonus>`-bearing quality: SR5 p.66
    gives a dwarf +2 to resist pathogens and toxins."""
    human = compute(_state("Human")).derived["special_armor"]
    dwarf = compute(_state("Dwarf")).derived["special_armor"]
    for key in ("toxin_contact", "toxin_ingestion", "pathogen_inhalation", "pathogen_injection"):
        assert human[key] == 0
        assert dwarf[key] == 2


def test_every_metatype_and_metavariant_resolves_its_references() -> None:
    """An unresolved grant is carried rather than dropped, so it would not
    raise — it would quietly become a name with no effect behind it."""
    unresolved = [
        (name, grant["name"])
        for name, meta in catalog()["all_metatypes"].items()
        for key in ("quality_grants", "power_grants")
        for grant in meta.get(key) or []
        if grant.get("unresolved")
    ]
    assert not unresolved


def test_a_metavariant_carries_its_own_grants() -> None:
    """Chargen offers six metatypes, but `.chum5` import resolves any of them,
    and a metavariant replaces its parent's grants rather than adding to them."""
    dryad = find_metatype("Elf", "Dryad")
    assert {g["name"] for g in dryad["quality_grants"]} == {
        "Low-Light Vision",
        "Glamour",
        "Symbiosis",
    }
