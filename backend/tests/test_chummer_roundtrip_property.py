"""The same import ⇄ export fixed point, on characters nobody wrote by hand.

``test_chummer_roundtrip.py`` pins four characters that were built to exercise
particular sections. They are good regression tests and bad explorers: between
them they name maybe eighty of the ~3,500 catalog entries, so a field that only
one weapon category sets, or a quality whose bonus survives compute but not
export, is invisible to them.

Here the character is drawn from the live catalog instead, and the property is
the one that matters: **a character that has been through Chummer once does not
change if it goes through again.** If it does, either the exporter drops
something the importer reads, or the importer resolves a name to something the
exporter then writes differently. Hypothesis shrinks the failure to the
smallest character that still shows it, which is the whole reason for the
dependency.

Entries that need a target chosen with them (`needs_extra`, `extra_kind`) are
left out: a quality with no target is not a roundtrip failure, it is an
incomplete character, and the engine is entitled to normalise it away.
"""

from __future__ import annotations

from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.data_loader import catalog
from tests.chum5_fixtures import _loop, build_chum5

# --------------------------------------------------------------------------- #
# Draw pools, taken from the live catalog once                                 #
# --------------------------------------------------------------------------- #

_ATTRS = ("BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL")


def _names(rows: list[dict[str, Any]], **skip_truthy: bool) -> list[str]:
    """SR5-sourced names, minus rows with any of the named flags set."""
    out = []
    for row in rows:
        if row.get("source") != "SR5" or row.get("hidden"):
            continue
        if any(row.get(flag) for flag in skip_truthy):
            continue
        name = row.get("name")
        if name:
            out.append(str(name))
    return sorted(set(out))


_C = catalog()
_METATYPES = ["Human", "Elf", "Dwarf", "Ork", "Troll"]
_WEAPONS = _names(_C["weapons"], from_cyberware=True, from_gear=True, add_gear_id=True)
_ARMOR = _names(_C["armor"])
_GEAR = _names(_C["gear"], needs_extra=True, requireparent=True)
_SPELLS = _names([s for s in _C["spells"] if s.get("learnable") is not False])
_POWERS = _names(_C["powers"], levels=True)
_COMPLEX_FORMS = _names(_C["complex_forms"], needs_extra=True)
_VEHICLES = _names(_C["vehicles"])
_LIFESTYLES = [row["name"] for row in _C["lifestyles"] if row.get("name")]
_QUALITIES = _names(_C["qualities"], needs_extra=True, extra_kind=True, metagenic=True, is_way=True)
_CYBERWARE = _names(_C["cyberware"]["items"], allow_subsystems=True, formula_rating=True)
_BIOWARE = _names(_C["bioware"]["items"], formula_rating=True)


def _pick(pool: list[str], max_size: int) -> st.SearchStrategy[list[str]]:
    """A short, duplicate-free selection from a catalog pool."""
    if not pool:
        return st.just([])
    return st.lists(st.sampled_from(pool), min_size=0, max_size=max_size, unique=True)


@st.composite
def characters(draw: st.DrawFn) -> bytes:
    """A Chummer-shaped document with a plausible spread of sections."""
    talent = draw(st.sampled_from(["Mundane", "Magician", "Adept", "Technomancer"]))
    awakened = talent in ("Magician", "Adept")
    return build_chum5(
        name=draw(st.sampled_from(["Chrome", "夜叉", "O'Malley", "X"])),
        metatype=draw(st.sampled_from(_METATYPES)),
        talent=talent,
        priorities=("D", "A", "B", "C", "E") if talent == "Mundane" else ("D", "B", "A", "C", "E"),
        attributes={attr: draw(st.integers(min_value=1, max_value=5)) for attr in _ATTRS},
        skills={"Pistols": draw(st.integers(min_value=0, max_value=6))},
        qualities=draw(_pick(_QUALITIES, 3)),
        spells=draw(_pick(_SPELLS, 4)) if talent == "Magician" else [],
        powers=[{"name": name} for name in draw(_pick(_POWERS, 3))] if talent == "Adept" else [],
        complex_forms=draw(_pick(_COMPLEX_FORMS, 3)) if talent == "Technomancer" else [],
        tradition="Hermetic" if talent == "Magician" else None,
        cyberware=[{"name": name} for name in draw(_pick(_CYBERWARE, 2))] if not awakened else [],
        bioware=[{"name": name} for name in draw(_pick(_BIOWARE, 2))] if not awakened else [],
        armor=[{"name": name} for name in draw(_pick(_ARMOR, 2))],
        weapons=[{"name": name} for name in draw(_pick(_WEAPONS, 3))],
        gear=[{"name": name} for name in draw(_pick(_GEAR, 4))],
        vehicles=[{"name": name} for name in draw(_pick(_VEHICLES, 2))],
        lifestyles=[{"name": name, "months": 1} for name in draw(_pick(_LIFESTYLES, 1))],
    )


# The catalog is read once at import; `_loop` is ~6 ms, so the default 100
# examples cost well under a second. `function_scoped_fixture` is not in play
# and there is no per-example setup, so the only health check worth silencing
# is the one about `catalog()` being slow the very first time it is touched.
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(characters())
def test_a_generated_character_survives_a_second_trip(xml: bytes) -> None:
    _loop(xml)


def test_the_draw_pools_are_not_accidentally_empty() -> None:
    """A typo in a filter flag would silently generate empty characters, and
    every property below would pass without testing anything."""
    for label, pool in (
        ("weapons", _WEAPONS),
        ("armor", _ARMOR),
        ("gear", _GEAR),
        ("spells", _SPELLS),
        ("powers", _POWERS),
        ("complex_forms", _COMPLEX_FORMS),
        ("vehicles", _VEHICLES),
        ("lifestyles", _LIFESTYLES),
        ("qualities", _QUALITIES),
        ("cyberware", _CYBERWARE),
        ("bioware", _BIOWARE),
    ):
        assert len(pool) >= 5, f"{label} pool is {len(pool)}"
