"""Mount blocking in body slots and individual ware containers."""

from typing import Any

from ...notices import Notice, notice, term, ui
from .limbs import _limb_slot_count, body_limb_slots

_MOUNT_SLOTS = {"wrist": "arm", "elbow": "arm", "shoulder": "arm", "ankle": "leg", "knee": "leg", "hip": "leg"}


def check_mount_blocks(
    rows: list[dict[str, Any]], specs: dict[str, dict[str, Any]], extra_limbs: dict[str, int]
) -> list[Notice]:
    """Count each ordinary subtree once, stopping at modular plugs.

    This is stored-equipment validation based on the mount accounting in
    CharacterCreate and Cyberware.SelectSide. A connector's own blocking
    tags reserve its slot; they do not conflict with its own mount.
    """
    children: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("parent_id"):
            children.setdefault(str(row["parent_id"]), []).append(row)

    def spec(row: dict[str, Any]) -> dict[str, Any]:
        return specs.get(str(row["ware_id"]), {})

    def group(root: dict[str, Any]) -> tuple[set[str], set[str]]:
        blocks: set[str] = set()
        mounts: set[str] = set()
        seen: set[str] = set()

        def visit(row: dict[str, Any]) -> None:
            key = str(row["id"])
            if key in seen or spec(row).get("mounts_to"):
                return
            seen.add(key)
            blocks.update(spec(row).get("blocks_mounts") or [])
            mount = str(spec(row).get("modular_mount") or "")
            if mount:
                mounts.add(mount)
            for child in children.get(key, []):
                visit(child)

        visit(root)
        return blocks, mounts

    body = body_limb_slots(extra_limbs)
    errors: list[Notice] = []
    # A known ware parent defines an individual container. Vehicle-mod hosts
    # are deliberately outside this character-body validation.
    scopes: list[tuple[dict[str, Any] | None, list[dict[str, Any]]]] = [
        (None, [row for row in rows if not row.get("parent_id")])
    ]
    scopes.extend((row, children[str(row["id"])]) for row in rows if str(row["id"]) in children)
    for parent, roots in scopes:
        # A multi-limb chassis needs internal limb locations that parent_id
        # alone cannot express. Do not treat its whole interior as one limb.
        if parent is not None and (
            _limb_slot_count(parent, body) > 1 or str(parent.get("limbslot") or "").lower() == "all"
        ):
            continue
        groups = [(root, *group(root)) for root in roots]
        mounts = set().union(*(mounts for _, _, mounts in groups))
        for mount in sorted(mounts & _MOUNT_SLOTS.keys()):
            participants = [root for root, blocks, mounts in groups if mount in blocks or mount in mounts]
            # Ordinary descendants reserve the same limb as their root.
            # A lone group may contain a full limb and its connector.
            if len(participants) < 2 or not any(mount in blocks for _, blocks, _ in groups):
                continue
            capacity = body[_MOUNT_SLOTS[mount]] if parent is None else 1
            weights = [(root, _limb_slot_count(root, body) if parent is None else 1) for root in participants]
            total = sum(weight for _, weight in weights)
            counts = [("", total, capacity)]
            if parent is None and total <= capacity:
                counts = [
                    (side, sum(weight for root, weight in weights if root.get("side") == side), max(1, capacity // 2))
                    for side in ("Left", "Right")
                ]
            for side, used, limit in counts:
                if used > limit:
                    errors.append(
                        notice(
                            "engine.ware.modularMountBlocked",
                            mount=mount,
                            name=term(str(parent["name"])) if parent else ui("engine.ware.bodyMounts"),
                            side=ui(f"engine.side.{side}") if side else "",
                            used=used,
                            max=limit,
                        )
                    )
    return errors
