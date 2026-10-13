"""Life modules, read back from a file this app wrote.

The mirror of :mod:`app.chummer_export.life_modules`, which explains why only
this app's own files can be read: Chummer saves what a module granted, not
which option was picked to grant it, and 219 of the 325 modules offer at least
one choice.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict
from ..data_loader._xml import _text
from ..life_module_format import V2_INPUT_FIELDS, standard_digest
from ..notices import Notice, NoticeError, notice


def life_module_choices_present(root: ET.Element) -> bool:
    """Whether this file carries the answers to its modules' choices.

    `chum5_to_state` asks before reading anything, so a Chummer-written life
    module character is refused with one clear notice rather than arriving with
    its modules silently dropped.
    """
    return root.find("lifemodulechoices") is not None or root.find("lifemoduleskillstate") is not None


def _import_life_modules(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read the modules in document order, and their answers."""
    ids = {str(row["id"]) for row in cat["life_modules"]}
    picked: list[str] = []
    for q in root.findall("./qualities/quality"):
        if _text(q.find("qualitytype")).lower() != "lifemodule":
            continue
        candidates = (_text(q.find("sourceid")), _text(q.find("id")), _text(q.find("guid")))
        mid = next((c for c in candidates if c in ids), None)
        if not mid:
            # A choice key names its module by position, so dropping one would
            # move every later module's answers onto the wrong module. There is
            # no partial read of a life module character.
            raise NoticeError(notice("engine.life.chum5ModuleUnknown", name=_text(q.find("name"))))
        picked.append(mid)
    if picked:
        st["life_modules"] = picked
    saved = root.find("lifemoduleskillstate")
    if saved is not None:
        try:
            if saved.get("version") != "2" or root.find("lifemodulechoices") is not None:
                raise ValueError("unsupported or conflicting life-module state")
            expected = {*V2_INPUT_FIELDS, "standard_state_digest"}
            if len(root.findall("lifemoduleskillstate")) != 1 or len(saved) != len(expected):
                raise ValueError("duplicate or missing life-module fields")
            if {c.tag for c in saved} != expected:
                raise ValueError("unknown life-module fields")
            data = {key: json.loads(_text(saved.find(key))) for key in V2_INPUT_FIELDS}
            if data["life_module_rules_version"] != 2 or data["life_modules"] != picked:
                raise ValueError("module acquisition list differs")
            if saved.findtext("standard_state_digest") != standard_digest(root):
                raise ValueError("standard skills were edited")
        except (ValueError, TypeError) as exc:
            raise NoticeError(notice("engine.life.chum5StateInvalid")) from exc
        st.update(data)
        return
    choices = {
        _text(c.find("key")): _text(c.find("value"))
        for c in root.findall("./lifemodulechoices/choice")
        if _text(c.find("key"))
    }
    if choices:
        st["life_module_choices"] = choices
