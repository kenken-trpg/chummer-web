"""What a quality still needs the player to pick, and how an ``extra`` key
is spelled.

Pure inspectors over a catalog spec: no state, no notices. ``gather`` /
``sides`` / ``validate`` all ask the same questions of the same ``<bonus>``
nodes, so the questions live here rather than in whichever of them came first.
"""

from __future__ import annotations

from typing import Any

from ..constants import (
    QUALITY_ADDSPIRIT_EXTRA_MARKER,
    QUALITY_ATTRIBUTE_EXTRA_MARKER,
    QUALITY_CONTACT_EXTRA_SUFFIX,
    QUALITY_OPTIONAL_POWER_EXTRA_SUFFIX,
    QUALITY_SPIRIT_CATEGORY_EXTRA_SUFFIX,
    QUALITY_TAKE_EXTRA_MARKER,
    quality_take_extra_key,
)


def quality_needs_extra(spec: dict[str, Any]) -> bool:
    return bool(spec.get("needs_extra")) or any(
        node.get("tag")
        in {
            "selecttext",
            "selectattributes",
            "skillgroupdisablechoice",
            "selectquality",
            "selectside",
            "actiondicepool",
            "selectexpertise",
        }
        or (
            node.get("tag") == "weaponcategorydv"
            and bool(str(((node.get("field_attrs") or {}).get("selectskill") or {}).get("limittoskill") or "").strip())
        )
        or (
            node.get("tag") == "weaponskillaccuracy"
            and (
                "selectskill" in (node.get("fields") or {}) or bool((node.get("field_attrs") or {}).get("selectskill"))
            )
            and not str((node.get("fields") or {}).get("name") or "").strip()
        )
        for node in (spec.get("bonus") or [])
    )


def _quality_has_actiondicepool(spec: dict[str, Any]) -> bool:
    return any(node.get("tag") == "actiondicepool" for node in (spec.get("bonus") or []))


def _quality_needs_spell_category(spec: dict[str, Any]) -> bool:
    return any(
        node.get("tag") == "limitspellcategory" and not str(node.get("value") or "").strip()
        for node in (spec.get("bonus") or [])
    )


def _quality_needs_spirit_category(spec: dict[str, Any]) -> bool:
    for node in spec.get("bonus") or []:
        if node.get("tag") != "limitspiritcategory":
            continue
        fields = node.get("fields") or {}
        if fields.get("spirit"):
            continue
        if not str(node.get("value") or "").strip():
            return True
    return False


def _quality_has_selectside(spec: dict[str, Any]) -> bool:
    return any(node.get("tag") == "selectside" for node in (spec.get("bonus") or []))


def _quality_limb_slot(spec: dict[str, Any]) -> str | None:
    """Infer limb slot for quality-level selectside (e.g. Crystal Limb)."""
    if not _quality_has_selectside(spec):
        return None
    name = str(spec.get("name") or "").lower()
    if "arm" in name:
        return "arm"
    if "leg" in name:
        return "leg"
    if "hand" in name:
        return "hand"
    if "foot" in name:
        return "foot"
    return None


def _quality_extra_key_owned(key: str, owned: set[str]) -> bool:
    if key in owned:
        return True
    if key.endswith(QUALITY_CONTACT_EXTRA_SUFFIX):
        return key[: -len(QUALITY_CONTACT_EXTRA_SUFFIX)] in owned
    if key.endswith(QUALITY_OPTIONAL_POWER_EXTRA_SUFFIX):
        return key[: -len(QUALITY_OPTIONAL_POWER_EXTRA_SUFFIX)] in owned
    if key.endswith(QUALITY_SPIRIT_CATEGORY_EXTRA_SUFFIX):
        return key[: -len(QUALITY_SPIRIT_CATEGORY_EXTRA_SUFFIX)] in owned
    if QUALITY_ATTRIBUTE_EXTRA_MARKER in key:
        return key.split(QUALITY_ATTRIBUTE_EXTRA_MARKER, 1)[0] in owned
    if QUALITY_ADDSPIRIT_EXTRA_MARKER in key:
        return key.split(QUALITY_ADDSPIRIT_EXTRA_MARKER, 1)[0] in owned
    if QUALITY_TAKE_EXTRA_MARKER in key:
        return key in owned
    return False


def has_extra_per_take(spec: dict[str, Any]) -> bool:
    """A quality taken more than once whose pick is a line of text, which
    each take answers for itself: Records on File names a megacorp per take,
    Close Combat Mage a spell. Chummer asks again on every take; a mechanical
    pick (a skill, an attribute) stays one per quality."""
    return (
        int(spec.get("max_takes") or 1) > 1
        and str(spec.get("extra_kind") or "") == "text"
        and quality_needs_extra(spec)
    )


def take_extra_keys(qualities: list[dict[str, Any]]) -> list[str]:
    """The `quality_extras` key each row of `qualities` reads its pick from.

    The takes are numbered in order, bought or granted alike (two Life
    Modules each naming a megacorp for Records on File); every quality
    without a pick per take reads the id, as before."""
    taken: dict[str, int] = {}
    keys: list[str] = []
    for spec in qualities:
        qid = str(spec["id"])
        if not has_extra_per_take(spec):
            keys.append(qid)
            continue
        take = taken.get(qid, 0)
        taken[qid] = take + 1
        keys.append(quality_take_extra_key(qid, take))
    return keys
