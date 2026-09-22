"""Foundry VTT shadowrun5e (0.34.5) export: Chummer's JSON export, as the
system's Chummer importer reads it (backend/app/fvtt_export)."""

from __future__ import annotations

import json
from typing import Any

from starlette.testclient import TestClient

from app.characters import compute_state
from app.data_loader import catalog
from app.fvtt_export import state_to_fvtt
from app.main import app
from app.models import (
    AdeptPowerInstall,
    ArmorInstall,
    ArmorModInstall,
    CharacterState,
    CommlinkInstall,
    ComplexFormInstall,
    ContactInstall,
    CyberwareInstall,
    GearInstall,
    LifestyleInstall,
    Priorities,
    SpellInstall,
    VehicleModInstall,
    WeaponAccessoryInstall,
    WeaponInstall,
    WeaponMountInstall,
)


def _state() -> CharacterState:
    c = catalog()
    trad = next(r["id"] for r in c["traditions"] if r["name"] == "Hermetic")
    wire = next(r["id"] for r in c["cyberware"]["items"] if r["name"] == "Wired Reflexes")
    quals = [r["id"] for r in c["qualities"] if r["name"] in ("Ambidextrous", "Distinctive Style")]
    return compute_state(
        CharacterState(
            id="fvtt",
            name="夜叉",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
            metatype="Elf",
            talent="Magician",
            tradition_id=trad,
            attributes={"BOD": 3, "AGI": 4, "REA": 3, "STR": 2, "CHA": 5, "INT": 4, "LOG": 4, "WIL": 4, "MAG": 5},
            skills={"Spellcasting": 5, "Pistols": 3},
            skill_groups={"Athletics": 2},
            skill_specializations={"Spellcasting": "Combat"},
            knowledge_skills={"Magical Theory": 3},
            knowledge_categories={"Magical Theory": "Academic"},
            native_languages=["Sperethiel"],
            quality_ids=quals,
            cyberware=[CyberwareInstall(ware_id=wire, rating=1, grade="Standard")],
            appearance="銀髪 & <細身>\n左頬に傷",
            background="元企業の内勤。\n\n今はフリー。",
        )
    )


def _char(state: CharacterState, locale: str = "ja") -> dict[str, Any]:
    out = state_to_fvtt(state, locale)
    # the importer takes the first character of `characters.character`
    assert set(out) == {"?xml", "characters"}
    char = out["characters"]["character"]
    assert isinstance(char, dict)
    return char


def _skill(char: dict[str, Any], english: str) -> dict[str, Any]:
    return next(s for s in char["skills"]["skill"] if s["name_english"] == english)


def test_the_fields_the_importer_dereferences_without_a_guard_are_there() -> None:
    char = _char(_state())
    # `nuyen.replace(...)`, `attributes[1].attribute`, `skills.skill` and
    # `metatype_english.toLowerCase()` throw when missing
    assert isinstance(char["nuyen"], str)
    assert char["attributes"][0] is None
    assert isinstance(char["attributes"][1]["attribute"], list)
    assert isinstance(char["skills"]["skill"], list)
    assert char["metatype_english"] == "Elf"


def test_every_value_is_a_string_or_a_container_the_way_chummer_prints_it() -> None:
    def walk(v: Any) -> None:
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        else:
            assert v is None or isinstance(v, str), v

    walk(state_to_fvtt(_state()))


def test_attributes_carry_the_unaugmented_base_and_the_finished_total() -> None:
    state = _state()
    rows = {a["name_english"]: a for a in _char(state)["attributes"][1]["attribute"]}
    totals = state.derived["totals"]
    # Wired Reflexes 1 lifts REA by one; the importer covers base -> total
    # with an ActiveEffect
    assert int(rows["REA"]["total"]) == totals["REA"] == int(rows["REA"]["base"]) + 1
    # the essence the ware cost comes off MAG in the total only
    assert int(rows["MAG"]["total"]) == totals["MAG"] < int(rows["MAG"]["base"])
    # a mundane special attribute and ESS are not written (no Foundry field)
    assert "RES" not in rows and "ESS" not in rows


def test_initiative_is_written_as_the_parts_the_importer_subtracts_from() -> None:
    state = _state()
    char = _char(state)
    d = state.derived
    assert int(char["initbonus"]) == d["initiative"]["value"] - d["totals"]["REA"] - d["totals"]["INT"]
    assert int(char["initdice"]) == d["initiative"]["dice"] == 2
    assert int(char["astralinitdice"]) == d["astral_initiative"]["dice"]


def test_magic_flags_tradition_and_reputation() -> None:
    state = _state()
    char = _char(state)
    assert (char["magician"], char["adept"], char["technomancer"]) == ("True", "False", "False")
    # the attribute that is not WIL becomes Foundry's drain attribute
    assert char["tradition"]["drainattributes"] == "WIL + LOG"
    assert char["initiationgrade"] is None
    assert char["calculatedstreetcred"] == str(state.derived["street_cred"])
    assert char["calculatednotoriety"] == str(state.derived["notoriety"])


def test_active_skills_are_matched_by_english_name_and_include_the_group_rating() -> None:
    char = _char(_state())
    pistols = _skill(char, "Pistols")
    assert pistols["rating"] == "3"
    assert pistols["knowledge"] == "False"
    assert pistols["name"] == catalog()["translations"]["Pistols"] != "Pistols"
    # a skill rated only through its group prints at the group's rating
    assert _skill(char, "Running")["rating"] == "2"
    spell = _skill(char, "Spellcasting")
    assert spell["skillspecializations"]["skillspecialization"][0]["name_english"] == "Combat"
    # unrated skills stay out: the importer lays the default skill set down first
    assert all(int(s["rating"]) > 0 or s["isnativelanguage"] == "True" for s in char["skills"]["skill"])
    assert char["skills"]["skillgroup"] == [
        {
            "name": catalog()["translations"].get("Athletics", "Athletics"),
            "name_english": "Athletics",
            "rating": "2",
            "isbroken": "False",
        }
    ]


def test_knowledge_and_native_language_skills() -> None:
    char = _char(_state())
    theory = _skill(char, "Magical Theory")
    assert (theory["knowledge"], theory["islanguage"], theory["rating"]) == ("True", "False", "3")
    assert theory["skillcategory_english"] == "Academic"
    native = _skill(char, "Sperethiel")
    assert (native["islanguage"], native["isnativelanguage"]) == ("True", "True")


def test_qualities_carry_the_guid_the_importer_matches_on_first() -> None:
    state = _state()
    rows = {q["name_english"]: q for q in _char(state)["qualities"]["quality"]}
    ambi = next(r for r in catalog()["qualities"] if r["name"] == "Ambidextrous")
    assert rows["Ambidextrous"]["sourceid"] == ambi["id"]
    assert rows["Ambidextrous"]["qualitytype_english"] == "Positive"
    assert rows["Ambidextrous"]["bp"] == str(ambi["karma"])
    assert rows["Distinctive Style"]["qualitytype_english"] == "Negative"


def test_english_locale_keeps_the_data_names() -> None:
    char = _char(_state(), "en")
    assert _skill(char, "Pistols")["name"] == "Pistols"
    assert char["metatype"] == "Elf"


def test_bio_text_is_escaped_html() -> None:
    char = _char(_state())
    assert char["description"] == "<p>銀髪 &amp; &lt;細身&gt;<br/>左頬に傷</p>"
    assert char["background"] == "<p>元企業の内勤。</p><p>今はフリー。</p>"
    assert char["concept"] is None


def _id(kind: str, name: str) -> str:
    rows = catalog()[kind]
    rows = rows.get("items", rows) if isinstance(rows, dict) else rows
    return str(next(r["id"] for r in rows if r["name"] == name))


def _mystic() -> CharacterState:
    return compute_state(
        CharacterState(
            id="fvtt-mystic",
            name="霞",
            priorities=Priorities(Heritage="D", Attributes="B", Talent="A", Skills="C", Resources="C"),
            metatype="Human",
            talent="Mystic Adept",
            attributes={"BOD": 3, "AGI": 4, "REA": 3, "STR": 2, "CHA": 4, "INT": 4, "LOG": 4, "WIL": 4, "MAG": 6},
            power_points_bought=2,
            spells=[SpellInstall(spell_id=_id("spells", "Fireball"))],
            adept_powers=[
                AdeptPowerInstall(power_id=_id("powers", "Improved Reflexes"), rating=1),
                AdeptPowerInstall(power_id=_id("powers", "Improved Ability (skill)"), rating=1, extra="Pistols"),
            ],
            contacts=[ContactInstall(name="Ms. ジョンソン", role="Fixer", connection=4, loyalty=2)],
            lifestyles=[LifestyleInstall(lifestyle_id=_id("lifestyles", "Medium"), months=2)],
        )
    )


def test_contacts_and_lifestyles() -> None:
    char = _char(_mystic())
    (contact,) = char["contacts"]["contact"]
    assert (contact["name"], contact["role"], contact["connection"], contact["loyalty"]) == (
        "Ms. ジョンソン",
        "Fixer",
        "4",
        "2",
    )
    assert (contact["family"], contact["blackmail"]) == ("False", "False")
    (life,) = char["lifestyles"]["lifestyle"]
    # lower-cased, the base lifestyle is the Foundry type key
    assert life["baselifestyle"].lower() == "medium"
    assert life["name"] == "中流"
    assert life["totalmonthlycost"] == "5000"


def test_spells_carry_every_keyword_in_english() -> None:
    (spell,) = _char(_mystic())["spells"]["spell"]
    assert spell["sourceid"] == _id("spells", "Fireball")
    assert spell["name_english"] == "Fireball"
    assert spell["category_english"] == "Combat"
    assert (spell["type_english"], spell["range_english"], spell["duration_english"]) == ("P", "LOS (A)", "I")
    assert spell["dv_english"] == "F-1"
    assert "Indirect" in spell["descriptors_english"]
    # the importer calls `.includes` on it for a combat spell
    assert isinstance(spell["damage_english"], str)
    assert spell["alchemy"] == "False"


def test_adept_powers_carry_the_level_and_the_points_spent() -> None:
    rows = {p["name_english"]: p for p in _char(_mystic())["powers"]["power"]}
    reflexes = rows["Improved Reflexes"]
    assert (reflexes["rating"], float(reflexes["totalpoints"])) == ("1", 1.5)
    ability = rows["Improved Ability (skill)"]
    assert ability["fullname_english"] == "Improved Ability (skill) (Pistols)"
    assert float(ability["totalpoints"]) == 0.5


def test_complex_forms_carry_the_fading_as_chummer_prints_it() -> None:
    state = compute_state(
        CharacterState(
            id="fvtt-techno",
            name="電",
            priorities=Priorities(Heritage="D", Attributes="B", Talent="A", Skills="C", Resources="C"),
            metatype="Human",
            talent="Technomancer",
            attributes={"BOD": 3, "AGI": 3, "REA": 3, "STR": 2, "CHA": 4, "INT": 5, "LOG": 5, "WIL": 4, "RES": 6},
            complex_forms=[
                ComplexFormInstall(form_id=_id("complex_forms", "Infusion of [Matrix Attribute]"), extra="Firewall")
            ],
        )
    )
    (form,) = _char(state, "en")["complexforms"]["complexform"]
    assert (form["target_english"], form["duration_english"], form["fv_english"]) == ("Device", "S", "L-2")
    assert form["fullname"] == "Infusion of [Matrix Attribute] (Firewall)"


def _samurai() -> CharacterState:
    sin = GearInstall(gear_id=_id("gear", "Fake SIN"), rating=4, extra="UCAS")
    gun = WeaponInstall(weapon_id=_id("weapons", "Ares Predator V"))
    return compute_state(
        CharacterState(
            id="fvtt-sam",
            name="鋼",
            priorities=Priorities(Heritage="D", Attributes="A", Talent="E", Skills="C", Resources="A"),
            metatype="Human",
            attributes={"BOD": 5, "AGI": 5, "REA": 4, "STR": 4, "CHA": 2, "INT": 4, "LOG": 3, "WIL": 3},
            skills={"Pistols": 5, "Blades": 3, "Throwing Weapons": 2},
            armor=[
                ArmorInstall(armor_id=_id("armor", "Armor Jacket")),
                ArmorInstall(armor_id=_id("armor", "Helmet")),
            ],
            cyberware=[CyberwareInstall(ware_id=_id("cyberware", "Wired Reflexes"), rating=1, grade="Alphaware")],
            weapons=[
                gun,
                WeaponInstall(weapon_id=_id("weapons", "Combat Knife")),
                WeaponInstall(weapon_id=_id("weapons", "Shuriken"), qty=3),
            ],
            weapon_accessories=[
                WeaponAccessoryInstall(accessory_id=_id("weapon_accessories", "Laser Sight"), parent_id=gun.id)
            ],
            commlinks=[CommlinkInstall(gear_id=_id("commlinks", "Meta Link"))],
            gear=[
                sin,
                GearInstall(gear_id=_id("gear", "Fake License"), rating=4, extra="Pistol", parent_id=sin.id),
                GearInstall(gear_id=_id("gear", "Ammo: Regular Ammo"), qty=2),
            ],
        )
    )


def test_armor_that_stacks_is_marked_with_a_plus() -> None:
    rows = {a["name_english"]: a for a in _char(_samurai())["armors"]["armor"]}
    assert rows["Armor Jacket"]["armor"] == "12"
    # the importer reads a "+" as an accessory
    assert rows["Helmet"]["armor"].startswith("+")
    assert rows["Armor Jacket"]["equipped"] == "True"


def test_armor_mods_go_nested_and_into_the_description() -> None:
    jacket = ArmorInstall(armor_id=_id("armor", "Armor Jacket"))
    state = compute_state(
        CharacterState(
            id="fvtt-mods",
            name="m",
            priorities=Priorities(Heritage="D", Attributes="A", Talent="E", Skills="C", Resources="A"),
            metatype="Human",
            attributes={"BOD": 5, "AGI": 5, "REA": 4, "STR": 4, "CHA": 2, "INT": 4, "LOG": 3, "WIL": 3},
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=_id("armor_mods", "Fire Resistance"), parent_id=jacket.id, rating=3)],
        )
    )
    row = _char(state, "en")["armors"]["armor"][0]
    (mod,) = row["armormods"]["armormod"]
    assert (mod["name_english"], mod["fullname_english"], mod["rating"]) == (
        "Fire Resistance",
        "Fire Resistance 3",
        "3",
    )
    assert int(mod["owncost"]) > 0
    # the importer never reads `armormods`, only `notes` as the description
    assert row["notes"] == "<p>Fire Resistance 3</p>"
    # the price stays the armor with its mods, as the sheet shows it
    assert int(row["owncost"]) == 1000 + int(mod["owncost"])
    plain = _char(_samurai())["armors"]["armor"][0]
    assert plain["armormods"] is None and plain["notes"] is None


def test_ware_carries_the_essence_and_the_foundry_grade() -> None:
    state = _samurai()
    (wire,) = _char(state)["cyberwares"]["cyberware"]
    assert wire["improvementsource"] == "Cyberware"
    assert wire["grade"] == "alpha"
    assert float(wire["ess"]) == state.derived["cyberware"][0]["essence"]


def test_gear_flags_steer_the_importer_and_a_license_rides_on_its_sin() -> None:
    rows = {g["name_english"]: g for g in _char(_samurai())["gears"]["gear"]}
    assert "Fake License" not in rows
    sin = rows["Fake SIN"]
    assert sin["issin"] == "True"
    (license_,) = sin["children"]["gear"]
    assert (license_["extra"], license_["rating"], license_["category_english"]) == ("Pistol", "4", "ID/Credsticks")
    link = rows["Meta Link"]
    assert (link["iscommlink"], link["devicerating"], link["firewall"]) == ("True", "1", "1")
    ammo = rows["Ammo: Regular Ammo"]
    # two boxes of ten, counted in rounds as Chummer does
    assert (ammo["isammo"], ammo["qty"]) == ("True", "20")


def test_weapons_carry_the_skill_the_figures_and_the_range_bands() -> None:
    state = _samurai()
    rows = {w["name_english"]: w for w in _char(state)["weapons"]["weapon"]}
    gun = rows["Ares Predator V"]
    assert (gun["type"], gun["skill"], gun["mode"]) == ("Ranged", "Pistols", "SA")
    assert gun["damage_noammo_english"] == "8P"
    assert gun["ranges"] == {"short": "0-5", "medium": "6-20", "long": "21-40", "extreme": "41-60"}
    # the sheet's accuracy already has the sight in it: the mod adds none
    sight = next(a for a in gun["accessories"]["accessory"] if a["name_english"] == "Laser Sight")
    assert (sight["accuracy"], sight["rc"]) == ("0", "0")
    knife = rows["Combat Knife"]
    assert (knife["type"], knife["skill"], knife["mode"], knife["ranges"]) == ("Melee", "Blades", None, None)
    # {STR} worked out: STR 4 -> {STR}, {STR}*2, {STR}*5, {STR}*7
    shuriken = rows["Shuriken"]
    assert shuriken["skill"] == "Throwing Weapons"
    assert shuriken["ranges"] == {"short": "0-4", "medium": "5-8", "long": "9-20", "extreme": "21-28"}


def test_ammo_with_a_gun_goes_as_its_clips_and_the_figures_leave_the_loaded_round_out() -> None:
    gun = WeaponInstall(weapon_id=_id("weapons", "Ares Predator V"))
    regular = GearInstall(gear_id=_id("gear", "Ammo: Regular Ammo"), qty=2, parent_id=gun.id)
    apds = GearInstall(gear_id=_id("gear", "Ammo: APDS"), parent_id=gun.id)
    gun.loaded_ammo_id = apds.id
    state = compute_state(
        CharacterState(
            id="fvtt-ammo",
            attributes={"BOD": 3, "AGI": 3, "REA": 3, "STR": 3, "CHA": 3, "INT": 3, "LOG": 3, "WIL": 3},
            name="弾",
            priorities=Priorities(Heritage="D", Attributes="A", Talent="E", Skills="C", Resources="A"),
            metatype="Human",
            weapons=[gun],
            gear=[regular, apds],
        )
    )
    # the sheet has the APDS in it; Foundry adds the equipped clip itself
    assert state.derived["weapons"][0]["ap"] == "-5"
    char = _char(state, "en")
    (row,) = char["weapons"]["weapon"]
    assert (row["damage_noammo_english"], row["rawap"]) == ("8P", "-1")
    clips = {c["english_name"]: c for c in row["clips"]["clip"]}
    assert clips["Ammo: Regular Ammo"]["count"] == "20"
    assert "ammotype" not in clips["Ammo: Regular Ammo"]
    assert clips["Ammo: APDS"]["ammotype"]["weaponbonusap_english"] == "-4"
    assert (row["currentammo"], row["availableammo"]) == ("Ammo: APDS", "30")
    # not a second time as loose gear
    assert not char["gears"]["gear"]


_PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


def _rigger() -> CharacterState:
    car = GearInstall(gear_id=_id("vehicles", "Ford Americar (Sedan)"))
    lynx = GearInstall(gear_id=_id("drones", "Steel Lynx Combat Drone (Large)"))
    gun = WeaponInstall(weapon_id=_id("weapons", "FN HAR"))
    pistol = WeaponInstall(weapon_id=_id("weapons", "Ares Predator V"))
    return compute_state(
        CharacterState(
            id="fvtt-rig",
            name="轍",
            priorities=Priorities(Heritage="D", Attributes="B", Talent="E", Skills="C", Resources="A"),
            metatype="Human",
            attributes={"BOD": 3, "AGI": 3, "REA": 5, "STR": 2, "CHA": 2, "INT": 4, "LOG": 5, "WIL": 3},
            vehicles=[car],
            drones=[lynx],
            vehicle_mods=[VehicleModInstall(mod_id=_id("vehicle_mods", "Smuggling Compartment"), parent_id=car.id)],
            weapon_mounts=[
                WeaponMountInstall(
                    parent_id=lynx.id, size_id=_id("weapon_mounts", "Heavy [SR5]"), weapon_install_id=gun.id
                )
            ],
            weapons=[gun, pistol],
            gear=[
                GearInstall(gear_id=_id("gear", "Medkit"), rating=3, parent_id=car.id),
                GearInstall(gear_id=_id("gear", "Medkit"), rating=6),
            ],
            portrait=_PNG,
            extra_portraits=[_PNG],
        )
    )


def test_vehicles_carry_their_stats_mods_stowed_gear_and_mounted_guns() -> None:
    char = _char(_rigger())
    rows = {v["name_english"]: v for v in char["vehicles"]["vehicle"]}
    car = rows["Ford Americar (Sedan)"]
    # the importer splits "on-road/off-road"
    assert (car["isdrone"], car["handling"], car["body"], car["pilot"]) == ("False", "4/3", "11", "1")
    assert [m["name_english"] for m in car["mods"]["mod"]] == ["Smuggling Compartment"]
    # beside its built-in Sensor Array
    (kit,) = [g for g in car["gears"]["gear"] if g["name_english"] == "Medkit"]
    assert kit["rating"] == "3"
    lynx = rows["Steel Lynx Combat Drone (Large)"]
    assert lynx["isdrone"] == "True"
    assert [w["name_english"] for w in lynx["weapons"]["weapon"]] == ["FN HAR"]
    # what sits in a vehicle is on the vehicle's actor, not the character's
    assert [(g["name_english"], g["rating"]) for g in char["gears"]["gear"]] == [("Medkit", "6")]
    assert [w["name_english"] for w in char["weapons"]["weapon"]] == ["Ares Predator V"]


def test_portraits_go_as_bare_base64_the_main_one_apart() -> None:
    char = _char(_rigger())
    bare = _PNG.split(",", 1)[1]
    assert char["mainmugshotbase64"] == bare
    assert char["othermugshots"] == {"mugshot": [{"stringbase64": bare}]}
    assert "mainmugshotbase64" not in _char(_samurai())


def test_fvtt_download_route() -> None:
    client = TestClient(app)
    ip = {"cf-connecting-ip": "203.0.113.57"}
    state = client.post("/api/characters/new", json={"name": "夜叉"}, headers=ip).json()
    r = client.post("/api/characters/fvtt", json={"state": state, "locale": "ja"}, headers=ip)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    assert "filename*=UTF-8''%E5%A4%9C%E5%8F%89.json" in r.headers["content-disposition"]
    body = json.loads(r.content)
    assert body["characters"]["character"]["name"] == "夜叉"
