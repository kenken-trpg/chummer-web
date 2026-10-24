"""Magic and resonance: tradition or stream, mentor, spells, adept powers,
complex forms, spirits, enhancements and initiation.

The mirror of :mod:`app.chummer_import.magic`.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from typing import Any

from ..data_loader._xml import parse_data
from ..engine.lookups import _mentor_by_id, _paragon_by_id, _stream_by_id, _tradition_by_id
from ..models import CharacterState
from ._common import _Ctx, _Names, _sub
from .improvements import _bonus_improvements, _with_rows, _write_improvements

#: Chummer's `Tradition.CustomMagicalTraditionGuidString`, the row in
#: `traditions.xml` that stands for "a tradition of the player's own". It
#: carries no drain expression, so this app's catalogue drops it — it is not
#: something to pick — but Chummer gives every magic-enabled character one as
#: a placeholder, so the export has to name it by id.
_CUSTOM_TRADITION_ID = "616ba093-306c-45fc-8f41-0b98c8cccb46"


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
        # the guid the power's improvements name it by
        {"guid": lambda r: r.id, "rating": lambda r: r.rating, "extra": lambda r: r.extra or ""},
    )
    _export_power_improvements(root, state)
    _named_list(
        "complexforms",
        "complexform",
        state.complex_forms,
        "form_id",
        "complexform",
        {"rating": lambda r: r.level or 1, "extra": lambda r: r.extra or ""},
    )


def _export_power_improvements(root: ET.Element, state: CharacterState) -> None:
    """What `Power.Create` leaves in `<improvements>` when it runs an adept
    power's `<bonus>` at its rating, under the power's guid — Chummer never
    runs it again on load. A power's pick (Improved Ability's skill,
    Improved Physical Attribute's attribute) is its extra."""
    definitions = {node.findtext("id") or "": node for node in parse_data("powers.xml").findall("./powers/power")}
    for row in state.adept_powers:
        definition = definitions.get(row.power_id)
        bonus = definition.find("bonus") if definition is not None else None
        if definition is None or bonus is None:
            continue
        rows = _bonus_improvements(bonus, int(row.rating or 1), row.extra or "")
        _write_improvements(root, _with_rows(root, rows, row.id, definition.findtext("name") or ""), row.id, "Power")


def _export_tradition_block(root: ET.Element, state: CharacterState, ctx: _Ctx) -> None:
    """Write `<tradition>` the way Chummer's own `Tradition.Save` does.

    `Tradition.Load` starts with `traditiontype` and **gives up on the whole
    element** if it is missing::

        if (!xmlNode.TryGetStringFieldQuickly("traditiontype", ref strTemp)
            || !Enum.TryParse(strTemp, out _eTraditionType))
        { _eTraditionType = TraditionType.None; return; }

    and `Character.Load` reaches that loader as soon as the element carries a
    `<guid>` — which is all this app used to write, alongside the name. So
    every magician exported from here opened in Chummer with **no tradition at
    all**: no drain attributes, no spirit types. The rest of the fields are
    written because Chummer keeps the tradition's own copy of them rather than
    looking them up again (a player may edit them), and a Custom tradition has
    nothing to look up.

    A technomancer's stream is the same element with `RES` as its type: the
    five spirit fields stay empty and the sprites it can compile are the
    `<spirits>` list. `<stream>`, the pre-5.200 spelling, is no longer written
    — Chummer prefers it over `<tradition>` when both are there, and it can
    only say the stream's name.
    """
    row = _tradition_by_id(state.tradition_id) or _stream_by_id(state.stream_id)
    if not row:
        # An adept has Magic and no tradition to go with it. Chummer still
        # holds one — the Custom row, every field of it blank — and writes it
        # out, so an export without the element is a field Chummer states and
        # this app does not. Written with its own id and nothing else, which
        # is what Chummer's own saves say (`prime.chum5`).
        if "MAG" in set(ctx["derived"].get("enabled_tabs") or []):
            _export_custom_tradition_block(root)
        return
    is_stream = not state.tradition_id
    spirits = row.get("spirits") or {}
    el = _sub(root, "tradition")
    # Chummer tells the data row (`sourceid`) from this character's copy of it
    # (`guid`) because a Custom tradition is edited per character; nothing here
    # is editable, so the two are the same id.
    _sub(el, "sourceid", row["id"])
    _sub(el, "guid", row["id"])
    _sub(el, "traditiontype", "RES" if is_stream else "MAG")
    _sub(el, "name", row.get("name") or "")
    _sub(el, "extra", "")
    # Possession for the traditions that say so in `traditions.xml`,
    # Materialization for the rest — Chummer's own default.
    _sub(el, "spiritform", row.get("spirit_form") or "Materialization")
    # Braced, as `traditions.xml` writes it. Chummer un-braces the expression
    # on the way out, but only repairs a brace-less one for saves older than
    # 5.214.77 — and this app stamps a current version.
    _sub(el, "drain", row.get("drain") or "")
    _sub(el, "source", row.get("source") or "")
    _sub(el, "page", row.get("page") or "")
    for tag, key in (
        ("spiritcombat", "combat"),
        ("spiritdetection", "detection"),
        ("spirithealth", "health"),
        ("spiritillusion", "illusion"),
        ("spiritmanipulation", "manipulation"),
    ):
        _sub(el, tag, spirits.get(key) or "")
    available = _sub(el, "spirits")
    for name in row.get("sprites") or []:
        _sub(available, "spirit", name)


def _export_custom_tradition_block(root: ET.Element) -> None:
    """The blank Custom tradition Chummer keeps for a character who has Magic
    but picked no tradition — an adept.

    `Tradition.Save`'s fields with `Tradition.ResetTradition`'s values: the
    name, drain and spirits empty, `spiritform` Chummer's default, and the
    source and page of the Custom row in `traditions.xml`. What matters is
    that `traditiontype` is there at all, since `Tradition.Load` gives up on
    the element without it.
    """
    el = _sub(root, "tradition")
    _sub(el, "sourceid", _CUSTOM_TRADITION_ID)
    _sub(el, "guid", _CUSTOM_TRADITION_ID)
    _sub(el, "traditiontype", "MAG")
    for tag in ("name", "extra"):
        _sub(el, tag, "")
    _sub(el, "spiritform", "Materialization")
    _sub(el, "drain", "")
    _sub(el, "source", "SR5")
    _sub(el, "page", "279")
    for tag in ("spiritcombat", "spiritdetection", "spirithealth", "spiritillusion", "spiritmanipulation"):
        _sub(el, tag, "")
    _sub(el, "spirits")


def _export_mentor_block(root: ET.Element, state: CharacterState, names: _Names, mentor_id: str) -> None:
    """Write the mentor spirit where Chummer looks for it, with the fields it reads.

    `Character.Load` collects mentors with
    `SelectNodes("mentorspirits/mentorspirit")` — a top-level `<mentorspirit>`,
    which is all this app used to write, is never seen, so every exported
    character opened in Chummer.exe with no mentor at all.

    The fields are `MentorSpirit.Save`'s. `mentortype` decides which data file
    Chummer resolves the mentor in (`MentorSpirit` → mentors.xml, `Paragon` →
    paragons.xml), and `sourceid` is the id it resolves there; `guid` is this
    character's own copy of it, and `id` is the same source id again, the older
    spelling Chummer still writes. `choice1` / `choice2` carry the raw bonus
    XML of the picks, which this app keeps in parsed form; the picks themselves
    ride in `extrachoice1` / `extrachoice2`, which is what Chummer reads back.
    """
    mentor = _mentor_by_id(mentor_id)
    is_paragon = mentor is None
    if is_paragon:
        mentor = _paragon_by_id(mentor_id)
    row = mentor or {}
    parent = _sub(root, "mentorspirits")
    el = _sub(parent, "mentorspirit")
    _sub(el, "sourceid", mentor_id)
    _sub(el, "guid", mentor_id)
    _sub(el, "name", names["mentor"].get(mentor_id, "") or row.get("name") or "")
    _sub(el, "mentortype", "Paragon" if is_paragon else "MentorSpirit")
    _sub(el, "extra", "")
    # Chummer holds at most two mentor picks, in two fixed fields. This app
    # keeps a list plus a map of what each pick resolved to, so the pair of
    # lists below is what actually round-trips; the two fields mirror the
    # first two picks so Chummer has something to show.
    for index, tag in enumerate(("extrachoice1", "extrachoice2")):
        _sub(el, tag, state.mentor_choices[index] if index < len(state.mentor_choices) else "")
    _sub(el, "source", row.get("source") or "")
    _sub(el, "page", row.get("page") or "")
    _sub(el, "advantage", row.get("advantage") or "")
    _sub(el, "disadvantage", row.get("disadvantage") or "")
    # Mentor's Mask is a quality this app does not model, so it is never on.
    _sub(el, "mentormask", "False")
    # Chummer falls back to the data file for an empty `bonus`, and an empty
    # `choice1` / `choice2` is what it writes for a mentor without picks.
    for tag in ("bonus", "choice1", "choice2"):
        _sub(el, tag, "")
    _sub(el, "notes", "")
    _sub(el, "id", mentor_id)
    # This app's own round-trip: the picks in full, and what each resolved to.
    choices = _sub(el, "choices")
    for picked in state.mentor_choices:
        _sub(choices, "choice", picked)
    extras = _sub(el, "extras")
    for key, value in sorted(state.mentor_extras.items()):
        extra_row = _sub(extras, "extra")
        _sub(extra_row, "key", key)
        _sub(extra_row, "value", value)


def _export_magic_tradition(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """The tradition, stream or mentor spirit a magician or technomancer has."""
    _export_tradition_block(root, state, ctx)
    if state.mentor_id:
        _export_mentor_block(root, state, names, state.mentor_id)
        _export_mentor_improvements(root, state, "adept" in set(ctx["derived"].get("enabled_tabs") or []))


def _export_mentor_improvements(root: ET.Element, state: CharacterState, adept: bool) -> None:
    """What `MentorSpirit.Create` leaves in `<improvements>`: the mentor's own
    `<bonus>` and each picked choice's, under the mentor's guid (its id, see
    `_export_mentor_block`). Free power levels go to an adept only, as
    `specificpower` checks. A paragon's are not written yet."""
    definition = next(
        (
            node
            for node in parse_data("mentors.xml").findall("./mentors/mentor")
            if node.findtext("id") == state.mentor_id
        ),
        None,
    )
    if definition is None:
        return
    bonuses = [("", definition.find("bonus"))]
    bonuses += [
        (choice.findtext("name") or "", choice.find("bonus"))
        for choice in definition.findall("./choices/choice")
        if choice.findtext("name") in state.mentor_choices
    ]
    extras = state.mentor_extras or {}
    # a power whose bonus asks for a pick (a skill, an attribute, a limit)
    picks = {
        node.findtext("name") or ""
        for node in parse_data("powers.xml").findall("./powers/power")
        if any(el.tag.startswith("select") for el in node.iterfind(".//bonus//"))
    }
    rows = []
    for choice, bonus in bonuses:
        for row in _bonus_improvements(bonus, 1, None) if bonus is not None else []:
            if row.kind.startswith("AdeptPowerFree"):
                if not adept:
                    continue
                # the power's own pick (Dragonslayer's Enhanced Accuracy skill)
                # is its extra, which Chummer saves as the unique name
                if row.improved in picks:
                    row = row._replace(unique=extras.get(f"{choice} / {row.improved}") or extras.get(choice, ""))
            rows.append(row)
    owner, guid = definition.findtext("name") or "", state.mentor_id or ""
    _write_improvements(root, _with_rows(root, rows, guid, owner), guid, "MentorSpirit")


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
    arts = _sub(root, "arts")
    for ic in state.initiations:
        if ic.option_id:
            el = _sub(arts if ic.kind == "art" else mms, "art" if ic.kind == "art" else "metamagic")
            _sub(el, "sourceid", ic.option_id)
            _sub(el, "name", names["metamagic"].get(ic.option_id) or names["art"].get(ic.option_id, ""))
            _sub(el, "grade", ic.grade)
        for aid in ic.art_ids:
            el = _sub(arts, "art")
            _sub(el, "sourceid", aid)
            _sub(el, "name", names["art"].get(aid, ""))
            _sub(el, "grade", ic.grade)


def _export_free_power_rows(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """A `<power>` row at rating 0 for each power free levels or points were
    written for and none was bought — the row `specificpower` and
    `selectpowers` add for them to land on, as a mentor's (Eagle's Combat
    Sense), a quality's or a Qi focus's. Chummer counts free levels on the
    power of that name and extra; with no row they count nowhere. The import
    reads a rating 0 row as nothing bought."""
    powers = root.find("powers")
    if powers is None:
        return
    have = {(p.findtext("name") or "", p.findtext("extra") or "") for p in powers.findall("power")}
    ids = {name: pid for pid, name in names["power"].items()}
    for imp in root.findall("./improvements/improvement"):
        if not (imp.findtext("improvementttype") or "").startswith("AdeptPowerFree"):
            continue
        key = (imp.findtext("improvedname") or "", imp.findtext("unique") or "")
        if key in have or key[0] not in ids:
            continue
        have.add(key)
        el = _sub(powers, "power")
        for field, value in (
            ("sourceid", ids[key[0]]),
            ("name", key[0]),
            ("guid", str(uuid.uuid5(uuid.NAMESPACE_URL, f"{state.id}:freepower:{key[0]}:{key[1]}"))),
            ("rating", 0),
            ("extra", key[1]),
        ):
            _sub(el, field, value)
