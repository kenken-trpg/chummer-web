"""RF skill overflow: provenance, atomic transfers, limits and saved identity."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from app.data_loader import catalog
from app.engine.life_module_skills import (
    LifeSkillEvent,
    LifeSkillGrant,
    life_skill_events,
    life_skill_key,
    resolve_life_module_skills,
)
from app.models.life_modules import LifeModuleSkillPolicy, LifeModuleTransfer, life_module_entry_ids, life_skill_policy
from tests.notice_asserts import has


@pytest.fixture
def skills():
    return {
        "skills": [
            {"id": "perception", "name": "Perception", "attribute": "INT", "skillgroup": None},
            {"id": "navigation", "name": "Navigation", "attribute": "INT", "skillgroup": "Outdoors"},
            {"id": "tracking", "name": "Tracking", "attribute": "INT", "skillgroup": "Outdoors"},
            {"id": "survival", "name": "Survival", "attribute": "WIL", "skillgroup": "Outdoors"},
            {"id": "first-aid", "name": "First Aid", "attribute": "LOG", "skillgroup": "Biotech"},
        ]
    }


def event(stage, *grants, entry_id=None):
    return LifeSkillEvent(entry_id or str(uuid4()), f"module-{stage}", stage, stage, tuple(grants))


def grant(name, amount, kind="skills", category="Professional"):
    return LifeSkillGrant(kind, name, amount, category)


def overflow_events():
    return [event("Further Education", grant("Perception", 6)), event("Real Life", grant("Perception", 3))]


def pick(pool, destination="navigation", ranks=1, **over):
    return LifeModuleTransfer(
        **{
            "id": str(uuid4()),
            "entry_id": pool.entry_id,
            "source_skill_id": pool.source_skill_id,
            "grant_fingerprint": pool.grant_fingerprint,
            "destination_skill_id": destination,
            "ranks": ranks,
            **over,
        }
    )


def test_defaults_and_explicit_settings():
    assert life_skill_policy().model_dump() == {"version": "rf66-76-v1", "active_cap": 7, "knowledge_cap": 9}
    assert life_skill_policy(active_cap=6, knowledge_cap=8).active_cap == 6
    for invalid in [0, -1, True, 7.0, 1001, 10**400]:
        with pytest.raises(ValidationError):
            life_skill_policy(active_cap=invalid)


def test_explicit_cap_controls_grants_and_overflow(skills):
    events = [event("Real Life", grant("Perception", 7))]
    result = resolve_life_module_skills(events, skills, [], policy=LifeModuleSkillPolicy(active_cap=6))
    assert result.free_active["skill:perception"] == 6
    assert result.pools[0].total == 1


@pytest.mark.parametrize("ranks", [0, -1, True, 1.0, "1", 1001, 10**400])
def test_transfer_model_rejects_non_integer_or_unbounded_levels(ranks):
    with pytest.raises(ValidationError):
        LifeModuleTransfer(
            id=str(uuid4()),
            entry_id=str(uuid4()),
            source_skill_id="p",
            grant_fingerprint="a" * 64,
            destination_skill_id="n",
            ranks=ranks,
        )


def test_migration_ids_are_deterministic_and_survive_character_id_change():
    ids = life_module_entry_ids("runner", ["one", "two"])
    assert ids == life_module_entry_ids("runner", ["one", "two"])
    assert life_module_entry_ids("copy", ["one", "two"], ids) == ids
    with pytest.raises(ValueError):
        life_module_entry_ids("runner", ["one", "two"], [ids[0], ids[0]])
    with pytest.raises(ValueError):
        life_module_entry_ids("runner", ["one", "two"], [])


def test_real_life_overflow_is_credit_and_does_not_mutate_input(skills):
    events = overflow_events()
    untouched = deepcopy(events)
    data = deepcopy(skills)
    result = resolve_life_module_skills(events, skills, [])
    assert result.free_active[life_skill_key("perception")] == 7
    pool = result.pools[0]
    assert (pool.before, pool.grant, pool.kept, pool.total, pool.remaining) == (6, 3, 1, 2, 2)
    assert has(result.errors, "engine.life.transferPending", remaining=2)
    assert not result.complete
    assert events == untouched and skills == data


def test_acquisitions_are_sorted_by_stage_without_shifting_their_ids(skills):
    events = overflow_events()
    forward = resolve_life_module_skills(events, skills, [])
    reverse = resolve_life_module_skills(list(reversed(events)), skills, [])
    assert forward.public() == reverse.public()


@pytest.mark.parametrize("stage", ["Nationality", "Formative Years", "Teen Years", "Further Education"])
def test_general_overflow_is_lost_and_does_not_reject_the_module(skills, stage):
    result = resolve_life_module_skills([event(stage, grant("Perception", 9))], skills, [])
    assert result.complete and not result.pools
    assert result.losses[0]["lost"] == 2
    assert has(result.warnings, "engine.life.skillExcessLost", lost=2)


def test_group_members_do_not_generate_credit_even_for_individual_grants(skills):
    result = resolve_life_module_skills([event("Real Life", grant("First Aid", 9))], skills, [])
    assert result.complete and not result.pools
    assert result.free_active[life_skill_key("first-aid")] == 7
    assert result.losses[0]["reason"] == "grouped"


def test_group_grants_expand_once_and_preserve_unequal_ratings(skills):
    events = [
        event("Teen Years", grant("Navigation", 6), grant("Tracking", 4), grant("Survival", 2)),
        event("Real Life", grant("Outdoors", 2, "skill_groups")),
    ]
    result = resolve_life_module_skills(events, skills, [])
    assert [result.free_active[life_skill_key(s)] for s in ["navigation", "tracking", "survival"]] == [7, 6, 4]
    group = next(g for g in result.groups if g["name"] == "Outdoors")
    assert group["uniform"] is False and group["free_uniform_rating"] is None
    assert result.losses[0]["lost"] == 1


def test_successful_split_transfer_and_recompute_fixed_point(skills):
    events = overflow_events()
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    picks = [pick(pool), pick(pool, "tracking")]
    result = resolve_life_module_skills(events, skills, picks)
    assert result.complete
    assert result.free_active == {"skill:perception": 7, "skill:navigation": 1, "skill:tracking": 1}
    assert result.pools[0].allocated == 2
    assert result.pools[0].remaining == 0
    assert (
        result.pools[0].total == result.pools[0].allocated + result.pools[0].remaining + result.pools[0].unallocatable
    )
    saved = json.loads(json.dumps([p.model_dump() for p in picks]))
    restored = [LifeModuleTransfer.model_validate(p) for p in saved]
    assert resolve_life_module_skills(events, skills, restored).public() == result.public()
    json.dumps(result.public())


@pytest.mark.parametrize("target", ["perception", "first-aid", "unknown", "Outdoors"])
def test_same_skill_different_attribute_and_unknown_targets_are_rejected(skills, target):
    events = overflow_events()
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    result = resolve_life_module_skills(events, skills, [pick(pool, target, 2)])
    assert has(result.errors, "engine.life.transferInvalidTarget")
    assert result.pools[0].allocated == 0
    assert result.pools[0].remaining == 2


def test_invalid_pool_is_atomic_regardless_of_input_row_order(skills):
    events = overflow_events()
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    picks = [pick(pool), pick(pool, "first-aid")]
    result = resolve_life_module_skills(events, skills, picks)
    assert result.free_active == {"skill:perception": 7}
    assert result.pools[0].status == "invalid"
    reverse = resolve_life_module_skills(events, skills, list(reversed(picks)))
    assert reverse.free_active == result.free_active


def test_overallocation_and_repeated_destination_do_not_create_free_levels(skills):
    events = overflow_events()
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    result = resolve_life_module_skills(events, skills, [pick(pool, ranks=3)])
    assert has(result.errors, "engine.life.transferOverallocated", total=2, requested=3)
    assert result.pools[0].allocated == 0
    duplicate = resolve_life_module_skills(events, skills, [pick(pool), pick(pool)])
    assert has(duplicate.errors, "engine.life.transferDuplicate")
    assert duplicate.free_active == {"skill:perception": 7}


def test_duplicate_transfer_ids_are_rejected(skills):
    events = overflow_events()
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    first = pick(pool)
    result = resolve_life_module_skills(events, skills, [first, pick(pool, "tracking", id=first.id)])
    assert has(result.errors, "engine.life.transferDuplicate")
    assert result.pools[0].allocated == 0


def test_capacity_uses_all_direct_grants_from_the_same_module(skills):
    events = overflow_events()
    events[1] = replace(events[1], grants=(*events[1].grants, grant("Navigation", 6)))
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    assert next(c for c in pool.candidates if c.skill_id == "navigation").capacity == 1
    result = resolve_life_module_skills(events, skills, [pick(pool, ranks=2)])
    assert has(result.errors, "engine.life.transferCapacity", requested=2, capacity=1)
    assert result.free_active["skill:navigation"] == 6


def test_capacity_does_not_double_count_a_pools_saved_allocation(skills):
    events = overflow_events()
    events[1] = replace(events[1], grants=(*events[1].grants, grant("Navigation", 5)))
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    result = resolve_life_module_skills(events, skills, [pick(pool, ranks=2)])
    assert result.complete
    assert next(c for c in result.pools[0].candidates if c.skill_id == "navigation").capacity == 2


def test_unavailable_targets_are_not_learnable(skills):
    events = overflow_events()
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    result = resolve_life_module_skills(
        events, skills, [pick(pool, ranks=2)], unavailable_skill_ids=frozenset({"navigation"})
    )
    assert has(result.errors, "engine.life.transferInvalidTarget")
    assert result.free_active == {"skill:perception": 7}


def test_only_unallocatable_remainder_is_lost(skills):
    events = overflow_events()
    events[1] = replace(events[1], grants=(*events[1].grants, grant("Navigation", 7), grant("Tracking", 6)))
    result = resolve_life_module_skills(events, skills, [])
    assert (result.pools[0].remaining, result.pools[0].unallocatable) == (1, 1)
    assert has(result.errors, "engine.life.transferPending", remaining=1)
    assert has(result.warnings, "engine.life.transferUnallocatable", lost=1)
    pool = result.pools[0]
    done = resolve_life_module_skills(events, skills, [pick(pool, "tracking")])
    assert done.complete and done.pools[0].unallocatable == 1


def test_all_targets_full_is_a_warning_not_an_unfinishable_error(skills):
    events = overflow_events()
    events[1] = replace(events[1], grants=(*events[1].grants, grant("Navigation", 7), grant("Tracking", 7)))
    result = resolve_life_module_skills(events, skills, [])
    assert result.complete
    assert result.pools[0].status == "unallocatable"
    assert (result.pools[0].remaining, result.pools[0].unallocatable) == (0, 2)


def test_exotic_requires_specific_target_and_uses_case_insensitive_identity(skills):
    skills["skills"].append({"id": "exotic", "name": "Exotic Skill", "attribute": "INT", "exotic": True})
    events = overflow_events()
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    invalid = resolve_life_module_skills(events, skills, [pick(pool, "exotic", 2)])
    assert has(invalid.errors, "engine.life.transferInvalidTarget")
    valid = resolve_life_module_skills(events, skills, [pick(pool, "exotic", 2, destination_specific="  Device  ")])
    assert valid.complete and valid.free_active["exotic:exotic:device"] == 2
    duplicate = resolve_life_module_skills(
        events,
        skills,
        [pick(pool, "exotic", destination_specific="Device"), pick(pool, "exotic", destination_specific="device")],
    )
    assert has(duplicate.errors, "engine.life.transferDuplicate")


def test_exotic_new_targets_prevent_false_unallocatable_remainder(skills):
    skills["skills"].append({"id": "exotic", "name": "Exotic Skill", "attribute": "INT", "exotic": True})
    events = [event("Real Life", grant("Perception", 100))]
    result = resolve_life_module_skills(events, skills, [])
    assert result.pools[0].remaining == 93 and result.pools[0].unallocatable == 0


def test_removal_or_new_acquisition_never_redirects_saved_transfers(skills):
    events = overflow_events()
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    row = pick(pool, ranks=2)
    removed = resolve_life_module_skills(events[:1], skills, [row])
    assert has(removed.errors, "engine.life.transferOrphan", transfer=row.id)
    assert "skill:navigation" not in removed.free_active
    readded = resolve_life_module_skills([events[0], replace(events[1], entry_id=str(uuid4()))], skills, [row])
    assert has(readded.errors, "engine.life.transferOrphan")
    assert readded.pools[0].allocated == 0


def test_semantic_definition_change_expires_transfer_but_translation_does_not(skills):
    events = overflow_events()
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    row = pick(pool, ranks=2)
    changed = [events[0], replace(events[1], grants=(grant("Perception", 4),))]
    result = resolve_life_module_skills(changed, skills, [row])
    assert has(result.errors, "engine.life.transferSourceChanged")
    translated = deepcopy(skills)
    translated["skills"][0]["name"] = "知覚"
    translated_events = [
        replace(e, name="経歴", grants=tuple(replace(g, name="知覚") for g in e.grants)) for e in events
    ]
    result = resolve_life_module_skills(translated_events, translated, [row])
    assert result.complete and result.pools[0].allocated == 2


def test_later_module_sees_prior_transfers_and_group_overflow_is_not_recycled(skills):
    events = overflow_events()
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    events.append(event("Real Life", grant("Navigation", 7)))
    result = resolve_life_module_skills(events, skills, [pick(pool, ranks=2)])
    assert result.complete
    assert result.free_active["skill:navigation"] == 7
    assert len(result.pools) == 1 and result.losses[0]["lost"] == 2


def test_knowledge_nine_and_native_zero_have_separate_semantics(skills):
    events = [
        event(
            "Nationality", grant("English", 0, "knowledge_skills", "Language"), grant("History", 8, "knowledge_skills")
        ),
        event("Teen Years", grant("History", 2, "knowledge_skills")),
    ]
    result = resolve_life_module_skills(events, skills, [])
    assert result.native_languages == ["English"]
    assert "English" not in result.free_knowledge
    assert result.free_knowledge["History"] == 9
    assert has(result.errors, "engine.life.transferPending", name="History", remaining=1)
    assert len(result.pools) == 1 and result.pools[0].kind == "knowledge"
    assert result.pools[0].source_skill_id == "History"


def test_knowledge_overflow_preserves_the_total_requested_across_later_modules(skills):
    events = [
        event("Nationality", grant("History", 8, "knowledge_skills")),
        event("Teen Years", grant("History", 2, "knowledge_skills")),
        event("Real Life", grant("History", 1, "knowledge_skills")),
    ]
    result = resolve_life_module_skills(events, skills, [])
    assert result.requested_knowledge["History"] == 11
    assert result.free_knowledge["History"] == 9
    assert [pool.total for pool in result.pools] == [1, 1]
    transfers = [
        pick(result.pools[0], "Law", source_kind="knowledge", destination_category="Academic"),
        pick(result.pools[1], "Medicine", source_kind="knowledge", destination_category="Professional"),
    ]
    resolved = resolve_life_module_skills(events, skills, transfers)
    assert resolved.complete
    assert resolved.free_knowledge == {"History": 9, "Law": 1, "Medicine": 1}
    assert resolved.knowledge_categories["Law"] == "Academic"
    assert (
        resolved.public()
        == resolve_life_module_skills(
            events, skills, [LifeModuleTransfer.model_validate(row.model_dump()) for row in transfers]
        ).public()
    )


def test_knowledge_transfer_rejects_invalid_rows_atomically(skills):
    events = [event("Real Life", grant("History", 11, "knowledge_skills"))]
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    valid = pick(pool, "Law", source_kind="knowledge", destination_category="Academic")
    invalid = pick(pool, "History", source_kind="knowledge", destination_category="Academic")
    result = resolve_life_module_skills(events, skills, [valid, invalid])
    assert has(result.errors, "engine.life.transferInvalidTarget")
    assert result.pools[0].allocated == 0
    assert "Law" not in result.free_knowledge
    over = resolve_life_module_skills(
        events, skills, [pick(pool, "Law", ranks=10, source_kind="knowledge", destination_category="Academic")]
    )
    assert has(over.errors, "engine.life.transferOverallocated")
    assert over.free_knowledge == {"History": 9}
    wrong_kind = resolve_life_module_skills(events, skills, [pick(pool, "Law", destination_category="Academic")])
    assert has(wrong_kind.errors, "engine.life.transferOrphan")


def test_knowledge_transfer_checks_catalog_category_and_later_native_language(skills):
    skills["knowledge"] = [{"name": "Medicine", "category": "Academic"}]
    events = [
        event("Teen Years", grant("History", 10, "knowledge_skills")),
        event("Real Life", grant("English", 0, "knowledge_skills", "Language")),
    ]
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    wrong_category = resolve_life_module_skills(
        events, skills, [pick(pool, "Medicine", source_kind="knowledge", destination_category="Professional")]
    )
    assert has(wrong_category.errors, "engine.life.transferInvalidTarget")
    native = resolve_life_module_skills(
        events, skills, [pick(pool, "English", source_kind="knowledge", destination_category="Language")]
    )
    assert has(native.errors, "engine.life.transferInvalidTarget")
    manual_native = resolve_life_module_skills(
        events,
        skills,
        [pick(pool, "Sperethiel", source_kind="knowledge", destination_category="Language")],
        known_native_languages=frozenset({"Sperethiel"}),
    )
    assert has(manual_native.errors, "engine.life.transferInvalidTarget")


def test_pools_share_capacity_in_stable_source_order(skills):
    skills["skills"].append({"id": "other", "name": "Other Skill", "attribute": "INT"})
    events = [
        event(
            "Real Life", grant("Perception", 9), grant("Other Skill", 9), grant("Navigation", 5), grant("Tracking", 7)
        )
    ]
    preview = resolve_life_module_skills(events, skills, [])
    assert [p.source_skill_id for p in preview.pools] == ["other", "perception"]
    assert preview.pools[1].provisional
    result = resolve_life_module_skills(events, skills, [pick(preview.pools[0], ranks=2)])
    assert result.complete and result.free_active["skill:navigation"] == 7
    assert result.pools[0].allocated == 2
    assert result.pools[1].unallocatable == 2
    assert not result.pools[1].provisional


def test_real_catalog_overflow_has_two_levels_and_preserves_original_choice_positions():
    data = catalog()
    ids = [
        "b332fa10-e0f5-43aa-bb38-52cdb0060da1",
        "06b4cc0f-3008-4209-ac32-04614a3dc354",
        "737d188a-85b5-47d8-91f2-39863983b464",
        "864c49cf-b44d-4c12-b70a-22228c282f2c",
        "3fb24f67-9d15-49d8-a598-5abbea335e8b",
    ]
    by_id = {m["id"]: m for m in data["life_modules"]}
    rows = [{**by_id[mid], "occurrence": i} for i, mid in enumerate(ids)]
    entry_ids = life_module_entry_ids("fixture", ids)
    events, errors = life_skill_events(rows, entry_ids, {"0:4": "Spanish", "1:5": "Seattle Streets"})
    assert not errors
    result = resolve_life_module_skills(events, data["skills"], [])
    pool = next(p for p in result.pools if p.source_name == "Perception")
    assert pool.entry_id == entry_ids[4]
    assert (pool.before, pool.grant, pool.kept, pool.total) == (6, 3, 1, 2)
    targets = [c.skill_id for c in pool.candidates if not c.specific_required and c.capacity]
    done = resolve_life_module_skills(events, data["skills"], [pick(pool, targets[0]), pick(pool, targets[1])])
    assert done.complete
    assert sum(g.amount for g in events[3].grants if g.name == "Perception") == 2


def test_choice_adapter_rejects_missing_or_disallowed_choices_without_guessing():
    data = catalog()
    row = next(m for m in data["life_modules"] if m["id"] == "b332fa10-e0f5-43aa-bb38-52cdb0060da1")
    row = {**row, "occurrence": 2}
    ids = life_module_entry_ids("fixture", ["rejected", "rejected", row["id"]])
    events, errors = life_skill_events([row], ids, {"0:4": "Spanish", "2:4": "Not a Language"})
    assert has(errors, "engine.life.choice", slot="2:4")
    assert events[0].entry_id == ids[2]
    assert not any(g.name == "Not a Language" for g in events[0].grants)


def test_invalid_catalog_grants_are_reported_instead_of_applied(skills):
    result = resolve_life_module_skills(
        [event("Real Life", grant("Unknown", 1), grant("Outdoors", -1, "skill_groups"))], skills, []
    )
    assert not result.complete and not result.free_active
    assert has(result.errors, "engine.life.skillGrantInvalid")


def test_duplicate_acquisition_ids_are_structural_errors(skills):
    events = overflow_events()
    events[1] = replace(events[1], entry_id=events[0].entry_id)
    with pytest.raises(ValueError, match="duplicate"):
        resolve_life_module_skills(events, skills, [])


@given(
    source=st.integers(min_value=8, max_value=1000),
    nav=st.integers(min_value=0, max_value=7),
    track=st.integers(min_value=0, max_value=7),
)
def test_grant_conservation_across_allocation_and_unallocatable_remainder(source, nav, track):
    skills = {
        "skills": [
            {"id": "perception", "name": "Perception", "attribute": "INT"},
            {"id": "navigation", "name": "Navigation", "attribute": "INT", "skillgroup": "Outdoors"},
            {"id": "tracking", "name": "Tracking", "attribute": "INT", "skillgroup": "Outdoors"},
        ]
    }
    events = [event("Real Life", grant("Perception", source), grant("Navigation", nav), grant("Tracking", track))]
    pool = resolve_life_module_skills(events, skills, []).pools[0]
    a = min(pool.total, 7 - nav)
    b = min(pool.total - a, 7 - track)
    picks = ([pick(pool, ranks=a)] if a else []) + ([pick(pool, "tracking", ranks=b)] if b else [])
    result = resolve_life_module_skills(events, skills, picks)
    assert result.complete
    assert source + nav + track == sum(result.free_active.values()) + sum(p.unallocatable for p in result.pools)
    assert all(0 <= val <= 7 for val in result.free_active.values())
    assert result.public() == resolve_life_module_skills(events, skills, picks).public()
