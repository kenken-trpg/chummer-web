"""Spirit resolution: summonable types, bound/unbound services, summoning tests.

``resolve_spirits`` clamps each spirit's Force and services against MAG and
tradition, prices bound spirits' reagents, and emits the public rows (with
attributes derived from ``spirit_attributes``). ``bind_extra_spirits`` folds
addspirit quality picks into the summonable list, and ``attach_spirit_tests``
builds the Summoning / Binding opposed tests.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog, eval_formula
from ...improvements import EffectsDict
from ...improvements.effect_rows import AddSpiritPickRow
from ...models import CharacterState, SpiritInstall
from ..bundle_types import SpiritsBundle
from ..constants import SPIRIT_REAGENT_YEN, SPIRIT_ROLE_LABELS, SPIRIT_TALENTS, quality_addspirit_extra_key
from ..dice import magic_opposed_test
from ..lookups import _spirit_by_id
from ._common import _active_skill_rating_from_state


def spirit_attributes(spec: dict[str, Any], force: int) -> dict[str, int]:
    extras = {"F": int(force)}
    out: dict[str, int] = {}
    for key, expr in (spec.get("attributes") or {}).items():
        value = int(eval_formula(str(expr or "F"), force, force, extras))
        out[key] = value if key == "INI" else max(1, value)
    return out


def addspirit_option_names() -> list[str]:
    return sorted(
        {
            str(item.get("name") or "")
            for item in catalog().get("spirits") or []
            if str(item.get("name") or "") and not str(item.get("name") or "").startswith("Homunculus")
        }
    )


def bind_extra_spirits(
    effects: EffectsDict,
    qualities: list[dict[str, Any]],
    state: CharacterState,
    warnings: list[str],
    skills_data: dict[str, Any] | None = None,
) -> list[AddSpiritPickRow]:
    """Resolve addspirit picks into extra summonable spirit types."""
    by_name = {q["name"]: q for q in qualities}
    extras = state.quality_extras or {}
    options = addspirit_option_names()
    option_set = set(options)
    resolved: list[str] = []
    picks: list[AddSpiritPickRow] = []
    index_by_quality: dict[str, int] = {}
    for slot in effects.get("add_spirit_slots") or []:
        source = str(slot.get("source") or "")
        spec = by_name.get(source)
        if not spec:
            continue
        skill = str(slot.get("skill") or "").strip()
        if skill:
            rating = _active_skill_rating_from_state(state, skill, skills_data)
            count = rating // max(1, int(slot.get("rating_divisor") or 1))
        else:
            count = 1
        allowed = [str(name).strip() for name in (slot.get("allowed") or []) if str(name).strip()]
        pick_options = [name for name in options if not allowed or name in allowed]
        for _ in range(max(0, count)):
            idx = int(index_by_quality.get(spec["id"], 0))
            index_by_quality[spec["id"]] = idx + 1
            key = quality_addspirit_extra_key(spec["id"], idx)
            picked = str(extras.get(key) or "").strip()
            row: AddSpiritPickRow = {
                "quality_id": spec["id"],
                "quality_name": spec["name"],
                "index": idx,
                "key": key,
                "value": picked,
                "options": pick_options,
                "skill": skill,
            }
            picks.append(row)
            if not picked:
                warnings.append(f"{source} の追加精霊（{idx + 1}）を選んでください")
                continue
            if picked not in option_set or (allowed and picked not in allowed):
                warnings.append(f"{source} の追加精霊が不正です（{picked}）")
                continue
            if picked not in resolved:
                resolved.append(picked)
    effects["extra_spirits"] = resolved
    effects["add_spirit_picks"] = picks
    return picks


def resolve_spirits(
    state: CharacterState,
    talent_name: str,
    mag: int,
    tradition: dict[str, Any] | None,
    *,
    limit_spirits: list[str] | None = None,
    extra_spirits: list[str] | None = None,
) -> SpiritsBundle:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    if talent_name not in SPIRIT_TALENTS:
        state.spirits = []
        return {"warnings": warnings, "public": public, "nuyen": 0}
    allowed = {name: role for role, name in (tradition.get("spirits") or {}).items()} if tradition else {}
    extra_set = {str(name).strip() for name in (extra_spirits or []) if str(name).strip()}
    for name in extra_set:
        allowed.setdefault(name, "extra")
    spirit_whitelist = {str(name).strip() for name in (limit_spirits or []) if str(name).strip()}
    if not tradition:
        warnings.append("精霊を召喚するには伝統を選んでください")
    kept: list[SpiritInstall] = []
    mag = max(0, int(mag or 0))
    for inst in state.spirits:
        spec = _spirit_by_id(inst.spirit_id)
        if not spec:
            continue
        role = allowed.get(spec["name"])
        if not tradition or not role:
            warnings.append(f"{spec['name']} はこの伝統では召喚できません")
            continue
        if spirit_whitelist and spec["name"] not in spirit_whitelist and spec["name"] not in extra_set:
            warnings.append(f"{spec['name']} はこの制限では召喚できません")
            continue
        if mag <= 0:
            warnings.append(f"{spec['name']} を召喚するには魔力が必要です")
            continue
        bound = bool(inst.bound)
        inst.bound = bound
        cap = mag if bound else max(1, mag * 2)
        force = max(1, min(cap, int(inst.force or 1)))
        inst.force = force
        if inst.hits is not None and inst.opposed_hits is not None:
            services = max(0, int(inst.hits) - int(inst.opposed_hits))
        elif bound:
            services = max(1, min(mag, int(inst.services or 1)))
        else:
            services = max(0, int(inst.services or 0))
        inst.services = services
        cost = force * SPIRIT_REAGENT_YEN if bound else 0
        nuyen += cost
        if bound is False and inst.hits is not None and inst.opposed_hits is not None and services <= 0:
            warnings.append(f"{spec['name']} の召喚に失敗しています（正味0）")
        attrs = spirit_attributes(spec, force)
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "spirit_id": spec["id"],
                "name": spec["name"],
                "role": role,
                "role_label": SPIRIT_ROLE_LABELS.get(role, role),
                "force": force,
                "force_max": cap,
                "services": services,
                "nuyen": cost,
                "bound": bound,
                "hits": inst.hits,
                "opposed_hits": inst.opposed_hits,
                "attributes": attrs,
                "powers": list(spec.get("powers") or []),
                "optionalpowers": list(spec.get("optionalpowers") or []),
                "skills": [
                    {"name": row["name"], "attribute": row.get("attribute") or "", "rating": force}
                    for row in (spec.get("skills") or [])
                ],
                "weaknesses": list(spec.get("weaknesses") or []),
                "source": spec.get("source"),
                "page": spec.get("page"),
            }
        )
    state.spirits = kept
    return {"warnings": warnings, "public": public, "nuyen": nuyen}


def attach_spirit_tests(
    public: list[dict[str, Any]],
    mag: int,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    skills_data: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    for item in public:
        bound = bool(item.get("bound"))
        force = int(item.get("force") or 1)
        skill = "Binding" if bound else "Summoning"
        vs = force * 2 if bound else force
        test = magic_opposed_test(
            skill,
            force,
            vs,
            mag,
            skill_totals,
            skill_bonus,
            attrs,
            item.get("hits"),
            item.get("opposed_hits"),
            skills_data=skills_data,
        )
        item["test"] = test
        if test.get("missing"):
            warnings.append(
                f"{item['name']} の{('結合' if bound else '召喚')}判定に{skill}が必要です（未習得・デフォルト不可）"
            )
    return warnings
