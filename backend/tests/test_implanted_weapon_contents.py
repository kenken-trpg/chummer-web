"""Accessories and ammo belong to an implant even while its limb is detached."""

import xml.etree.ElementTree as ET
from copy import deepcopy

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.models import CharacterState, CyberwareInstall, GearInstall, WeaponAccessoryInstall, WeaponInstall
from tests.engine_support import _ware_id
from tests.test_centaur_grants import _centaur
from tests.test_centaur_modular_limbs import _connectors


def _id(bucket: str, name: str) -> str:
    return next(row["id"] for row in catalog()[bucket] if row["name"] == name)


def _state() -> CharacterState:
    ware = _connectors()
    ware.extend(
        [
            CyberwareInstall(
                id="gun", ware_id=_ware_id("cyberware", "Heavy Pistol"), parent_id="leg-0", loaded_ammo_id="apds"
            ),
            CyberwareInstall(id="other-gun", ware_id=_ware_id("cyberware", "Heavy Pistol"), parent_id="leg-1"),
        ]
    )
    return compute(
        _centaur(
            cyberware=ware,
            weapon_accessories=[
                WeaponAccessoryInstall(
                    id="grip", accessory_id=_id("weapon_accessories", "Personalized Grip"), parent_id="gun"
                )
            ],
            gear=[
                GearInstall(id="regular", gear_id=_id("gear", "Ammo: Regular Ammo"), parent_id="gun", qty=3),
                GearInstall(id="apds", gear_id=_id("gear", "Ammo: APDS"), parent_id="gun", qty=2),
            ],
        )
    )


def _gun(state: CharacterState, inst_id: str = "gun") -> dict:
    return next(row for row in state.derived["weapons"] if row["id"] == inst_id)


def test_contents_keep_host_cost_and_stats_when_detached() -> None:
    state = _state()
    gun = _gun(state)
    assert {r["name"] for r in gun["accessories"]} == {"Personalized Grip", "Smartgun System, Internal"}
    assert next(r for r in gun["accessories"] if r["included"])["nuyen"] == 0
    assert gun["loaded_ammo_id"] == "apds"
    assert gun["ap"] != gun["ap_noammo"]
    assert len(gun["ammo_gear"]) == 2
    assert len(_gun(state, "other-gun")["accessories"]) == 1
    assert not _gun(state, "other-gun")["ammo_gear"]
    original = deepcopy(gun)
    cost = state.derived["nuyen_spent"]
    owned = [row.model_dump() for row in state.gear + state.weapon_accessories]
    for connected in (False, False, True):
        next(r for r in state.cyberware if r.id == "leg-0").parent_id = "hip-0" if connected else None
        compute(state)
        current = _gun(state)
        assert current["modular_equipped"] is connected
        assert current["loaded_ammo_id"] == "apds"
        assert current["accessories"] == original["accessories"]
        for key in ("damage", "ap", "accuracy", "nuyen"):
            assert current[key] == original[key]
        assert state.derived["nuyen_spent"] == cost
        assert [row.model_dump() for row in state.gear + state.weapon_accessories] == owned


def test_detached_contents_survive_json_and_two_chum5_roundtrips_and_reconnect() -> None:
    state = _state()
    next(r for r in state.cyberware if r.id == "leg-0").parent_id = None
    compute(state)
    cost = state.derived["nuyen_spent"]
    for _ in range(2):
        state = compute(CharacterState.model_validate_json(state.model_dump_json()))
        xml = state_to_chum5(state)
        root = ET.fromstring(xml)
        generated = root.findall("./weapons/weapon[cyberware='True']")
        assert len(generated) == 2
        assert len({w.findtext("guid") for w in generated}) == 2
        for node in generated:
            owner = next(w for w in root.findall(".//cyberware") if w.findtext("guid") == node.findtext("parentid"))
            assert owner.findtext("weaponguid") == node.findtext("guid")
        raw, warnings = chum5_to_state(xml)
        assert not warnings
        state = compute(CharacterState.model_validate(raw))
        assert not state.weapons
        assert len(state.gear) == 2
        assert len(state.weapon_accessories) == 3
        gun = next(r for r in state.derived["weapons"] if len(r["accessories"]) == 2)
        assert gun["modular_equipped"] is False
        ammo = next(r for r in gun["ammo_gear"] if r["name"] == "Ammo: APDS")
        assert ammo["loaded"] and gun["loaded_ammo_id"] == ammo["id"]
        assert sorted(r["qty"] for r in gun["ammo_gear"]) == [2, 3]
        assert all(r.parent_id == gun["id"] for r in state.gear)
        assert state.derived["nuyen_spent"] == cost
    implant = next(r for r in state.cyberware if r.id == gun["id"])
    leg = next(r for r in state.cyberware if r.id == implant.parent_id)
    hip = next(
        r for r in state.derived["cyberware"] if r["name"] == "Modular Connector, Hip" and r.get("limb_agi") == 0
    )
    leg.parent_id = hip["id"]
    compute(state)
    assert _gun(state, implant.id)["modular_equipped"] is True
    assert state.derived["nuyen_spent"] == cost


def test_missing_owner_and_incompatible_ammo_are_still_rejected() -> None:
    state = _state()
    state.gear.append(GearInstall(id="bad", gear_id=_id("gear", "Respirator"), parent_id="gun"))
    compute(state)
    assert not any(r.id == "bad" for r in state.gear)
    state.cyberware = [r for r in state.cyberware if r.id != "gun"]
    compute(state)
    assert not state.gear
    assert all(r.parent_id != "gun" for r in state.weapon_accessories)


@pytest.mark.parametrize("guid_only", [False, True])
def test_import_matches_by_parent_or_weapon_guid(guid_only: bool) -> None:
    root = ET.fromstring(state_to_chum5(_state()))
    for node in root.findall("./weapons/weapon[cyberware='True']"):
        node.find("parentid" if guid_only else "guid").text = ""  # type: ignore[union-attr]
    raw, warnings = chum5_to_state(ET.tostring(root))
    assert not warnings
    state = compute(CharacterState.model_validate(raw))
    assert not state.weapons
    assert len(state.weapon_accessories) == 3
    assert len(state.gear) == 2


def test_purchased_weapon_ammo_selection_also_survives_chum5() -> None:
    state = compute(
        _centaur(
            weapons=[WeaponInstall(id="pistol", weapon_id=_id("weapons", "Ares Predator V"), loaded_ammo_id="apds")],
            gear=[
                GearInstall(id="regular", gear_id=_id("gear", "Ammo: Regular Ammo"), parent_id="pistol"),
                GearInstall(id="apds", gear_id=_id("gear", "Ammo: APDS"), parent_id="pistol"),
            ],
        )
    )
    cost = state.derived["nuyen_spent"]
    raw, warnings = chum5_to_state(state_to_chum5(state))
    assert not warnings
    restored = compute(CharacterState.model_validate(raw))
    gun = _gun(restored, restored.weapons[0].id)
    assert next(r for r in gun["ammo_gear"] if r["loaded"])["name"] == "Ammo: APDS"
    assert restored.derived["nuyen_spent"] == cost
