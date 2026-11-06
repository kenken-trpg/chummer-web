"""The `...nonretroactive` essence multipliers in career: each piece keeps the
ones it was bought under (Chummer's `<extraessadditivemultiplier>` /
`<extraessmultiplicativemultiplier>`, `Cyberware.SaveNonRetroactiveEssenceModifiers`).

Only Chummer's own "Adapsin Applied as Multiplier, Not Grade" pack grants
one, so these run under it: Adapsin is then
`<cyberwaretotalessmultipliernonretroactive>90`, and an Alphaware arm is
0.8 without it and 0.72 under it.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from app import dataset_store
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.customdata import dataset_hash
from app.data_loader import reset_catalog
from app.engine import compute, snapshot_career_baseline
from app.models import CharacterState, CyberwareInstall
from tests.engine_support import _mundane, _ware_id
from tests.test_customdata_adapsin_multiplier import _KEY, _PACK


@pytest.fixture
def pack() -> Iterator[None]:
    dataset = dataset_hash(_PACK)
    dataset_store.remember(dataset, [_KEY], _PACK)
    reset_catalog()
    try:
        yield
    finally:
        reset_catalog()
        dataset_store.reset()


def _under_pack(state: CharacterState) -> CharacterState:
    state.settings = state.settings.model_copy(update={"customdata": [_KEY], "dataset": dataset_hash(_PACK)})
    return compute(state)


def _arm(arm_id: str = "arm") -> CyberwareInstall:
    return CyberwareInstall(id=arm_id, ware_id=_ware_id("cyberware", "Obvious Full Arm"), grade="Alphaware")


def _adapsin() -> CyberwareInstall:
    return CyberwareInstall(id="ad", ware_id=_ware_id("bioware", "Adapsin"))


def _built(*, adapsin: bool) -> CharacterState:
    return _mundane("nonretro", cyberware=[_arm()], bioware=[_adapsin()] if adapsin else [])


def _career(state: CharacterState) -> CharacterState:
    state = _under_pack(state)
    state.career = True
    state.career_baseline = snapshot_career_baseline(state)
    return _under_pack(state)


def _again(state: CharacterState, **change: object) -> CharacterState:
    """The state as a client would send it back, with `change` written over."""
    data = state.model_dump()
    data.update(change)
    return _under_pack(CharacterState.model_validate(data))


def _essence(state: CharacterState) -> dict[str, float]:
    return {str(row["id"]): float(row["essence"]) for row in state.derived["cyberware"]}


def _held(state: CharacterState, ware_id: str) -> tuple[float | None, float | None]:
    [row] = [row for row in state.cyberware + state.bioware if row.id == ware_id]
    return row.ess_extra_additive, row.ess_extra_multiplicative


def test_in_chargen_the_bonus_counts_live_and_nothing_is_held(pack: None) -> None:
    st = _under_pack(_built(adapsin=True))
    assert _essence(st) == {"arm": 0.72}
    assert _held(st, "arm") == (None, None)


def test_entering_career_keeps_what_each_piece_had(pack: None) -> None:
    st = _career(_built(adapsin=True))
    assert _essence(st) == {"arm": 0.72}
    assert _held(st, "arm") == (0.0, 0.9)
    # Adapsin's bonus is a cyberware one: bioware holds none of it
    assert _held(st, "ad") == (0.0, 1.0)


def test_taking_adapsin_out_in_career_leaves_the_arm_as_it_was(pack: None) -> None:
    st = _career(_built(adapsin=True))
    gone = _again(st, bioware=[])
    assert _essence(gone) == {"arm": 0.72}
    # and an arm bought after it went takes none
    more = _again(gone, cyberware=[row.model_dump() for row in gone.cyberware] + [_arm("new").model_dump()])
    assert _essence(more) == {"arm": 0.72, "new": 0.8}


def test_adapsin_bought_in_career_counts_on_ware_bought_after_it(pack: None) -> None:
    st = _career(_built(adapsin=False))
    assert _essence(st) == {"arm": 0.8}
    with_adapsin = _again(st, bioware=[_adapsin().model_dump()])
    assert _essence(with_adapsin) == {"arm": 0.8}
    more = _again(
        with_adapsin, cyberware=[row.model_dump() for row in with_adapsin.cyberware] + [_arm("new").model_dump()]
    )
    assert _essence(more) == {"arm": 0.8, "new": 0.72}
    assert _held(more, "new") == (0.0, 0.9)


def test_back_in_chargen_the_held_values_are_dropped(pack: None) -> None:
    st = _career(_built(adapsin=False))
    back = _again(st, career=False, career_baseline=None, bioware=[_adapsin().model_dump()])
    assert _held(back, "arm") == (None, None)
    assert _essence(back) == {"arm": 0.72}


def test_a_career_save_keeps_the_held_values_through_chum5(pack: None) -> None:
    st = _career(_built(adapsin=True))
    xml = state_to_chum5(st)
    assert b"<extraessmultiplicativemultiplier>0.9</extraessmultiplicativemultiplier>" in xml
    raw, _ = chum5_to_state(xml)
    back = CharacterState.model_validate(raw)
    [arm] = back.cyberware
    assert (arm.ess_extra_additive, arm.ess_extra_multiplicative) == (0.0, 0.9)
    # and the arm keeps 0.72 with Adapsin taken out
    assert _essence(_again(back, bioware=[])) == {str(arm.id): 0.72}


def test_a_chargen_save_holds_nothing() -> None:
    st = compute(_built(adapsin=False))
    raw, _ = chum5_to_state(state_to_chum5(st))
    [arm] = CharacterState.model_validate(raw).cyberware
    assert (arm.ess_extra_additive, arm.ess_extra_multiplicative) == (None, None)
