"""Programs — the software slotted into a cyberdeck or RCC.

Each program occupies one of the host device's program slots; some carry a
``[Skill]`` / ``[Group]`` / free-text pick that ``gear_extra_options`` enumerates.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import PROGRAM_HOSTS, catalog, eval_formula
from ...models import CharacterState, GearInstall
from ..selects import gear_extra_options
from ._common import _clamp_rating, _program_label


def _resolve_programs(
    state: CharacterState,
    cyberdecks: list[dict[str, Any]],
    rccs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[str]]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("programs") or []}
    hosts: dict[str, tuple[str, dict[str, Any]]] = {}
    for row in cyberdecks:
        hosts[str(row.get("id") or "")] = ("cyberdecks", row)
    for row in rccs:
        hosts[str(row.get("id") or "")] = ("rccs", row)
    kept: list[GearInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    for inst in list(state.programs or []):
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        want_kind = PROGRAM_HOSTS.get(str(spec.get("category") or ""), "cyberdecks")
        host = hosts.get(inst.parent_id or "")
        if not inst.parent_id or not host:
            warnings.append(f"{spec['name']} は本体に装着してください")
            continue
        kind, _parent = host
        if kind != want_kind:
            label = "サイバーデッキ" if want_kind == "cyberdecks" else "RCC"
            warnings.append(f"{spec['name']} は{label}に装着してください")
            continue
        extra_kind = str(spec.get("extra_kind") or "")
        extra = (inst.extra or "").strip()
        options = gear_extra_options(spec)
        if extra_kind == "skill":
            if extra and extra not in options:
                warnings.append(f"{spec['name']} の技能指定が無効です（{extra}）")
                extra = ""
            if not extra:
                warnings.append(f"{spec['name']} の技能を選んでください")
        elif extra_kind == "group":
            if extra and extra not in options:
                warnings.append(f"{spec['name']} の技能グループ指定が無効です（{extra}）")
                extra = ""
            if not extra:
                warnings.append(f"{spec['name']} の技能グループを選んでください")
        elif extra_kind == "text" and not extra:
            warnings.append(f"{spec['name']} の対象を入力してください")
        inst.extra = extra or None
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        cost = int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "label": _program_label(spec, extra),
                "category": spec.get("category") or "",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "parent_id": inst.parent_id,
                "extra": extra,
                "needs_extra": bool(extra_kind),
                "extra_kind": extra_kind,
                "extra_options": options,
                "nuyen": cost,
                "program_host": spec.get("program_host") or want_kind,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        children.setdefault(str(item.get("parent_id") or ""), []).append(item)
    for row in list(cyberdecks) + list(rccs):
        kids = children.get(str(row.get("id") or "")) or []
        row["program_used"] = len(kids)
        row["program_max"] = int(row.get("programs") or 0)
        if row["program_max"] > 0 and len(kids) > row["program_max"]:
            warnings.append(f"{row['name']} のプログラムが上限超過（{len(kids)}/{row['program_max']}）")
        keys = [f"{kid['name']}|{kid.get('extra') or ''}" for kid in kids]
        if len(keys) != len(set(keys)):
            warnings.append(f"{row['name']} に同じプログラムが重複しています")
    state.programs = kept
    return public, nuyen, warnings
