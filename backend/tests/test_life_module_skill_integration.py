"""RF v2 through CharacterState, patch, compute and file persistence."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from copy import deepcopy
from uuid import uuid4

import pytest

from app.characters import apply_patch, import_character, new_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.models import CharacterCreate, CharacterPatch
from app.models.life_modules import LifeModuleSkillAdvancement, LifeModuleTransfer
from app.notices import NoticeError
from tests.notice_asserts import has

MODULES = [
    "b332fa10-e0f5-43aa-bb38-52cdb0060da1",
    "06b4cc0f-3008-4209-ac32-04614a3dc354",
    "737d188a-85b5-47d8-91f2-39863983b464",
    "864c49cf-b44d-4c12-b70a-22228c282f2c",
    "3fb24f67-9d15-49d8-a598-5abbea335e8b",
]


def history():
    return apply_patch(
        new_character(CharacterCreate(build_method="LifeModule")),
        CharacterPatch(
            life_modules=MODULES,
            life_module_choices={"0:4": "Spanish", "1:5": "Seattle Streets"},
        ),
    )


def allocated():
    state = history()
    pool = state.derived["life_module_skills"]["pools"][0]
    target = next(c for c in pool["candidates"] if c["name"] == "Navigation")
    transfer = LifeModuleTransfer(
        id=str(uuid4()),
        entry_id=pool["entry_id"],
        source_skill_id=pool["source_skill_id"],
        grant_fingerprint=pool["grant_fingerprint"],
        destination_skill_id=target["skill_id"],
        ranks=2,
    )
    return apply_patch(state, CharacterPatch(life_module_transfers=[transfer]))


def knowledge_allocated():
    state = apply_patch(history(), CharacterPatch(settings={"chargen_knowledge_skill_max": 4}))
    pools = state.derived["life_module_skills"]["pools"]
    transfers = []
    for pool in pools:
        if pool["kind"] == "active":
            target = next(c for c in pool["candidates"] if c["name"] == "Navigation")
            destination, category, ranks = target["skill_id"], None, 2
        else:
            destination = "Law" if pool["source_name"] == "Government Procedures" else "Medicine"
            category = next(row["category"] for row in catalog()["skills"]["knowledge"] if row["name"] == destination)
            ranks = 1
        transfers.append(
            LifeModuleTransfer(
                id=str(uuid4()),
                entry_id=pool["entry_id"],
                source_kind=pool["kind"],
                source_skill_id=pool["source_skill_id"],
                grant_fingerprint=pool["grant_fingerprint"],
                destination_skill_id=destination,
                destination_category=category,
                ranks=ranks,
            )
        )
    return apply_patch(state, CharacterPatch(life_module_transfers=transfers))


def test_v2_state_uses_rf_caps_and_exposes_an_unallocated_pool():
    state = history()
    assert state.life_module_rules_version == 2
    assert len(set(state.life_module_entry_ids)) == len(MODULES)
    assert state.derived["skill_rating_max"] == 7 and state.derived["knowledge_rating_max"] == 9
    assert state.derived["skill_totals"]["Perception"] == 7
    assert has(state.derived["errors"], "engine.life.transferPending", remaining=2)
    assert state.skills == {} and state.skill_groups == {}


def test_allocation_persists_and_recomputes_without_becoming_a_purchase():
    state = allocated()
    assert not state.derived["errors"]
    assert state.derived["skill_totals"]["Navigation"] == 2
    assert state.derived["karma_chargen"]["skills"] == 0
    assert state.derived["karma"]["spent"] == 245
    assert state.skills == {} and state.exotic_skills == []
    assert compute(state).model_dump() == state.model_dump()
    restored = import_character(state.model_dump())
    assert restored.id != state.id
    assert restored.life_module_entry_ids == state.life_module_entry_ids
    assert restored.derived == state.derived


def test_knowledge_overflow_is_free_and_survives_files_and_career():
    state = knowledge_allocated()
    assert not state.derived["errors"]
    assert state.derived["life_module_skills"]["free_knowledge"]["Law"] == 1
    assert state.derived["life_module_skills"]["free_knowledge"]["Medicine"] == 1
    assert state.knowledge_skills == {}
    assert compute(state).derived == state.derived
    restored = import_character(state.model_dump())
    assert restored.derived == state.derived
    from_chum5, _ = chum5_to_state(state_to_chum5(state))
    assert import_character(from_chum5).derived == state.derived
    career = apply_patch(state, CharacterPatch(career=True))
    assert not career.derived["errors"]
    assert career.life_module_skill_snapshot is not None
    assert career.life_module_skill_snapshot.free_knowledge["Law"] == 1
    assert compute(career).derived == career.derived


def test_manual_purchase_above_transfer_is_priced_from_the_resolved_free_floor():
    state = apply_patch(allocated(), CharacterPatch(skills={"Navigation": 1}))
    assert not state.derived["errors"]
    assert state.skills == {"Navigation": 1}
    assert state.derived["skill_totals"]["Navigation"] == 3
    assert state.derived["karma_chargen"]["skills"] == 6


def test_removing_source_never_reassigns_a_transfer_to_another_acquisition():
    state = allocated()
    old_ids = state.life_module_entry_ids
    state = apply_patch(state, CharacterPatch(life_modules=MODULES[:-1]))
    assert state.life_module_entry_ids == old_ids[:-1]
    assert has(state.derived["errors"], "engine.life.transferOrphan")
    assert state.derived["skill_totals"].get("Navigation", 0) == 0


def test_invalid_transfer_is_saved_but_not_applied():
    state = allocated()
    bad = state.life_module_transfers[0].model_copy(update={"ranks": 3})
    state = apply_patch(state, CharacterPatch(life_module_transfers=[bad]))
    assert state.life_module_transfers[0].ranks == 3
    assert has(state.derived["errors"], "engine.life.transferOverallocated")
    assert state.derived["skill_totals"].get("Navigation", 0) == 0


def test_chum5_bakes_resolved_skill_values_but_restores_original_purchase_inputs():
    state = apply_patch(allocated(), CharacterPatch(skills={"Navigation": 1}))
    raw = state_to_chum5(state)
    root = ET.fromstring(raw)
    assert root.find("lifemodulechoices") is None
    sid = state.life_module_transfers[0].destination_skill_id
    skill = next(s for s in root.findall("./newskills/skills/skill") if s.findtext("suid") == sid)
    assert int(skill.findtext("base")) + int(skill.findtext("karma")) == 3
    payload, _ = chum5_to_state(raw)
    restored = import_character(payload)
    assert restored.skills == {"Navigation": 1}
    assert restored.life_module_entry_ids == state.life_module_entry_ids
    assert restored.life_module_transfers == state.life_module_transfers
    assert restored.derived == state.derived


@pytest.mark.parametrize("edit", ["skill", "version", "conflicting-marker"])
def test_chum5_rejects_edited_standard_skills_and_incompatible_state(edit):
    root = ET.fromstring(state_to_chum5(allocated()))
    if edit == "skill":
        root.find("./newskills/skills/skill/base").text = "12"
    elif edit == "version":
        root.find("lifemoduleskillstate").set("version", "3")
    else:
        ET.SubElement(root, "lifemodulechoices")
    with pytest.raises(NoticeError, match="engine.life.chum5StateInvalid"):
        chum5_to_state(ET.tostring(root))


def test_unallocated_creation_cannot_enter_career():
    with pytest.raises(NoticeError, match="engine.life.creationIncomplete"):
        apply_patch(history(), CharacterPatch(career=True))


def test_career_entry_freezes_transfers_and_never_resurrects_discarded_levels():
    state = allocated()
    career = apply_patch(state, CharacterPatch(career=True))
    assert career.life_module_skill_snapshot is not None
    assert not career.derived["errors"]
    assert career.derived["skill_rating_max"] == 12
    assert career.derived["skill_totals"]["Perception"] == 7
    assert career.derived["skill_totals"]["Navigation"] == 2
    assert career.derived["karma"]["spent"] == state.derived["karma"]["spent"]
    assert compute(career).model_dump() == career.model_dump()


def test_career_snapshot_accepts_older_active_transfers_without_new_fields():
    career = apply_patch(allocated(), CharacterPatch(career=True))
    saved = career.model_dump()
    for row in saved["life_module_transfers"]:
        row.pop("source_kind")
        row.pop("destination_category")
    restored = import_character(saved)
    assert not has(restored.derived["errors"], "engine.life.careerFrozen")
    assert restored.life_module_skill_snapshot == career.life_module_skill_snapshot


def test_final_allocation_and_career_entry_in_one_patch_uses_the_updated_candidate():
    unallocated = history()
    transfers = allocated().life_module_transfers
    # The acquisitions are independently created, so use this state's UUID.
    transfers = [transfers[0].model_copy(update={"entry_id": unallocated.life_module_entry_ids[-1]})]
    state = apply_patch(unallocated, CharacterPatch(life_module_transfers=transfers, career=True))
    assert state.career and not state.derived["errors"]
    assert state.derived["skill_totals"]["Navigation"] == 2


def test_career_growth_is_priced_from_seven_to_eight_and_preserves_receiver():
    state = apply_patch(allocated(), CharacterPatch(career=True))
    source = state.life_module_transfers[0].source_skill_id
    row = LifeModuleSkillAdvancement(id=str(uuid4()), kind="active", target_id=source, levels=1)
    grown = apply_patch(state, CharacterPatch(life_module_skill_advancements=[row]))
    assert not grown.derived["errors"]
    assert grown.derived["skill_totals"]["Perception"] == 8
    assert grown.derived["skill_totals"]["Navigation"] == 2
    assert grown.derived["karma"]["spent"] - state.derived["karma"]["spent"] == 16
    assert grown.life_module_skill_advancements[0].price.per_rating == 2
    assert grown.skills == state.skills
    assert compute(grown).derived == grown.derived
    payload, _ = chum5_to_state(state_to_chum5(grown))
    restored = import_character(payload)
    assert restored.derived == grown.derived
    assert restored.life_module_skill_snapshot == grown.life_module_skill_snapshot


@pytest.mark.parametrize(
    "patch",
    [
        {"life_modules": MODULES[:-1]},
        {"skills": {"Perception": 1}},
        {"life_module_transfers": []},
        {"settings": {"chargen_skill_max": 6}},
        {"build_method": "Karma"},
    ],
)
def test_career_creation_inputs_are_frozen_at_the_api_boundary(patch):
    state = apply_patch(allocated(), CharacterPatch(career=True))
    with pytest.raises(NoticeError, match="engine.life.careerFrozen"):
        apply_patch(state, CharacterPatch(**patch))


def test_growth_history_is_a_prefix_and_last_raise_can_be_undone():
    state = apply_patch(allocated(), CharacterPatch(career=True))
    source = state.life_module_transfers[0].source_skill_id
    rows = [LifeModuleSkillAdvancement(id=str(uuid4()), kind="active", target_id=source, levels=1)]
    one = apply_patch(state, CharacterPatch(life_module_skill_advancements=rows))
    two = apply_patch(
        one,
        CharacterPatch(
            life_module_skill_advancements=[
                *one.life_module_skill_advancements,
                rows[0].model_copy(update={"id": str(uuid4())}),
            ]
        ),
    )
    undone = apply_patch(two, CharacterPatch(life_module_skill_advancements=two.life_module_skill_advancements[:-1]))
    assert undone.derived == one.derived
    with pytest.raises(NoticeError, match="engine.life.advancementInvalid"):
        apply_patch(two, CharacterPatch(life_module_skill_advancements=two.life_module_skill_advancements[1:]))


def test_return_to_creation_keeps_growth_as_purchase_inputs_and_reports_creation_cap():
    state = apply_patch(allocated(), CharacterPatch(career=True))
    source = state.life_module_transfers[0].source_skill_id
    grown = apply_patch(
        state,
        CharacterPatch(
            life_module_skill_advancements=[
                LifeModuleSkillAdvancement(id=str(uuid4()), kind="active", target_id=source, levels=1)
            ]
        ),
    )
    creation = apply_patch(grown, CharacterPatch(career=False))
    assert creation.life_module_skill_snapshot is None
    assert creation.skills["Perception"] == 1
    assert has(creation.derived["errors"], "engine.life.purchaseCap", requested=8, cap=7)
    assert creation.life_module_skill_advancements == grown.life_module_skill_advancements


def test_legacy_career_is_not_silently_migrated():
    state = allocated().model_dump()
    state.update(career=True, life_module_rules_version=None, life_module_entry_ids=[], life_module_transfers=[])
    legacy = import_character(state)
    assert legacy.life_module_rules_version == 1
    assert legacy.life_module_skill_snapshot is None
    assert legacy.derived["life_module_skills"] is None
    assert has(legacy.derived["warnings"], "engine.life.legacyCareer")


def test_group_growth_raises_current_ratings_and_does_not_reuse_overlapping_purchase_counts(monkeypatch):
    cat = catalog()
    rows = deepcopy(cat["life_modules"])
    school = next(m for m in rows if m["id"] == MODULES[3])
    school["grants"].append({"kind": "skill_groups", "name": "Engineering", "choice": "", "value": 1, "category": ""})
    monkeypatch.setitem(cat, "life_modules", rows)
    members = [s for s in cat["skills"]["skills"] if s.get("skillgroup") == "Engineering"]
    creation = apply_patch(
        allocated(), CharacterPatch(skill_groups={"Engineering": 1}, skills={s["name"]: 2 for s in members})
    )
    assert not creation.derived["errors"]
    assert {creation.derived["skill_totals"][s["name"]] for s in members} == {4}
    career = apply_patch(creation, CharacterPatch(career=True))
    grown = apply_patch(
        career,
        CharacterPatch(
            life_module_skill_advancements=[
                LifeModuleSkillAdvancement(id=str(uuid4()), kind="group", target_id="Engineering", levels=1)
            ]
        ),
    )
    assert not grown.derived["errors"]
    assert {grown.derived["skill_totals"][s["name"]] for s in members} == {5}
    assert grown.derived["karma"]["spent"] - career.derived["karma"]["spent"] == 25
    assert grown.skill_groups == {"Engineering": 1}


def test_knowledge_growth_uses_karma_without_a_new_free_knowledge_allowance():
    career = apply_patch(allocated(), CharacterPatch(career=True))
    grown = apply_patch(
        career,
        CharacterPatch(
            life_module_skill_advancements=[
                LifeModuleSkillAdvancement(id=str(uuid4()), kind="knowledge", target_id="Run Debriefs", levels=1)
            ]
        ),
    )
    assert not grown.derived["errors"]
    assert grown.derived["karma_chargen"]["knowledge"] - career.derived["karma_chargen"]["knowledge"] == 1
    assert grown.derived["karma"]["spent"] - career.derived["karma"]["spent"] == 1
    assert grown.knowledge_skills == career.knowledge_skills


def test_new_growth_uses_updated_price_but_prior_growth_is_not_repriced():
    career = apply_patch(allocated(), CharacterPatch(career=True))
    sid = career.life_module_transfers[0].source_skill_id
    row = LifeModuleSkillAdvancement(id=str(uuid4()), kind="active", target_id=sid, levels=1)
    one = apply_patch(career, CharacterPatch(life_module_skill_advancements=[row]))
    two = apply_patch(
        one,
        CharacterPatch(
            settings={"karma_active_skill": 3},
            life_module_skill_advancements=[
                *one.life_module_skill_advancements,
                row.model_copy(update={"id": str(uuid4())}),
            ],
        ),
    )
    assert not two.derived["errors"]
    assert [r.price.per_rating for r in two.life_module_skill_advancements] == [2, 3]
    assert two.derived["career_advancement_karma"] == 16 + 27
