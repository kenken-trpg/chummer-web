"""Technomancer (Resonance / Emerged) resolution.

The mirror of ``engine/magic/`` for the RES side: complex forms (with fading
and threading tests), sprites (compile / register, opposed tests), the living
persona, and the addecho quality grants. ``compute`` drives every ``resolve_*``
/ ``attach_*`` here.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine`` — so the import graph stays a DAG.
"""

from __future__ import annotations

import math
from typing import Any

from ..data_loader import MATRIX_ATTRIBUTES, eval_formula
from ..models import CharacterState, ComplexFormInstall, SpriteInstall
from .bundle_types import ComplexFormsBundle, SpritesBundle, SubmersionBundle
from .constants import COMPLEX_FORM_KARMA, COMPLEX_FORM_TALENTS, RES_TALENTS, SPRITE_TALENTS
from .dice import magic_opposed_test, skill_dice_pool
from .lookups import _complex_form_by_id, _default_stream, _echo_by_name, _sprite_by_id, _stream_by_id
from .magic import spell_drain_value, tradition_resist
from .priority import resolve_talent


def sprite_attributes(spec: dict[str, Any], level: int) -> dict[str, Any]:
    extras = {"F": int(level)}
    raw: dict[str, int] = {}
    for key, expr in (spec.get("attributes") or {}).items():
        value = int(eval_formula(str(expr or "F"), level, level, extras))
        if key == "INI":
            raw[key] = value
        elif key in {"BOD", "AGI", "REA", "STR"}:
            raw[key] = value
        else:
            raw[key] = max(1, value)
    matrix = {
        "attack": int(raw.get("CHA") or 0),
        "sleaze": int(raw.get("INT") or 0),
        "dataprocessing": int(raw.get("LOG") or 0),
        "firewall": int(raw.get("WIL") or 0),
        "initiative": int(raw.get("INI") or 0),
    }
    return {"attributes": raw, "matrix": matrix}


def _cyberadept_res_penalty_reduction(
    submersion_grade: int,
    ess_lost_cyber: float,
    ess_lost_bio: float,
) -> int:
    if submersion_grade <= 0:
        return 0
    non_cyber = float(ess_lost_bio or 0)
    cyber = float(ess_lost_cyber or 0)
    if math.ceil(non_cyber - 1e-9) == math.floor(non_cyber + 1e-9):
        max_bonus = int(math.ceil(cyber - 1e-9))
    else:
        max_bonus = int(math.floor(cyber + 1e-9))
    bonus = sum(i // 2 for i in range(1, submersion_grade + 1))
    return min(bonus, max_bonus)


def apply_granted_echoes(
    effects: dict[str, Any],
    submersion: SubmersionBundle,
    qualities: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    by_name = {q["name"]: q for q in qualities}
    public_echoes = list(submersion.get("echoes") or [])
    echo_names = list(submersion.get("echo_names") or [])
    bonus_sources = list(submersion.get("bonus_sources") or [])
    seen_echo_ids = {str(row.get("echo_id") or "") for row in public_echoes}

    for row in effects.get("grant_echoes") or []:
        source = str(row.get("source") or "")
        q = by_name.get(source)
        if not q:
            continue
        echo_name = str(row.get("name") or "").strip()
        spec = _echo_by_name(echo_name)
        if not spec:
            warnings.append(f"{source} のエコー {echo_name} が見つかりません")
            continue
        if spec["id"] in seen_echo_ids:
            continue
        seen_echo_ids.add(spec["id"])
        echo_names.append(spec["name"])
        public_echoes.append(
            {
                "id": f"grant:{spec['id']}",
                "echo_id": spec["id"],
                "name": spec["name"],
                "grade": 0,
                "extra": None,
                "granted": True,
                "source_quality": source,
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
        if spec.get("bonus"):
            bonus_sources.append((f"{source}: {spec['name']}", list(spec.get("bonus") or [])))

    submersion["echoes"] = public_echoes
    submersion["echo_names"] = echo_names
    submersion["bonus_sources"] = bonus_sources


def _complex_form_fading_mod(
    effects: dict[str, Any] | None,
    name: str,
    label: str,
    extra: str,
) -> int:
    total = int((effects or {}).get("fading_value") or 0)
    for row in (effects or {}).get("fading_value_specific") or []:
        specific = str(row.get("specific") or "").strip()
        if not specific:
            continue
        value = int(row.get("value") or 0)
        if name == specific or label == specific:
            total += value
            continue
        if "[Matrix Attribute]" in specific and extra and label == specific.replace("[Matrix Attribute]", extra):
            total += value
    return total


def _required_names(spec: dict[str, Any]) -> list[str]:
    return [name for names in (spec.get("required") or {}).values() for name in names]


def resolve_complex_forms(
    state: CharacterState,
    talent_name: str,
    res: int,
    attrs: dict[str, int],
    quality_names: set[str],
    effects: dict[str, Any] | None = None,
) -> ComplexFormsBundle:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    stream = _stream_by_id(state.stream_id) or (_default_stream() if talent_name in COMPLEX_FORM_TALENTS else None)
    if talent_name in COMPLEX_FORM_TALENTS and stream:
        state.stream_id = stream["id"]
    resist, resist_attrs = tradition_resist(stream, attrs)
    resist += int((effects or {}).get("fading_resist") or 0)
    if talent_name not in COMPLEX_FORM_TALENTS:
        state.complex_forms = []
        if talent_name not in RES_TALENTS:
            state.stream_id = None
        return {
            "warnings": warnings,
            "public": public,
            "free_max": 0,
            "used": 0,
            "paid": 0,
            "karma": 0,
            "stream": None,
            "resist": resist,
            "resist_attrs": resist_attrs,
        }
    talent = resolve_talent(state.priorities.Talent, talent_name)
    free_max = int(talent.get("cfp") or 0)
    seen: set[str] = set()
    kept: list[ComplexFormInstall] = []
    res = max(0, int(res or 0))
    for inst in state.complex_forms:
        spec = _complex_form_by_id(inst.form_id)
        if not spec:
            continue
        if spec["id"] in seen:
            warnings.append(f"{spec['name']} は重複しているため外しました")
            continue
        missing = [name for name in _required_names(spec) if name not in quality_names]
        if missing:
            warnings.append(f"{spec['name']} には {' / '.join(missing)} が必要です")
            continue
        extra = (inst.extra or "").strip()
        if spec.get("needs_extra") and extra not in MATRIX_ATTRIBUTES:
            warnings.append(f"{spec['name']} はマトリクス能力値を選んでください")
            extra = extra if extra in MATRIX_ATTRIBUTES else ""
            inst.extra = extra or None
        seen.add(spec["id"])
        level_max = max(1, res * 2) if res else 1
        chosen = int(inst.level) if inst.level else (res or 1)
        chosen = max(1, min(level_max, chosen))
        inst.level = chosen
        label = spec["name"]
        if extra:
            label = spec["name"].replace("[Matrix Attribute]", extra)
        fade_mod = _complex_form_fading_mod(effects, spec["name"], label, extra)
        fade = spell_drain_value(str(spec.get("fv") or ""), chosen, mod=fade_mod)
        physical = bool(res) and chosen > res
        free = len(kept) < free_max
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "form_id": spec["id"],
                "name": spec["name"],
                "label": label,
                "target": spec.get("target") or "",
                "duration": spec.get("duration") or "",
                "fv": spec.get("fv") or "",
                "fade_mod": fade_mod,
                "extra": extra,
                "needs_extra": bool(spec.get("needs_extra")),
                "options": list(MATRIX_ATTRIBUTES) if spec.get("needs_extra") else [],
                "level": chosen,
                "level_min": 1,
                "level_max": level_max,
                "fade": fade,
                "fade_code": None if fade is None else ("P" if physical else "S"),
                "physical": physical,
                "resist": int(resist),
                "resist_attrs": resist_attrs,
                "free": free,
                "karma": 0 if free else COMPLEX_FORM_KARMA,
                "source": spec.get("source"),
                "page": spec.get("page"),
            }
        )
    state.complex_forms = kept
    paid = max(0, len(public) - free_max)
    return {
        "warnings": warnings,
        "public": public,
        "free_max": free_max,
        "used": len(public),
        "paid": paid,
        "karma": paid * COMPLEX_FORM_KARMA,
        "stream": (
            {
                "id": stream["id"],
                "name": stream["name"],
                "drain": stream.get("drain") or "",
                "drain_attrs": list(stream.get("drain_attrs") or []),
                "sprites": list(stream.get("sprites") or []),
                "source": stream.get("source"),
                "page": stream.get("page"),
            }
            if stream
            else None
        ),
        "resist": resist,
        "resist_attrs": resist_attrs,
    }


def resolve_sprites(
    state: CharacterState,
    talent_name: str,
    res: int,
    stream: dict[str, Any] | None,
) -> SpritesBundle:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    errors: list[str] = []
    if talent_name not in SPRITE_TALENTS:
        state.sprites = []
        return {"warnings": warnings, "errors": errors, "public": public}
    allowed = set(stream.get("sprites") or []) if stream else set()
    kept: list[SpriteInstall] = []
    res = max(0, int(res or 0))
    registered_count = 0
    for inst in state.sprites:
        spec = _sprite_by_id(inst.sprite_id)
        if not spec:
            continue
        if allowed and spec["name"] not in allowed:
            warnings.append(f"{spec['name']} はこのストリームではコンパイルできません")
            continue
        if res <= 0:
            warnings.append(f"{spec['name']} をコンパイルするには共振力が必要です")
            continue
        registered = bool(inst.registered)
        inst.registered = registered
        cap = res if registered else max(1, res * 2)
        level = max(1, min(cap, int(inst.level or 1)))
        inst.level = level
        if inst.hits is not None and inst.opposed_hits is not None:
            services = max(0, int(inst.hits) - int(inst.opposed_hits))
        elif registered:
            services = max(1, min(res, int(inst.services or 1)))
        else:
            services = max(0, int(inst.services or 0))
        inst.services = services
        if registered:
            registered_count += 1
        if registered is False and inst.hits is not None and inst.opposed_hits is not None and services <= 0:
            warnings.append(f"{spec['name']} のコンパイルに失敗しています（正味0）")
        stats = sprite_attributes(spec, level)
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "sprite_id": spec["id"],
                "name": spec["name"],
                "level": level,
                "level_max": cap,
                "services": services,
                "registered": registered,
                "hits": inst.hits,
                "opposed_hits": inst.opposed_hits,
                "attributes": stats["attributes"],
                "matrix": stats["matrix"],
                "powers": list(spec.get("powers") or []),
                "skills": [
                    {"name": row["name"], "attribute": row.get("attribute") or "", "rating": level}
                    for row in (spec.get("skills") or [])
                ],
                "source": spec.get("source"),
                "page": spec.get("page"),
            }
        )
    state.sprites = kept
    if registered_count > res:
        errors.append(f"登録できるスプライトは共振力までです（{registered_count}/{res}）")
    return {"warnings": warnings, "errors": errors, "public": public}


def attach_complex_form_tests(
    public: list[dict[str, Any]],
    res: int,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    skills_data: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    for item in public:
        level = int(item.get("level") or 1)
        dice = skill_dice_pool("Software", skill_totals, skill_bonus, attrs, skills_data, attr_override="RES")
        item["test"] = {
            **dice,
            "force": level,
            "limit": level,
            "limit_name": "Level",
            "vs": 0,
            "drain": item.get("fade"),
            "drain_code": item.get("fade_code"),
            "physical": bool(item.get("physical")),
        }
        if dice.get("missing"):
            warnings.append(
                f"{item['label'] or item['name']} のスレッディングにはSoftwareが必要です（未習得・デフォルト不可）"
            )
    return warnings


def attach_sprite_tests(
    public: list[dict[str, Any]],
    res: int,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    skills_data: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    for item in public:
        registered = bool(item.get("registered"))
        level = int(item.get("level") or 1)
        skill = "Registering" if registered else "Compiling"
        test = magic_opposed_test(
            skill,
            level,
            level * 2,
            res,
            skill_totals,
            skill_bonus,
            attrs,
            item.get("hits"),
            item.get("opposed_hits"),
            limit_name="Level",
            days=level if registered else None,
            skills_data=skills_data,
        )
        item["test"] = test
        if test.get("missing"):
            warnings.append(
                f"{item['name']} の{('登録' if registered else 'コンパイル')}判定に{skill}が必要です（未習得・デフォルト不可）"
            )
    return warnings


def living_persona(
    attrs: dict[str, int],
    res: int,
    persona_bonus: dict[str, int] | None = None,
    matrix_initiative_dice: int = 0,
) -> dict[str, int]:
    bonus = persona_bonus or {}
    return {
        "device_rating": int(res),
        "attack": int(attrs.get("CHA") or 0) + int(bonus.get("attack") or 0),
        "sleaze": int(attrs.get("INT") or 0) + int(bonus.get("sleaze") or 0),
        "dataprocessing": int(attrs.get("LOG") or 0) + int(bonus.get("dataprocessing") or 0),
        "firewall": int(attrs.get("WIL") or 0) + int(bonus.get("firewall") or 0),
        "matrix_initiative_dice": max(0, int(matrix_initiative_dice or 0)),
    }
