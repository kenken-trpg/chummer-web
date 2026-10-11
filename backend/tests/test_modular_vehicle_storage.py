"""Vehicle-mounted modular ware keeps contents without supplying personal effects."""

from copy import deepcopy

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.models import CharacterState, CyberwareInstall, GearInstall, VehicleModInstall, WeaponAccessoryInstall
from tests.engine_support import _ware_id
from tests.notice_asserts import has
from tests.test_centaur_grants import _centaur
from tests.test_engine_vehicles import DOBERMAN, DRONE_ARM


def _id(bucket: str, name: str) -> str:
    return next(r["id"] for r in catalog()[bucket] if r["name"] == name)


def _state() -> CharacterState:
    return compute(
        _centaur(
            drones=[GearInstall(id="drone", gear_id=DOBERMAN)],
            vehicle_mods=[VehicleModInstall(id="drone-arm", mod_id=DRONE_ARM, parent_id="drone")],
            cyberware=[
                CyberwareInstall(id="arm", ware_id=_ware_id("cyberware", "Obvious Full Arm"), side="Left"),
                CyberwareInstall(
                    id="body-mount",
                    ware_id=_ware_id("cyberware", "Modular Connector, Wrist"),
                    parent_id="arm",
                    side="Left",
                ),
                CyberwareInstall(
                    id="vehicle-mount",
                    ware_id=_ware_id("cyberware", "Modular Connector, Wrist"),
                    parent_id="drone-arm",
                    side="Left",
                ),
                CyberwareInstall(
                    id="hand",
                    ware_id=_ware_id("cyberware", "Obvious Hand, Modular"),
                    parent_id="body-mount",
                    side="Left",
                ),
                CyberwareInstall(id="blade", ware_id=_ware_id("cyberware", "Hand Blade"), parent_id="hand"),
                CyberwareInstall(id="wires", ware_id=_ware_id("cyberware", "Skillwires"), rating=4),
                CyberwareInstall(id="jack", ware_id=_ware_id("cyberware", "Skilljack"), rating=4),
            ],
            weapon_accessories=[
                WeaponAccessoryInstall(
                    id="grip", accessory_id=_id("weapon_accessories", "Personalized Grip"), parent_id="blade"
                )
            ],
            # Deliberately saved out of parent order, with two nested containers.
            gear=[
                GearInstall(id="mask", gear_id=_id("gear", "Respirator"), parent_id="inner", rating=4, equipped=True),
                GearInstall(id="soft", gear_id=_id("gear", "Activesoft"), parent_id="inner", rating=4, extra="Archery"),
                GearInstall(id="inner", gear_id=_id("gear", "Custom Item"), parent_id="box"),
                GearInstall(id="box", gear_id=_id("gear", "Custom Item"), parent_id="hand", cost=25),
                GearInstall(id="ordinary", gear_id=_id("gear", "Respirator"), rating=1),
            ],
        )
    )


def _move(state: CharacterState, parent_id: str | None) -> CharacterState:
    next(r for r in state.cyberware if r.id == "hand").parent_id = parent_id
    return compute(state)


def test_move_to_vehicle_separates_personal_effects_from_connection_and_ownership() -> None:
    state = _state()
    assert state.derived["skillsoft"]["Archery"] == 4
    original = deepcopy(state.derived)
    gear = [r.model_dump() for r in state.gear]
    accessories = [r.model_dump() for r in state.weapon_accessories]
    _move(state, "vehicle-mount")
    assert state.derived["skillsoft"].get("Archery", 0) == 0
    assert state.derived["special_armor"]["toxin_inhalation"] == 1
    assert original["special_armor"]["toxin_inhalation"] > 1
    assert state.derived["nuyen_spent"] == original["nuyen_spent"]
    for row in state.derived["gear"]:
        if row["id"] == "ordinary":
            assert "vehicle_hosted" not in row and "modular_equipped" not in row
        else:
            assert row["vehicle_hosted"] is True
            assert row["modular_equipped"] is True
    hand = next(r for r in state.derived["cyberware"] if r["id"] == "hand")
    assert hand["modular_equipped"] is True and hand["essence"] == 0
    assert not has(state.derived["errors"], "engine.ware.modularMountMismatch")
    assert [r.model_dump() for r in state.gear] == gear
    assert [r.model_dump() for r in state.weapon_accessories] == accessories
    assert next(r for r in state.derived["weapons"] if r["id"] == "blade")["accessories"]
    _move(state, "body-mount")
    for key in ("gear", "skillsoft", "special_armor", "essence", "nuyen_spent", "body_limb_slots"):
        assert state.derived[key] == original[key]


def test_detach_from_vehicle_then_reconnect_to_body_restores_effects() -> None:
    state = _move(_state(), "vehicle-mount")
    cost = state.derived["nuyen_spent"]
    _move(state, None)
    for row in state.derived["gear"]:
        assert "vehicle_hosted" not in row
        if row["id"] != "ordinary":
            assert row["modular_equipped"] is False
    assert state.derived["skillsoft"].get("Archery", 0) == 0
    assert state.derived["special_armor"]["toxin_inhalation"] == 1
    _move(state, "body-mount")
    assert state.derived["skillsoft"]["Archery"] == 4
    assert state.derived["special_armor"]["toxin_inhalation"] > 1
    assert state.derived["nuyen_spent"] == cost


def test_vehicle_subtree_survives_json_and_two_chum5_roundtrips() -> None:
    state = _move(_state(), "vehicle-mount")
    cost = state.derived["nuyen_spent"]
    for _ in range(2):
        state = compute(CharacterState.model_validate_json(state.model_dump_json()))
        raw, warnings = chum5_to_state(state_to_chum5(state))
        assert not warnings
        state = compute(CharacterState.model_validate(raw))
        assert len(state.gear) == 5
        assert len(state.weapon_accessories) == 1
        assert state.derived["nuyen_spent"] == cost
        assert state.derived["skillsoft"].get("Archery", 0) == 0
        assert state.derived["special_armor"]["toxin_inhalation"] == 1
        hand = next(r for r in state.cyberware if r.ware_id == _ware_id("cyberware", "Obvious Hand, Modular"))
        connector = next(r for r in state.cyberware if r.id == hand.parent_id)
        assert connector.parent_id == state.vehicle_mods[0].id
        blade = next(r for r in state.derived["weapons"] if r.get("from_ware"))
        assert blade["vehicle_id"] == state.drones[0].id
        assert all(r.get("vehicle_hosted") for r in state.derived["gear"] if r.get("modular_equipped") is True)
    body_mount = next(r for r in state.cyberware if r.ware_id == connector.ware_id and r.id != connector.id)
    hand.parent_id = body_mount.id
    compute(state)
    assert state.derived["skillsoft"]["Archery"] == 4
    assert all("vehicle_hosted" not in r for r in state.derived["gear"])


def test_vehicle_connection_still_reports_grade_and_occupancy_errors() -> None:
    state = _state()
    next(r for r in state.cyberware if r.id == "vehicle-mount").grade = "Alphaware"
    state.cyberware.append(
        CyberwareInstall(
            id="other-hand",
            ware_id=_ware_id("cyberware", "Obvious Hand, Modular"),
            parent_id="vehicle-mount",
            side="Left",
        )
    )
    _move(state, "vehicle-mount")
    assert has(state.derived["errors"], "engine.ware.modularGradeMismatch")
    assert has(state.derived["errors"], "engine.ware.modularMountOccupied")
    assert len(state.gear) == 5


def test_implanted_weapon_and_held_gear_export_with_the_vehicle_and_return_to_character() -> None:
    from app.fvtt_export import state_to_fvtt

    state = _state()
    for parent_id, hosted in [("vehicle-mount", True), ("body-mount", False), ("vehicle-mount", True)]:
        _move(state, parent_id)
        blade = next(r for r in state.derived["weapons"] if r["id"] == "blade")
        assert blade.get("vehicle_id") == ("drone" if hosted else None)
        assert "mounted_on" not in blade
        export = state_to_fvtt(state, "en")["characters"]["character"]
        personal = export["weapons"]["weapon"] or []
        vehicle = export["vehicles"]["vehicle"][0]
        vehicle_weapons = vehicle["weapons"]["weapon"] or []
        assert any(r["guid"] == "blade" for r in personal) is not hosted
        assert any(r["guid"] == "blade" for r in vehicle_weapons) is hosted
        personal_gear = export["gears"]["gear"] or []
        vehicle_gear = vehicle["gears"]["gear"] or []
        assert any(r["guid"] == "mask" for r in personal_gear) is not hosted
        assert any(r["guid"] == "mask" for r in vehicle_gear) is hosted


def test_vehicle_mount_cannot_take_a_weapon_owned_by_an_implant() -> None:
    from app.models import WeaponMountInstall
    from tests.engine_support import HEAVY_SR5_MOUNT

    state = _move(_state(), "vehicle-mount")
    state.drones.append(GearInstall(id="other-drone", gear_id=DOBERMAN))
    state.weapon_mounts.append(
        WeaponMountInstall(id="mount", parent_id="other-drone", size_id=HEAVY_SR5_MOUNT, weapon_install_id="blade")
    )
    compute(state)
    assert state.weapon_mounts[0].weapon_install_id is None
    blade = next(r for r in state.derived["weapons"] if r["id"] == "blade")
    assert blade["vehicle_id"] == "drone"
    assert "mounted_on" not in blade
    assert has(state.derived["warnings"], "engine.gear.weaponMountEmpty")
