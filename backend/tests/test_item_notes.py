"""A row's own note, and the player's name for a piece of gear, a vehicle or
a spirit, go through a .chum5 as Chummer saves them (`<notes>`,
`<armorname>`, `<gearname>`, `<vehiclename>`, `<crittername>`).

Nothing is computed from these; they only have to come back."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog, catalog_list
from app.engine import compute
from app.engine.constants import quality_take_extra_key
from app.models import CharacterState
from app.models.gear import (
    ArmorInstall,
    CommlinkInstall,
    CyberwareInstall,
    GearInstall,
    LifestyleInstall,
    WeaponAccessoryInstall,
    WeaponInstall,
)
from app.models.magic import (
    AdeptPowerInstall,
    FocusInstall,
    QiFocusInstall,
    SpellInstall,
    SpiritInstall,
    SpriteInstall,
)
from tests.engine_support import FORD_AMERICAR, HERMETIC, SPIRIT_FIRE, _adept, _mage, _mundane, _techno

POWER_FOCUS = "62bfb38d-5515-440b-83ed-289ed926d27e"
NOTE = "Bought off Dodger.\n\nDo not tell the fixer. "


def _id(rows: list[dict], name: str) -> str:
    return next(str(row["id"]) for row in rows if row.get("name") == name)


def _reimport(state: CharacterState) -> CharacterState:
    return CharacterState.model_validate(chum5_to_state(state_to_chum5(compute(state)))[0])


def _gear_state() -> CharacterState:
    cat = catalog()
    weapon = _id([w for w in cat["weapons"] if w.get("purchasable")], "Ares Predator V")
    return _mundane(
        "notes-gear",
        armor=[ArmorInstall(id="a", armor_id=_id(cat["armor"], "Armor Jacket"), notes=NOTE, nickname="Old Faithful")],
        weapons=[WeaponInstall(id="w", weapon_id=weapon, notes="Serial filed off")],
        weapon_accessories=[
            WeaponAccessoryInstall(
                accessory_id=_id(cat["weapon_accessories"], "Laser Sight"), parent_id="w", notes="Red dot"
            )
        ],
        cyberware=[CyberwareInstall(ware_id=_id(cat["cyberware"]["items"], "Datajack"), notes="Left temple")],
        gear=[GearInstall(gear_id=_id(catalog_list("gear"), "Medkit"), notes="Restock", nickname="Doc")],
        commlinks=[
            CommlinkInstall(gear_id=_id(catalog_list("commlinks"), "Meta Link"), notes="Burner", nickname="Spare")
        ],
        vehicles=[GearInstall(gear_id=FORD_AMERICAR, notes="Stolen plates", nickname="Betsy")],
        drones=[GearInstall(gear_id=str(catalog_list("drones")[0]["id"]), nickname="Buzz")],
        lifestyles=[LifestyleInstall(lifestyle_id=_id(catalog_list("lifestyles"), "Low"), notes="Above a noodle bar")],
    )


def test_gear_rows_keep_their_notes_and_names() -> None:
    back = _reimport(_gear_state())
    assert (back.armor[0].notes, back.armor[0].nickname) == (NOTE, "Old Faithful")
    assert back.weapons[0].notes == "Serial filed off"
    # the Predator comes with its smartgun; the laser sight is the one bought
    assert [row.notes for row in back.weapon_accessories if row.notes] == ["Red dot"]
    assert back.cyberware[0].notes == "Left temple"
    assert (back.gear[0].notes, back.gear[0].nickname) == ("Restock", "Doc")
    assert (back.commlinks[0].notes, back.commlinks[0].nickname) == ("Burner", "Spare")
    assert (back.vehicles[0].notes, back.vehicles[0].nickname) == ("Stolen plates", "Betsy")
    assert back.drones[0].nickname == "Buzz"
    assert back.lifestyles[0].notes == "Above a noodle bar"


def test_names_are_written_under_chummers_tags() -> None:
    root = ET.fromstring(state_to_chum5(compute(_gear_state())))
    assert root.findtext("./armors/armor/armorname") == "Old Faithful"
    assert root.findtext("./armors/armor/notes") == NOTE
    assert {el.text for el in root.iter("gearname")} == {"Doc", "Spare"}
    assert {el.text for el in root.iter("vehiclename")} == {"Betsy", "Buzz"}


def test_an_empty_note_is_not_written() -> None:
    cat = catalog()
    state = _mundane("notes-none", armor=[ArmorInstall(armor_id=_id(cat["armor"], "Armor Jacket"))])
    armor = ET.fromstring(state_to_chum5(compute(state))).find("./armors/armor")
    assert armor is not None
    assert armor.find("notes") is None
    assert armor.find("armorname") is None


def test_magic_rows_keep_their_notes_and_names() -> None:
    cat = catalog()
    mage = _mage(
        "notes-mage",
        tradition_id=HERMETIC,
        spells=[SpellInstall(spell_id=_id(cat["spells"], "Heal"), notes="Learned from Mama Rose")],
        spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, services=2, nickname="Hammer", notes="Owes one")],
        foci=[FocusInstall(gear_id=POWER_FOCUS, force=1, nickname="Spurs", notes="Grandfather's")],
    )
    back = _reimport(mage)
    assert back.spells[0].notes == "Learned from Mama Rose"
    assert (back.spirits[0].nickname, back.spirits[0].notes) == ("Hammer", "Owes one")
    assert (back.foci[0].nickname, back.foci[0].notes) == ("Spurs", "Grandfather's")

    adept = _adept(
        "notes-adept",
        adept_powers=[AdeptPowerInstall(power_id=_id(cat["powers"], "Improved Reflexes"), notes="Since the accident")],
    )
    assert _reimport(adept).adept_powers[0].notes == "Since the accident"

    qi = _adept(
        "notes-qi",
        qi_foci=[
            QiFocusInstall(
                power_id=_id(cat["powers"], "Combat Sense"), rating=2, nickname="Prayer beads", notes="Kept"
            ),
            QiFocusInstall(rating=1, bonded=False, notes="Not bonded yet"),
        ],
    )
    assert [(row.nickname, row.notes) for row in _reimport(qi).qi_foci] == [
        ("Prayer beads", "Kept"),
        ("", "Not bonded yet"),
    ]

    techno = _techno(
        "notes-techno",
        sprites=[SpriteInstall(sprite_id=_id(catalog_list("sprites"), "Courier Sprite"), nickname="Thassa")],
    )
    assert _reimport(techno).sprites[0].nickname == "Thassa"


def _gid(bucket: str, name: str) -> str:
    return _id(catalog_list(bucket), name)


def test_what_is_put_inside_other_gear_keeps_its_notes_and_name() -> None:
    """Programs on a deck, apps on a commlink, an autosoft on a vehicle, and
    the contents of a kit, of goggles and of a sensor housing: each is a row
    of its own, with a note and a name of its own (Chummer's `<children>`)."""
    state = _mundane(
        "notes-nested",
        commlinks=[CommlinkInstall(id="c", gear_id=_gid("commlinks", "Meta Link"))],
        apps=[GearInstall(gear_id=_gid("apps", "Diagnostics"), parent_id="c", notes="app", nickname="Doc")],
        cyberdecks=[GearInstall(id="d", gear_id=_gid("cyberdecks", "Erika MCD-1"))],
        vehicles=[GearInstall(id="v", gear_id=FORD_AMERICAR)],
        programs=[
            GearInstall(gear_id=_gid("programs", "Browse"), parent_id="d", notes="program", nickname="Spider"),
            GearInstall(gear_id=_gid("programs", "Clearsight Autosoft"), parent_id="v", rating=2, notes="autosoft"),
        ],
        gear=[
            GearInstall(id="m", gear_id=_gid("gear", "Medkit"), rating=3),
            GearInstall(gear_id=_gid("gear", "Medkit Supplies"), parent_id="m", notes="supplies", nickname="Refill"),
        ],
        optics=[
            GearInstall(id="o", gear_id=_gid("optics", "Contacts"), rating=3),
            GearInstall(gear_id=_gid("optics", "Vision Enhancement"), parent_id="o", notes="vision"),
        ],
        sensors=[
            GearInstall(id="s", gear_id=_gid("sensors", "Handheld Housing"), rating=3),
            GearInstall(id="ss", gear_id=_gid("sensors", "Single Sensor"), parent_id="s", notes="sensor"),
            GearInstall(gear_id=_gid("sensors", "Camera"), parent_id="ss", notes="camera", nickname="Eye"),
        ],
    )
    back = _reimport(state)
    texts = sorted(
        (row.notes, row.nickname)
        for rows in (back.apps, back.programs, back.gear, back.optics, back.sensors)
        for row in rows
        if row.parent_id
    )
    assert texts == [
        ("app", "Doc"),
        ("autosoft", ""),
        ("camera", "Eye"),
        ("program", "Spider"),
        ("sensor", ""),
        ("supplies", "Refill"),
        ("vision", ""),
    ]


def test_quality_notes_come_back_by_take() -> None:
    """Keyed as `quality_extras` is: a take with its own text has its own
    note, and the levels of one quality share theirs."""
    cat = catalog()
    ambi = _id(cat["qualities"], "Ambidextrous")
    gremlins = _id(cat["qualities"], "Gremlins")
    records = _id(cat["qualities"], "Records on File")
    second = quality_take_extra_key(records, 1)
    state = _mundane(
        "notes-quality",
        quality_ids=[ambi, gremlins, gremlins, records, records],
        quality_extras={records: "Ares", second: "Renraku"},
        quality_notes={ambi: "Writes with both", gremlins: "Not near the deck", records: "Old job", second: "Arcology"},
    )
    root = ET.fromstring(state_to_chum5(compute(state)))
    notes = [
        (q.findtext("name"), q.findtext("notes"))
        for q in root.findall("./qualities/quality")
        if q.find("notes") is not None
    ]
    # each level of Gremlins says it, as Chummer's own rows do
    assert notes.count(("Gremlins", "Not near the deck")) == 2
    back = _reimport(state)
    assert back.quality_notes == state.quality_notes


def test_the_notes_cost_nothing() -> None:
    plain = _gear_state()
    for rows in (plain.armor, plain.weapons, plain.gear, plain.vehicles, plain.commlinks, plain.lifestyles):
        for row in rows:
            row.notes = ""
            if hasattr(row, "nickname"):
                row.nickname = ""
    assert compute(_gear_state()).derived["nuyen"] == compute(plain).derived["nuyen"]


_SAVES = sorted((Path(__file__).resolve().parents[1] / "vendor" / "chummer-tests").rglob("*.chum5"))
_TAGS = ("notes", "armorname", "gearname", "vehiclename", "crittername")
_ROWS = (
    "./qualities/quality",
    "./powers/power",
    "./spells/spell",
    "./spirits/spirit",
    "./cyberwares/cyberware",
    "./armors/armor",
    "./weapons/weapon",
    ".//accessories/accessory",
    "./gears/gear",
    "./vehicles/vehicle",
    "./vehicles/vehicle/gears/gear",
    ".//weaponmount/weapons/weapon",
    ".//children/gear",
    "./lifestyles/lifestyle",
)


def _texts(root: ET.Element, kept: set[tuple[str, str]] | None = None) -> list[tuple[str, str]]:
    """Each note and name, from the rows `kept` names by list and name.

    A piece that came with another (`<parentid>`: a drone's own autosoft) is
    rebuilt by this app from what brought it, and a row the import does not
    take (a spirit outside the tradition) is a question for `--roundtrip`.
    """
    return sorted(
        (tag, text)
        for path in _ROWS
        for row in root.findall(path)
        if not (row.findtext("parentid") or "").strip() and (kept is None or (path, row.findtext("name") or "") in kept)
        for tag in _TAGS
        if (text := row.findtext(tag) or "").strip()
    )


def _rows(root: ET.Element) -> set[tuple[str, str]]:
    return {(path, row.findtext("name") or "") for path in _ROWS for row in root.findall(path)}


@pytest.mark.skipif(not _SAVES, reason="Chummer's test saves are fetched by `make reconcile`; absent in CI")
@pytest.mark.parametrize("path", _SAVES, ids=lambda p: p.stem)
def test_chummers_own_saves_keep_every_note(path: Path) -> None:
    """Every note and name in Chummer's test characters, word for word —
    `--fidelity` only sees that a field is there."""
    original = ET.fromstring(path.read_bytes())
    state = CharacterState.model_validate(chum5_to_state(path.read_bytes())[0])
    exported = ET.fromstring(state_to_chum5(compute(state)))
    kept = _rows(exported) & _rows(original)
    assert _texts(exported, kept) == _texts(original, kept)
