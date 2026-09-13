"""Lifestyles, contacts and martial arts."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict
from ..data_loader._xml import _int, _text
from ..engine.constants import (
    QUALITY_CONTACT_EXTRA_SUFFIX,
)
from ..notices import Notice, notice, ui
from ._common import _is_uuid, _Resolver


def _import_lifestyles(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read lifestyles, contacts and martial arts."""
    ls_r = _Resolver(cat["lifestyles"])
    lq_r = _Resolver(cat.get("lifestyle_qualities") or [])
    # Chummer fills `<extra>` with display text ("Cramped [-10%]") on a
    # quality that asks for nothing; keep it only where a pick is asked for.
    lq_pick = {str(row["id"]) for row in cat.get("lifestyle_qualities") or [] if row.get("needs_extra")}
    lifestyles = []
    for ls in root.findall("./lifestyles/lifestyle"):
        base = _text(ls.find("baselifestyle")) or _text(ls.find("name"))
        lid = ls_r.by_name.get(base.lower())
        if lid:
            quality_ids: list[str] = []
            quality_extras: dict[str, str] = {}
            for q in ls.findall("./lifestylequalities/lifestylequality"):
                # a built-in one (the free Grid Subscription) comes with the
                # lifestyle and is derived again from it
                if _text(q.find("lifestylequalitysource")).lower() == "builtin":
                    continue
                data_id = _text(q.find("id"))
                qid = data_id if data_id in lq_r.ids else lq_r.resolve(q, warn, ui("engine.kind.lifestyleQuality"))
                if not qid:
                    continue
                quality_ids.append(qid)
                if qid in lq_pick and _text(q.find("extra")):
                    quality_extras[qid] = _text(q.find("extra"))
            lifestyles.append(
                {
                    "id": str(uuid.uuid4()),
                    "lifestyle_id": lid,
                    "months": max(1, _int(ls.find("months"), 1)),
                    # the points bought above the lifestyle's own; the
                    # engine holds them to what the lifestyle allows
                    "comforts": max(0, _int(ls.find("comforts"))),
                    "area": max(0, _int(ls.find("area"))),
                    "security": max(0, _int(ls.find("security"))),
                    "quality_ids": quality_ids,
                    "quality_extras": quality_extras,
                }
            )
        elif base:
            warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.lifestyle"), name=base))
    st["lifestyles"] = lifestyles

    contacts = []
    for c in root.findall("./contacts/contact"):
        nm = _text(c.find("name"))
        if not nm and not _text(c.find("role")):
            continue
        guid = _text(c.find("guid"))
        contacts.append(
            {
                "id": guid if _is_uuid(guid) else str(uuid.uuid4()),
                "name": nm,
                "role": _text(c.find("role")) or None,
                "connection": max(1, _int(c.find("connection"), 1)),
                "loyalty": max(1, _int(c.find("loyalty"), 1)),
                "group": _text(c.find("type")).lower() == "group" or _text(c.find("isgroup")).lower() == "true",
            }
        )
    st["contacts"] = contacts
    # a `<selectcontact>` pick came in as the contact's name (see
    # `_quality_extra_in`); point it at the row it names
    ids_by_name: dict[str, str] = {}
    for row in contacts:
        ids_by_name.setdefault(str(row["name"]), str(row["id"]))
    extras = st.get("quality_extras") or {}
    for key, value in list(extras.items()):
        if key.endswith(QUALITY_CONTACT_EXTRA_SUFFIX):
            if value in ids_by_name:
                extras[key] = ids_by_name[value]
            else:
                del extras[key]

    ma_r = _Resolver(cat["martial_arts"])
    marts = []
    for m in root.findall("./martialarts/martialart"):
        aid = ma_r.resolve(m, warn, ui("engine.kind.martialArt"))
        if aid:
            techs = [_text(t.find("name")) for t in m.findall("./martialarttechniques/martialarttechnique")]
            techs = [t for t in techs if t]
            marts.append({"id": str(uuid.uuid4()), "art_id": aid, "techniques": techs})
    st["martial_arts"] = marts
