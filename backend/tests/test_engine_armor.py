"""Armor, armor mods, stacking and encumbrance."""

from app.data_loader import catalog
from app.engine import (
    compute,
    default_attributes,
    find_metatype,
)
from app.models import (
    ArmorInstall,
    ArmorModInstall,
    CharacterState,
    CyberwareInstall,
    GearInstall,
    Priorities,
)
from tests.engine_support import (
    ARM,
    ARMOR_JACKET,
    EYES,
    HERMETIC,
    HOLY_TEXT,
    HOLY_TEXT_POWER_CHOICE,
    MENTOR_SPIRIT,
    ORTHOSKIN,
    _adept,
    _armor_mod_named,
    _human,
    _mage,
    _mundane,
)
from tests.notice_asserts import has

LIMB_ARMOR = "8ea736c6-5a90-471c-9320-18432ec9aaf0"
OCULAR_DRONE = "fde2bfc3-c7a2-435e-a220-4896f49d8ca9"


def test_limb_armor_uses_arm_capacity() -> None:
    state = CharacterState(
        id="arm",
        name="Arm",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM),
            CyberwareInstall(ware_id=LIMB_ARMOR, rating=2, parent_id="arm1"),
        ],
    )
    out = compute(state)
    assert out.derived["essence"] == 5.0
    assert out.derived["armor"] == 2
    assert out.derived["nuyen_spent"] == 21000
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["capacity_used"] == 2
    assert arm["capacity_max"] == 15
    assert out.derived["condition_monitor"]["physical"] == 10


def test_capacity_overflow_is_reported() -> None:
    state = CharacterState(
        id="overflow",
        name="Overflow",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[
            CyberwareInstall(id="eyes1", ware_id=EYES, rating=1),
            CyberwareInstall(ware_id=OCULAR_DRONE, parent_id="eyes1"),
        ],
    )
    out = compute(state)
    assert has(out.derived["errors"], "engine.ware.capacityOver")


def test_orthoskin_adds_armor_and_essence() -> None:
    state = CharacterState(
        id="ortho",
        name="Ortho",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[CyberwareInstall(ware_id=ORTHOSKIN, rating=2)],
    )
    out = compute(state)
    assert out.derived["essence"] == 5.5
    assert out.derived["armor"] == 2
    assert out.derived["nuyen_spent"] == 12000
    assert out.derived["essence_lost_bio"] == 0.5


MYSTIC_ARMOR = "da5f9389-a5fd-48ed-8825-8852ff5c56a8"


def test_holy_text_mentor_selectpowers_grants_mystic_armor() -> None:
    out = compute(
        _adept(
            "holy-text",
            quality_ids=[MENTOR_SPIRIT],
            mentor_id=HOLY_TEXT,
            mentor_choices=[HOLY_TEXT_POWER_CHOICE],
            mentor_extras={HOLY_TEXT_POWER_CHOICE: "Mystic Armor"},
        )
    )
    assert out.derived["mentor"]["name"] == "Holy Text"
    choice = next(row for row in out.derived["mentor"]["choices"] if row["name"] == HOLY_TEXT_POWER_CHOICE)
    assert "Mystic Armor" in choice["extra_options"]
    assert choice["extra"] == "Mystic Armor"
    names = {item["name"]: item for item in out.derived["adept_powers"]}
    assert names["Mystic Armor"]["power_id"] == MYSTIC_ARMOR
    assert names["Mystic Armor"]["free_levels"] == 1
    assert names["Mystic Armor"]["cost"] == 0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "selectpowers" not in tags


ARMOR_VEST = "4ad1eeab-daf3-4495-a73d-fbb0ce89be5b"
HELMET = "fd6e194b-89ea-4030-9203-87341442eadb"
CHEM_PROT = "480b7c5d-758b-4833-8bfd-9487e2455f7d"
FIRE_RES = "dd246520-7306-40fb-88b4-c9cb031208fc"
INSULATION = "497b5d6b-df0c-401d-91de-42a224b1fa87"
NONCONDUCT = "0cfb049a-a1bd-4daa-96be-9468c37d9c3c"
CHEM_SEAL = "1e002d2e-cd93-4cef-a666-b6c6449f4e9f"
THERMAL_DAMPING = "ba32a6e9-4e6f-47fe-8fd7-c3194a5174d6"
SHOCK_FRILLS = "dbdaf817-9bfa-4938-a195-b53c63b53e7c"
SOFTWEAVE = "cf8accf5-4117-4419-ab73-957489038ab9"
GEL_PACKS = "ed43ded4-1b2f-410a-9322-166c39306d03"
FULL_BODY = "9ee80c97-9197-4dd5-baed-f77cfd2cee17"
FBA_HELMET = "71c20b15-de11-49eb-93fe-f4d7491283e3"
URBAN_EXPLORER = "d8d9154d-c8d3-4593-a408-9f5b259f0363"
UE_HELMET = "812a7926-3980-4c26-9935-5f1b66abacda"
DIVING_ARMOR = "f2aab6fa-645a-4d39-a612-91d3ee9e6bce"


def test_armor_jacket_adds_armor_and_nuyen() -> None:
    out = compute(_mundane("jacket", armor=[ArmorInstall(armor_id=ARMOR_JACKET)]))
    assert out.derived["armor"] == 12
    assert out.derived["nuyen_spent"] == 1000
    assert out.derived["worn_armor"] == "Armor Jacket"
    assert out.derived["errors"] == []


def test_armor_wireless_bonus_toggles_effect() -> None:
    spec = next(a for a in catalog()["armor"] if a.get("wirelessbonus"))  # e.g. Armanté Suit
    base = _mundane("wl-armor", skills={"Con": 3})

    def social_pool(wireless: bool) -> int:
        st = base.model_copy(deep=True)
        st.armor = [ArmorInstall(armor_id=spec["id"], wireless=wireless)]
        out = compute(st)
        row = out.derived["armor_items"][0]
        assert row["has_wireless"] is True and row["wireless"] is wireless
        return out.derived["skill_bonus"].get("Con", 0)

    assert social_pool(True) == social_pool(False) + 1  # Social Active +1 while wireless


def test_armor_wireless_defaults_on() -> None:
    spec = next(a for a in catalog()["armor"] if a.get("wirelessbonus"))
    out = compute(_mundane("wl-default", armor=[ArmorInstall(armor_id=spec["id"])]))
    assert out.derived["armor_items"][0]["wireless"] is True


def test_helmet_stacks_on_jacket() -> None:
    st = _mundane("helm", armor=[ArmorInstall(armor_id=ARMOR_JACKET), ArmorInstall(armor_id=HELMET)])
    st.attributes["STR"] = 3  # the helmet's +2 fits under STR (SR5 p.169)
    out = compute(st)
    assert out.derived["armor"] == 14
    assert out.derived["nuyen_spent"] == 1100


def test_two_armor_suits_use_highest() -> None:
    out = compute(
        _mundane(
            "stack",
            armor=[ArmorInstall(armor_id=ARMOR_JACKET), ArmorInstall(armor_id=ARMOR_VEST)],
        )
    )
    assert out.derived["armor"] == 12
    assert out.derived["nuyen_spent"] == 1500
    assert has(out.derived["warnings"], "engine.gear.armorHighestOnly")


def test_orthoskin_stacks_with_jacket() -> None:
    out = compute(
        _mundane(
            "skin-jacket",
            armor=[ArmorInstall(armor_id=ARMOR_JACKET)],
            bioware=[CyberwareInstall(ware_id=ORTHOSKIN, rating=2)],
        )
    )
    assert out.derived["armor"] == 14
    assert out.derived["nuyen_spent"] == 13000


def test_chemical_protection_on_jacket() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "chem-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=CHEM_PROT, parent_id=jacket.id, rating=2)],
        )
    )
    row = out.derived["armor_items"][0]
    assert out.derived["armor"] == 12
    assert out.derived["nuyen_spent"] == 1500
    assert row["capacity_used"] == 2
    assert row["capacity_max"] == 12
    assert row["mods"][0]["nuyen"] == 500
    assert row["mods"][0]["special_armor"]["toxin_contact"] == 2
    assert row["mods"][0]["special_armor"]["pathogen_contact"] == 2
    assert out.derived["special_armor"]["toxin_contact"] == 2
    assert out.derived["special_armor"]["pathogen_contact"] == 2
    assert out.derived["errors"] == []


def test_fire_resistance_adds_special_armor() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "fire-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=FIRE_RES, parent_id=jacket.id, rating=2)],
        )
    )
    assert out.derived["armor"] == 12
    assert out.derived["special_armor"]["fire"] == 2
    assert out.derived["armor_items"][0]["mods"][0]["special_armor"]["fire"] == 2
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "firearmor" not in tags


def test_insulation_and_nonconductivity_add_special_armor() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "insul-jacket",
            armor=[jacket],
            armor_mods=[
                ArmorModInstall(mod_id=INSULATION, parent_id=jacket.id, rating=3),
                ArmorModInstall(mod_id=NONCONDUCT, parent_id=jacket.id, rating=1),
            ],
        )
    )
    assert out.derived["armor"] == 12
    assert out.derived["special_armor"]["cold"] == 3
    assert out.derived["special_armor"]["electricity"] == 1


def test_chemical_seal_grants_contact_and_inhalation_immunity() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "seal-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=CHEM_SEAL, parent_id=jacket.id)],
        )
    )
    immunities = out.derived["special_armor"]["immunities"]
    assert immunities["toxin_contact"] is True
    assert immunities["toxin_inhalation"] is True
    assert immunities["pathogen_contact"] is True
    assert immunities["pathogen_inhalation"] is True
    assert out.derived["armor_items"][0]["mods"][0]["special_armor"]["immunities"]["toxin_contact"] is True


def test_thermal_damping_adds_sneaking_physical_limit() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    baseline = compute(_mundane("damp-base", armor=[jacket]))
    out = compute(
        _mundane(
            "damp-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=THERMAL_DAMPING, parent_id=jacket.id, rating=2)],
        )
    )
    row = out.derived["armor_items"][0]["mods"][0]
    assert out.derived["armor"] == 12
    assert out.derived["nuyen_spent"] == 2000
    assert row["nuyen"] == 1000
    assert row["capacity_cost"] == 2
    assert row["limit_modifiers"] == [
        {
            "limit": "physical",
            "value": 2,
            "condition": "LimitCondition_TestSneakingThermal",
            "condition_label": {"key": "engine.limitCond.sneakingThermal", "params": {}},
            "source": "",
        }
    ]
    assert out.derived["limit_modifiers"] == [
        {
            "limit": "physical",
            "value": 2,
            "condition": "LimitCondition_TestSneakingThermal",
            "condition_label": {"key": "engine.limitCond.sneakingThermal", "params": {}},
            "source": "Thermal Damping",
        }
    ]
    assert out.derived["limits"]["physical"] == baseline.derived["limits"]["physical"]
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "limitmodifier" not in tags
    assert out.derived["errors"] == []


def test_unequipped_armor_drops_thermal_damping_limit() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET, equipped=False)
    out = compute(
        _mundane(
            "unequip-damp",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=THERMAL_DAMPING, parent_id=jacket.id, rating=2)],
        )
    )
    assert out.derived["limit_modifiers"] == []
    assert out.derived["armor_items"][0]["mods"][0]["limit_modifiers"][0]["value"] == 2


def test_unequipped_armor_drops_special_armor() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET, equipped=False)
    out = compute(
        _mundane(
            "unequip-fire",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=FIRE_RES, parent_id=jacket.id, rating=2)],
        )
    )
    assert out.derived["special_armor"]["fire"] == 0
    assert out.derived["armor_items"][0]["mods"][0]["special_armor"]["fire"] == 2


def test_shock_frills_uses_capacity() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "shock-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=SHOCK_FRILLS, parent_id=jacket.id)],
        )
    )
    row = out.derived["armor_items"][0]
    assert out.derived["nuyen_spent"] == 1250
    assert row["capacity_used"] == 2
    assert out.derived["errors"] == []


def test_ynt_softweave_doubles_jacket_cost_and_capacity() -> None:
    spec = next(item for item in catalog()["armor_mods"] if item["id"] == SOFTWEAVE)
    assert spec["purchasable"] is True
    assert spec["cost"] == "Armor Cost"
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "softweave-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=SOFTWEAVE, parent_id=jacket.id)],
        )
    )
    row = out.derived["armor_items"][0]
    weave = row["mods"][0]
    assert weave["name"] == "YNT Softweave Armor"
    assert weave["nuyen"] == 1000
    assert weave["capacity_cost"] == -6
    assert row["nuyen"] == 2000
    assert row["capacity_used"] == 0
    assert row["capacity_max"] == 18
    assert out.derived["nuyen_spent"] == 2000
    assert out.derived["errors"] == []


def test_ynt_softweave_rounds_odd_capacity_up() -> None:
    vest = ArmorInstall(armor_id=ARMOR_VEST)
    out = compute(
        _mundane(
            "softweave-vest",
            armor=[vest],
            armor_mods=[ArmorModInstall(mod_id=SOFTWEAVE, parent_id=vest.id)],
        )
    )
    row = out.derived["armor_items"][0]
    assert row["nuyen"] == 1000
    assert row["capacity_used"] == 0
    assert row["capacity_max"] == 14
    assert out.derived["nuyen_spent"] == 1000
    assert out.derived["errors"] == []


def test_ynt_softweave_keeps_chem_prot_inside_expanded_capacity() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "softweave-chem",
            armor=[jacket],
            armor_mods=[
                ArmorModInstall(mod_id=CHEM_PROT, parent_id=jacket.id, rating=2),
                ArmorModInstall(mod_id=SOFTWEAVE, parent_id=jacket.id),
            ],
        )
    )
    row = out.derived["armor_items"][0]
    assert out.derived["nuyen_spent"] == 2500
    assert row["capacity_used"] == 2
    assert row["capacity_max"] == 18
    assert out.derived["errors"] == []


def test_armor_mod_capacity_overflow() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "overflow",
            armor=[jacket],
            armor_mods=[
                ArmorModInstall(mod_id=FIRE_RES, parent_id=jacket.id, rating=6),
                ArmorModInstall(mod_id=CHEM_PROT, parent_id=jacket.id, rating=6),
                ArmorModInstall(mod_id=SHOCK_FRILLS, parent_id=jacket.id),
            ],
        )
    )
    row = out.derived["armor_items"][0]
    assert row["capacity_used"] == 14
    assert has(out.derived["errors"], "engine.gear.capacityOver")


def test_full_body_armor_helmet_adds_armor() -> None:
    suit = ArmorInstall(armor_id=FULL_BODY)
    out = compute(
        _mundane(
            "fba",
            armor=[suit],
            armor_mods=[ArmorModInstall(mod_id=FBA_HELMET, parent_id=suit.id)],
        )
    )
    assert out.derived["armor"] == 18
    assert out.derived["nuyen_spent"] == 2500
    assert out.derived["armor_items"][0]["mods"][0]["capacity_cost"] == 0


def test_urban_explorer_helmet_fits_only_jumpsuit() -> None:
    suit = ArmorInstall(armor_id=URBAN_EXPLORER)
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    ok = compute(
        _mundane(
            "ue-helm",
            armor=[suit],
            armor_mods=[ArmorModInstall(mod_id=UE_HELMET, parent_id=suit.id)],
        )
    )
    bad = compute(
        _mundane(
            "ue-on-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=UE_HELMET, parent_id=jacket.id)],
        )
    )
    assert ok.derived["armor"] == 11
    assert ok.derived["nuyen_spent"] == 750
    assert has(bad.derived["warnings"], "engine.gear.doesNotFit")
    assert bad.derived["nuyen_spent"] == 1000


def test_fba_helmet_rejected_on_jacket() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "fba-on-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=FBA_HELMET, parent_id=jacket.id)],
        )
    )
    assert has(out.derived["warnings"], "engine.gear.doesNotFit")
    assert out.derived["armor"] == 12
    assert out.derived["nuyen_spent"] == 1000


def test_armor_mod_without_parent_is_dropped() -> None:
    out = compute(_mundane("orphan-mod", armor_mods=[ArmorModInstall(mod_id=CHEM_PROT, rating=1)]))
    assert has(out.derived["warnings"], "engine.gear.mountOnArmor")
    assert out.derived["nuyen_spent"] == 0


def test_gel_packs_add_armor() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "gel",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=GEL_PACKS, parent_id=jacket.id)],
        )
    )
    assert out.derived["armor"] == 14
    assert out.derived["nuyen_spent"] == 2500
    assert out.derived["armor_items"][0]["capacity_used"] == 0


def test_diving_armor_includes_chemical_protection() -> None:
    out = compute(_mundane("dive", armor=[ArmorInstall(armor_id=DIVING_ARMOR)]))
    row = out.derived["armor_items"][0]
    names = [mod["name"] for mod in row["mods"]]
    assert "Chemical Protection" in names
    assert row["mods"][0]["included"] is True
    assert row["mods"][0]["rating"] == 4
    assert row["mods"][0]["nuyen"] == 0
    assert row["mods"][0]["special_armor"]["toxin_contact"] == 4
    assert row["mods"][0]["special_armor"]["pathogen_contact"] == 4
    assert out.derived["special_armor"]["toxin_contact"] == 4
    assert out.derived["special_armor"]["pathogen_contact"] == 4
    assert row["capacity_used"] == 0
    assert out.derived["nuyen_spent"] == 1750


def test_duplicate_chemical_protection_is_rejected() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "dup-chem",
            armor=[jacket],
            armor_mods=[
                ArmorModInstall(mod_id=CHEM_PROT, parent_id=jacket.id, rating=2),
                ArmorModInstall(mod_id=CHEM_PROT, parent_id=jacket.id, rating=3),
            ],
        )
    )
    assert len(out.derived["armor_items"][0]["mods"]) == 1
    assert has(out.derived["warnings"], "engine.gear.duplicateMod")
    assert out.derived["nuyen_spent"] == 1500


def test_softweave_adds_four_to_jacket_avail() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "avail-softweave",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=SOFTWEAVE, parent_id=jacket.id)],
        )
    )
    row = out.derived["armor_items"][0]
    weave = row["mods"][0]
    assert row["avail"] == "6"
    assert row["avail_value"] == 6
    assert weave["avail"] == "4"
    assert weave["avail_additive"] is True
    assert weave["avail_folded"] is True
    assert out.derived["avail_limit"] == 12
    assert out.derived["errors"] == []


RESIST_PATHOGENS_TOXINS = "5c022754-f7cf-479f-80b2-de8454fd76e4"


def test_resistance_pathogens_toxins_special_armor() -> None:
    out = compute(_human("rpt", quality_ids=[RESIST_PATHOGENS_TOXINS]))
    sa = out.derived["special_armor"]
    assert sa["toxin_contact"] == 1
    assert sa["toxin_ingestion"] == 1
    assert sa["pathogen_injection"] == 1
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "toxiningestionresist" not in tags
    assert "pathogeninjectionresist" not in tags


ALCHEMICAL_ARMORER = "e508350b-f61d-4878-bd6d-98f8c9e3588b"
ALTER_BALLISTICS = "243313e6-a9af-456a-9631-6581d869aa02"


def test_alchemical_armorer_grants_alter_ballistics() -> None:
    out = compute(
        _mage(
            "aa",
            tradition_id=HERMETIC,
            quality_ids=[ALCHEMICAL_ARMORER],
        )
    )
    spell = next(s for s in out.derived["spells"] if s["name"] == "Alter Ballistics")
    assert spell["spell_id"] == ALTER_BALLISTICS
    assert spell["free"] is True
    assert spell["granted"] is True
    assert spell["alchemical"] is True
    assert spell["karma"] == 0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "addspell" not in tags


BALLISTIC_SHIELD = "943d19f7-ee6b-4ce9-8a43-93d3fe5100f2"


def test_shield_is_armor_you_can_hit_people_with() -> None:
    """A Ballistic Shield is armour with an `<addweapon>`: one purchase, two
    rows, and the weapon row is charged nothing on its own."""
    out = compute(_mundane("shield", armor=[ArmorInstall(armor_id=BALLISTIC_SHIELD, equipped=True)]))
    row = next(w for w in out.derived["weapons"] if w["name"] == "Ballistic Shield")
    assert row["damage"] == "3S"  # STR 1
    assert row["damage_formula"] == "({STR}+2)S"
    assert row["from_armor"] is True
    assert row["source_armor_id"] == out.derived["armor_items"][0]["id"]
    assert out.derived["nuyen_spent"] == 1200


def _armor_named(name: str) -> str:
    return next(item["id"] for item in catalog()["armor"] if item["name"] == name)


def _custom_fit_state(stack_with: str | None, strength: int = 4) -> CharacterState:
    """Armor Jacket worn under a Mortimer of London Greatcoat, whose bundled
    Custom Fit (Stack) is pointed at `stack_with`."""
    coat = ArmorInstall(armor_id=_armor_named("Mortimer of London: Greatcoat Coat"))
    st = _mundane("custom-fit", armor=[ArmorInstall(armor_id=ARMOR_JACKET), coat])
    st.attributes["STR"] = strength
    st = compute(st)
    if stack_with is not None:
        fit = next(
            mod
            for mod in st.armor_mods
            if mod.parent_id == coat.id and mod.mod_id == _armor_mod_named("Custom Fit (Stack)")
        )
        fit.stack_with = stack_with
    return st


def test_custom_fit_stack_adds_the_override_to_the_armor_it_names() -> None:
    """`<selectarmor>` (RG p.59): the Greatcoat tailored to the Armor Jacket
    adds its +3 on top of the jacket's 12 instead of competing with it."""
    out = compute(_custom_fit_state("Armor Jacket")).derived
    assert out["armor"] == 15
    assert out["worn_armor"] == "Armor Jacket"
    assert not any(w["key"] == "engine.gear.armorHighestOnly" for w in out["warnings"])
    contributes = {row["name"]: row["contributes"] for row in out["armor_items"]}
    assert contributes == {"Armor Jacket": 12, "Mortimer of London: Greatcoat Coat": 3}
    fit = next(mod for mod in out["armor_mods"] if mod["name"] == "Custom Fit (Stack)")
    assert (fit["select_armor"], fit["stack_with"]) == (True, "Armor Jacket")


def test_custom_fit_stack_does_nothing_until_it_names_a_worn_armor() -> None:
    for target in ("", "Lined Coat"):
        out = compute(_custom_fit_state(target)).derived
        assert out["armor"] == 12
        assert any(w["key"] == "engine.gear.armorHighestOnly" for w in out["warnings"])


def test_stacked_armor_counts_only_up_to_strength() -> None:
    """SR5 p.169: accessories (and a Custom Fit piece) add to worn armor only
    up to the wearer's Strength — Chummer's cap, said as a warning."""

    def helmet(strength: int) -> dict:
        st = _mundane("helm-str", armor=[ArmorInstall(armor_id=ARMOR_JACKET), ArmorInstall(armor_id=HELMET)])
        st.attributes["STR"] = strength
        return compute(st).derived

    weak = helmet(1)
    assert weak["armor"] == 13
    assert has(weak["warnings"], "engine.gear.armorAccessoryCapped")
    assert {r["name"]: r["contributes"] for r in weak["armor_items"]} == {"Armor Jacket": 12, "Helmet": 1}
    strong = helmet(2)
    assert strong["armor"] == 14
    assert not has(strong["warnings"], "engine.gear.armorAccessoryCapped")


def test_custom_fit_stack_shares_the_strength_cap() -> None:
    out = compute(_custom_fit_state("Armor Jacket", strength=2)).derived
    assert out["armor"] == 14
    assert has(out["warnings"], "engine.gear.armorAccessoryCapped")


def test_accessories_alone_are_capped_too() -> None:
    st = _mundane("helm-only", armor=[ArmorInstall(armor_id=HELMET)])
    st.attributes["STR"] = 1
    assert compute(st).derived["armor"] == 1


def test_armor_encumbrance_is_minus_one_per_two_points_past_strength() -> None:
    """SR5 p.169: nothing up to STR + 1, then −1 per 2 full points past STR."""
    from app.engine.gear.armor import armor_encumbrance

    assert [armor_encumbrance(load, 3) for load in (3, 4, 5, 6, 7, 8)] == [0, 0, -1, -1, -2, -2]
    assert armor_encumbrance(0, 0) == 0


def test_heavy_stacked_armor_lowers_agility_and_reaction() -> None:
    """A Ballistic Shield's +6 on STR 3: armor counts +3 (the cap) and the
    load of 6 costs 1 AGI and 1 REA, said as a warning."""

    def shield(strength: int) -> dict:
        st = _mundane(
            "shield",
            armor=[ArmorInstall(armor_id=ARMOR_JACKET), ArmorInstall(armor_id=_armor_named("Ballistic Shield"))],
        )
        st.attributes.update({"STR": strength, "AGI": 3, "REA": 3})
        return compute(st).derived

    heavy = shield(3)
    assert heavy["armor"] == 15
    assert (heavy["totals"]["AGI"], heavy["totals"]["REA"]) == (2, 2)
    assert has(heavy["warnings"], "engine.gear.armorEncumbrance")
    light = shield(5)
    assert (light["totals"]["AGI"], light["totals"]["REA"]) == (3, 3)
    assert not has(light["warnings"], "engine.gear.armorEncumbrance")


HOLSTER = "5977fb0b-b74e-4eb9-b433-9b7c9877b14f"
MEDKIT = "ae9c37df-6d82-44c1-aa21-6c87e45e2dc1"


def test_gear_carried_in_armor_takes_its_armor_capacity() -> None:
    """A Holster or a Medkit in armor takes its `<armorcapacity>` from the
    armor's capacity, as a mod does, and is paid for as gear."""
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "carried",
            armor=[jacket],
            gear=[
                GearInstall(gear_id=HOLSTER, parent_id=jacket.id),
                GearInstall(gear_id=MEDKIT, rating=2, parent_id=jacket.id),
            ],
        )
    )
    row = out.derived["armor_items"][0]
    assert row["capacity_used"] == 8
    assert {g["name"] for g in row["gear"]} == {"Holster", "Medkit"}
    assert out.derived["nuyen_spent"] == 1000 + 150 + 500
    assert out.derived["errors"] == []
    assert not has(out.derived["warnings"], "engine.gear.doesNotFit")


def test_gear_over_the_armors_capacity_is_an_error() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "overfull",
            armor=[jacket],
            gear=[GearInstall(gear_id=MEDKIT, parent_id=jacket.id) for _ in range(3)],
        )
    )
    row = out.derived["armor_items"][0]
    assert row["capacity_used"] == 15 > row["capacity_max"]
    assert has(out.derived["errors"], "engine.gear.capacityOver")
