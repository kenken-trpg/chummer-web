"""Ids and character builders shared by the `test_engine_*.py` files."""

from app.data_loader import catalog
from app.engine import (
    compute,
    default_attributes,
    find_metatype,
)
from app.models import (
    CharacterState,
    CyberwareInstall,
    GearInstall,
    Priorities,
    WeaponInstall,
)

DATAJACK = "47c48542-48c3-417e-91f0-b5a456183f05"
MUSCLE = "46f80a44-80ae-41d7-a7c8-a119c4cff70f"
WIRED = "bea0ded3-821f-449c-9507-815088f68b86"
EYES = "8e414ade-2764-4dc7-bdc4-83bb4a086034"
ARM = "df01eed6-a019-4198-b88d-4ba8f9aaefdf"
ORTHOSKIN = "96e4809a-71e6-4b98-9740-c6c44bc33aa9"
TONER = "69ab0255-a76b-4190-a8be-0473fed231ef"
SUPRATHYROID = "d1a314d9-3b83-4d62-854d-90e3788eea83"
QUALIA = "b110516e-36e8-4c69-a682-066e91c02351"
CUSTOM_STR = "7d61f860-0637-4214-914d-c68022361d24"


def _karma_human(cid: str, **attrs: int) -> CharacterState:
    values = default_attributes(find_metatype("Human", None))
    values.update(attrs)
    return CharacterState(
        id=cid,
        name=cid,
        build_method="Karma",
        priorities=Priorities(),
        metatype="Human",
        attributes=values,
    )


DEAD_SIN = "c0d411e6-ca88-4011-b56c-9f594882beb4"


CHANGELING_I = "3ea0d4dd-5ed7-4ab0-817f-68d7d67ab3d1"


def _human(cid: str, **kwargs: object) -> CharacterState:
    return CharacterState(
        id=cid,
        name=cid,
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        **kwargs,  # type: ignore[arg-type]
    )


IMPROVED_REFLEXES = "fea9e769-5f2c-4bae-9610-56c0825e145a"


def _adept(cid: str, letter: str = "B", **kwargs: object) -> CharacterState:
    attrs = default_attributes(find_metatype("Human", None))
    return CharacterState(
        id=cid,
        name=cid,
        priorities=Priorities(
            Heritage="C",
            Attributes="A",
            Talent=letter,
            Skills="B" if letter == "D" else "D",
            Resources="E",
        ),
        metatype="Human",
        talent="Adept",
        attributes=attrs,
        **kwargs,  # type: ignore[arg-type]
    )


MISSILE_MASTERY = "1221e699-e61b-4aed-adbb-a8eec02a65e2"
MASTER_ARCHER = "3c0862c4-1070-44dd-8866-0ba89276246b"  # weaponcategorydice: Bows +1
MENTOR_SPIRIT = "ced3fecf-2277-4b20-b1e0-894162ca9ae2"
HOLY_TEXT = "2dcbe44e-3789-4cf2-b51b-0337c239ce7c"
HOLY_TEXT_POWER_CHOICE = "Adept: Gain 1 free level of Mystic Armor or Empathic Healing (choose one)."
CHAOS = "2c6a5ac3-0d61-46dd-86a3-a630ebc91070"
RAPID_HEALING = "4676b6f7-120d-4344-81ac-5922445a521b"


HERMETIC = "19320625-bc1a-492f-8904-da6a847e5700"
STUNBOLT = "47423962-6b73-4cc3-ad4e-e8d037cf9507"


def _mage(cid: str, letter: str = "A", **kwargs: object) -> CharacterState:
    attrs = kwargs.pop("attributes", None) or default_attributes(find_metatype("Human", None))
    return CharacterState(
        id=cid,
        name=cid,
        priorities=Priorities(
            Heritage="C",
            Attributes="B" if letter == "A" else "A",
            Talent=letter,
            Skills="D",
            Resources="E",
        ),
        metatype="Human",
        talent="Magician",
        attributes=attrs,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


POWER_POINT_META = "406f096a-c093-4a02-b60f-002eb01a20b9"


SPIRIT_FIRE = "c0178bf8-1fc5-4c56-9ce1-92a3ae1adc45"
SPIRIT_BEASTS = "c5e35ac9-5737-4003-8c9e-eb016d2bccd2"
WEAPON_FOCUS = "25b0168d-7052-4f76-b8e5-162d67b8ab6e"


def _mage_rich(cid: str, **kwargs: object) -> CharacterState:
    attrs = kwargs.pop("attributes", None) or default_attributes(find_metatype("Human", None))
    return CharacterState(
        id=cid,
        name=cid,
        priorities=Priorities(Heritage="E", Attributes="C", Talent="A", Skills="D", Resources="B"),
        metatype="Human",
        talent="Magician",
        attributes=attrs,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


ARMOR_JACKET = "36a4cd30-c32c-44d0-847a-0c15fb51072a"
RESTRICTED_GEAR = "ce939b04-5fc6-49e9-a747-9c9d1254449e"
META_LINK = "89a0f3c9-5ef6-41cd-981f-4ac690ee2ab3"
LOW_LIFESTYLE = "451eef87-d18e-4bee-a972-1ee165b08522"
PREDATOR = "971c711b-db32-4339-9203-865ef38f350e"
ERIKA_DECK = "b6d1476d-a08c-43fc-be0e-68ca9330a43e"
RADIO_SHACK_RCC = "9d410862-89ae-408c-8342-82f7e6c1ae8f"
SENSOR_ARRAY = "2ca81a10-d0f7-4b39-ac93-a84f2f69f9d9"
ATMOSPHERE = "5c3b9966-ad7e-42e3-b0e0-f656021784cf"


def _mundane(cid: str, **kwargs: object) -> CharacterState:
    return CharacterState(
        id=cid,
        name=cid,
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        **{"priorities": Priorities(), **kwargs},
    )


FORD_AMERICAR = "898906ec-f2b9-43a4-98ad-6f79230b9a0c"
MECHANICAL_ARM = "3154f81c-f85c-414d-abe4-8289aa6e9766"
STANDARD_SR5_MOUNT = "079a5c61-aee6-4383-81b7-32540f7a0a0b"
HAND_BLADE = "ba93ab8d-fd7f-4fc4-bfa3-5f987fd15d77"


CLEANER = "373638b9-4334-4645-99f5-c3673e4f809b"
COURIER_SPRITE = "acf0c123-0881-4f13-8a98-010516e74019"
EDITOR = "6b4ed8d5-75c8-4415-9578-15afa4ac8494"


def _techno(cid: str, letter: str = "A", **kwargs: object) -> CharacterState:
    table = {
        "A": Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
        "B": Priorities(Heritage="C", Attributes="D", Talent="B", Skills="A", Resources="E"),
        "C": Priorities(Heritage="E", Attributes="B", Talent="C", Skills="A", Resources="D"),
    }
    attrs = kwargs.pop("attributes", None) or default_attributes(find_metatype("Human", None))
    return CharacterState(
        id=cid,
        name=cid,
        priorities=table[letter],
        metatype="Human",
        talent="Technomancer",
        attributes=attrs,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def _karate_id() -> str:
    return next(item["id"] for item in catalog()["martial_arts"] if item["name"] == "Karate")


BLANDNESS = "9cffd452-8489-48d5-888c-ac35459d9174"


MEDIUM_LIFESTYLE = "9cb0222c-14c1-4bea-bf83-055513a1f33e"
LIFESTYLE_GYM = "23c785d3-e086-46a6-8491-603fa1e6963d"
LIFESTYLE_CRAMPED = "ff0cb981-4459-46e7-ab75-d8c5bcb0c486"
JAZZ = "929c4835-1754-4999-9215-9859e8ec5384"
DEALER_CONNECTION = "ef6796eb-6559-4f22-bfa6-7e6571a3690d"
BLACK_MARKET_PIPELINE = "a68a897e-412f-4659-a637-4848f39a9c90"


MADE_MAN = "45be40cc-a21a-4771-b47d-a532ea60b205"


CODESLINGER = "41cc3e26-ae55-4e28-bd6a-b08866c21424"
MANABOLT = "85c12bae-3954-483c-a211-d8ee43a1c65e"
HEAL = "92fe97e1-2f16-4398-b12b-b29bfa23c75d"
CRITICAL_STRIKE = "dbf16604-164c-485c-96c8-fe3136cd5caa"
DARK_ALLY = "39384189-d15a-4f2e-97a9-7f9a0b85ef64"
PLANT_SPIRIT = next(s["id"] for s in catalog()["spirits"] if s["name"] == "Plant Spirit")


def _drug_state(active: bool, gear_id: str = JAZZ) -> CharacterState:
    return CharacterState(
        id="drug",
        name="Drug",
        priorities=Priorities(Heritage="C", Attributes="A", Talent="E", Skills="B", Resources="D"),
        metatype="Human",
        attributes={
            "BOD": 3,
            "AGI": 3,
            "REA": 4,
            "STR": 3,
            "WIL": 3,
            "LOG": 3,
            "INT": 3,
            "CHA": 3,
            "EDG": 3,
            "MAG": 0,
            "RES": 0,
            "ESS": 6,
        },
        gear=[GearInstall(gear_id=gear_id, active=active)],
    )


NOVACOKE = "836f54d5-1e11-49ea-b115-34c14ed843c9"  # `<quality rating="1">High Pain Tolerance`
REFLEX_RECORDER_OPTIMIZATION = "afe25e41-8d6c-4476-9d18-ecd23219207c"


def _quality_id(name: str) -> str:
    return next(q["id"] for q in catalog()["qualities"] if q["name"] == name)


def _surge_thirty(cid: str, *, changeling: bool = True) -> CharacterState:
    """30 karma of metagenic qualities each way — the most Class I allows."""
    names = [
        "Metagenic Improvement (Agility)",  # +15
        "Dermal Alteration (Granite Shell)",  # +15
        "Deformity (Quasimodo)",  # -15
        "Adiposis",  # -10
        "Astral Hazing",  # -5
    ]
    ids = [_quality_id(n) for n in names]
    return _mundane(cid, quality_ids=[CHANGELING_I, *ids] if changeling else ids)


CYBERLIMB_OPTIMIZATION = "2a6ab1b1-f008-4c92-83d9-a298a5dad855"  # CF p.87


def _optimized_arm(**kwargs: object) -> CharacterState:
    arm = next(w for w in catalog()["cyberware"]["items"] if w["name"] == "Obvious Full Arm")
    return _human(
        "optimized",
        cyberware=[
            CyberwareInstall(id="arm", ware_id=arm["id"], side="Left"),
            CyberwareInstall(id="opt", ware_id=CYBERLIMB_OPTIMIZATION, parent_id="arm"),
        ],
        weapons=[WeaponInstall(id="w", weapon_id=PREDATOR)],
        **kwargs,
    )


def _ware_id(kind: str, name: str) -> str:
    return next(str(w["id"]) for w in catalog()[kind]["items"] if w["name"] == name)


def _quality_row(out: dict, name: str) -> dict:
    return next(q for q in out["qualities"] if q["name"] == name)


def _career_quality(name: str) -> dict:
    return next(q for q in catalog()["qualities"] if q["name"] == name)


def _into_career(name: str, quality_ids: list[str]):
    from app.engine import snapshot_career_baseline

    st = compute(_mundane(name, quality_ids=quality_ids))
    st.career = True
    st.career_baseline = snapshot_career_baseline(st)
    return st


def _ware_named(name: str) -> str:
    return next(item["id"] for item in catalog()["cyberware"]["items"] if item["name"] == name)


def _armor_mod_named(name: str) -> str:
    return next(item["id"] for item in catalog()["armor_mods"] if item["name"] == name)
