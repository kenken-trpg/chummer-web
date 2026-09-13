"""Weapons, accessories, ammo, ranges and natural / implant weapons."""

from app.data_loader import catalog
from app.engine import (
    compute,
    default_attributes,
    find_metatype,
)
from app.engine.gear import _append_natural_weapons, apply_reach_bonus
from app.improvements import collect_effects
from app.models import (
    AdeptPowerInstall,
    CharacterState,
    ContactInstall,
    CyberwareInstall,
    FocusInstall,
    GearInstall,
    LifestyleInstall,
    MartialArtInstall,
    Priorities,
    WeaponAccessoryInstall,
    WeaponInstall,
)
from tests.engine_support import (
    ARM,
    BLACK_MARKET_PIPELINE,
    CRITICAL_STRIKE,
    CUSTOM_STR,
    HAND_BLADE,
    HERMETIC,
    LOW_LIFESTYLE,
    MASTER_ARCHER,
    MISSILE_MASTERY,
    ORTHOSKIN,
    PREDATOR,
    WEAPON_FOCUS,
    _adept,
    _human,
    _karate_id,
    _mage_rich,
    _mundane,
    _optimized_arm,
    _surge_thirty,
    _ware_id,
)
from tests.notice_asserts import has


def test_missile_mastery_lands_in_a_thrown_weapons_dv() -> None:
    """`<throwstr>` is STR for a thrown weapon's `{STR}` only. The engine now
    resolves `{STR}` itself, so it has to add it there — the sheet used to."""
    knife = GearInstall(gear_id=THROWING_KNIFE_GEAR)
    plain = compute(_adept("tk", gear=[knife])).derived
    mastered = compute(
        _adept("tk-mm", gear=[knife], adept_powers=[AdeptPowerInstall(power_id=MISSILE_MASTERY)])
    ).derived

    def dv(out: dict) -> int:
        return int(str(out["weapons"][0]["damage"]).rstrip("PS"))

    assert dv(mastered) == dv(plain) + 1
    # only the throw gets it: the character's STR itself does not move
    assert mastered["totals"]["STR"] == plain["totals"]["STR"]


def test_master_archer_leaves_non_bows_weapon_alone() -> None:
    out = compute(
        _adept(
            "ma-pistol",
            adept_powers=[AdeptPowerInstall(power_id=MASTER_ARCHER)],
            weapons=[WeaponInstall(weapon_id=PREDATOR)],
        )
    )
    assert out.derived["weapons"][0].get("category_dice", 0) == 0


PENETRATING_STRIKE = "70311f5c-a019-47b9-be21-e9a8d270e32e"
SHARKSKIN = "f84dc64d-a158-45bd-b81c-0a8c98f77415"


KATANA = "8f266b4c-4035-4ba3-aa89-3289d0f42ce1"


def test_weapon_focus_requires_target_weapon() -> None:
    out = compute(
        _mage_rich(
            "wf-empty",
            tradition_id=HERMETIC,
            foci=[FocusInstall(gear_id=WEAPON_FOCUS, force=2)],
        )
    )
    row = out.derived["foci"][0]
    assert row["needs_weapon"] is True
    assert row["weapon_type"] == "Melee"
    assert row["weapon_dice"] == 2
    assert has(out.derived["warnings"], "engine.foci.weaponPick")


def test_weapon_focus_adds_dice_to_melee_weapon() -> None:
    weapon = WeaponInstall(weapon_id=KATANA)
    out = compute(
        _mage_rich(
            "wf-katana",
            tradition_id=HERMETIC,
            weapons=[weapon],
            foci=[FocusInstall(gear_id=WEAPON_FOCUS, force=2, extra=weapon.id)],
        )
    )
    focus = out.derived["foci"][0]
    assert focus["weapon_id"] == weapon.id
    assert focus["weapon_name"] == "Katana"
    assert focus["weapon_dice"] == 2
    assert any(opt["id"] == weapon.id for opt in focus["weapon_options"])
    blade = next(item for item in out.derived["weapons"] if item["id"] == weapon.id)
    assert blade["focus_dice"] == 2
    assert out.derived["errors"] == []
    assert not has(out.derived["warnings"], "engine.foci.weaponPick")


def test_weapon_focus_rejects_ranged_weapon() -> None:
    predator_id = next(item["id"] for item in catalog()["weapons"] if item["name"] == "Ares Predator V")
    weapon = WeaponInstall(weapon_id=predator_id)
    out = compute(
        _mage_rich(
            "wf-ranged",
            tradition_id=HERMETIC,
            weapons=[weapon],
            foci=[FocusInstall(gear_id=WEAPON_FOCUS, force=1, extra=weapon.id)],
        )
    )
    focus = out.derived["foci"][0]
    assert focus["weapon_id"] == ""
    assert has(out.derived["warnings"], "engine.foci.weaponTypeOnly", type="Melee")
    gun = next(item for item in out.derived["weapons"] if item["id"] == weapon.id)
    assert gun.get("focus_dice", 0) == 0


LIGHT_FIRE_70 = "67474de7-d29b-4b31-a6ae-1e2e981fa5d2"
KNIFE = "eb16de72-e646-4880-aa5b-21a5a0a2b342"
INTERNAL_SMARTGUN = "d57d2c64-1f61-4f5f-a465-8ce0dfacec6a"
SMARTLINK_WARE = "35dba0e2-1d3d-4386-a657-17fedca4622d"  # Smartlink (Eyeware) cyberware, +2
APDS = "ef9c8aae-26df-4fe6-88b3-79fbb5eb77c5"
REGULAR_AMMO = "b2a0b340-c793-4322-8422-8b03d18a6fae"
GEL_ROUNDS = "0c8d16cb-6e96-4d95-8454-104a36091cf9"
SPARE_CLIP = "75ccb148-e774-429c-b854-a27816439626"
SPEED_LOADER = "f87701a0-4ea2-47db-bcac-f5b8396c369e"
SUPER_WARHAWK = "61c59a89-3c51-46b7-880a-933b29394315"
FLASH_BANG = "f4b92e14-fe1f-4be4-ad73-aed10e1f73b4"
THROWING_KNIFE_GEAR = "d9bf2003-1911-4e65-b6a1-8babb761dd85"
ANTIOCH = "504cba24-2141-4879-8062-782332e83386"
MINI_HE = "daecdfc8-15d5-4864-9e20-13e4a0dca88e"
MINI_FLASH = "f092fca8-46a9-4351-a06a-362846e6546a"


def test_an_included_internal_smartgun_adds_nothing_to_the_predators_avail() -> None:
    """The Predator V comes with its smartgun, and its printed 5R already
    covers it: Chummer leaves `IncludedInWeapon` accessories out of the total."""
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "avail-smartgun",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=INTERNAL_SMARTGUN, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    smart = next(acc for acc in row["accessories"] if acc["name"] == "Smartgun System, Internal")
    assert smart["included"] is True
    assert smart["avail"] == "2R"
    assert smart["avail_additive"] is True
    assert row["avail"] == "5R"
    assert out.derived["errors"] == []


def test_a_retrofitted_internal_smartgun_adds_its_restricted_avail() -> None:
    """Bought on top of a weapon that lacks one, the `+2R` does count."""
    weapon = WeaponInstall(weapon_id=LIGHT_FIRE_70)
    out = compute(
        _mundane(
            "avail-retrofit",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=INTERNAL_SMARTGUN, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    assert row["avail"] == "5R"  # Light Fire 70 3R + retrofit 2R


def test_predator_purchase() -> None:
    out = compute(_mundane("predator", weapons=[WeaponInstall(weapon_id=PREDATOR, qty=1)]))
    row = out.derived["weapons"][0]
    assert row["nuyen"] == 725
    assert row["damage"] == "8P"
    assert row["ap"] == "-1"
    assert row["accuracy"] == "5"  # base 5; the included smartgun gives nothing without a smartlink
    assert any(acc["name"] == "Smartgun System, Internal" and acc["included"] for acc in row["accessories"])
    assert out.derived["errors"] == []


LASER_SIGHT = "521f9c2e-dfb2-42a6-b707-9808ae4885de"
GAS_VENT_2 = "b3827611-f631-461e-8660-e744593ba2d2"
SILENCER = "0da6149e-982f-4051-825b-52c1b79c7e52"


def test_predator_laser_sight() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-laser",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=LASER_SIGHT, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    assert row["accuracy"] == "6"  # base 5 + laser sight 1; smartgun withheld (no smartlink)
    assert row["nuyen"] == 850
    assert out.derived["nuyen_spent"] == 850
    names = {acc["name"] for acc in row["accessories"]}
    assert "Laser Sight" in names
    assert "Smartgun System, Internal" in names
    assert out.derived["errors"] == []


def test_internal_smartgun_retrofit_costs_weapon_price() -> None:
    spec = next(item for item in catalog()["weapon_accessories"] if item["id"] == INTERNAL_SMARTGUN)
    assert spec["purchasable"] is True
    assert spec["cost"] == "Weapon Cost"
    weapon = WeaponInstall(weapon_id=LIGHT_FIRE_70)
    out = compute(
        _mundane(
            "smartgun-retrofit",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=INTERNAL_SMARTGUN, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    smart = next(acc for acc in row["accessories"] if acc["name"] == "Smartgun System, Internal")
    assert smart["included"] is False
    assert smart["nuyen"] == 200
    assert row["accuracy"] == "7"  # Light Fire 70 base 7; retrofit smartgun inert without a smartlink
    assert row["nuyen"] == 400
    assert out.derived["nuyen_spent"] == 400
    assert out.derived["errors"] == []


def test_internal_smartgun_qty_scales() -> None:
    weapon = WeaponInstall(weapon_id=LIGHT_FIRE_70, qty=2)
    out = compute(
        _mundane(
            "smartgun-qty",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=INTERNAL_SMARTGUN, parent_id=weapon.id)],
        )
    )
    assert out.derived["weapons"][0]["nuyen"] == 800
    assert out.derived["nuyen_spent"] == 800


def test_internal_smartgun_forbidden_on_melee() -> None:
    weapon = WeaponInstall(weapon_id=KNIFE)
    out = compute(
        _mundane(
            "smartgun-knife",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=INTERNAL_SMARTGUN, parent_id=weapon.id)],
        )
    )
    assert out.derived["nuyen_spent"] == 10
    assert out.derived["weapons"][0]["accessories"] == []
    assert has(out.derived["warnings"], "engine.gear.doesNotFit")


def test_predator_keeps_included_internal_smartgun() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-dup-smart",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=INTERNAL_SMARTGUN, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    smarts = [acc for acc in row["accessories"] if acc["name"] == "Smartgun System, Internal"]
    assert len(smarts) == 1
    assert smarts[0]["included"] is True
    assert smarts[0]["nuyen"] == 0
    assert row["nuyen"] == 725
    assert row["accuracy"] == "5"  # duplicate smartgun still adds nothing without a smartlink


def test_smartlink_ware_activates_smartgun_accuracy() -> None:
    base = compute(_mundane("sl-none", weapons=[WeaponInstall(weapon_id=PREDATOR)]))
    assert base.derived["weapons"][0]["accuracy"] == "5"

    linked = compute(
        _mundane(
            "sl-cyber",
            weapons=[WeaponInstall(weapon_id=PREDATOR)],
            cyberware=[CyberwareInstall(ware_id=SMARTLINK_WARE)],
        )
    )
    row = linked.derived["weapons"][0]
    assert row["accuracy"] == "7"  # base 5 + smartgun 2, now that a smartlink is present
    assert linked.derived["errors"] == []


def test_smartlink_ware_without_smartgun_leaves_accuracy_alone() -> None:
    # A smartlink on its own does nothing; the Knife has no smartgun system.
    out = compute(
        _mundane(
            "sl-noweapon",
            weapons=[WeaponInstall(weapon_id=KNIFE)],
            cyberware=[CyberwareInstall(ware_id=SMARTLINK_WARE)],
        )
    )
    knife = out.derived["weapons"][0]
    base = compute(_mundane("sl-knife-base", weapons=[WeaponInstall(weapon_id=KNIFE)]))
    assert knife["accuracy"] == base.derived["weapons"][0]["accuracy"]


def test_predator_apds_changes_ap() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-apds",
            weapons=[weapon],
            gear=[GearInstall(gear_id=APDS, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    ammo = row["ammo_gear"][0]
    assert ammo["name"] == "Ammo: APDS"
    assert ammo["loaded"] is True
    assert ammo["nuyen"] == 120
    assert ammo["costfor"] == 10
    assert row["ap"] == "-5"
    assert row["damage"] == "8P"
    assert row["nuyen"] == 845
    assert out.derived["nuyen_spent"] == 845
    assert out.derived["errors"] == []


def test_predator_apds_qty_two() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-apds-2",
            weapons=[weapon],
            gear=[GearInstall(gear_id=APDS, parent_id=weapon.id, qty=2)],
        )
    )
    assert out.derived["weapons"][0]["nuyen"] == 965
    assert out.derived["nuyen_spent"] == 965


def test_predator_regular_ammo_keeps_stats() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-regular",
            weapons=[weapon],
            gear=[GearInstall(gear_id=REGULAR_AMMO, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    assert row["ap"] == "-1"
    assert row["damage"] == "8P"
    assert row["nuyen"] == 745


def test_predator_gel_rounds_stun() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-gel",
            weapons=[weapon],
            gear=[GearInstall(gear_id=GEL_ROUNDS, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    assert row["damage"] == "8S"
    assert row["ap"] == "0"
    assert row["nuyen"] == 750


def test_predator_spare_clip() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-clip",
            weapons=[weapon],
            gear=[GearInstall(gear_id=SPARE_CLIP, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    clip = row["ammo_gear"][0]
    assert clip["name"] == "Spare Clip"
    assert clip["loaded"] is False
    assert row["ap"] == "-1"
    assert row["nuyen"] == 730


def test_speed_loader_needs_cylinder() -> None:
    pistol = WeaponInstall(weapon_id=LIGHT_FIRE_70)
    revolver = WeaponInstall(weapon_id=SUPER_WARHAWK)
    rejected = compute(
        _mundane(
            "speed-clip",
            weapons=[pistol],
            gear=[GearInstall(gear_id=SPEED_LOADER, parent_id=pistol.id)],
        )
    )
    assert rejected.derived["weapons"][0]["ammo_gear"] == []
    assert has(rejected.derived["warnings"], "engine.gear.doesNotFit")
    accepted = compute(
        _mundane(
            "speed-cy",
            weapons=[revolver],
            gear=[GearInstall(gear_id=SPEED_LOADER, parent_id=revolver.id)],
        )
    )
    assert accepted.derived["weapons"][0]["ammo_gear"][0]["name"] == "Speed Loader"
    assert accepted.derived["nuyen_spent"] == 425


def test_apds_forbidden_on_melee() -> None:
    weapon = WeaponInstall(weapon_id=KNIFE)
    out = compute(
        _mundane(
            "knife-apds",
            weapons=[weapon],
            gear=[GearInstall(gear_id=APDS, parent_id=weapon.id)],
        )
    )
    assert out.derived["weapons"][0]["ammo_gear"] == []
    assert out.derived["nuyen_spent"] == 10
    assert has(out.derived["warnings"], "engine.gear.doesNotFit")


def test_predator_ammo_switch() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    apds = GearInstall(gear_id=APDS, parent_id=weapon.id)
    gel = GearInstall(gear_id=GEL_ROUNDS, parent_id=weapon.id)
    first = compute(_mundane("pred-switch", weapons=[weapon], gear=[apds, gel]))
    row = first.derived["weapons"][0]
    assert row["ap"] == "-5"
    assert row["damage"] == "8P"
    assert row["ammo_gear"][0]["loaded"] is True
    assert row["ammo_gear"][1]["loaded"] is False
    weapon.loaded_ammo_id = gel.id
    switched = compute(_mundane("pred-switch-gel", weapons=[weapon], gear=[apds, gel]))
    row = switched.derived["weapons"][0]
    assert row["damage"] == "8S"
    assert row["ap"] == "0"
    assert row["ammo_gear"][0]["loaded"] is False
    assert row["ammo_gear"][1]["loaded"] is True
    assert switched.derived["nuyen_spent"] == 870


def test_flash_bang_becomes_weapon() -> None:
    grenade = GearInstall(gear_id=FLASH_BANG, qty=2)
    out = compute(_mundane("flash-bang", gear=[grenade]))
    assert out.derived["nuyen_spent"] == 200
    assert len(out.derived["weapons"]) == 1
    row = out.derived["weapons"][0]
    assert row["name"] == "Grenade: Flash-Bang"
    assert row["from_gear"] is True
    assert row["source_gear_id"] == grenade.id
    assert row["id"] == grenade.id
    assert row["qty"] == 2
    assert row["nuyen"] == 200
    assert row["damage"].startswith("10S")
    assert row["ap"] == "-4"
    assert out.derived["gear"][0]["add_weapon"] == "Grenade: Flash-Bang"


def test_throwing_knife_gear_is_weapon() -> None:
    knife = GearInstall(gear_id=THROWING_KNIFE_GEAR)
    out = compute(_mundane("throw-knife", gear=[knife]))
    assert out.derived["nuyen_spent"] == 25
    row = out.derived["weapons"][0]
    assert row["name"] == "Throwing Knife"
    assert row["from_gear"] is True
    assert row["damage_formula"] == "({STR}+1)P"
    assert row["damage"] == f"{out.derived['totals']['STR'] + 1}P"


def test_weapon_range_table_loads_from_ranges_xml() -> None:
    table = catalog()["weapon_ranges"]
    # firearm bands are literal integers …
    assert table["Heavy Pistols"] == {
        "min": "0",
        "short": "5",
        "medium": "20",
        "long": "40",
        "extreme": "60",
    }
    # … Strength-scaled bands keep the {STR} formula for the client to resolve
    assert table["Bows"]["long"] == "{STR}*30"
    assert table["Standard Grenade"]["short"] == "{STR}*2"


def test_weapon_rows_carry_range_name() -> None:
    out = compute(_mundane("range-name", weapons=[WeaponInstall(weapon_id=PREDATOR)]))
    row = out.derived["weapons"][0]
    # no explicit <range> on the Predator — the sheet falls back to category
    assert row["range"] == "" and row["alt_range"] == ""
    assert row["category"] == "Heavy Pistols"
    assert row["category"] in catalog()["weapon_ranges"]


def test_total_recoil_compensation_folds_in_strength_and_free_point() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["STR"] = 5  # ceil(5 / 3) = 2
    out = compute(
        CharacterState(
            id="rc",
            name="RC",
            priorities=Priorities(),
            metatype="Human",
            attributes=attrs,
            weapons=[WeaponInstall(weapon_id=PREDATOR)],  # gun RC 0
        )
    )
    row = out.derived["weapons"][0]
    assert row["rc"] in ("0", "")  # the gun's own RC is untouched
    assert row["rc_total"] == 3  # 0 + ⌈5/3⌉ (2) + 1 free
    assert out.derived["recoil"] == {"str": 5, "str_rc": 2, "free": 1}


def test_melee_weapon_has_no_recoil_total() -> None:
    combat_axe = next(w["id"] for w in catalog()["weapons"] if w["name"] == "Combat Axe")
    out = compute(_mundane("rc-melee", weapons=[WeaponInstall(weapon_id=combat_axe)]))
    assert out.derived["weapons"][0]["rc_total"] == 0


def test_minigrenade_loads_into_launcher() -> None:
    launcher = WeaponInstall(weapon_id=ANTIOCH)
    he = GearInstall(gear_id=MINI_HE, parent_id=launcher.id)
    flash = GearInstall(gear_id=MINI_FLASH, parent_id=launcher.id)
    first = compute(_mundane("antioch-he", weapons=[launcher], gear=[he, flash]))
    assert first.derived["nuyen_spent"] == 3400
    assert len(first.derived["weapons"]) == 1
    row = first.derived["weapons"][0]
    assert row["name"] == "Ares Antioch-2"
    assert row["damage"] == "16P (-2/m)"
    assert row["ap"] == "-2"
    assert row["ammo_gear"][0]["loaded"] is True
    launcher.loaded_ammo_id = flash.id
    switched = compute(_mundane("antioch-flash", weapons=[launcher], gear=[he, flash]))
    row = switched.derived["weapons"][0]
    assert row["damage"] == "10S (10m Radius)"
    assert row["ap"] == "-4"
    assert row["ammo_gear"][1]["loaded"] is True
    assert switched.derived["nuyen_spent"] == 3400


def test_barrel_accessories_conflict() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "barrel-full",
            weapons=[weapon],
            weapon_accessories=[
                WeaponAccessoryInstall(accessory_id=GAS_VENT_2, parent_id=weapon.id),
                WeaponAccessoryInstall(accessory_id=SILENCER, parent_id=weapon.id),
            ],
        )
    )
    assert has(out.derived["errors"], "engine.gear.noFreeMount")


def test_hand_blade_on_cyberarm_is_weapon() -> None:
    arm = CyberwareInstall(id="arm1", ware_id=ARM)
    blade = CyberwareInstall(id="blade1", ware_id=HAND_BLADE, parent_id=arm.id)
    out = compute(_mundane("arm-blade", cyberware=[arm, blade]))
    row = next(item for item in out.derived["weapons"] if item["from_ware"])
    assert row["name"] == "Hand Blade"
    assert row["id"] == "blade1"
    assert row["source_ware_id"] == "blade1"
    assert row["weapon_id"] == "5ec246dc-c129-4e61-a27a-c4d82b223bea"
    assert row["nuyen"] == 2500
    assert row["ap"] == "-2"
    assert row["damage"] == "5P"  # empty cyberarm STR base is 3
    assert row["limb_str"] == 3
    assert out.derived["nuyen_spent"] == 17500
    assert out.derived["essence"] == 5.0
    assert out.derived["errors"] == []


def test_hand_blade_uses_customized_limb_str() -> None:
    arm = CyberwareInstall(id="arm1", ware_id=ARM)
    custom = CyberwareInstall(ware_id=CUSTOM_STR, rating=3, parent_id="arm1")
    blade = CyberwareInstall(id="blade1", ware_id=HAND_BLADE, parent_id="arm1")
    out = compute(_mundane("arm-blade-str", cyberware=[arm, custom, blade]))
    row = next(item for item in out.derived["weapons"] if item["from_ware"])
    assert row["damage"] == "5P"
    assert row["limb_str"] == 3
    arm_row = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm_row["limb_str"] == 3


def test_meat_hand_blade_uses_character_str() -> None:
    blade = CyberwareInstall(id="blade1", ware_id=HAND_BLADE)
    out = compute(_mundane("meat-blade", cyberware=[blade]))
    row = next(item for item in out.derived["weapons"] if item["from_ware"])
    assert row["damage"] == "3P"
    assert row.get("limb_str") in (None, 0)
    assert out.derived["essence"] == 5.75


def test_implant_weapon_is_hidden_from_catalog() -> None:
    hidden = next(item for item in catalog()["weapons"] if item["name"] == "Hand Blade" and item.get("from_cyberware"))
    assert hidden["hidden"] is True
    from app.catalog_view import public_catalog

    names = {item["name"] for item in public_catalog()["weapons"]}
    assert "Hand Blade" not in names
    ware = next(item for item in catalog()["cyberware"]["items"] if item["id"] == HAND_BLADE)
    assert ware["add_weapon"] == "Hand Blade"
    assert ware["add_weapon_id"] == hidden["id"]


MAGLOCK = "d0cde5ea-d524-451d-9fd6-eeccd1439293"
ANTI_TAMPER = "caa0f85d-e6f0-415a-98c7-fc4f16139964"


def test_ammo_quantity_multiplies_cost() -> None:
    out = compute(_mundane("ammo", gear=[GearInstall(gear_id=REGULAR_AMMO, qty=10)]))
    assert out.derived["gear"][0]["nuyen"] == 200
    assert out.derived["nuyen_spent"] == 200


def test_maglock_anti_tamper_attaches() -> None:
    lock = GearInstall(gear_id=MAGLOCK, rating=3)
    circuit = GearInstall(gear_id=ANTI_TAMPER, rating=2, parent_id=lock.id)
    out = compute(_mundane("lock", gear=[lock, circuit]))
    assert {row["name"] for row in out.derived["gear"]} == {"Maglock", "Anti-Tamper Circuits"}
    assert out.derived["nuyen_spent"] == 300 + 500
    assert out.derived["errors"] == []


def test_martial_art_extra_technique_and_kick_reach() -> None:
    out = compute(
        _human(
            "karate-kick",
            martial_arts=[MartialArtInstall(art_id=_karate_id(), techniques=["Counterstrike", "Kick Attack"])],
        )
    )
    row = out.derived["martial_arts"][0]
    assert row["karma"] == 12
    assert out.derived["unarmed_reach"] == 1
    assert out.derived["martial_art_points"]["techniques"] == 2
    assert out.derived["errors"] == []


def test_penetrating_strike_unarmed_ap() -> None:
    out = compute(
        _adept(
            "penetrating",
            adept_powers=[AdeptPowerInstall(power_id=PENETRATING_STRIKE, rating=2)],
        )
    )
    assert out.derived["unarmed_ap"] == -2
    assert out.derived["power_points"]["used"] == 0.5
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "unarmedap" not in tags


def test_sharkskin_unarmed_reach() -> None:
    out = compute(
        _human(
            "sharkskin",
            bioware=[
                CyberwareInstall(ware_id=ORTHOSKIN),
                CyberwareInstall(ware_id=SHARKSKIN),
            ],
        )
    )
    assert out.derived["unarmed_reach"] == 1
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "unarmedreach" not in tags


def test_troll_reach_and_lifestyle_cost() -> None:
    out = compute(
        CharacterState(
            id="troll-reach",
            name="Troll",
            priorities=Priorities(Heritage="A", Attributes="B", Talent="E", Skills="C", Resources="C"),
            metatype="Troll",
            attributes=default_attributes(find_metatype("Troll", None)),
            lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, months=1)],
        )
    )
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "reach" not in tags
    assert "lifestylecost" not in tags
    assert out.derived["reach"] == 1
    assert out.derived["unarmed_reach"] >= 1
    assert out.derived["lifestyle_cost_mod"] == 100
    assert out.derived["lifestyle"]["nuyen"] == 4000


def test_black_market_pipeline_discounts_weapons() -> None:
    weapon = next(w for w in catalog()["weapons"] if w.get("name") == "Ares Predator V")
    contact = ContactInstall(name="Fence", connection=3, loyalty=2)
    base = compute(_mundane("bmp0", weapons=[WeaponInstall(weapon_id=weapon["id"])]))
    disc = compute(
        _mundane(
            "bmp1",
            quality_ids=[BLACK_MARKET_PIPELINE],
            quality_extras={
                BLACK_MARKET_PIPELINE: "Weapons",
                f"{BLACK_MARKET_PIPELINE}:contact": contact.id,
            },
            contacts=[contact],
            weapons=[WeaponInstall(weapon_id=weapon["id"])],
        )
    )
    assert disc.derived["nuyen_spent"] == int(round(base.derived["nuyen_spent"] * 0.9))
    assert disc.derived["black_market_contact_id"] == contact.id
    assert any(c.get("black_market_pipeline") for c in disc.derived["contacts"])


def test_black_market_pipeline_lowers_weapon_avail_by_two() -> None:
    spear = next(w for w in catalog()["weapons"] if w.get("name") == "Cougar Collapsible Spear")
    contact = ContactInstall(name="Arms Dealer", connection=2, loyalty=2)
    bare = compute(_mundane("bmp-avail0", weapons=[WeaponInstall(weapon_id=spear["id"])]))
    linked = compute(
        _mundane(
            "bmp-avail1",
            quality_ids=[BLACK_MARKET_PIPELINE],
            quality_extras={
                BLACK_MARKET_PIPELINE: "Weapons",
                f"{BLACK_MARKET_PIPELINE}:contact": contact.id,
            },
            contacts=[contact],
            weapons=[WeaponInstall(weapon_id=spear["id"])],
        )
    )
    assert bare.derived["weapons"][0]["avail"] == "14R"
    assert has(bare.derived["errors"], "engine.gear.availOver")
    assert linked.derived["weapons"][0]["avail_base"] == 14
    assert linked.derived["weapons"][0]["avail"] == "12R"
    assert linked.derived["weapons"][0].get("black_market_avail") is True
    assert linked.derived["black_market_avail_bonus"] == 2
    assert not has(linked.derived["errors"], "engine.gear.availOver")


DEATH_DEALER_ADEPT = "cfc637e9-0071-4313-a25b-b411793f2321"


PRACTICE_PRACTICE_PRACTICE = "81fc0829-3456-4701-8ecc-f101d145b538"
KRIME_CALLIOPE = "7fffffff-e125-44fb-8977-7fffffffc59c"


def test_practice_practice_practice_weapon_skill_accuracy() -> None:
    missing = compute(_human("ppp-empty", quality_ids=[PRACTICE_PRACTICE_PRACTICE]))
    assert has(missing.derived["warnings"], "engine.skills.pickSkill")
    base = compute(
        _human(
            "ppp-base",
            weapons=[WeaponInstall(weapon_id=KRIME_CALLIOPE)],
        )
    )
    out = compute(
        _human(
            "ppp",
            quality_ids=[PRACTICE_PRACTICE_PRACTICE],
            quality_extras={PRACTICE_PRACTICE_PRACTICE: "Gunnery"},
            weapons=[WeaponInstall(weapon_id=KRIME_CALLIOPE)],
        )
    )
    base_weapon = base.derived["weapons"][0]
    weapon = out.derived["weapons"][0]
    assert base_weapon["accuracy"] == "4"
    assert weapon["accuracy"] == "5"
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "weaponskillaccuracy" not in tags


def test_death_dealer_adept_weapon_dv_and_skill_select() -> None:
    missing = compute(
        _adept(
            "dda-empty",
            quality_ids=[DEATH_DEALER_ADEPT],
            adept_powers=[AdeptPowerInstall(power_id=CRITICAL_STRIKE)],
            weapons=[WeaponInstall(weapon_id=KATANA)],
        )
    )
    assert has(missing.derived["errors"], "engine.qualities.pickWeaponSkill")
    out = compute(
        _adept(
            "dda-blades",
            quality_ids=[DEATH_DEALER_ADEPT],
            quality_extras={DEATH_DEALER_ADEPT: "Blades"},
            adept_powers=[AdeptPowerInstall(power_id=CRITICAL_STRIKE)],
            weapons=[WeaponInstall(weapon_id=KATANA)],
        )
    )
    katana = next(w for w in out.derived["weapons"] if w["name"] == "Katana")
    assert katana["damage_formula"] == "({STR}+4)P"
    assert katana["damage"] == "5P"  # STR 1
    assert "weaponcategorydv" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


SPECIAL_MODIFICATIONS = "0dd183a3-85ce-4029-9de5-9b6aa1eb539c"
SM_IMPROVED_AP = "b741b729-106e-46f2-9143-0f745fd48789"
SM_DAMAGE = "3c82e17b-76cd-47b9-9bda-c3131a64e0ee"
SM_AMMO_CAP = "9084d801-c654-4eec-960e-4186a6de81d6"


def test_special_modifications_grants_limit() -> None:
    out = compute(_mundane("sm-limit", quality_ids=[SPECIAL_MODIFICATIONS]))
    assert out.derived["special_modification_limit"] == {"used": 0, "max": 2}
    assert "specialmodificationlimit" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_special_modifications_stacks_twice() -> None:
    out = compute(_mundane("sm-x2", quality_ids=[SPECIAL_MODIFICATIONS, SPECIAL_MODIFICATIONS]))
    assert out.derived["special_modification_limit"]["max"] == 4
    assert len([q for q in out.derived["qualities"] if q["id"] == SPECIAL_MODIFICATIONS]) == 2
    assert out.derived["karma"]["spent"] == 10


def test_special_modification_improved_ap() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "sm-ap",
            quality_ids=[SPECIAL_MODIFICATIONS],
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=SM_IMPROVED_AP, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    assert row["ap"] == "-2"
    assert out.derived["special_modification_limit"] == {"used": 1, "max": 2}
    assert any(acc["name"] == "Special Modification: Improved AP" for acc in row["accessories"])
    assert out.derived["errors"] == []


def test_special_modification_requires_quality() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "sm-noq",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=SM_IMPROVED_AP, parent_id=weapon.id)],
        )
    )
    assert not any(acc["name"].startswith("Special Modification:") for acc in out.derived["weapons"][0]["accessories"])
    assert has(out.derived["warnings"], "engine.gear.needsSpecialMods")


def test_special_modification_damage_costs_two() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "sm-dmg",
            quality_ids=[SPECIAL_MODIFICATIONS],
            weapons=[weapon],
            weapon_accessories=[
                WeaponAccessoryInstall(accessory_id=SM_DAMAGE, parent_id=weapon.id),
                WeaponAccessoryInstall(accessory_id=SM_IMPROVED_AP, parent_id=weapon.id),
            ],
        )
    )
    row = out.derived["weapons"][0]
    assert row["damage"] == "9P"
    assert not any(acc["name"] == "Special Modification: Improved AP" for acc in row["accessories"])
    assert out.derived["special_modification_limit"] == {"used": 2, "max": 2}
    assert has(out.derived["warnings"], "engine.gear.specialModsOver")


def test_special_modification_ammo_capacity() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "sm-ammo",
            quality_ids=[SPECIAL_MODIFICATIONS],
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=SM_AMMO_CAP, parent_id=weapon.id)],
        )
    )
    assert out.derived["weapons"][0]["ammo"] == "23(c)"


def test_the_negative_karma_limit_does_not_clip_a_changelings_metagenic_qualities() -> None:
    """`exceednegativequalitiesnobonus` withholds karma past the negative 25 —
    counted the same way, so a Changeling's metagenic 30 keeps all of it."""
    state = _surge_thirty("mg-nobonus")
    state.settings.exceed_negative_qualities = True
    state.settings.exceed_negative_qualities_no_bonus = True
    out = compute(state)
    assert not has(out.derived["warnings"], "engine.qualities.negativeNoBonus")


def _shapeshifter_natural_weapon_nodes() -> tuple[str, list[dict[str, object]]]:
    """The Ursine shifter's bite and claws, straight out of `metatypes.xml`.

    Every `<naturalweapon>` in the catalog sits on a Shapeshifter metavariant,
    and `catalog()["metatypes"]` offers only the five core metatypes — so the
    grant is reached here through `all_metatypes`, the way it would reach the
    engine if a Shapeshifter were ever selectable.
    """
    base = catalog()["all_metatypes"]["Shapeshifter: Ursine"]
    variant = next(mv for mv in base["metavariants"] if mv["name"] == "Human")
    return base["name"], list(variant["bonus"])


def test_natural_weapon_nodes_become_weapon_rows() -> None:
    source, nodes = _shapeshifter_natural_weapon_nodes()
    effects = collect_effects([(source, nodes)])
    assert [row["name"] for row in effects["natural_weapons"]] == ["Bite (Ursine Form)", "Claws"]
    assert not [row for row in effects["unimplemented"] if row["tag"] == "naturalweapon"]

    weapons: list[dict[str, object]] = []
    _append_natural_weapons(weapons, effects)
    bite, claws = weapons
    assert (bite["name"], bite["damage"], bite["ap"], bite["reach"]) == (
        "Bite (Ursine Form)",
        "({STR}+2)P",
        "-2",
        "0",
    )
    assert (claws["damage"], claws["ap"], claws["reach"]) == ("({STR}+3)P", "-1", "1")
    # Melee, Unarmed Combat, free, and not something the player bought: the row
    # has no catalog weapon behind it and never enters `state.weapons`, so the
    # `.chum5` export cannot write it back out as a purchase.
    assert bite["type"] == "Melee"
    assert bite["useskill"] == "Unarmed Combat"
    assert (bite["nuyen"], bite["qty"], bite["weapon_id"]) == (0, 1, "")
    assert bite["natural"] is True
    assert bite["natural_source"] == "Shapeshifter: Ursine"


def test_natural_weapons_take_the_unarmed_reach_bonus() -> None:
    """A natural weapon is an Unarmed Combat attack, so Reach from a quality
    lands on it like it lands on any other melee weapon."""
    source, nodes = _shapeshifter_natural_weapon_nodes()
    effects = collect_effects([(source, nodes)])
    weapons: list[dict[str, object]] = []
    _append_natural_weapons(weapons, effects)
    apply_reach_bonus(weapons, 1)
    assert [w["reach"] for w in weapons] == ["1", "2"]


BIOWARE_CLAWS = "dfd48ff5-3ecf-47b4-81fd-62b1ff3f74e4"
RAZOR_CLAWS = "72a6fe4e-056d-4f04-872d-d911f2e66946"


def test_quality_addweapon_grows_a_natural_weapon() -> None:
    """Razor Claws is a quality that is also a weapon (RF p.104).

    The row is `natural` like a metatype's own attack: free, no accessories,
    and named after the quality that grew it.
    """
    out = compute(_mundane("claws-quality", quality_ids=[RAZOR_CLAWS]))
    row = next(w for w in out.derived["weapons"] if w["name"] == "Razor Claws")
    assert (row["damage"], row["ap"]) == ("2P", "-1")  # STR 1
    assert row["damage_formula"] == "({STR}+1)P"
    assert (row["nuyen"], row["qty"]) == (0, 1)
    assert row["natural"] is True
    assert row["natural_source"] == "Razor Claws"
    # The quality's karma is the whole price: growing claws costs no nuyen.
    assert out.derived["nuyen_spent"] == 0


def test_bioware_claws_become_a_weapon_row() -> None:
    """Bioware claws are `<addweapon>` implants like a cyberspur (CF p.72), and
    the row says which tab to delete them from."""
    out = compute(_mundane("claws-bio", bioware=[CyberwareInstall(ware_id=BIOWARE_CLAWS)]))
    row = next(w for w in out.derived["weapons"] if w["name"].startswith("Claws"))
    # An implant weapon resolves STR from the body it is in, so no placeholder
    # is left for the client: STR 1 claws do 2P.
    assert (row["damage"], row["ap"]) == ("2P", "-3")
    assert row["from_ware"] is True
    assert row["ware_kind"] == "bioware"


def test_granted_weapons_are_loaded_but_never_for_sale() -> None:
    """Claws, fangs and shield bashes have to be in `catalog()["weapons"]` for
    the rows above to find a spec — and out of the shop, so nobody buys a pair
    of fangs off the weapons tab."""
    from app.catalog_view import public_catalog

    granted = {"Razor Claws", "Fangs", "Ballistic Shield", "Claws (Bio-Weapon)"}
    specs = {item["name"] for item in catalog()["weapons"]}
    assert granted <= specs
    assert granted.isdisjoint({item["name"] for item in public_catalog()["weapons"]})
    # Every `<addweapon>` in the catalog now resolves to one of those specs.
    sources: list[dict[str, object]] = [
        *catalog()["armor"],
        *catalog()["qualities"],
        *catalog()["gear"],
        *catalog()["cyberware"]["items"],
        *catalog()["bioware"]["items"],
    ]
    assert [i["name"] for i in sources if i.get("add_weapon") and not i.get("add_weapon_id")] == []


def test_cyberlimb_optimization_adds_accuracy_to_the_picked_skill() -> None:
    out = compute(_optimized_arm(skill_picks={"ware:opt:acc0": "Pistols"})).derived
    assert out["skill_pick_slots"][0]["picked"] == "Pistols"
    assert out["weapons"][0]["accuracy"] == "6"
    assert out["skill_bonus"].get("Pistols", 0) == 0
    assert not any(w["key"] == "engine.skills.pickSkill" for w in out["warnings"])

    other = compute(_optimized_arm(skill_picks={"ware:opt:acc0": "Longarms"})).derived
    assert other["weapons"][0]["accuracy"] == "5"


def test_a_limit_accuracy_reads_as_the_number_rolled_against() -> None:
    """`Physical` (SR5 p.169) becomes the character's Physical limit once it
    is known; the formula stays beside it."""
    blade = _ware_id("cyberware", "Hand Blade")
    out = compute(_human("blade", cyberware=[CyberwareInstall(ware_id=blade)])).derived
    weapon = next(w for w in out["weapons"] if w["name"] == "Hand Blade")
    assert weapon["accuracy_formula"] == "Physical"
    assert weapon["accuracy"] == str(out["limits"]["physical"])


def test_add_accuracy_keeps_a_limit_a_word() -> None:
    from app.engine.formulas import _add_accuracy

    assert _add_accuracy("5", 1) == "6"
    assert _add_accuracy("Physical-1", 1) == "Physical"
    assert _add_accuracy("Physical", 2) == "Physical+2"
    assert _add_accuracy("Physical+1", -2) == "Physical-1"
    assert _add_accuracy("Physical", 0) == "Physical"


def test_osmium_mace_reads_its_strength_thresholds() -> None:
    """`number({STR} >= 5)` (Osmium Mace, TCT p.185): +1 Accuracy and +2 DV
    at STR 5, again at STR 7 — now a number, not the formula."""
    mace = next(w["id"] for w in catalog()["weapons"] if w["name"] == "Osmium Mace")

    def at(strength: int) -> tuple[str, str]:
        attrs = default_attributes(find_metatype("Human", None))
        attrs["STR"] = strength
        ch = _human("mace", weapons=[WeaponInstall(weapon_id=mace)], career=True)
        ch.attributes = attrs
        row = compute(ch).derived["weapons"][0]
        return str(row["accuracy"]), str(row["damage"])

    assert at(4) == ("3", "6P")
    assert at(5) == ("4", "9P")
    assert at(6) == ("4", "10P")  # a human stops at 6; the STR 7 step is below


def test_eval_attr_stat_handles_number_tests() -> None:
    from app.engine.formulas import _eval_attr_stat

    assert _eval_attr_stat("3+number({STR} >= 5)", {"STR": 5}) == "4"
    assert _eval_attr_stat("3+number({STR} >= 5)", {"STR": 4}) == "3"
    assert _eval_attr_stat("3+number({STR} >= 5)+number({STR} >= 7)", {"STR": 7}) == "5"
    assert _eval_attr_stat("({STR}+2+(2*number({STR} >= 5))+(2*number({STR} >= 7)))P", {"STR": 7}) == "13P"
    assert _eval_attr_stat("({STR}+5)P", {"STR": 3}) == "8P"
    # a signed number is not a sum
    assert _eval_attr_stat("+1", {"STR": 3}) == "+1"


def test_a_ware_weapon_keeps_its_formula_too() -> None:
    """A Hand Blade's `({STR}+2)P` is resolved against the limb in rows.py;
    the sheet shows the formula on hover for it as for a hand-held blade."""
    blade = _ware_id("cyberware", "Hand Blade")
    out = compute(_human("blade", cyberware=[CyberwareInstall(ware_id=blade)])).derived
    weapon = next(w for w in out["weapons"] if w["name"] == "Hand Blade")
    assert weapon["damage_formula"] == "({STR}+2)P"
    assert weapon["damage"] == f"{out['totals']['STR'] + 2}P"


def test_elemental_body_grows_a_weapon_that_scales_with_magic() -> None:
    """Elemental Body (SG p.170) is a power whose `<addweapon>` sits in its
    bonus; the weapon is hidden in `weapons.xml`, so the power is the only way
    in. DV `({MAG}*2)P` and AP `-{MAG}*0.5` resolve against the adept's Magic."""
    power = next(p["id"] for p in catalog()["powers"] if p["name"] == "Elemental Body")
    out = compute(_adept("elemental", adept_powers=[AdeptPowerInstall(power_id=power)])).derived
    mag = int(out["totals"]["MAG"])
    weapon = next(w for w in out["weapons"] if w["name"] == "Elemental Body")
    assert weapon["natural"] is True
    assert weapon["damage_formula"] == "({MAG}*2)P"
    assert weapon["damage"] == f"{mag * 2}P"
    assert weapon["ap"] == str(int(-mag * 0.5))
    assert out["unimplemented_bonuses"] == []

    bare = compute(_adept("no-power")).derived
    assert not any(w["name"] == "Elemental Body" for w in bare["weapons"])


def test_what_a_weapon_comes_with_sits_on_its_internal_mount() -> None:
    """Chummer puts an included accessory on the weapon's "Internal" mount
    unless the weapon's entry names a `<mount>` for it — the Ingram's
    built-in gas vent (a barrel accessory) leaves the barrel to an Electronic
    Firing."""
    ingram = next(row for row in catalog()["weapons"] if row["name"] == "Ingram Smartgun X")
    firing = next(row for row in catalog()["weapon_accessories"] if row["name"] == "Electronic Firing")
    weapon = WeaponInstall(weapon_id=ingram["id"])
    out = compute(
        _mundane(
            "ingram",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=firing["id"], parent_id=weapon.id)],
        )
    )
    mounts = {acc["name"]: acc["mount"] for acc in out.derived["weapons"][0]["accessories"]}
    assert mounts["Gas-Vent 2 System"] == "Internal"
    assert mounts["Electronic Firing"] == "Barrel"
    assert not has(out.derived["errors"], "engine.gear.noFreeMount")
