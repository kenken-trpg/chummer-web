"""Building the quality list a character actually has.

`sanitize_quality_ids` drops what contradicts what came before it; `gather_qualities`
walks the chosen ids and follows every `<freequality>` / `<addqualities>` /
`<selectquality>` a quality chains in, plus the ones a tradition forces on its
follower. Nothing here validates — that is `_validate`.
"""

from __future__ import annotations

import re
from typing import Any

from ...improvements import granted_quality_names
from ...models import CharacterState
from ..constants import MAG_TALENTS
from ..lookups import _quality_by_id, _quality_by_name, _tradition_by_id


def is_way_quality(name: str) -> bool:
    return bool(re.fullmatch(r"The .+ Way", (name or "").strip()))


def sanitize_quality_ids(quality_ids: list[str]) -> tuple[list[str], list[str]]:
    kept: list[str] = []
    removed: list[str] = []
    for qid in quality_ids:
        spec = _quality_by_id(qid)
        if not spec:
            continue
        incoming_forbid = set((spec.get("forbidden") or {}).get("quality") or [])
        next_kept: list[str] = []
        for existing_id in kept:
            existing = _quality_by_id(existing_id)
            if not existing:
                continue
            existing_forbid = set((existing.get("forbidden") or {}).get("quality") or [])
            if spec["name"] in existing_forbid or existing["name"] in incoming_forbid:
                removed.append(existing["name"])
                continue
            next_kept.append(existing_id)
        next_kept.append(qid)
        kept = next_kept
    counts: dict[str, int] = {}
    limited: list[str] = []
    for qid in kept:
        spec = _quality_by_id(qid)
        if not spec:
            continue
        if _at_quality_limit(spec, counts):
            removed.append(spec["name"])
            continue
        taken = counts.get(qid, 0)
        counts[qid] = taken + 1
        limited.append(qid)
    return limited, removed


def _at_quality_limit(spec: dict[str, Any], counts: dict[str, int]) -> bool:
    """Would one more take of `spec` go over its limit? `<includeinlimit>`
    counts the named siblings too (Indomitable, SR5 p.75: Physical, Mental and
    Social share one limit of 3); `<limitwithinclusions>` sets that shared cap
    apart from the per-kind `limit` (Tough as Nails, RF p.150: 3 each, 4 in
    all)."""
    max_takes = spec.get("max_takes")
    own = counts.get(str(spec["id"]), 0)
    if max_takes is not None and own >= int(max_takes):
        return True
    siblings = set(spec.get("includeinlimit") or [])
    if not siblings:
        return False
    shared = own + sum(
        count
        for qid, count in counts.items()
        if qid != spec["id"] and ((_quality_by_id(qid) or {}).get("name") in siblings)
    )
    cap = int(spec.get("limitwithinclusions") or 0) or (int(max_takes) if max_takes is not None else 0)
    return bool(cap) and shared >= cap


def tradition_quality_grants(state: CharacterState, talent: dict[str, Any]) -> list[tuple[str, str]]:
    """The qualities a tradition forces on its follower, each with its pick.

    A tradition belongs to the awakened alone — ``resolve_spells`` clears it
    for everyone else — so a mundane build is handed nothing. The grants ride
    the tradition's ``<bonus>`` either singly (Traditionalist Shaman's Code of
    Honor, FA p.74) or inside ``<addqualities>``.
    """
    if talent.get("name") not in MAG_TALENTS:
        return []
    tradition = _tradition_by_id(state.tradition_id)
    grants: list[tuple[str, str]] = []
    for node in (tradition or {}).get("bonus") or []:
        if node.get("tag") in ("addquality", "addqualities"):
            grants.extend(granted_quality_names(node))
    return grants


def gather_qualities(
    state: CharacterState, talent: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    qualities: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    free_ids: set[str] = set()
    state.quality_ids, dropped = sanitize_quality_ids(list(state.quality_ids))
    pending = list(state.quality_ids)
    talent_quality = _quality_by_name(talent.get("quality") or "")
    if talent_quality:
        pending.append(talent_quality["id"])
    # The tradition's own grants come free, like the ones a quality chains in
    # below: the follower never chose them, so they cost no karma either way.
    forced_extras: dict[str, str] = {}
    for name, select in tradition_quality_grants(state, talent):
        granted = _quality_by_name(name)
        if not granted or granted["id"] in pending:
            continue
        pending.append(granted["id"])
        free_ids.add(granted["id"])
        if select:
            forced_extras[granted["id"]] = select
    if forced_extras:
        state.quality_extras = {**(state.quality_extras or {}), **forced_extras}
    extras = {key: str(value).strip() for key, value in (state.quality_extras or {}).items() if str(value).strip()}
    index = 0
    while index < len(pending):
        qid = pending[index]
        index += 1
        spec = _quality_by_id(qid)
        if not spec:
            continue
        if _at_quality_limit(spec, counts):
            continue
        taken = counts.get(qid, 0)
        counts[qid] = taken + 1
        qualities.append(spec)
        for node in spec.get("bonus") or []:
            tag = node.get("tag")
            if tag == "freequality":
                child_id = str(node.get("value") or "").strip()
                if child_id and counts.get(child_id, 0) == 0:
                    free_ids.add(child_id)
                    pending.append(child_id)
            elif tag == "addqualities":
                raw = (node.get("fields") or {}).get("addquality") or node.get("value") or ""
                names = raw if isinstance(raw, list) else [raw]
                for name in names:
                    child = _quality_by_name(str(name).strip())
                    if child and counts.get(child["id"], 0) == 0:
                        free_ids.add(child["id"])
                        pending.append(child["id"])
            elif tag == "selectquality":
                raw = (node.get("fields") or {}).get("quality") or node.get("value") or []
                options = [str(item).strip() for item in (raw if isinstance(raw, list) else [raw]) if str(item).strip()]
                picked = extras.get(qid, "")
                if picked and picked in options:
                    child = _quality_by_name(picked)
                    if child and counts.get(child["id"], 0) == 0:
                        free_ids.add(child["id"])
                        pending.append(child["id"])
    return qualities, sorted(free_ids), dropped
