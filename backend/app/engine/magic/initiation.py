"""Initiation resolution.

``resolve_initiation`` validates each grade's chosen metamagic or metamagic art
(audience gates, duplicates, required trees), tallies the discounted karma, and
emits the public rows plus the MAG-maximum bonus. ``apply_free_metamagics``
folds addmetamagic grants (grade 0, no karma) into that result.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.
"""

from __future__ import annotations

import math
from typing import Any

from ...models import CharacterState, InitiationChoice
from ..bundle_types import InitiationBundle
from ..constants import INITIATION_KARMA_FLAT, INITIATION_KARMA_PER_GRADE, MAG_TALENTS
from ..lookups import _magic_art_by_id, _metamagic_by_id, _metamagic_by_name
from ..requirements import requirement_tree_met
from ._common import _magic_grade_discount


def apply_free_metamagics(
    effects: dict[str, Any],
    initiation: InitiationBundle,
    talent_name: str,
    warnings: list[str],
) -> None:
    """Grant forced free metamagics from addmetamagic (grade 0, no initiation karma)."""
    can_adept = talent_name in {"Adept", "Mystic Adept"}
    can_magician = talent_name in MAG_TALENTS and talent_name != "Adept"
    metamagic_names: set[str] = set(initiation.get("metamagic_names") or set())
    public_metas: list[dict[str, Any]] = list(initiation.get("metamagics") or [])
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = list(initiation.get("bonus_sources") or [])
    seen = {str(row.get("name") or "") for row in public_metas}
    for gift in effects.get("free_metamagics") or []:
        name = str(gift.get("name") or "").strip()
        source = str(gift.get("source") or "")
        forced = bool(gift.get("forced"))
        if not name:
            continue
        spec = _metamagic_by_name(name)
        if not spec:
            warnings.append(f"{source} のメタマジック {name} が見つかりません")
            continue
        if not forced:
            if can_adept and not can_magician and not spec.get("adept"):
                warnings.append(f"{name} はアデプト向けではありません")
                continue
            if can_magician and not can_adept and not spec.get("magician"):
                warnings.append(f"{name} は魔術師向けではありません")
                continue
        if name in seen and not spec.get("repeatable"):
            continue
        seen.add(name)
        metamagic_names.add(name)
        public_metas.append(
            {
                "id": f"free-meta:{source}:{spec['id']}",
                "metamagic_id": spec["id"],
                "name": spec["name"],
                "grade": 0,
                "free": True,
                "source_quality": source,
                "adept": bool(spec.get("adept")),
                "magician": bool(spec.get("magician")),
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
        if spec.get("bonus"):
            bonus_sources.append((spec["name"], list(spec.get("bonus") or [])))
    initiation["metamagic_names"] = metamagic_names
    initiation["metamagics"] = public_metas
    initiation["bonus_sources"] = bonus_sources


def initiation_karma_for_grade(
    grade: int, *, group: bool = False, ordeal: bool = False, schooling: bool = False
) -> int:
    base = INITIATION_KARMA_FLAT + int(grade) * INITIATION_KARMA_PER_GRADE
    return math.floor(base * _magic_grade_discount(group=group, ordeal=ordeal, schooling=schooling) + 0.5)


def initiation_karma_total(grade: int, choices: list[InitiationChoice] | None = None) -> int:
    flags = {int(c.grade): c for c in (choices or [])}
    total = 0
    for g in range(1, max(0, int(grade)) + 1):
        c = flags.get(g)
        total += initiation_karma_for_grade(
            g,
            group=bool(c and c.group),
            ordeal=bool(c and c.ordeal),
            schooling=bool(c and c.schooling),
        )
    return total


def resolve_initiation(
    state: CharacterState,
    talent_name: str,
    mag: int,
    quality_names: set[str],
    errors: list[str],
) -> InitiationBundle:
    warnings: list[str] = []
    empty: InitiationBundle = {
        "warnings": warnings,
        "grade": 0,
        "karma": 0,
        "choices": [],
        "metamagics": [],
        "arts": [],
        "art_names": set(),
        "metamagic_names": set(),
        "bonus_sources": [],
        "mag_max_bonus": 0,
    }
    if talent_name not in MAG_TALENTS:
        state.initiate_grade = 0
        state.initiations = []
        return empty

    can_adept = talent_name in {"Adept", "Mystic Adept"}
    can_magician = talent_name in MAG_TALENTS and talent_name != "Adept"
    grade = max(0, int(state.initiate_grade or 0))
    by_grade: dict[int, InitiationChoice] = {}
    for inst in state.initiations or []:
        g = int(inst.grade or 0)
        if g >= 1:
            by_grade[g] = InitiationChoice(
                id=inst.id,
                grade=g,
                kind=inst.kind or "metamagic",
                option_id=inst.option_id or "",
                group=bool(inst.group),
                ordeal=bool(inst.ordeal),
                schooling=bool(inst.schooling),
            )

    kept_choices: list[InitiationChoice] = []
    for g in range(1, grade + 1):
        choice = by_grade.get(g) or InitiationChoice(grade=g, kind="metamagic", option_id="")
        choice.grade = g
        kept_choices.append(choice)
    state.initiate_grade = grade
    state.initiations = kept_choices

    art_names: set[str] = set()
    metamagic_names: set[str] = set()
    public_choices: list[dict[str, Any]] = []
    public_metas: list[dict[str, Any]] = []
    public_arts: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    seen_meta: set[str] = set()
    seen_art: set[str] = set()

    for choice in kept_choices:
        g = choice.grade
        kind = "art" if choice.kind == "art" else "metamagic"
        choice.kind = kind
        option_id = (choice.option_id or "").strip()
        row = {
            "id": choice.id,
            "grade": g,
            "kind": kind,
            "option_id": option_id,
            "name": "",
            "karma": initiation_karma_for_grade(
                g, group=choice.group, ordeal=choice.ordeal, schooling=choice.schooling
            ),
            "group": bool(choice.group),
            "ordeal": bool(choice.ordeal),
            "schooling": bool(choice.schooling),
            "source": "",
            "page": "",
        }
        if not option_id:
            warnings.append(f"イニシエーション等級 {g} の Art／メタマジックを選んでください")
            public_choices.append(row)
            continue

        if kind == "art":
            spec = _magic_art_by_id(option_id)
            if not spec:
                warnings.append(f"未知の Art を等級 {g} から外しました")
                choice.option_id = ""
                row["option_id"] = ""
                public_choices.append(row)
                continue
            if spec["name"] in seen_art:
                warnings.append(f"{spec['name']} は重複しているため外しました")
                choice.option_id = ""
                row["option_id"] = ""
                public_choices.append(row)
                continue
            seen_art.add(spec["name"])
            art_names.add(spec["name"])
            public_arts.append(
                {
                    "id": choice.id,
                    "art_id": spec["id"],
                    "name": spec["name"],
                    "grade": g,
                    "source": spec.get("source") or "",
                    "page": spec.get("page") or "",
                }
            )
            if spec.get("bonus"):
                bonus_sources.append((spec["name"], list(spec.get("bonus") or [])))
            row.update(
                {
                    "option_id": spec["id"],
                    "name": spec["name"],
                    "source": spec.get("source") or "",
                    "page": spec.get("page") or "",
                }
            )
            public_choices.append(row)
            continue

        spec = _metamagic_by_id(option_id)
        if not spec:
            warnings.append(f"未知のメタマジックを等級 {g} から外しました")
            choice.option_id = ""
            row["option_id"] = ""
            public_choices.append(row)
            continue
        if not spec.get("repeatable") and spec["name"] in seen_meta:
            warnings.append(f"{spec['name']} は重複しているため外しました")
            choice.option_id = ""
            row["option_id"] = ""
            public_choices.append(row)
            continue
        if can_adept and not can_magician and not spec.get("adept"):
            warnings.append(f"{spec['name']} はアデプト向けではありません")
            choice.option_id = ""
            row["option_id"] = ""
            public_choices.append(row)
            continue
        if can_magician and not can_adept and not spec.get("magician"):
            warnings.append(f"{spec['name']} は魔術師向けではありません")
            choice.option_id = ""
            row["option_id"] = ""
            public_choices.append(row)
            continue

        ctx = {
            "qualities": set(quality_names) | {talent_name},
            "arts": set(art_names),
            "metamagics": set(metamagic_names),
            "powers": set(),
            "metatypes": set(),
            "metatype_categories": set(),
            "magenabled": True,
            "resenabled": False,
            "cyberware": set(),
            "bioware": set(),
            "spells": set(),
            "tradition": "",
            "skills": {},
            "knowledge": {},
            "essence": 6.0,
            "ess_lost": 0.0,
        }
        if spec.get("required_tree") and not requirement_tree_met(spec.get("required_tree"), ctx):
            needed = [name for names in (spec.get("required") or {}).values() for name in names]
            label = " / ".join(needed) if needed else "前提"
            warnings.append(f"{spec['name']} には {label} が必要です")

        seen_meta.add(spec["name"])
        metamagic_names.add(spec["name"])
        public_metas.append(
            {
                "id": choice.id,
                "metamagic_id": spec["id"],
                "name": spec["name"],
                "grade": g,
                "adept": bool(spec.get("adept")),
                "magician": bool(spec.get("magician")),
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
        if spec.get("bonus"):
            bonus_sources.append((spec["name"], list(spec.get("bonus") or [])))
        row.update(
            {
                "option_id": spec["id"],
                "name": spec["name"],
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
        public_choices.append(row)

    if grade > 0 and mag <= 0:
        errors.append("イニシエーションには魔力が必要です")
    elif grade > mag:
        errors.append(f"イニシエーション等級は魔力以下です（等級 {grade} / MAG {mag}）")

    return {
        "warnings": warnings,
        "grade": grade,
        "karma": initiation_karma_total(grade, kept_choices),
        "choices": public_choices,
        "metamagics": public_metas,
        "arts": public_arts,
        "art_names": art_names,
        "metamagic_names": metamagic_names,
        "bonus_sources": bonus_sources,
        "mag_max_bonus": grade,
    }
