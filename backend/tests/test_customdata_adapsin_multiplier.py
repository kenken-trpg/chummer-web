"""Chummer's own "Adapsin Applied as Multiplier, Not Grade" custom data, and
the file names it and other bundled packs use.

The pack swaps Adapsin's `<adapsin />` (the grade swap: Alphaware becomes
Alphaware (Adapsin), 0.7) for `<cyberwaretotalessmultipliernonretroactive>90`
(Alphaware's 0.8 times 0.9, 0.72). Its file is
`amend_AdapsinMultiplier_bioware.xml`: Chummer reads every `*_bioware.xml`
beside `bioware.xml` (`XmlManager`), so the tag in the middle is allowed, and
this app used to drop the file as data it does not load. The test save
Bastion is built under it (essence 1.00 in Chummer, 1.04 here before).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app import dataset_store
from app.chummer_import import chum5_to_state
from app.customdata import base_files_of, build_overlay, dataset_hash
from app.data_loader import reset_catalog
from app.engine import compute
from app.engine.pricing import apply_ware_essence_multipliers
from app.improvements import empty_effects
from app.models import CharacterState, CyberwareInstall
from tests.engine_support import _mundane, _ware_id

_MANIFEST = b"<manifest><guid>af931dbd-78d0-4808-9c1a-067a7293dd1c</guid><version>1</version></manifest>"
_AMEND = b"""<chummer><biowares><bioware><name>Adapsin</name><bonus>
<adapsin amendoperation="remove" />
<cyberwaretotalessmultipliernonretroactive>90</cyberwaretotalessmultipliernonretroactive>
</bonus></bioware></biowares></chummer>"""
_KEY = "af931dbd-78d0-4808-9c1a-067a7293dd1c>1"
_PACK = {
    "Adapsin Applied as Multiplier, Not Grade/manifest.xml": _MANIFEST,
    "Adapsin Applied as Multiplier, Not Grade/amend_AdapsinMultiplier_bioware.xml": _AMEND,
}


def _under_pack(state: CharacterState) -> CharacterState:
    """`state` computed under the pack, the way a request that names it is."""
    dataset = dataset_hash(_PACK)
    _, report = dataset_store.remember(dataset, [_KEY], _PACK)
    assert report.applied == 1
    state = state.model_copy(deep=True)
    state.settings = state.settings.model_copy(update={"customdata": [_KEY], "dataset": dataset})
    reset_catalog()
    try:
        return compute(state)
    finally:
        reset_catalog()
        dataset_store.reset()


def _arm_essence(state: CharacterState) -> float:
    [arm] = state.derived["cyberware"]
    return float(arm["essence"])


def _adapsin_and_an_arm() -> CharacterState:
    return _mundane(
        "adapsin",
        cyberware=[CyberwareInstall(id="arm", ware_id=_ware_id("cyberware", "Obvious Full Arm"), grade="Alphaware")],
        bioware=[CyberwareInstall(id="ad", ware_id=_ware_id("bioware", "Adapsin"))],
    )


def test_a_file_with_a_tag_before_its_data_file_is_merged_into_that_file() -> None:
    _, report = build_overlay(_PACK, [_KEY])
    assert [(c.file, c.entry) for c in report.changes] == [("bioware.xml", "Adapsin")]
    assert report.ignored == []


@pytest.mark.parametrize(
    ("filename", "base"),
    [
        ("amend_german_books.xml", "books.xml"),
        ("custom_energy_weapons.xml", "weapons.xml"),
        ("amend_cyberlimbheadware_cyberware.xml", "cyberware.xml"),
        ("custom_qualities.xml", "qualities.xml"),
    ],
)
def test_other_bundled_packs_names_reach_their_data_file(filename: str, base: str) -> None:
    assert base_files_of(filename)[-1] == base
    assert base_files_of("manifest.xml") == []


def test_a_tagged_file_for_data_this_app_lacks_is_still_set_apart() -> None:
    files = {
        "d/manifest.xml": b"<manifest><guid>g</guid><version>1</version></manifest>",
        "d/amend_sprite_critters.xml": b"<chummer><critters /></chummer>",
    }
    _, report = build_overlay(files, ["g>1"])
    assert report.ignored == ["critters.xml"]
    assert report.skipped == []


def test_without_the_pack_adapsin_is_a_grade() -> None:
    assert _arm_essence(compute(_adapsin_and_an_arm())) == 0.7


def test_under_the_pack_adapsin_multiplies_the_grade() -> None:
    assert _arm_essence(_under_pack(_adapsin_and_an_arm())) == 0.72


def test_a_bioware_total_multiplier_reaches_bioware_only() -> None:
    cyber = [{"id": "c", "ess_raw": 1.0, "ess_grade": 1.0, "ess_self": True}]
    bio = [{"id": "b", "ess_raw": 1.0, "ess_grade": 1.0, "ess_self": True}]
    effects = empty_effects()
    effects["bioware_total_ess_multiplier"] = 50
    assert apply_ware_essence_multipliers(cyber, bio, effects) == (1.0, 0.5)


_BASTION = next(
    iter((Path(__file__).resolve().parents[1] / "vendor" / "chummer-tests").glob("*/Bastion.chum5")),
    None,
)


@pytest.mark.skipif(_BASTION is None, reason="the Chummer test saves are not fetched (make reconcile)")
def test_bastion_has_the_essence_chummer_saved() -> None:
    assert _BASTION is not None
    raw, _ = chum5_to_state(_BASTION.read_bytes())
    state = CharacterState.model_validate(raw)
    assert float(compute(state).derived["essence"]) == 1.04
    # `<totaless>1.00</totaless>` in the save
    assert float(_under_pack(state).derived["essence"]) == 1.0
