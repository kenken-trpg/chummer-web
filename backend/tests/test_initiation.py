"""The branches of ``resolve_initiation`` that take a choice away again.

Every rejection path in this module does the same two things: it appends a
warning, and it sets ``choice.option_id = ""`` — a **mutation of the
character**, not just of the payload. `compute()` is called on load, on every
patch, and again on import, so a gate that is wrong by one condition does not
merely mislabel a metamagic; it deletes the player's selection, permanently,
behind a single line of warning text.

`test_engine.py` covers the paths where a choice is accepted. This file covers
the paths where one is taken away, and — just as importantly — the two places
that *warn without* taking it away, so the difference stays deliberate.

One line stays unreached on purpose: no magic art in the shipped data carries
a ``<bonus>``, so the arts' ``bonus_sources`` append has no input to give it.

``apply_free_metamagics`` is exercised directly rather than through a
character: its refusals depend on ``forced`` and on the audience flags of an
``<addmetamagic>`` grant, and every such grant in the shipped data is forced,
so no character reachable from the catalog can drive them.
"""

from __future__ import annotations

from typing import Any

from app.data_loader import catalog
from app.engine import compute, default_attributes, find_metatype
from app.engine.magic.initiation import apply_free_metamagics
from app.improvements.effects import empty_effects
from app.models import CharacterState, CyberwareInstall, InitiationChoice, Priorities

# SR5 core, chosen for what each one gates on rather than for what it does.
QUICKENING = "4ea558ed-0fe8-4b9e-b2fa-afffb3eb2476"  # magician-only
POWER_POINT = "406f096a-c093-4a02-b60f-002eb01a20b9"  # adept-only, and the one repeatable metamagic
MASKING = "505d9fe3-852c-459b-8f9e-3e22c1b91b9a"  # open to both, requires the Adept quality
GEOMANCY = "5b922bcf-4114-4c49-a4f3-0f3dcb45dd2f"
NECROMANCY = "fa64531c-5f86-45a0-aaaf-b8425a5b6dd1"
# 5.31 and 5.25 essence: the cheapest way to take a magician's MAG to zero
CUANMIZTLI = "1a112bdd-df4c-4f9f-94cd-f940fa597dda"
MCT_KURO = "6796a057-b452-4a74-96be-eb710a38977e"


# Priority A buys Magician; Adept and Mystic Adept are only offered from B
# down, and asking for one at A resolves to a different talent entirely --
# which would quietly make every gate test below a test of nothing.
_TALENT_PRIORITY = {"Magician": "A", "Adept": "B", "Mystic Adept": "B"}


def _initiate(talent: str, cid: str, choices: list[InitiationChoice], **kwargs: Any) -> CharacterState:
    attrs = kwargs.pop("attributes", None) or default_attributes(find_metatype("Human", None))
    grade = kwargs.pop("initiate_grade", None)
    return CharacterState(
        id=cid,
        name=cid,
        priorities=Priorities(
            Heritage="C",
            Attributes="A" if talent != "Magician" else "B",
            Talent=_TALENT_PRIORITY[talent],
            Skills="D",
            Resources="E",
        ),
        metatype="Human",
        talent=talent,
        attributes=attrs,
        initiate_grade=grade if grade is not None else max((c.grade for c in choices), default=1),
        initiations=choices,
        **kwargs,
    )


def _warns(out: CharacterState, needle: str) -> bool:
    return any(needle in warn for warn in out.derived["warnings"])


def _meta_names(out: CharacterState) -> list[str]:
    return [row["name"] for row in out.derived["initiation"]["metamagics"]]


def _art_names(out: CharacterState) -> list[str]:
    return [row["name"] for row in out.derived["initiation"]["arts"]]


# --- choices that get taken away ------------------------------------------


def test_an_unknown_metamagic_id_is_stripped_from_the_character() -> None:
    out = compute(
        _initiate("Magician", "unknown-meta", [InitiationChoice(grade=1, kind="metamagic", option_id="nope")])
    )
    assert _warns(out, "未知のメタマジック")
    assert _meta_names(out) == []
    # the state itself, not only the payload: this is what gets written back
    assert out.initiations[0].option_id == ""


def test_an_unknown_art_id_is_stripped_from_the_character() -> None:
    out = compute(_initiate("Magician", "unknown-art", [InitiationChoice(grade=1, kind="art", option_id="nope")]))
    assert _warns(out, "未知の Art")
    assert _art_names(out) == []
    assert out.initiations[0].option_id == ""


def test_the_same_metamagic_twice_keeps_the_first_and_drops_the_second() -> None:
    out = compute(
        _initiate(
            "Magician",
            "dup-meta",
            [
                InitiationChoice(grade=1, kind="metamagic", option_id=QUICKENING),
                InitiationChoice(grade=2, kind="metamagic", option_id=QUICKENING),
            ],
        )
    )
    assert _warns(out, "重複しているため外しました")
    assert _meta_names(out) == ["Quickening"]
    assert out.initiations[0].option_id == QUICKENING
    assert out.initiations[1].option_id == ""


def test_a_repeatable_metamagic_may_be_taken_twice() -> None:
    # Power Point is the only repeatable one in the data, and taking it twice
    # is the whole point of it — the duplicate check must not reach it
    base = compute(_initiate("Adept", "pp-once", [InitiationChoice(grade=1, kind="metamagic", option_id=POWER_POINT)]))
    twice = compute(
        _initiate(
            "Adept",
            "pp-twice",
            [
                InitiationChoice(grade=1, kind="metamagic", option_id=POWER_POINT),
                InitiationChoice(grade=2, kind="metamagic", option_id=POWER_POINT),
            ],
        )
    )
    assert not _warns(twice, "重複")
    assert _meta_names(twice) == ["Power Point", "Power Point"]
    assert twice.derived["power_points"]["max"] == base.derived["power_points"]["max"] + 1


def test_the_same_art_twice_keeps_the_first_and_drops_the_second() -> None:
    out = compute(
        _initiate(
            "Magician",
            "dup-art",
            [
                InitiationChoice(grade=1, kind="art", option_id=GEOMANCY),
                InitiationChoice(grade=2, kind="art", option_id=GEOMANCY),
            ],
        )
    )
    assert _art_names(out) == ["Geomancy"]
    assert out.initiations[1].option_id == ""


def test_two_different_arts_are_both_kept() -> None:
    out = compute(
        _initiate(
            "Magician",
            "two-arts",
            [
                InitiationChoice(grade=1, kind="art", option_id=GEOMANCY),
                InitiationChoice(grade=2, kind="art", option_id=NECROMANCY),
            ],
        )
    )
    assert _art_names(out) == ["Geomancy", "Necromancy"]
    assert not _warns(out, "重複")


# --- the audience gates ---------------------------------------------------


def test_an_adept_cannot_take_a_magician_metamagic() -> None:
    out = compute(
        _initiate("Adept", "adept-quick", [InitiationChoice(grade=1, kind="metamagic", option_id=QUICKENING)])
    )
    assert _warns(out, "Quickening はアデプト向けではありません")
    assert _meta_names(out) == []
    assert out.initiations[0].option_id == ""


def test_a_magician_cannot_take_an_adept_metamagic() -> None:
    out = compute(
        _initiate("Magician", "mage-pp", [InitiationChoice(grade=1, kind="metamagic", option_id=POWER_POINT)])
    )
    assert _warns(out, "Power Point は魔術師向けではありません")
    assert _meta_names(out) == []
    assert out.initiations[0].option_id == ""


def test_a_mystic_adept_passes_both_gates() -> None:
    # can_adept and can_magician are both true, so neither gate may fire;
    # a gate written with `or` instead of `and` would strip both of these
    out = compute(
        _initiate(
            "Mystic Adept",
            "mystic",
            [
                InitiationChoice(grade=1, kind="metamagic", option_id=QUICKENING),
                InitiationChoice(grade=2, kind="metamagic", option_id=POWER_POINT),
            ],
        )
    )
    assert _meta_names(out) == ["Quickening", "Power Point"]
    assert not _warns(out, "向けではありません")


# --- warnings that do NOT take the choice away ----------------------------


def test_an_unmet_requirement_warns_but_keeps_the_metamagic() -> None:
    # Masking requires the Adept quality. A plain Magician is told so, and
    # keeps it: the prerequisite may be met later, and silently deleting a
    # paid-for metamagic on the way past is the worse failure.
    out = compute(_initiate("Magician", "masking", [InitiationChoice(grade=1, kind="metamagic", option_id=MASKING)]))
    assert _warns(out, "Masking には")
    assert _meta_names(out) == ["Masking"]
    assert out.initiations[0].option_id == MASKING


def test_a_grade_with_nothing_chosen_is_reported_but_still_costs_karma() -> None:
    out = compute(_initiate("Magician", "empty-grade", [InitiationChoice(grade=1, kind="metamagic", option_id="")]))
    assert _warns(out, "等級 1 の Art／メタマジックを選んでください")
    row = out.derived["initiation"]["choices"][0]
    assert row["name"] == ""
    # the grade was still bought, so the karma is still spent
    assert row["karma"] == 13
    assert out.derived["initiation"]["karma"] == 13


# --- the grade list itself ------------------------------------------------


def test_choices_above_the_grade_are_dropped_and_missing_ones_filled_in() -> None:
    out = compute(
        _initiate(
            "Magician",
            "grade-trim",
            [
                InitiationChoice(grade=2, kind="metamagic", option_id=QUICKENING),
                InitiationChoice(grade=3, kind="art", option_id=GEOMANCY),
            ],
            initiate_grade=2,
        )
    )
    # one row per grade from 1 to the grade, no more and no fewer
    assert [c.grade for c in out.initiations] == [1, 2]
    assert out.initiations[0].option_id == ""  # grade 1 was never chosen
    assert out.initiations[1].option_id == QUICKENING
    assert _art_names(out) == []  # the grade-3 art is gone with its grade


def test_a_junk_kind_is_read_as_a_metamagic() -> None:
    out = compute(
        _initiate("Magician", "junk-kind", [InitiationChoice(grade=1, kind="wizardry", option_id=QUICKENING)])
    )
    assert out.initiations[0].kind == "metamagic"
    assert _meta_names(out) == ["Quickening"]


def test_a_mage_who_burned_out_gets_an_error_not_a_warning() -> None:
    # two 5-essence cyberlimb packages take MAG to 0. Initiation is then not a
    # thing to warn about and carry on with -- there is no magic left to
    # initiate, so it has to block the build like any other invalid state.
    out = compute(
        _initiate(
            "Magician",
            "burnout",
            [InitiationChoice(grade=1, kind="metamagic", option_id=QUICKENING)],
            cyberware=[
                CyberwareInstall(ware_id=CUANMIZTLI, grade="Standard", rating=1),
                CyberwareInstall(ware_id=MCT_KURO, grade="Standard", rating=1),
            ],
        )
    )
    assert out.derived["totals"]["MAG"] == 0
    assert "イニシエーションには魔力が必要です" in out.derived["errors"]


# --- apply_free_metamagics ------------------------------------------------


def _bundle() -> dict[str, Any]:
    return {"metamagic_names": set(), "metamagics": [], "bonus_sources": []}


def _grant(name: str, *, forced: bool = False, source: str = "Test Quality") -> dict[str, Any]:
    return {"name": name, "source": source, "forced": forced}


def _apply(talent: str, grants: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    effects = empty_effects()
    effects["free_metamagics"] = grants  # type: ignore[typeddict-item]
    bundle = _bundle()
    warnings: list[str] = []
    apply_free_metamagics(effects, bundle, talent, warnings)  # type: ignore[arg-type]
    return bundle, warnings


def test_a_free_metamagic_with_no_name_is_ignored_silently() -> None:
    bundle, warnings = _apply("Magician", [_grant("")])
    assert bundle["metamagics"] == []
    assert warnings == []


def test_a_free_metamagic_that_is_not_one_names_the_quality_that_granted_it() -> None:
    # a quality naming a metamagic the data does not have -- the quality name
    # is the only thing that makes the message actionable
    bundle, warnings = _apply("Magician", [_grant("Astral Karate", source="Seer")])
    assert warnings == ["Seer のメタマジック Astral Karate が見つかりません"]
    assert bundle["metamagics"] == []


def test_an_unforced_grant_still_has_to_suit_the_character() -> None:
    adept, adept_warnings = _apply("Adept", [_grant("Quickening")])
    assert adept["metamagics"] == []
    assert adept_warnings == ["Quickening はアデプト向けではありません"]

    mage, mage_warnings = _apply("Magician", [_grant("Power Point")])
    assert mage["metamagics"] == []
    assert mage_warnings == ["Power Point は魔術師向けではありません"]


def test_a_forced_grant_overrides_the_audience() -> None:
    # `forced` is how the data says "this quality gives it to you regardless"
    bundle, warnings = _apply("Adept", [_grant("Quickening", forced=True)])
    assert [row["name"] for row in bundle["metamagics"]] == ["Quickening"]
    assert warnings == []


def test_granting_the_same_metamagic_twice_adds_it_once() -> None:
    bundle, _ = _apply("Magician", [_grant("Quickening", forced=True), _grant("Quickening", forced=True)])
    assert [row["name"] for row in bundle["metamagics"]] == ["Quickening"]


def test_a_repeatable_metamagic_may_be_granted_twice() -> None:
    bundle, _ = _apply("Adept", [_grant("Power Point", forced=True), _grant("Power Point", forced=True)])
    assert [row["name"] for row in bundle["metamagics"]] == ["Power Point", "Power Point"]


def test_a_granted_metamagic_brings_its_bonus_along() -> None:
    bundle, _ = _apply("Adept", [_grant("Power Point", forced=True)])
    assert bundle["bonus_sources"] == [("Power Point", [{"tag": "adeptpowerpoints", "value": "1"}])]
    row = bundle["metamagics"][0]
    assert row["grade"] == 0  # free metamagics sit outside the karma-bearing grades
    assert row["free"] is True
    assert row["source_quality"] == "Test Quality"


def test_the_ids_this_file_pins_are_still_the_entries_it_means() -> None:
    """A data update that renumbers these would otherwise turn every test
    above into a test of the unknown-id branch, and they would all still pass."""
    by_id = {item["id"]: item["name"] for item in catalog()["metamagics"]}
    assert by_id[QUICKENING] == "Quickening"
    assert by_id[POWER_POINT] == "Power Point"
    assert by_id[MASKING] == "Masking"
    arts = {item["id"]: item["name"] for item in catalog()["magic_arts"]}
    assert arts[GEOMANCY] == "Geomancy"
    assert arts[NECROMANCY] == "Necromancy"
