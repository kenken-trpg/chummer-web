"""Life modules, and the picks the engine needs to rebuild what they grant.

The mirror of :mod:`app.chummer_import.life_modules`.

Chummer keeps a life module as a quality of its own type (``Quality.cs``
writes ``<qualitytype>LifeModule</qualitytype>`` and, only for that type, a
``<stage>``), and keeps what the module granted nowhere — the bonuses are
baked into the character's skills and attributes. This app does the opposite:
the state holds the module ids and the answers to their choices, and the
engine re-derives the grants on every compute.

So the modules go out in Chummer's shape, for Chummer to read, and the answers
go out beside them in ``<lifemodulechoices>``, which Chummer ignores and the
importer here reads back. A file Chummer itself wrote has no such element, and
the importer refuses it rather than guessing which option each ``<extra>``
came from.
"""

from __future__ import annotations

import json
import uuid
import xml.etree.ElementTree as ET
from typing import Any

from ..data_loader import catalog
from ..engine.priority import normalize_build_method
from ..life_module_format import V2_INPUT_FIELDS, standard_digest
from ..models import CharacterState
from ._common import _Ctx, _Names, _sub


def export_life_modules(qualities: ET.Element, state: CharacterState) -> None:
    """Write the chosen modules into the ``<qualities>`` the caller made.

    Document order is the state's order, and the importer reads it back the
    same way: a choice key names the module by its position (the engine's
    `occurrence`), so a reordering would move the answers onto other modules.
    """
    rows = {str(row["id"]): row for row in catalog()["life_modules"]}
    # Archived modules came from a desktop snapshot. Keep their identity on
    # export for provenance; the reader will snapshot them again because the
    # desktop file has no record of their original choices.
    for index, mid in enumerate(state.life_modules or state.life_module_archive):
        row: dict[str, Any] = rows.get(mid) or {}
        quality = _sub(qualities, "quality")
        fields = {
            "sourceid": mid,
            "guid": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{state.id}:lifemodule:{index}:{mid}")),
            "name": row.get("name") or "",
            "extra": "",
            "bp": row.get("karma") or 0,
            "qualitytype": "LifeModule",
            "qualitysource": "LifeModule",
            # Chummer writes this one only for a life module, and reads it
            # back only for one; it is what orders the stages on its screen.
            "stage": row.get("stage") or "",
            "contributetobp": "False",
            "contributetolimit": "False",
            "implemented": "True",
            "print": "True",
            "source": row.get("source") or "",
            "page": row.get("page") or "",
        }
        for key, value in fields.items():
            _sub(quality, key, value)


def _export_life_module_choices(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """``<lifemodulechoices>``: the answers, and the marker that says this
    file came from here.

    Written whenever the character builds from life modules, even with no
    modules chosen yet and no choices to record — its presence is what tells
    the importer the modules in this file can be read rather than guessed at.
    """
    if normalize_build_method(state.build_method) != "LifeModule":
        return
    if state.life_module_rules_version == 2:
        el = ET.SubElement(root, "lifemoduleskillstate", {"version": "2"})
        # Typed JSON in individual XML fields; never evaluated as expressions.
        # Omit the legacy marker so an old app refuses v2 instead of treating
        # baked standard ratings as purchases and adding the grants twice.
        data = state.model_dump(mode="json")
        for key in V2_INPUT_FIELDS:
            _sub(el, key, json.dumps(data[key], sort_keys=True, ensure_ascii=False))
        _sub(el, "standard_state_digest", standard_digest(root))
        return
    el = _sub(root, "lifemodulechoices")
    for key, value in sorted(state.life_module_choices.items()):
        choice = _sub(el, "choice")
        _sub(choice, "key", key)
        _sub(choice, "value", value)
