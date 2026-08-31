"""Apps — commlink software (the low-rent cousin of a cyberdeck program).

An app rides on a commlink rather than a deck; otherwise the pick / pricing
handling mirrors :mod:`app.engine.gear.programs`.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog, eval_formula
from ...models import CharacterState, GearInstall
from ..selects import gear_extra_options
from ._common import _clamp_rating, _program_label


def _resolve_apps(
    state: CharacterState, commlinks: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int, list[str]]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("apps") or []}
    hosts = {str(row.get("id") or ""): row for row in commlinks}
    kept: list[GearInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    for inst in list(state.apps or []):
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        host = hosts.get(inst.parent_id or "")
        if not inst.parent_id or not host:
            warnings.append(f"{spec['name']} は通信機に装着してください")
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
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        children.setdefault(str(item.get("parent_id") or ""), []).append(item)
    for row in commlinks:
        kids = children.get(str(row.get("id") or "")) or []
        row["apps"] = kids
        keys = [f"{kid['name']}|{kid.get('extra') or ''}" for kid in kids]
        if len(keys) != len(set(keys)):
            warnings.append(f"{row['name']} に同じアプリが重複しています")
    state.apps = kept
    return public, nuyen, warnings
