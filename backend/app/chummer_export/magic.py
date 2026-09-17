"""Magic and resonance: tradition or stream, mentor, spells, adept powers,
complex forms, spirits, enhancements and initiation.

The mirror of :mod:`app.chummer_import.magic`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from ..models import CharacterState
from ._common import _Ctx, _Names, _sub


def _export_spell_lists(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """`<spells>`, `<powers>` and `<complexforms>` — three lists of the same
    shape, each an id and the name that id resolves to."""

    def _named_list(
        container: str,
        item: str,
        rows: list[Any],
        id_key: str,
        bag: str,
        extra: dict[str, Any] | None = None,
    ) -> ET.Element:
        parent = _sub(root, container)
        for row in rows:
            iid = getattr(row, id_key)
            el = _sub(parent, item)
            _sub(el, "sourceid", iid)
            _sub(el, "name", names[bag].get(iid, ""))
            for k, fn in (extra or {}).items():
                _sub(el, k, fn(row))
        return parent

    _named_list(
        "spells",
        "spell",
        state.spells,
        "spell_id",
        "spell",
        {"alchemical": lambda r: "True" if r.alchemical else "False"},
    )
    _named_list(
        "powers",
        "power",
        state.adept_powers,
        "power_id",
        "power",
        {"rating": lambda r: r.rating, "extra": lambda r: r.extra or ""},
    )
    _named_list(
        "complexforms",
        "complexform",
        state.complex_forms,
        "form_id",
        "complexform",
        {"rating": lambda r: r.level or 1, "extra": lambda r: r.extra or ""},
    )


def _export_magic_tradition(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """The tradition, stream or mentor spirit a magician or technomancer has."""
    if state.tradition_id:
        tr = _sub(root, "tradition")
        _sub(tr, "guid", state.tradition_id)
        _sub(tr, "name", names["tradition"].get(state.tradition_id, ""))
    if state.stream_id:
        # A technomancer's stream is a tradition-shaped thing of its own;
        # Chummer reads it from `<stream>`.
        _sub(root, "stream", names["stream"].get(state.stream_id, ""))
    if state.mentor_id:
        me = _sub(root, "mentorspirit")
        _sub(me, "guid", state.mentor_id)
        _sub(me, "name", names["mentor"].get(state.mentor_id, ""))
        # Chummer holds at most two mentor picks, in two fixed fields. This app
        # keeps a list plus a map of what each pick resolved to, so the pair of
        # lists below is what actually round-trips; the two fields mirror the
        # first two picks so Chummer has something to show.
        for index, tag in enumerate(("extrachoice1", "extrachoice2")):
            _sub(me, tag, state.mentor_choices[index] if index < len(state.mentor_choices) else "")
        choices = _sub(me, "choices")
        for picked in state.mentor_choices:
            _sub(choices, "choice", picked)
        extras = _sub(me, "extras")
        for key, value in sorted(state.mentor_extras.items()):
            row = _sub(extras, "extra")
            _sub(row, "key", key)
            _sub(row, "value", value)


def _export_spirits(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write bound spirits and registered sprites into one `<spirits>`.

    Chummer keeps both in the same list and tells them apart by `<type>`; a
    sprite's Level is its `<force>`. The hits of the summoning/compiling test
    are this app's own and ride along as extra children.
    """
    spirits = _sub(root, "spirits")
    for srow in state.spirits:
        el = _sub(spirits, "spirit")
        _sub(el, "guid", srow.id)
        _sub(el, "name", names["spirit"].get(srow.spirit_id, ""))
        _sub(el, "type", "Spirit")
        _sub(el, "force", srow.force)
        _sub(el, "services", srow.services)
        _sub(el, "bound", "True" if srow.bound else "False")
        _sub(el, "fettered", "False")
        if srow.hits is not None:
            _sub(el, "hits", srow.hits)
        if srow.opposed_hits is not None:
            _sub(el, "opposedhits", srow.opposed_hits)
    for prow in state.sprites:
        el = _sub(spirits, "spirit")
        _sub(el, "guid", prow.id)
        _sub(el, "name", names["sprite"].get(prow.sprite_id, ""))
        _sub(el, "type", "Sprite")
        _sub(el, "force", prow.level)
        _sub(el, "services", prow.services)
        _sub(el, "bound", "True" if prow.registered else "False")
        _sub(el, "fettered", "False")
        if prow.hits is not None:
            _sub(el, "hits", prow.hits)
        if prow.opposed_hits is not None:
            _sub(el, "opposedhits", prow.opposed_hits)


def _export_enhancements(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write the adept-power enhancements (`<enhancements>`)."""
    el = _sub(root, "enhancements")
    for eid in state.adept_enhancements:
        row = _sub(el, "enhancement")
        _sub(row, "sourceid", eid)
        _sub(row, "name", names["enhancement"].get(eid, ""))


def _export_initiation(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write initiation and submersion grades, and the metamagics on them."""
    grades = _sub(root, "initiationgrades")
    init_by_grade = {int(c.grade): c for c in state.initiations}
    sub_by_grade = {int(c.grade): c for c in state.submersions}

    def _emit_grade(i: int, res: bool, choice: object) -> None:
        grade_el = _sub(grades, "initiationgrade")
        _sub(grade_el, "grade", i)
        _sub(grade_el, "res", "True" if res else "False")
        _sub(grade_el, "group", "True" if getattr(choice, "group", False) else "False")
        _sub(grade_el, "ordeal", "True" if getattr(choice, "ordeal", False) else "False")
        _sub(grade_el, "schooling", "True" if getattr(choice, "schooling", False) else "False")

    for i in range(1, state.initiate_grade + 1):
        _emit_grade(i, False, init_by_grade.get(i))
    for i in range(1, state.submersion_grade + 1):
        _emit_grade(i, True, sub_by_grade.get(i))
    mms = _sub(root, "metamagics")
    for ic in state.initiations:
        el = _sub(mms, "metamagic")
        _sub(el, "sourceid", ic.option_id)
        _sub(el, "name", names["metamagic"].get(ic.option_id) or names["art"].get(ic.option_id, ""))
