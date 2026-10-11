"""Centaur's innate grant path through compute; chargen exposure is separate."""

from copy import deepcopy

import pytest

from app.characters import apply_patch
from app.data_loader import catalog
from app.data_loader.loaders.metatype_grants import resolve_metatype_grants
from app.dataset_store import remember
from app.engine import compute, default_attributes, find_metatype, snapshot_career_baseline
from app.models import CharacterPatch, CharacterState, Priorities, SettingsState, WeaponInstall
from tests.engine_support import _quality_id
from tests.notice_asserts import has
from tests.test_centaur_data import CENTAUR_ID, KICK_SELECT, NATURAL_WEAPON_ID, QUALITY_IDS, SEARCH_ID


def _centaur(**kwargs: object) -> CharacterState:
    return CharacterState(
        id="centaur-grants",
        name="Centaur",
        metatype="Centaur",
        priorities=Priorities(),
        attributes=default_attributes(find_metatype("Centaur", None)),
        **kwargs,  # type: ignore[arg-type]
    )


@pytest.mark.parametrize("variant", ["Nartaki", "Elf", "Missing variant"])
def test_stale_variant_is_cleared_without_replacing_centaur(variant: str) -> None:
    assert find_metatype("Centaur", variant)["id"] == CENTAUR_ID
    out = compute(_centaur(metavariant=variant))
    assert out.metavariant is None
    assert has(out.derived["warnings"], "engine.meta.invalidVariant", name=variant, metatype="Centaur")
    assert {q["id"] for q in out.derived["qualities"]} == set(QUALITY_IDS.values())
    assert len(out.derived["weapons"]) == 1
    assert compute(out).metavariant is None


def test_species_patch_with_stale_variant_keeps_centaur_grants() -> None:
    state = _centaur(metavariant="Nartaki")
    state.metatype = "Human"
    state.attributes = default_attributes(find_metatype("Human", "Nartaki"))
    out = apply_patch(state, CharacterPatch(metatype="Centaur"))
    assert out.metavariant is None
    assert has(out.derived["warnings"], "engine.meta.invalidVariant", name="Nartaki", metatype="Centaur")
    assert {q["id"] for q in out.derived["qualities"]} == set(QUALITY_IDS.values())


@pytest.mark.parametrize("method", ["Priority", "SumToTen", "Karma"])
def test_innate_qualities_are_free_outside_both_quality_allowances(method: str) -> None:
    out = compute(_centaur(build_method=method))
    assert {q["id"] for q in out.derived["qualities"]} == set(QUALITY_IDS.values())
    for row in out.derived["qualities"]:
        assert row["origin"] == "Metatype"
        assert row["origin_id"] == CENTAUR_ID
        assert row["origin_name"] == "Centaur"
        assert row["free"] and row["karma"] == 0
        assert row["removable"] is False
        assert row["page"]
    assert out.quality_ids == []
    assert out.weapons == []
    assert out.derived["karma_chargen"]["qualities"] == 0
    assert out.derived["metagenic"]["count"] == 0
    assert not has(out.derived["warnings"], "engine.qualities.metagenicNeedsChangeling")
    assert not has(out.derived["errors"], "engine.qualities.positiveCap")
    assert out.derived["unimplemented_bonuses"] == []


def test_fixed_powers_keep_standard_ids_and_the_kick_is_generated_once() -> None:
    out = compute(_centaur())
    powers = out.derived["metatype_info"]["powers"]
    assert [p["id"] for p in powers] == [SEARCH_ID, NATURAL_WEAPON_ID]
    assert powers[1]["select"] == KICK_SELECT
    assert powers[0]["action"] == "Complex"
    assert powers[0]["range"] == powers[0]["duration"] == "Special"
    assert all(p["origin_id"] == CENTAUR_ID for p in powers)
    assert [(p["source"], p["page"]) for p in powers] == [("SR5", "400"), ("SR5", "399")]
    weapons = out.derived["weapons"]
    assert len(weapons) == 1
    kick = weapons[0]
    assert kick["weapon_id"] == "e4124dde-69f2-4322-884a-620ba7792b82"
    assert kick["damage"] == "5P"
    assert kick["ap"] == "+1"
    assert kick["reach"] == "1"
    assert kick["accuracy_formula"] == "Physical"
    assert int(kick["accuracy"]) == out.derived["limits"]["physical"]
    assert kick["useskill"] == "Unarmed Combat"
    assert kick["nuyen"] == 0 and kick["accessories"] == []
    assert kick["natural"] and kick["origin_id"] == CENTAUR_ID


def test_recompute_and_json_reload_do_not_persist_or_duplicate_grants() -> None:
    state = compute(_centaur())
    first = deepcopy(state.derived)
    assert compute(state).derived == first
    loaded = CharacterState.model_validate_json(state.model_dump_json())
    assert compute(loaded).derived == first
    assert loaded.quality_ids == [] and loaded.weapons == []
    assert loaded.quality_extras == {}


def test_purchased_overlap_is_preserved_while_the_innate_effect_is_applied_once() -> None:
    magic = QUALITY_IDS["Magic Sense"]
    kick = QUALITY_IDS["Natural Weapon: Kick (Centaur)"]
    blandness = _quality_id("Blandness")
    state = compute(_centaur(quality_ids=[magic, kick, blandness]))
    assert state.quality_ids == [magic, kick, blandness]
    assert len(state.derived["qualities"]) == 5
    assert len(state.derived["weapons"]) == 1
    assert next(q for q in state.derived["qualities"] if q["id"] == magic)["karma"] == 0
    # Change the species directly: no purchased records or other-source effects are erased.
    state.metatype = "Human"
    state.attributes = default_attributes(find_metatype("Human", None))
    compute(state)
    assert state.quality_ids == [magic, kick, blandness]
    assert "powers" not in state.derived["metatype_info"]
    assert not any(q.get("origin") == "Metatype" for q in state.derived["qualities"])
    assert next(q for q in state.derived["qualities"] if q["id"] == magic)["karma"] == 7
    state.metatype = "Centaur"
    state.attributes = default_attributes(find_metatype("Centaur", None))
    compute(state)
    assert len(state.derived["qualities"]) == 5
    assert len(state.derived["weapons"]) == 1


def test_switching_to_human_removes_only_derived_innate_grants() -> None:
    state = compute(_centaur(quality_ids=[_quality_id("Blandness")]))
    state.metatype = "Human"
    state.attributes = default_attributes(find_metatype("Human", None))
    compute(state)
    assert [q["name"] for q in state.derived["qualities"]] == ["Blandness"]
    assert state.derived["weapons"] == []
    assert "powers" not in state.derived["metatype_info"]


def test_metatype_patch_preserves_purchased_weapons_and_regenerates_only_the_kick() -> None:
    pistol = next(w["id"] for w in catalog()["weapons"] if w["name"] == "Ares Predator V")
    state = compute(_centaur(weapons=[WeaponInstall(id="bought-pistol", weapon_id=pistol)]))
    state = apply_patch(state, CharacterPatch(metatype="Human", metavariant=None))
    assert [w.weapon_id for w in state.weapons] == [pistol]
    assert [w["name"] for w in state.derived["weapons"]] == ["Ares Predator V"]
    assert not any(q.get("origin") == "Metatype" for q in state.derived["qualities"])
    state = apply_patch(state, CharacterPatch(metatype="Centaur", metavariant=None))
    assert [w.id for w in state.weapons] == ["bought-pistol"]
    assert len([w for w in state.derived["weapons"] if w.get("origin") == "Metatype"]) == 1
    state = apply_patch(state, CharacterPatch(attributes={**state.attributes, "STR": 5}))
    kick = next(w for w in state.derived["weapons"] if w.get("origin") == "Metatype")
    assert kick["damage"] == "7P"
    assert int(kick["accuracy"]) == state.derived["limits"]["physical"]


def test_innate_grants_are_not_career_purchases_or_buyoffs() -> None:
    state = compute(_centaur())
    state.career_baseline = snapshot_career_baseline(state)
    assert state.career_baseline.quality_ids == []
    state.career = True
    compute(state)
    assert all(q.get("career_cost") is None for q in state.derived["qualities"])
    assert state.derived["qualities_removed"] == []
    assert state.derived["karma_chargen"]["qualities"] == 0


def test_a_historical_purchase_overlapping_an_innate_grant_is_not_refunded_or_removed() -> None:
    from app.engine.compute._career_qualities import career_quality_karma

    magic = QUALITY_IDS["Magic Sense"]
    grant = next(q for q in catalog()["all_metatypes"]["Centaur"]["quality_grants"] if q["id"] == magic)
    delta, costs, removed = career_quality_karma([grant], [magic], [magic])
    assert delta == 7  # preserve the historical spend excluded from today's free-quality sum
    assert costs == [None]
    assert removed == []


def test_career_transition_does_not_charge_a_purchase_record_that_was_free_at_chargen() -> None:
    magic = QUALITY_IDS["Magic Sense"]
    state = compute(_centaur(quality_ids=[magic]))
    state.career_baseline = snapshot_career_baseline(state)
    assert state.career_baseline.quality_ids == []
    state.career = True
    compute(state)
    assert state.quality_ids == [magic]
    assert state.derived["karma_chargen"]["qualities"] == 0
    assert state.derived["qualities_removed"] == []


def test_catalog_grants_are_not_mutated_by_compute() -> None:
    meta = catalog()["all_metatypes"]["Centaur"]
    before = deepcopy(meta)
    compute(_centaur())
    assert meta == before


def test_reference_resolution_prefers_ids_and_keeps_unknown_grants_visible() -> None:
    meta = {"id": CENTAUR_ID, "name": "Centaur"}
    definitions = [{"id": "first", "name": "Search"}, {"id": "second", "name": "Search"}]
    grants = resolve_metatype_grants(meta, [{"name": "Search"}, {"name": "second"}, {"name": "Missing"}], definitions)
    assert [g["id"] for g in grants] == ["first", "second", ""]
    assert grants[2]["name"] == "Missing" and grants[2]["unresolved"]


def test_custom_power_definition_keeps_its_id_and_applies_its_bonus_once() -> None:
    normal = compute(_centaur())
    xml = f"""<chummer><powers><power><id>{SEARCH_ID}</id><source>CUSTOM</source>
    <bonus><initiative>2</initiative></bonus></power></powers></chummer>""".encode()
    _, report = remember("centaur-custom-power", ["centaur"], {"centaur/amend_critterpowers.xml": xml})
    assert not report.skipped
    state = compute(_centaur(settings=SettingsState(dataset="centaur-custom-power", customdata=["centaur"])))
    power = state.derived["metatype_info"]["powers"][0]
    assert power["id"] == SEARCH_ID and power["source"] == "CUSTOM"
    initiative = deepcopy(state.derived["initiative"])
    assert initiative["value"] == normal.derived["initiative"]["value"] + 2
    assert compute(state).derived["initiative"] == initiative
    assert compute(_centaur()).derived["initiative"] == normal.derived["initiative"]


def test_unknown_custom_grant_is_reported_instead_of_silently_disappearing() -> None:
    xml = f"""<chummer><metatypes><metatype><id>{CENTAUR_ID}</id><powers>
    <power amendoperation="addnode">Missing innate power</power>
    </powers></metatype></metatypes></chummer>""".encode()
    _, report = remember("centaur-unknown-power", ["centaur"], {"centaur/amend_metatypes.xml": xml})
    assert not report.skipped
    state = compute(_centaur(settings=SettingsState(dataset="centaur-unknown-power", customdata=["centaur"])))
    assert has(state.derived["warnings"], "engine.meta.unknownGrant")
    assert state.derived["metatype_info"]["powers"][-1]["name"] == "Missing innate power"
