"""Submersion resolution.

``resolve_submersion`` mirrors initiation for technomancers: it validates each
grade's chosen echo (unknown / over-max-takes / needs-extra), tallies the
discounted karma, and emits the public rows plus the RES-maximum bonus.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.
"""

from __future__ import annotations

import math
from typing import Any

from ...models import CharacterState, SubmersionChoice
from ..constants import RES_TALENTS, SUBMERSION_KARMA_FLAT, SUBMERSION_KARMA_PER_GRADE
from ..lookups import _echo_by_id
from ._common import _magic_grade_discount


def submersion_karma_for_grade(
    grade: int, *, group: bool = False, ordeal: bool = False, schooling: bool = False
) -> int:
    base = SUBMERSION_KARMA_FLAT + int(grade) * SUBMERSION_KARMA_PER_GRADE
    return math.floor(base * _magic_grade_discount(group=group, ordeal=ordeal, schooling=schooling) + 0.5)


def submersion_karma_total(grade: int, choices: list[SubmersionChoice] | None = None) -> int:
    flags = {int(c.grade): c for c in (choices or [])}
    total = 0
    for g in range(1, max(0, int(grade)) + 1):
        c = flags.get(g)
        total += submersion_karma_for_grade(
            g,
            group=bool(c and c.group),
            ordeal=bool(c and c.ordeal),
            schooling=bool(c and c.schooling),
        )
    return total


def resolve_submersion(
    state: CharacterState,
    talent_name: str,
    res: int,
    quality_names: set[str],
    errors: list[str],
) -> dict[str, Any]:
    warnings: list[str] = []
    empty = {
        "warnings": warnings,
        "grade": 0,
        "karma": 0,
        "choices": [],
        "echoes": [],
        "echo_names": [],
        "bonus_sources": [],
        "res_max_bonus": 0,
    }
    if talent_name not in RES_TALENTS:
        state.submersion_grade = 0
        state.submersions = []
        return empty

    grade = max(0, int(state.submersion_grade or 0))
    by_grade: dict[int, SubmersionChoice] = {}
    for inst in state.submersions or []:
        g = int(inst.grade or 0)
        if g >= 1:
            by_grade[g] = SubmersionChoice(
                id=inst.id,
                grade=g,
                echo_id=inst.echo_id or "",
                extra=inst.extra,
                group=bool(inst.group),
                ordeal=bool(inst.ordeal),
                schooling=bool(inst.schooling),
            )

    kept_choices: list[SubmersionChoice] = []
    for g in range(1, grade + 1):
        choice = by_grade.get(g) or SubmersionChoice(grade=g, echo_id="")
        choice.grade = g
        kept_choices.append(choice)
    state.submersion_grade = grade
    state.submersions = kept_choices

    public_choices: list[dict[str, Any]] = []
    public_echoes: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    taken_counts: dict[str, int] = {}
    echo_names: list[str] = []

    for choice in kept_choices:
        g = choice.grade
        echo_id = (choice.echo_id or "").strip()
        extra = (choice.extra or "").strip() or None
        choice.extra = extra
        row = {
            "id": choice.id,
            "grade": g,
            "echo_id": echo_id,
            "name": "",
            "extra": extra,
            "karma": submersion_karma_for_grade(
                g, group=choice.group, ordeal=choice.ordeal, schooling=choice.schooling
            ),
            "group": bool(choice.group),
            "ordeal": bool(choice.ordeal),
            "schooling": bool(choice.schooling),
            "needs_extra": False,
            "source": "",
            "page": "",
        }
        if not echo_id:
            warnings.append(f"サブマージョン等級 {g} のエコーを選んでください")
            public_choices.append(row)
            continue

        spec = _echo_by_id(echo_id)
        if not spec:
            warnings.append(f"未知のエコーを等級 {g} から外しました")
            choice.echo_id = ""
            choice.extra = None
            row["echo_id"] = ""
            row["extra"] = None
            public_choices.append(row)
            continue

        count = taken_counts.get(spec["id"], 0)
        max_takes = spec.get("max_takes")
        if max_takes is not None and count >= int(max_takes):
            warnings.append(f"{spec['name']} は最大 {max_takes} 回までです（等級 {g} から外しました）")
            choice.echo_id = ""
            choice.extra = None
            row["echo_id"] = ""
            row["extra"] = None
            public_choices.append(row)
            continue

        if spec.get("needs_extra") and not extra:
            warnings.append(f"{spec['name']} の対象（プログラム名など）を入力してください")

        taken_counts[spec["id"]] = count + 1
        echo_names.append(spec["name"])
        public_echoes.append(
            {
                "id": choice.id,
                "echo_id": spec["id"],
                "name": spec["name"],
                "grade": g,
                "extra": extra,
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
        if spec.get("bonus"):
            bonus_sources.append((spec["name"], list(spec.get("bonus") or [])))
        row.update(
            {
                "echo_id": spec["id"],
                "name": spec["name"],
                "extra": extra,
                "needs_extra": bool(spec.get("needs_extra")),
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
        public_choices.append(row)

    if grade > 0 and res <= 0:
        errors.append("サブマージョンには共振力が必要です")
    elif grade > res:
        errors.append(f"サブマージョン等級は共振力以下です（等級 {grade} / RES {res}）")

    return {
        "warnings": warnings,
        "grade": grade,
        "karma": submersion_karma_total(grade, kept_choices),
        "choices": public_choices,
        "echoes": public_echoes,
        "echo_names": echo_names,
        "bonus_sources": bonus_sources,
        "res_max_bonus": grade,
    }
