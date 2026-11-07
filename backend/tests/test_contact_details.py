"""A contact's own description — where, who, what they want, notes — goes
through a .chum5 as Chummer saves it (`Contact.Save` / `Contact.Load`).

Nothing is computed from these; they only have to come back."""

import xml.etree.ElementTree as ET

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute
from app.models import CharacterState, ContactInstall
from app.models.social import CONTACT_DETAIL_TAGS
from tests.engine_support import _mundane

DETAILS = {
    "location": "Seattle, Redmond Barrens ",
    "metatype": "Ork",
    "gender": "Female",
    "age": "Middle-aged",
    "contact_type": "Fixer",
    "preferred_payment": "Cash (Credstick)",
    "hobbies_vice": "Drugs (BTLs)",
    "personal_life": "Divorced",
    "notes": "Owes us one.\n\nNever call before noon.\n",
}


def _state(**details: str) -> CharacterState:
    return compute(_mundane("contacts", contacts=[ContactInstall(id="c", name="Dodger", role="Fixer", **details)]))


def _contact_xml(state: CharacterState) -> ET.Element:
    root = ET.fromstring(state_to_chum5(state))
    return next(el for el in root.iter("contact") if el.findtext("name") == "Dodger")


def _reimport(xml: bytes) -> ContactInstall:
    state = CharacterState.model_validate(chum5_to_state(xml)[0])
    return next(row for row in state.contacts if row.name == "Dodger")


def test_every_field_is_written_under_chummers_name() -> None:
    el = _contact_xml(_state(**DETAILS))
    for field, tag in CONTACT_DETAIL_TAGS.items():
        assert el.findtext(tag) == DETAILS[field], tag


def test_every_field_comes_back_as_it_was_written() -> None:
    """Trailing spaces and line breaks included: it is the player's text."""
    back = _reimport(state_to_chum5(_state(**DETAILS)))
    assert {field: getattr(back, field) for field in DETAILS} == DETAILS


def test_an_empty_field_is_not_written() -> None:
    el = _contact_xml(_state(age="Young"))
    assert el.findtext("age") == "Young"
    assert el.find("notes") is None
    assert el.find("location") is None


def test_the_details_cost_nothing() -> None:
    plain = _state()
    described = _state(**DETAILS)
    assert described.derived["contact_points"] == plain.derived["contact_points"]
    assert described.derived["karma"] == plain.derived["karma"]


def _with(el_changes: dict[str, str]) -> bytes:
    root = ET.fromstring(state_to_chum5(_state()))
    contact = next(el for el in root.iter("contact") if el.findtext("name") == "Dodger")
    for tag, text in el_changes.items():
        ET.SubElement(contact, tag).text = text
    return ET.tostring(root)


def test_an_old_save_names_the_gender_sex() -> None:
    """Chummer still reads `<sex>` when there is no `<gender>`."""
    assert _reimport(_with({"sex": "Male"})).gender == "Male"


def test_gender_wins_over_sex() -> None:
    assert _reimport(_with({"gender": "Female", "sex": "Male"})).gender == "Female"


def test_whitespace_alone_is_nothing() -> None:
    back = _reimport(_with({"notes": "  \n ", "location": "\t"}))
    assert (back.notes, back.location) == ("", "")
