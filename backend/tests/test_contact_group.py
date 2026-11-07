"""A group contact goes through a .chum5 as Chummer saves it: `<type>` is
Contact / Enemy / Pet (`Contact.ConvertToContactType` reads anything else as
an Enemy) and the group is `<group>` (`Contact.IsGroup`).

This app once wrote `<type>Group</type>`, which Chummer opened as an Enemy
with no group, and read only its own spelling back, so Chummer's group
contacts came in as ordinary ones."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute
from app.models import CharacterState, ContactInstall
from tests.engine_support import _mundane

_SAVES = Path(__file__).resolve().parents[1] / "vendor" / "chummer-tests"


def _state() -> CharacterState:
    return _mundane(
        "group-contact",
        contacts=[
            ContactInstall(name="The Ancients", role="Gang", connection=3, loyalty=1, group=True),
            ContactInstall(name="Sam", role="Fixer", connection=2, loyalty=2),
        ],
    )


def _contacts(root: ET.Element) -> list[tuple[str, str, str]]:
    return [
        (c.findtext("name") or "", c.findtext("type") or "", c.findtext("group") or "")
        for c in root.findall("./contacts/contact")
    ]


def test_written_as_chummer_reads_it() -> None:
    root = ET.fromstring(state_to_chum5(compute(_state())))
    assert _contacts(root) == [("The Ancients", "Contact", "True"), ("Sam", "Contact", "False")]


def test_read_back() -> None:
    back = CharacterState.model_validate(chum5_to_state(state_to_chum5(compute(_state())))[0])
    assert [(c.name, c.group) for c in back.contacts] == [("The Ancients", True), ("Sam", False)]


def test_this_apps_older_exports_still_read() -> None:
    root = ET.fromstring(state_to_chum5(compute(_state())))
    for c in root.findall("./contacts/contact"):
        if c.findtext("group") == "True":
            c.find("type").text = "Group"  # type: ignore[union-attr]
        c.remove(c.find("group"))  # type: ignore[arg-type]
    back = CharacterState.model_validate(chum5_to_state(ET.tostring(root))[0])
    assert [(c.name, c.group) for c in back.contacts] == [("The Ancients", True), ("Sam", False)]


@pytest.mark.skipif(not _SAVES.exists(), reason="Chummer's test saves are fetched by `make reconcile`; absent in CI")
def test_chummers_own_group_contact() -> None:
    """Ushi Resub's fixer is the one group contact in Chummer's test saves."""
    raw = next(_SAVES.rglob("Ushi Resub.chum5")).read_bytes()
    state = CharacterState.model_validate(chum5_to_state(raw)[0])
    assert [c.name for c in state.contacts if c.group] == ["Shi no dairinin"]
    exported = ET.fromstring(state_to_chum5(compute(state)))
    assert ("Shi no dairinin", "Contact", "True") in _contacts(exported)
    assert {kind for _, kind, _ in _contacts(exported)} == {"Contact"}
