"""`<metatypeid>` / `<metavariantid>`: where Chummer's orphan check finds the
owner of a metatype's own improvements (Character.Load, "Orphaned
Improvements were found")."""

from __future__ import annotations

import re

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute, default_attributes, find_metatype
from app.models import CharacterState, Priorities

EMPTY = "00000000-0000-0000-0000-000000000000"


def _xml(metatype: str, metavariant: str | None = None) -> str:
    state = compute(
        CharacterState(
            id="ids",
            name="ids",
            metatype=metatype,
            metavariant=metavariant,
            priorities=Priorities(Heritage="C", Attributes="A", Talent="E", Skills="B", Resources="D"),
            attributes=default_attributes(find_metatype(metatype, metavariant)),
        )
    )
    return state_to_chum5(state).decode()


def _orphans(xml: str) -> list[str]:
    """Chummer's test: a guid `sourcename` that no `<guid>`, `<metatypeid>`
    or `<metavariantid>` in the save names."""
    owners = set(re.findall(r"<(?:guid|metatypeid|metavariantid)>([^<]+)</", xml))
    return [name for name in re.findall(r"<sourcename>([0-9a-fA-F-]{36})</sourcename>", xml) if name not in owners]


def _field(xml: str, tag: str) -> str:
    found = re.search(rf"<{tag}>([^<]*)</{tag}>", xml)
    return found.group(1) if found else ""


def test_a_dwarf_owns_its_lifestyle_cost() -> None:
    xml = _xml("Dwarf")
    assert _field(xml, "metatypeid") == find_metatype("Dwarf", None)["id"]
    assert _field(xml, "metavariantid") == EMPTY
    assert "<improvementttype>LifestyleCost</improvementttype>" in xml
    assert _orphans(xml) == []


def test_a_metavariant_has_its_own_id() -> None:
    base = find_metatype("Elf", None)
    wakyambi = next(v for v in base["metavariants"] if v["name"] == "Wakyambi")
    xml = _xml("Elf", "Wakyambi")
    assert (_field(xml, "metatypeid"), _field(xml, "metavariantid")) == (base["id"], wakyambi["id"])


def test_a_shapeshifter_form_bonus_is_not_an_orphan() -> None:
    xml = _xml("Shapeshifter: Vulpine", "Human")
    assert _orphans(xml) == []


def test_the_import_ignores_them() -> None:
    st, warnings = chum5_to_state(_xml("Dwarf").encode())
    assert (st["metatype"], warnings) == ("Dwarf", [])
