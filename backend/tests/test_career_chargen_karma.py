"""Karma paid at chargen stays paid in career (`compute/_career_items.py`).

Chummer never gives chargen karma back when something is deleted; this app
worked karma out again from what is held, so it did.
"""

from app.engine import compute, snapshot_career_baseline
from app.models import CharacterState, ContactInstall, SpiritInstall
from tests.engine_support import HERMETIC, SPIRIT_FIRE, _mage, _mundane


def _career(state: CharacterState) -> CharacterState:
    state = compute(state)
    state.career = True
    state.career_baseline = snapshot_career_baseline(state)
    return compute(state)


def _left(state: CharacterState) -> int:
    return int(compute(state).derived["karma"]["remaining"])


def _spent(derived: dict, key: str) -> int:
    return sum(int(row["amount"]) for row in derived["karma_spend_breakdown"] if row["notice"]["key"] == key)


def _contacts() -> list[ContactInstall]:
    # 12 points against CHA 1's 3 free: 9 karma at chargen
    return [
        ContactInstall(name="Fixer", connection=3, loyalty=3),
        ContactInstall(name="Doc", connection=3, loyalty=3),
    ]


def test_a_contact_dropped_in_career_gives_no_karma_back() -> None:
    st = _career(_mundane("ck-contact-drop", contacts=_contacts()))
    before = _left(st)
    assert _spent(st.derived, "engine.spend.contactsOver") == 9
    st.contacts = st.contacts[:1]
    assert _left(st) == before


def test_a_contact_added_or_raised_in_career_costs_no_karma() -> None:
    """Chummer's `AddContact` makes no expense; contact points are chargen only."""
    st = _career(_mundane("ck-contact-add", contacts=_contacts()))
    before = _left(st)
    st.contacts[0].loyalty = 6
    st.contacts.append(ContactInstall(name="Talismonger", connection=4, loyalty=4))
    out = compute(st).derived
    assert out["karma"]["remaining"] == before
    assert _spent(out, "engine.spend.contactsOver") == 9


def test_spirit_services_used_or_the_spirit_sent_away_give_no_karma_back() -> None:
    st = _career(
        _mage(
            "ck-spirit",
            tradition_id=HERMETIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, services=2)],
        )
    )
    before = _left(st)
    st.spirits[0].services = 1
    assert _left(st) == before
    st.spirits = []
    assert _left(st) == before


def test_the_record_is_made_on_the_first_career_pass_and_kept() -> None:
    st = _career(_mundane("ck-record", contacts=_contacts()))
    assert st.career_baseline is not None
    assert st.career_baseline.chargen_karma == {"contacts": {"points": 9}, "spirits": {}}


def test_dropping_the_record_takes_what_is_held_now_as_chargen() -> None:
    """The way back for a player who mistyped at chargen: a baseline without
    the record is recorded again from what is held."""
    st = _career(_mundane("ck-reset", contacts=_contacts()))
    before = _left(st)
    st.contacts = st.contacts[:1]
    assert st.career_baseline is not None
    st.career_baseline.chargen_karma = None
    assert _left(st) == before + 6


def test_outside_career_dropping_a_contact_still_gives_the_karma_back() -> None:
    st = compute(_mundane("ck-chargen", contacts=_contacts()))
    before = int(st.derived["karma"]["remaining"])
    st.contacts = st.contacts[:1]
    assert _left(st) == before + 6
