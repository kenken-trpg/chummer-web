"""Construction must consume inventory exactly once without refunding purchases."""

from __future__ import annotations

import pytest

from app.characters import apply_patch
from app.data_loader import catalog_list
from app.engine import compute
from app.engine.gear.deck_modules import ADD_MODULE, COPROCESSOR, DECK_BUILDER
from app.engine.gear.electronic_modifications import FIVE_PARTS, SINGLE_PARTS
from app.models import (
    CharacterPatch,
    ElectronicPartsAllocation,
    ElectronicPartsSupply,
    GearInstall,
)
from app.notices import NoticeError
from tests.engine_support import ERIKA_DECK, _mundane
from tests.notice_asserts import has

MODIFY = "821d8a12-b883-49de-9ccf-f39c42fba860"


def setup_construction(parts_id: str = FIVE_PARTS, qty: int = 1):
    deck = GearInstall(gear_id=ERIKA_DECK)
    parts = GearInstall(gear_id=parts_id, qty=qty)
    state = compute(_mundane("construction", cyberdecks=[deck], gear=[parts]))
    mod = GearInstall(gear_id=MODIFY, parent_id=deck.id)
    state = apply_patch(state, CharacterPatch(gear=[*state.gear, mod]))
    return state, deck, parts, mod


def complete(state, parts, mod):
    record = state.electronic_modification_records[0].model_copy(deep=True)
    record.status = "completed"
    record.allocations = [ElectronicPartsAllocation(source_id=parts.id, units=16)]
    return apply_patch(state, CharacterPatch(electronic_modification_records=[record]))


@pytest.mark.parametrize(("parts_id", "qty", "remaining"), [(FIVE_PARTS, 1, 4), (SINGLE_PARTS, 4, 0)])
def test_consumption_preserves_payment_and_is_idempotent(parts_id, qty, remaining):
    state, deck, parts, mod = setup_construction(parts_id, qty)
    assert state.derived["cyberdecks"][0]["array"] == [4, 3, 2, 1]
    spent = state.derived["nuyen_spent"]
    out = complete(state, parts, mod)
    row = next(r for r in out.derived["gear"] if r["id"] == parts.id)
    assert row["parts_remaining_units"] == remaining
    assert out.derived["cyberdecks"][0]["array"] == [5, 2, 2, 1]
    assert out.derived["nuyen_spent"] == spent == 50500
    frozen = out.model_dump()
    assert compute(out).model_dump() == frozen
    assert compute(type(out).model_validate_json(out.model_dump_json())).model_dump() == frozen
    assert (
        apply_patch(
            out, CharacterPatch(electronic_modification_records=out.electronic_modification_records)
        ).model_dump()
        == frozen
    )
    removed = apply_patch(out, CharacterPatch(gear=[r for r in out.gear if r.id != mod.id], cyberdecks=[]))
    assert removed.electronic_modification_records == out.electronic_modification_records
    assert next(r for r in removed.derived["gear"] if r["id"] == parts.id)["parts_remaining_units"] == remaining


def test_insufficient_parts_and_duplicate_allocations_are_atomic():
    state, _, parts, mod = setup_construction(SINGLE_PARTS)
    before = state.model_dump()
    with pytest.raises(NoticeError):
        complete(state, parts, mod)
    assert state.model_dump() == before
    record = state.electronic_modification_records[0].model_copy(deep=True)
    record.status = "completed"
    record.allocations = [ElectronicPartsAllocation(source_id=parts.id, units=8)] * 2
    with pytest.raises(NoticeError):
        apply_patch(state, CharacterPatch(electronic_modification_records=[record]))


def test_consumed_purchase_and_parent_cannot_be_removed_or_discounted():
    state, _, parts, mod = setup_construction()
    state = complete(state, parts, mod)
    for rows in (
        [r for r in state.gear if r.id != parts.id],
        [r.model_copy(update={"discounted": True}) if r.id == parts.id else r for r in state.gear],
    ):
        with pytest.raises(NoticeError):
            apply_patch(state, CharacterPatch(gear=rows))
    with pytest.raises(NoticeError):
        apply_patch(state, CharacterPatch(electronic_modification_records=[]))


def test_quarter_pack_supplies_and_explicit_correction():
    state, _, parts, mod = setup_construction()
    state = apply_patch(
        state, CharacterPatch(electronic_parts_supplies=[ElectronicPartsSupply(id=f"s{i}", units=1) for i in range(16)])
    )
    record = state.electronic_modification_records[0].model_copy(deep=True)
    record.status = "completed"
    record.allocations = [ElectronicPartsAllocation(source_id=f"s{i}", units=1) for i in range(16)]
    state = apply_patch(state, CharacterPatch(electronic_modification_records=[record]))
    assert state.derived["nuyen_spent"] == 50500
    record = state.electronic_modification_records[0].model_copy(update={"status": "cancelled", "note": "wrong entry"})
    out = apply_patch(state, CharacterPatch(electronic_modification_records=[record]))
    assert out.derived["cyberdecks"][0]["array"] == [4, 3, 2, 1]
    out = apply_patch(out, CharacterPatch(electronic_parts_supplies=[]))
    assert out.electronic_modification_records[0].status == "cancelled"


def test_new_patch_without_history_is_pending_and_legacy_is_unverified():
    state, _, _, _ = setup_construction()
    assert state.derived["gear"][-1]["modification_status"] == "pending"
    legacy = state.model_copy(update={"electronic_modification_records": []}, deep=True)
    out = compute(legacy)
    assert out.derived["gear"][-1]["modification_status"] == "unverified"
    assert out.derived["cyberdecks"][0]["array"] == [5, 2, 2, 1]


def test_module_pools_keep_overflow_and_do_not_apply_invalid_effects():
    deck = GearInstall(gear_id=ERIKA_DECK)
    mod = GearInstall(gear_id=ADD_MODULE, parent_id=deck.id)
    normal = GearInstall(gear_id=COPROCESSOR, parent_id=deck.id, qty=2)
    wired = GearInstall(gear_id=COPROCESSOR, parent_id=mod.id)
    out = compute(_mundane("pools", cyberdecks=[deck], gear=[mod, normal, wired]))
    assert len(out.gear) == 3
    assert out.derived["cyberdecks"][0]["module_used"] == 2
    assert out.derived["matrix_initiative"]["cold_dice"] == 4
    assert has(out.derived["warnings"], "engine.gear.modulesOver", used=2, max=1)
    assert next(r for r in out.derived["gear"] if r["id"] == normal.id)["module_valid"] is False
    assert next(r for r in out.derived["gear"] if r["id"] == wired.id)["module_valid"] is True
    out.quality_ids = [DECK_BUILDER]
    out = compute(out)
    assert out.derived["cyberdecks"][0]["module_max"] == 2
    assert out.derived["matrix_initiative"]["cold_dice"] == 4  # no stacking


def test_spare_disabled_and_other_device_modules_never_leak_effects():
    decks = [GearInstall(gear_id=ERIKA_DECK), GearInstall(gear_id=ERIKA_DECK)]
    for parent, enabled in [(None, True), (decks[0].id, False), (decks[1].id, True), ("missing", True)]:
        out = compute(
            _mundane(
                "scoped", cyberdecks=decks, gear=[GearInstall(gear_id=COPROCESSOR, parent_id=parent, equipped=enabled)]
            )
        )
        assert len(out.gear) == 1
        assert out.derived["matrix_initiative"]["cold_dice"] == 3
    assert all(not s.get("armor_capacity") for s in catalog_list("gear") if s.get("category") == "Cyberdeck Modules")


def test_chummer_export_uses_residual_packs_and_keeps_quarters():
    import xml.etree.ElementTree as ET

    from app.chummer_export import state_to_chum5
    from app.chummer_import import chum5_to_state
    from app.models import CharacterState

    state, _, parts, mod = setup_construction()
    state = complete(state, parts, mod)
    state.electronic_parts_supplies = [ElectronicPartsSupply(units=1, note="scrap")]
    root = ET.fromstring(state_to_chum5(state))
    parts_nodes = [g for g in root.findall("./gears/gear") if g.findtext("sourceid") in (SINGLE_PARTS, FIVE_PARTS)]
    assert sorted(float(g.findtext("qty")) for g in parts_nodes) == [0.25, 1.0]
    data, _ = chum5_to_state(ET.tostring(root))
    out = compute(CharacterState(**data))
    assert sum(r["parts_remaining_units"] for r in out.derived["gear"] if "parts_remaining_units" in r) == 5
    assert out.electronic_modification_records == []  # external format limitation
    assert next(r for r in out.derived["gear"] if r["gear_id"] == SINGLE_PARTS)["nuyen"] == 0


def test_completed_snapshot_is_frozen_and_reparenting_is_rejected():
    state, _, parts, mod = setup_construction()
    state = complete(state, parts, mod)
    record = state.electronic_modification_records[0].model_dump()
    deck = state.cyberdecks[0].model_copy(update={"array_order": ["firewall", "sleaze", "attack", "dataprocessing"]})
    out = apply_patch(state, CharacterPatch(cyberdecks=[deck]))
    assert out.electronic_modification_records[0].model_dump() == record
    other = GearInstall(gear_id=ERIKA_DECK)
    with pytest.raises(NoticeError):
        apply_patch(
            state,
            CharacterPatch(
                cyberdecks=[*state.cyberdecks, other],
                gear=[r.model_copy(update={"parent_id": other.id}) if r.id == mod.id else r for r in state.gear],
            ),
        )


def test_reservation_cannot_be_reused_and_cancellation_releases_it():
    state, deck, parts, mod = setup_construction()
    record = state.electronic_modification_records[0].model_copy(
        update={"allocations": [ElectronicPartsAllocation(source_id=parts.id, units=16)]}
    )
    state = apply_patch(state, CharacterPatch(electronic_modification_records=[record]))
    other = GearInstall(gear_id=ERIKA_DECK)
    another_mod = GearInstall(gear_id=MODIFY, parent_id=other.id)
    state = apply_patch(state, CharacterPatch(cyberdecks=[deck, other], gear=[*state.gear, another_mod]))
    second = state.electronic_modification_records[1].model_copy(
        update={"allocations": [ElectronicPartsAllocation(source_id=parts.id, units=16)]}
    )
    with pytest.raises(NoticeError):
        apply_patch(state, CharacterPatch(electronic_modification_records=[record, second]))
    state = apply_patch(state, CharacterPatch(gear=[r for r in state.gear if r.id != mod.id]))
    assert next(r for r in state.derived["gear"] if r["id"] == parts.id)["parts_reserved_units"] == 0


def test_hardware_shop_supply_can_only_be_registered_once():
    shop = GearInstall(gear_id="4edec80a-e8df-4817-9728-4a6fc04d183e", extra="Hardware")
    state = compute(_mundane("shop", gear=[shop]))
    supply = ElectronicPartsSupply(kind="equipment", equipment_id=shop.id, units=8)
    state = apply_patch(state, CharacterPatch(electronic_parts_supplies=[supply]))
    with pytest.raises(NoticeError):
        apply_patch(state, CharacterPatch(electronic_parts_supplies=[supply.model_copy(update={"units": 100})]))
    with pytest.raises(NoticeError):
        apply_patch(
            state,
            CharacterPatch(
                electronic_parts_supplies=[
                    *state.electronic_parts_supplies,
                    ElectronicPartsSupply(kind="equipment", equipment_id=shop.id, units=8),
                ]
            ),
        )


def test_increase_records_preconstruction_value_and_permanent_damage():
    deck = GearInstall(gear_id=ERIKA_DECK)
    parts = GearInstall(gear_id=FIVE_PARTS, qty=2)
    state = compute(_mundane("increase", cyberdecks=[deck], gear=[parts]))
    mod = GearInstall(gear_id="e2c6eded-5897-4ae6-9911-230292d3f858", parent_id=deck.id)
    state = apply_patch(state, CharacterPatch(gear=[*state.gear, mod]))
    assert state.derived["cyberdecks"][0]["attack"] == 4
    assert "matrix_permanent_damage" not in state.derived["cyberdecks"][0]
    record = state.electronic_modification_records[0].model_copy(
        update={
            "status": "completed",
            "required_units": 1,
            "allocations": [ElectronicPartsAllocation(source_id=parts.id, units=40)],
        }
    )
    out = apply_patch(state, CharacterPatch(electronic_modification_records=[record]))
    assert out.electronic_modification_records[0].required_units == 40  # (4+1)*2 packs
    assert out.electronic_modification_records[0].host_snapshot["attack"] == 4
    assert out.derived["cyberdecks"][0]["attack"] == 5
    assert out.derived["cyberdecks"][0]["matrix_permanent_damage"] == 2
    assert out.derived["cyberdecks"][0]["matrix_condition_monitor"] == 7
    assert out.derived["cyberdecks"][0]["construction_attributes"]["attack"] == 4


def test_discount_and_parent_multiplier_survive_consumption():
    bag = GearInstall(gear_id="f1d60d11-b2e1-41ba-8cb5-34ce86ee584e", qty=2)
    parts = GearInstall(gear_id=FIVE_PARTS, parent_id=bag.id, discounted=True)
    deck = GearInstall(gear_id=ERIKA_DECK)
    state = compute(_mundane("container", cyberdecks=[deck], gear=[bag, parts]))
    spent = state.derived["nuyen_spent"]
    mod = GearInstall(gear_id=MODIFY, parent_id=deck.id)
    state = apply_patch(state, CharacterPatch(gear=[*state.gear, mod]))
    out = complete(state, parts, mod)
    assert out.derived["nuyen_spent"] == spent
    assert next(r for r in out.derived["gear"] if r["id"] == parts.id)["parts_remaining_units"] == 24
    with pytest.raises(NoticeError):
        apply_patch(out, CharacterPatch(gear=[r for r in out.gear if r.id != bag.id]))


def test_two_root_modifications_do_not_create_unlimited_module_slots():
    deck = GearInstall(gear_id=ERIKA_DECK)
    mods = [GearInstall(gear_id=ADD_MODULE, parent_id=deck.id) for _ in range(2)]
    modules = [GearInstall(gear_id=COPROCESSOR, parent_id=m.id) for m in mods]
    out = compute(_mundane("double-mod", cyberdecks=[deck], gear=[*mods, *modules]))
    assert len(out.gear) == 4
    assert out.derived["cyberdecks"][0]["hardwired_module_max"] == 0
    assert out.derived["matrix_initiative"]["cold_dice"] == 3
    assert has(out.derived["warnings"], "engine.gear.modificationsOver")


def test_career_transition_and_chummer_balance_preserve_spending():
    from app.chummer_export import state_to_chum5
    from app.chummer_import import chum5_to_state
    from app.models import CharacterState

    state, _, parts, mod = setup_construction()
    out = complete(state, parts, mod)
    career = apply_patch(out, CharacterPatch(career=True))
    assert career.electronic_modification_records == out.electronic_modification_records
    assert career.derived["nuyen_spent"] == out.derived["nuyen_spent"]
    data, _ = chum5_to_state(state_to_chum5(career))
    restored = compute(CharacterState(**data))
    assert restored.derived["nuyen"] == career.derived["nuyen"]
    assert sum(r["parts_remaining_units"] for r in restored.derived["gear"] if "parts_remaining_units" in r) == 4


def test_api_validates_construction_atomically_and_preserves_generated_ids():
    from starlette.testclient import TestClient

    from app.main import app

    state, deck, parts, mod = setup_construction()
    client = TestClient(app)
    record = state.electronic_modification_records[0].model_dump()
    record.update(status="completed", allocations=[{"source_id": parts.id, "units": 16}])
    body = {"state": state.model_dump(), "patch": {"electronic_modification_records": [record]}}
    response = client.post("/api/characters/patch", json=body)
    assert response.status_code == 200
    saved = response.json()
    assert saved["electronic_modification_records"][0]["id"] == record["id"]
    assert next(r for r in saved["derived"]["gear"] if r["id"] == parts.id)["parts_remaining_units"] == 4
    retry = client.post(
        "/api/characters/patch",
        json={"state": saved, "patch": {"electronic_modification_records": saved["electronic_modification_records"]}},
    )
    assert retry.status_code == 200
    assert retry.json()["derived"]["nuyen_spent"] == saved["derived"]["nuyen_spent"]
    record["allocations"][0]["units"] = 24
    refused = client.post("/api/characters/patch", json=body)
    assert refused.status_code == 400


def test_foundry_export_omits_drafts_and_exports_remaining_parts():
    from app.fvtt_export import state_to_fvtt

    state, _, parts, mod = setup_construction()
    rows = state_to_fvtt(state)["characters"]["character"]["gears"]["gear"]
    assert mod.id not in {r["guid"] for r in rows}
    saved = complete(state, parts, mod)
    rows = state_to_fvtt(saved)["characters"]["character"]["gears"]["gear"]
    assert next(r for r in rows if r["guid"] == parts.id)["qty"] == "1.0"
    assert mod.id in {r["guid"] for r in rows}


def test_sheet_exports_free_supply_remaining_and_reports_fractional_stock():
    from app.xlsx_export import state_to_xlsx
    from app.xlsx_export.check import roundtrip_differences
    from app.xlsx_import._sheet import Workbook

    state = compute(
        _mundane(
            "sheet-parts",
            electronic_parts_supplies=[
                ElectronicPartsSupply(units=8, note="salvaged"),
                ElectronicPartsSupply(units=1, note="quarter"),
            ],
        )
    )
    cells = Workbook(state_to_xlsx(state)).cells("装備")
    assert cells["E3"] == "2"
    assert cells["C3"] == "0"
    assert has(roundtrip_differences(state), "engine.export.xlsxNoPlace")


def test_add_attack_and_nested_increase_use_separate_materials():
    from app.engine.gear.electronic_modifications import ADD_ATTACK
    from app.models import CommlinkInstall

    spec = next(s for s in catalog_list("commlinks") if s.get("devicerating") == "2")
    link = CommlinkInstall(gear_id=spec["id"])
    parts = GearInstall(gear_id=FIVE_PARTS, qty=2)
    state = compute(_mundane("add-attack", commlinks=[link], gear=[parts]))
    add = GearInstall(gear_id=ADD_ATTACK, parent_id=link.id)
    state = apply_patch(state, CharacterPatch(gear=[*state.gear, add]))
    assert state.derived["gear"][-1]["material_required_units"] == 16  # DR 2 * 2 packs
    state = complete(state, parts, add)
    assert state.derived["commlinks"][0]["attack"] == 1
    increase = GearInstall(gear_id="e2c6eded-5897-4ae6-9911-230292d3f858", parent_id=add.id)
    state = apply_patch(state, CharacterPatch(gear=[*state.gear, increase]))
    second = state.electronic_modification_records[1].model_copy(
        update={"status": "completed", "allocations": [ElectronicPartsAllocation(source_id=parts.id, units=16)]}
    )
    saved = apply_patch(
        state, CharacterPatch(electronic_modification_records=[state.electronic_modification_records[0], second])
    )
    assert saved.derived["commlinks"][0]["attack"] == 2
    assert saved.electronic_modification_records[1].host_snapshot["attack"] == 1
    assert next(r for r in saved.derived["gear"] if r["id"] == parts.id)["parts_remaining_units"] == 8
