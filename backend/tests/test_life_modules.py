"""Life-module free ratings and persistence, using the pinned Chummer data."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from app.characters import apply_patch, import_character, new_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.data_loader.loaders import life_modules as life_loader
from app.engine import compute
from app.models import CharacterCreate, CharacterPatch
from app.notices import NoticeError
from tests.notice_asserts import has


def module(name: str, stage: str | None = None) -> dict:
    return next(m for m in catalog()["life_modules"] if m["name"] == name and (stage is None or m["stage"] == stage))


def runner():
    return new_character(CharacterCreate(name="History", build_method="LifeModule"))


@pytest.mark.parametrize("metatype,allowed", [("Human", False), ("Ork", True), ("Troll", True)])
def test_module_metatype_requirements_reject_effects_until_matched(metatype, allowed):
    base = runner()
    spec = module("Trog Ganger")
    state = apply_patch(base, CharacterPatch(metatype=metatype, life_modules=[spec["id"]]))
    assert has(state.derived["errors"], "engine.life.requirement") is not allowed
    baseline = apply_patch(base, CharacterPatch(metatype=metatype))
    assert state.derived["karma"]["spent"] - baseline.derived["karma"]["spent"] == (spec["karma"] if allowed else 0)


@pytest.mark.parametrize("talent,allowed", [("Mundane", False), ("Magician", True)])
def test_module_quality_requirements_include_selected_talent(talent, allowed):
    base = runner()
    spec = module("Magical Education (Magician)")
    state = apply_patch(base, CharacterPatch(talent=talent, life_modules=[spec["id"]]))
    assert has(state.derived["errors"], "engine.life.requirement") is not allowed


def test_pool_and_method_do_not_inherit_priority_or_karma_defaults():
    state = runner()
    assert state.build_method == "LifeModule"
    assert state.derived["karma"]["pool"] == 750
    assert state.derived["karma_chargen"]["enabled"]
    assert not has(state.derived["errors"], "engine.priority.oneEach")
    assert has(state.derived["errors"], "engine.life.missingStage", stage="life.stage.Nationality")


def test_grants_are_paid_once_and_remove_without_leaving_ratings():
    base = runner()
    spec = module("Bounty Hunter")
    state = apply_patch(base, CharacterPatch(life_modules=[spec["id"]]))
    assert state.derived["totals"]["BOD"] == 2
    assert state.derived["karma"]["spent"] == 100
    assert state.derived["karma_chargen"]["skills"] == 0
    assert state.attributes == base.attributes
    assert state.skills == base.skills
    assert compute(state).model_dump() == state.model_dump()
    assert import_character(state.model_dump()).derived == state.derived
    removed = apply_patch(state, CharacterPatch(life_modules=[]))
    assert removed.derived == base.derived


def test_purchased_attribute_is_priced_above_the_free_module_rating():
    base = runner()
    state = apply_patch(
        base, CharacterPatch(life_modules=[module("Bounty Hunter")["id"]], attributes={**base.attributes, "BOD": 2})
    )
    assert state.derived["totals"]["BOD"] == 3
    assert state.derived["karma_chargen"]["attributes"] == 15
    assert state.derived["karma"]["spent"] == 115
    assert state.attributes["BOD"] == 2


def test_repeated_adult_modules_stack_without_double_charging_skills():
    mid = module("Bounty Hunter")["id"]
    state = apply_patch(runner(), CharacterPatch(life_modules=[mid, mid]))
    assert state.derived["totals"]["BOD"] == 3
    assert state.derived["karma"]["spent"] == 200
    assert state.derived["karma_chargen"]["skills"] == 0


def test_choice_and_native_language_are_derived_and_not_added_to_purchases():
    spec = module("SINless")
    picks = {
        f"0:{choice['key']}": choice["options"][0] if choice["options"] else "Seattle" for choice in spec["choices"]
    }
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    assert not has(state.derived["errors"], "engine.life.choice")
    assert not state.native_languages
    assert any(row["name"] == "English" and row["native"] for row in state.derived["knowledge_skills"])
    assert state.derived["karma"]["spent"] == 15
    assert state.knowledge_skills == {}


def test_missing_or_invalid_choices_are_reported_and_not_applied():
    spec = module("SINless")
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices={"0:4": "invalid"}))
    assert has(state.derived["errors"], "engine.life.choice")
    assert not any(row["name"] == "invalid" for row in state.derived["knowledge_skills"])


def test_unknown_and_unsupported_modules_never_grant_partial_benefits(monkeypatch):
    # Every pinned candidate is supported, so an unsupported one has to be made
    # up here: the module grants BOD and names a quality that does not exist.
    root = ET.fromstring("""<chummer><modules><module><id>broken</id><name>Mystery</name>
      <stage>Real Life</stage><karma>100</karma><bonus><attributelevel><name>BOD</name></attributelevel>
      <addqualities><addquality>No Such Quality</addquality></addqualities></bonus></module></modules></chummer>""")
    monkeypatch.setattr(life_loader, "data_root", lambda _: root)
    row = life_loader.load_life_modules()[0]
    assert row["unsupported"] == ["addquality:No Such Quality"]
    monkeypatch.setitem(catalog(), "life_modules", [row])
    state = apply_patch(runner(), CharacterPatch(life_modules=["unknown", row["id"]]))
    assert has(state.derived["errors"], "engine.life.unknown")
    assert has(state.derived["errors"], "engine.life.unsupported")
    assert state.derived["karma"]["spent"] == 0
    assert state.derived["totals"]["BOD"] == 1


def test_childhood_cannot_repeat():
    spec = module("Corp Drone")
    picks = {f"0:{c['key']}": c["options"][0] if c["options"] else "Seattle" for c in spec["choices"]}
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"], spec["id"]], life_module_choices=picks))
    assert has(state.derived["errors"], "engine.life.duplicateStage", stage="life.stage.Formative Years")
    assert state.derived["karma"]["spent"] == 40


def test_disabled_modules_are_still_listed_for_visibility():
    rows = catalog()["life_modules"]
    assert {row["stage"] for row in rows} == {
        "Nationality",
        "Formative Years",
        "Teen Years",
        "Further Education",
        "Real Life",
    }
    # The pinned data is fixed, so this is a canary on a data refresh: every
    # candidate is selectable, and a listed-but-disabled row is only exercised
    # with the synthetic module above.
    assert len(rows) == 325
    assert not [row["name"] for row in rows if row["unsupported"]]


def test_chum5_does_not_silently_drop_the_history():
    with pytest.raises(NoticeError, match="engine.life.chum5Unsupported"):
        state_to_chum5(runner())
    with pytest.raises(NoticeError, match="engine.life.chum5Unsupported"):
        chum5_to_state(b"<character><buildmethod>LifeModule</buildmethod></character>")


def test_knowledge_purchases_are_priced_above_module_grants():
    base = runner()
    state = apply_patch(
        base,
        CharacterPatch(
            life_modules=[module("Bounty Hunter")["id"]],
            knowledge_skills={"Crook Hangouts": 1},
            settings={"knowledge_points_expression": "0"},
        ),
    )
    assert state.derived["karma_chargen"]["knowledge"] == 4


def test_custom_pool_is_honored():
    state = apply_patch(runner(), CharacterPatch(settings={"karma_chargen_pool": 900}))
    assert state.derived["karma"]["pool"] == 900


def test_excess_free_ratings_are_explicitly_rejected():
    state = apply_patch(runner(), CharacterPatch(life_modules=[module("Bounty Hunter")["id"]] * 7))
    assert has(state.derived["errors"], "engine.life.ratingCap", name="BOD", rating=8, cap=6)


@pytest.mark.parametrize(
    "name,level",
    [
        ("Fugitive", 2),
        ("Gang Warfare", 2),
        ("Ganger", 2),
        ("Organized Crime", 2),
        ("Political Activist", 2),
        ("Terrorist", 2),
        ("Framed", 2),
        ("Corp Silver Spooner", 3),
    ],
)
def test_nested_quality_levels_unlock_modules_and_apply_the_quality(name, level):
    spec = module(name)
    assert not spec["unsupported"]
    assert spec["quality_levels"] == [{"group": "SINner", "level": level}]
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]]))
    expected = catalog()["quality_levels"]["SINner"][level]
    assert [q["name"] for q in state.derived["qualities"] if q["name"].startswith("SINner")] == [expected]
    assert state.quality_ids == []
    assert compute(state).model_dump() == state.model_dump()
    restored = import_character(state.model_dump())

    # Import intentionally creates a new character ID. Generated contact IDs
    # follow that identity, but their contents and all other results agree.
    def without_contact_ids(derived):
        return {**derived, "contacts": [{**contact, "id": None} for contact in derived["contacts"]]}

    assert without_contact_ids(restored.derived) == without_contact_ids(state.derived)
    assert compute(restored).model_dump() == restored.model_dump()
    assert apply_patch(state, CharacterPatch(life_modules=[])).derived == runner().derived


def test_nested_quality_levels_take_highest_and_restore_purchased_quality_on_removal():
    levels = catalog()["quality_levels"]["SINner"]
    purchased = next(q["id"] for q in catalog()["qualities"] if q["name"] == levels[1])
    base = apply_patch(runner(), CharacterPatch(quality_ids=[purchased]))
    low, high = module("Framed")["id"], module("Corp Silver Spooner")["id"]
    state = apply_patch(base, CharacterPatch(life_modules=[low, high]))
    assert [q["name"] for q in state.derived["qualities"] if q["name"].startswith("SINner")] == [levels[3]]
    assert state.quality_ids == [purchased]
    assert import_character(state.model_dump()).derived == state.derived
    downgraded = apply_patch(state, CharacterPatch(life_modules=[low]))
    assert [q["name"] for q in downgraded.derived["qualities"] if q["name"].startswith("SINner")] == [levels[2]]
    assert apply_patch(downgraded, CharacterPatch(life_modules=[])).derived == base.derived


@pytest.mark.parametrize("group,level", [("Unknown", 1), ("SINner", 99)])
def test_unknown_nested_quality_levels_still_block_the_whole_module(monkeypatch, group, level):
    root = ET.fromstring(
        f"<chummer><modules><module><id>nested</id><name>Nested</name><bonus>"
        f'<addqualities><qualitylevel group="{group}">{level}</qualitylevel></addqualities>'
        "</bonus></module></modules></chummer>"
    )
    monkeypatch.setattr(life_loader, "data_root", lambda _: root)
    row = life_loader.load_life_modules()[0]
    assert row["unsupported"] == ["qualitylevel:unknown"]
    assert row["quality_levels"] == []


@pytest.mark.parametrize(
    "spec",
    [r for r in catalog()["life_modules"] if r["quality_choice_grants"] and not r["unsupported"]],
    ids=lambda r: r["id"],
)
def test_quality_extra_modules_preserve_choices_and_remove_grants(spec):
    base = runner()
    if spec["required"]:
        base = apply_patch(base, CharacterPatch(metatype="Ork"))
    picks = {f"0:{c['key']}": c["options"][0] if c["options"] else "Seattle" for c in spec["choices"]}
    state = apply_patch(base, CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    assert not has(state.derived["errors"], "engine.life.choice")
    assert not has(state.derived["errors"], "engine.life.requirement")
    for grant in spec["quality_choice_grants"]:
        quality = next(q for q in state.derived["qualities"] if q["id"] == grant["quality_id"])
        assert quality["extra"] == (grant["value"] or picks[f"0:{grant['choice']}"])
        assert quality["free"]
    assert state.quality_extras == base.quality_extras
    assert state.life_module_choices == picks
    assert compute(state).model_dump() == state.model_dump()
    restored = import_character(state.model_dump())
    assert restored.life_module_choices == picks
    assert restored.derived["qualities"] == state.derived["qualities"]
    assert apply_patch(state, CharacterPatch(life_modules=[], life_module_choices={})).derived == base.derived


def test_missing_and_invalid_quality_choices_are_not_granted():
    spec = module("Decker", "Real Life")
    grant = next(g for g in spec["quality_choice_grants"] if g["quality_id"] == "41cc3e26-ae55-4e28-bd6a-b08866c21424")
    for picked in ("", "not a matrix action"):
        state = apply_patch(
            runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices={f"0:{grant['choice']}": picked})
        )
        assert has(state.derived["errors"], "engine.life.choice")
        assert not any(q["id"] == grant["quality_id"] for q in state.derived["qualities"])


def test_quality_extra_conflicts_do_not_overwrite_purchased_extras():
    spec = module("Street Urchin")
    grant = spec["quality_choice_grants"][0]
    base = apply_patch(
        runner(), CharacterPatch(quality_ids=[grant["quality_id"]], quality_extras={grant["quality_id"]: "Original"})
    )
    state = apply_patch(
        base, CharacterPatch(life_modules=[spec["id"]], life_module_choices={f"0:{grant['choice']}": "Different"})
    )
    assert has(state.derived["errors"], "engine.life.qualityChoiceConflict")
    assert state.quality_extras == base.quality_extras
    assert next(q for q in state.derived["qualities"] if q["id"] == grant["quality_id"])["extra"] == "Original"


def test_mr_johnson_contacts_are_free_distinct_and_not_persisted_as_purchases():
    spec = module("Mr. Johnson")
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices={"0:q0": "Ares"}))
    contacts = state.derived["contacts"]
    assert len(contacts) == len({c["id"] for c in contacts}) == 3
    assert all(c["connection"] == 4 and c["loyalty"] == 3 and c["billable"] == 0 for c in contacts)
    assert state.contacts == []
    assert compute(state).derived["contacts"] == contacts


@pytest.mark.parametrize(
    "name,quality_name,rating",
    [
        ("Pit Fighter", "High Pain Tolerance", 2),
        ("Street Preacher", "High Pain Tolerance", 2),
        ("Environmental Combat Specialist (By Type)", "High Pain Tolerance", 2),
        ("Private Investigator/Detective", "In Debt", 5),
    ],
)
def test_rated_quality_grants_apply_each_free_level_and_restore(name, quality_name, rating):
    base = runner()
    spec = module(name)
    state = apply_patch(base, CharacterPatch(life_modules=[spec["id"]]))
    assert not has(state.derived["errors"], "engine.life.unsupported")
    rows = [q for q in state.derived["qualities"] if q["name"] == quality_name]
    assert len(rows) == rating
    assert all(q["free"] for q in rows)
    assert state.quality_ids == []
    if quality_name == "In Debt":
        assert state.derived["nuyen"] - base.derived["nuyen"] == 25000
    else:
        assert state.derived["condition_monitor"]["threshold_offset"] == 2
    assert compute(state).model_dump() == state.model_dump()
    assert import_character(state.model_dump()).derived == state.derived
    assert apply_patch(state, CharacterPatch(life_modules=[])).derived == base.derived


def test_rated_quality_grants_reject_over_cap_and_manual_purchase_conflicts():
    spec = module("Pit Fighter")
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"], spec["id"]]))
    assert has(state.derived["errors"], "engine.life.ratingCap", name="High Pain Tolerance", rating=4, cap=3)
    qid = next(q["id"] for q in catalog()["qualities"] if q["name"] == "High Pain Tolerance")
    base = apply_patch(runner(), CharacterPatch(quality_ids=[qid]))
    state = apply_patch(base, CharacterPatch(life_modules=[spec["id"]]))
    assert has(state.derived["errors"], "engine.life.ratedQualityConflict")
    assert state.quality_ids == [qid]
    assert apply_patch(state, CharacterPatch(life_modules=[])).derived == base.derived


def test_skillgroup_extra_uses_catalog_choices_and_rejects_unknown_group():
    spec = module("Isolated Rural Upbringing", "Teen Years")
    grant = spec["quality_choice_grants"][0]
    choice = next(c for c in spec["choices"] if c["key"] == grant["choice"])
    assert choice["options"] == catalog()["skills"]["groups"]
    valid = apply_patch(
        runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices={f"0:{grant['choice']}": "Athletics"})
    )
    assert "Athletics" in valid.derived["disabled_skill_groups"]
    state = apply_patch(
        runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices={f"0:{grant['choice']}": "Not a group"})
    )
    assert has(state.derived["errors"], "engine.life.choice")
    assert not any(q["id"] == grant["quality_id"] for q in state.derived["qualities"])


def test_quality_id_reference_resolves_without_guessing_a_name():
    spec = module("Snake Charmer")
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]]))
    assert not spec["unsupported"]
    assert any(
        q["id"] == "f8f216b5-1c29-467d-9fb5-c9812408203d" and q["name"] == "Inspired" and q["free"]
        for q in state.derived["qualities"]
    )


@pytest.mark.parametrize(
    "module_name,quality_name,extra",
    [
        ("Have You Heard The Good Word?", "Silence is Golden", ""),
        ("Matrix Royalty", "Too Pretty To Hit", ""),
        ("Dock Rat", "Phobia (Common, Mild)", "Deep water"),
        ("Poor Kid", "Home Ground", "You Know A Guy"),
    ],
)
def test_known_quality_reference_variants_preserve_the_grant(module_name, quality_name, extra):
    spec = module(module_name)
    assert not spec["unsupported"]
    picks = {f"0:{c['key']}": c["options"][0] if c["options"] else extra or "Seattle" for c in spec["choices"]}
    base = runner()
    state = apply_patch(base, CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    quality = next(q for q in state.derived["qualities"] if q["name"] == quality_name)
    assert quality["free"]
    assert quality["extra"] == extra
    assert compute(state).model_dump() == state.model_dump()
    assert import_character(state.model_dump()).derived == state.derived
    assert apply_patch(state, CharacterPatch(life_modules=[], life_module_choices={})).derived == base.derived


def test_embedded_quality_options_apply_only_the_selected_quality(monkeypatch):
    root = ET.fromstring("""<chummer><modules><module><id>choice</id><name>Education</name>
      <stage>Real Life</stage><karma>10</karma><bonus><addqualities><addquality>
      <options><quality>College Education</quality><quality>Technical School Education</quality></options>
      </addquality></addqualities></bonus></module></modules></chummer>""")
    monkeypatch.setattr(life_loader, "data_root", lambda _: root)
    row = life_loader.load_life_modules()[0]
    assert not row["unsupported"]
    monkeypatch.setitem(catalog(), "life_modules", [row])
    key = f"0:{row['choices'][0]['key']}"
    for name in ["College Education", "Technical School Education"]:
        state = apply_patch(runner(), CharacterPatch(life_modules=[row["id"]], life_module_choices={key: name}))
        assert [(q["name"], q["free"]) for q in state.derived["qualities"]] == [(name, True)]
    invalid = apply_patch(runner(), CharacterPatch(life_modules=[row["id"]], life_module_choices={key: "Made Man"}))
    assert has(invalid.derived["errors"], "engine.life.choice")
    assert not invalid.derived["qualities"]


PARIAH = ("Corporate Pariah I", "Corporate Pariah II")


def _warm_body_picks(level: str = PARIAH[0], extra: str = "Ares Macrotechnology") -> tuple[dict, dict[str, str]]:
    spec = module("Warm Body")
    picks = {f"0:{c['key']}": (c["options"][0] if c["options"] else "Seattle") for c in spec["choices"]}
    key = next(c["key"] for c in spec["choices"] if tuple(c["options"]) == PARIAH)
    picks[f"0:{key}"] = level
    picks[f"0:x{key}"] = extra
    return spec, picks


@pytest.mark.parametrize("level", PARIAH)
def test_warm_body_corporate_pariah_level_and_text_are_both_picked(level):
    spec, picks = _warm_body_picks(level)
    assert not spec["unsupported"]
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    assert not has(state.derived["errors"], "engine.life.choice")
    granted = [(q["name"], q["extra"], q["free"]) for q in state.derived["qualities"]]
    assert (level, "Ares Macrotechnology", True) in granted
    assert not [name for name, _, _ in granted if name in set(PARIAH) - {level}]


@pytest.mark.parametrize(
    "level,extra",
    [(PARIAH[0], ""), (PARIAH[0], "[Corp]"), ("Corporate Pariah III", "Ares Macrotechnology")],
)
def test_warm_body_rejects_an_unanswered_level_or_text(level, extra):
    spec, picks = _warm_body_picks(level, extra)
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    assert has(state.derived["errors"], "engine.life.choice")
    assert not [q for q in state.derived["qualities"] if q["name"].startswith("Corporate Pariah")]


@pytest.mark.parametrize("name", ["Day Job", "Corporate Pariah", "Silence Golden"])
def test_ambiguous_or_unknown_quality_names_are_not_guessed(monkeypatch, name):
    root = ET.fromstring(
        f"<chummer><modules><module><id>unknown</id><bonus><addqualities><addquality>{name}</addquality></addqualities></bonus></module></modules></chummer>"
    )
    monkeypatch.setattr(life_loader, "data_root", lambda _: root)
    row = life_loader.load_life_modules()[0]
    assert row["unsupported"] == [f"addquality:{name}"]
    assert not row["quality_grants"]


@pytest.mark.parametrize("category", ["Academic", "Professional"])
def test_corp_college_student_category_specialization_and_day_job(category):
    spec = module("Corp College Student")
    assert not spec["unsupported"]
    picks = {f"0:{c['key']}": c["options"][0] if c["options"] else f"Detail {c['key']}" for c in spec["choices"]}
    category_key = next(c["key"] for c in spec["choices"] if c["kind"] == "knowledge_categories")
    picks[f"0:{category_key}"] = category
    base = runner()
    state = apply_patch(base, CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    assert not has(state.derived["errors"], "engine.life.choice")
    job = next(q for q in state.derived["qualities"] if q["name"] == "Day Job (10 hrs)")
    assert job["free"]
    assert state.derived["skill_specializations"]["Etiquette"] == "Academic"
    knowledge = next(g for g in spec["grants"] if g.get("category_choice"))
    assert (
        next(k for k in state.derived["knowledge_skills"] if k["name"] == picks[f"0:{knowledge['choice']}"])["category"]
        == category
    )
    assert state.derived["karma_chargen"]["specializations"] == 0
    assert state.skill_specializations == base.skill_specializations
    assert state.knowledge_categories == base.knowledge_categories
    assert compute(state).model_dump() == state.model_dump()
    assert import_character(state.model_dump()).derived == state.derived
    assert apply_patch(state, CharacterPatch(life_modules=[], life_module_choices={})).derived == base.derived


@pytest.mark.parametrize("category", ["", "Language", "Invalid"])
def test_unselected_or_disallowed_knowledge_category_does_not_grant_the_skill(category):
    spec = module("Corp College Student")
    grant = next(g for g in spec["grants"] if g.get("category_choice"))
    picks = {f"0:{grant['choice']}": "History of Art", f"0:{grant['category_choice']}": category}
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    assert has(state.derived["errors"], "engine.life.choice", slot=f"0:{grant['category_choice']}")
    assert not any(k["name"] == "History of Art" for k in state.derived["knowledge_skills"])


def test_inline_knowledge_specialization_is_free():
    spec = module("Anarcho-Teen")
    picks = {f"0:{c['key']}": c["options"][0] if c["options"] else "Corporations" for c in spec["choices"]}
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    assert (
        next(k for k in state.derived["knowledge_skills"] if k["name"] == "Agriculture")["spec"] == "Urban Agriculture"
    )
    assert state.derived["karma_chargen"]["specializations"] == 0
    assert state.skill_specializations == {}


def test_placeholder_specialization_requires_a_pick_and_does_not_overwrite_existing_spec():
    spec = module("Environmental Combat Specialist (By Type)")
    choice = next(c for c in spec["choices"] if c["kind"] == "specializations")
    grant = next(g for g in spec["specialization_grants"] if g.get("choice") == choice["key"])
    empty = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]]))
    assert has(empty.derived["errors"], "engine.life.choice", slot=f"0:{choice['key']}")
    picked = apply_patch(empty, CharacterPatch(life_module_choices={f"0:{choice['key']}": "Desert"}))
    assert picked.derived["skill_specializations"][grant["skill"]] == "Desert"
    assert picked.derived["karma_chargen"]["specializations"] == 0
    conflict = apply_patch(picked, CharacterPatch(skill_specializations={grant["skill"]: "Urban"}))
    assert has(conflict.derived["errors"], "engine.life.specializationConflict")
    assert conflict.skill_specializations[grant["skill"]] == "Urban"


@pytest.mark.parametrize("name", ["General Azania", "Pretoria (PWV Metroplex)", "Zulu Nation", "SINless"])
def test_azanian_versions_grant_native_and_additional_languages(name):
    spec = next(r for r in catalog()["life_modules"] if r["parent"] == "Azanian Confederation" and r["name"] == name)
    assert not spec["unsupported"]
    picks = {f"0:{c['key']}": c["options"][0] if c["options"] else "Johannesburg" for c in spec["choices"]}
    picks.update({"0:0": "English", "0:1": "Afrikaans"})
    base = runner()
    state = apply_patch(base, CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    assert not has(state.derived["errors"], "engine.life.choice")
    knowledge = {k["name"]: k for k in state.derived["knowledge_skills"]}
    assert knowledge["English"]["native"]
    assert knowledge["Afrikaans"]["rating"] == 1
    assert knowledge["Afrikaans"]["category"] == "Language"
    assert any(q["name"] == "SINner (National)" for q in state.derived["qualities"]) is (name != "SINless")
    assert state.native_languages == base.native_languages
    assert state.knowledge_skills == base.knowledge_skills
    assert compute(state).model_dump() == state.model_dump()
    assert import_character(state.model_dump()).derived == state.derived
    assert apply_patch(state, CharacterPatch(life_modules=[], life_module_choices={})).derived == base.derived


@pytest.mark.parametrize("city", ["New Hlobane", "Durban"])
def test_zulu_city_accepts_named_or_custom_city_but_keeps_languages_restricted(city):
    spec = module("Zulu Nation")
    choice = next(c for c in spec["choices"] if c.get("allow_custom"))
    assert choice["options"] == ["New Hlobane"]
    picks = {f"0:{choice['key']}": city, "0:0": "Not a language", "0:1": "Afrikaans", "0:q0": "Azania"}
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    assert has(state.derived["errors"], "engine.life.choice", slot="0:0")
    assert not any(k["name"] == "Not a language" for k in state.derived["knowledge_skills"])
    assert next(k for k in state.derived["knowledge_skills"] if k["name"] == city)["rating"] == 2
    picks[f"0:{choice['key']}"] = "[City]"
    invalid = apply_patch(state, CharacterPatch(life_module_choices=picks))
    assert has(invalid.derived["errors"], "engine.life.choice", slot=f"0:{choice['key']}")
    assert not any(k["name"] == "[City]" for k in invalid.derived["knowledge_skills"])


def test_language_category_repair_is_scoped_to_azanian_parent(monkeypatch):
    root = ET.fromstring(
        "<chummer><modules><module><id>unrelated</id><bonus><knowledgeskilllevel><option><name>English</name></option><val>1</val></knowledgeskilllevel></bonus></module></modules></chummer>"
    )
    monkeypatch.setattr(life_loader, "data_root", lambda _: root)
    row = life_loader.load_life_modules()[0]
    assert row["grants"][0]["category"] == "Professional"
