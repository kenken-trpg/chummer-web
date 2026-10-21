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
from dataclasses import dataclass, field
from typing import Any

from ...improvements import EffectsDict
from ...improvements.effect_rows import MetamagicLimitRow
from ...models import CharacterState, InitiationChoice
from ...notices import Notice, notice, term, terms
from ...rules import current_rules
from ..bundle_types import InitiationBundle
from ..constants import MAG_TALENTS
from ..lookups import _magic_art_by_id, _metamagic_by_id, _metamagic_by_name
from ..requirements import requirement_tree_met
from ._common import _magic_grade_discount


def apply_free_metamagics(
    effects: EffectsDict,
    initiation: InitiationBundle,
    talent_name: str,
    warnings: list[Notice],
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
            warnings.append(notice("engine.initiation.metamagicUnknown", source=term(source), name=term(name)))
            continue
        if not forced:
            if can_adept and not can_magician and not spec.get("adept"):
                warnings.append(notice("engine.initiation.notForAdepts", name=term(name)))
                continue
            if can_magician and not can_adept and not spec.get("magician"):
                warnings.append(notice("engine.initiation.notForMagicians", name=term(name)))
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
    base = current_rules().karma_initiation_flat + int(grade) * current_rules().karma_initiation_per_grade
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


def _metamagic_limits_by_grade(rows: list[MetamagicLimitRow] | None) -> dict[int, list[str]]:
    """``<metamagiclimit>`` rows folded into {grade: [allowed metamagic names]}.

    A grade the tradition says nothing about stays unrestricted — the two
    traditions that carry the tag (FA p.69) only script their first grades.
    """
    out: dict[int, list[str]] = {}
    for row in rows or []:
        grade = int(row.get("grade") or 0)
        name = str(row.get("name") or "").strip()
        if grade <= 0 or not name:
            continue
        allowed = out.setdefault(grade, [])
        if name not in allowed:
            allowed.append(name)
    return out


def resolve_initiation(
    state: CharacterState,
    talent_name: str,
    mag: int,
    quality_names: set[str],
    errors: list[Notice],
    *,
    metamagic_limits: list[MetamagicLimitRow] | None = None,
    critter_powers: set[str] | None = None,
) -> InitiationBundle:
    if talent_name not in MAG_TALENTS:
        state.initiate_grade = 0
        state.initiations = []
        return {
            "warnings": [],
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

    grade = max(0, int(state.initiate_grade or 0))
    kept_choices = _kept_choices(state, grade)
    tally = _Tally(
        state=state,
        talent_name=talent_name,
        quality_names=quality_names,
        critter_powers=critter_powers,
        limits=_metamagic_limits_by_grade(metamagic_limits),
    )
    for choice in kept_choices:
        _keep_extra_arts(choice, tally)
        row = _choice_row(choice, tally.limits)
        _take_option(choice, row, tally)
        tally.choices.append(row)

    if grade > 0 and mag <= 0:
        errors.append(notice("engine.initiation.needsMagic"))
    elif grade > mag:
        errors.append(notice("engine.initiation.gradeOverMagic", grade=grade, magic=mag))

    return {
        "warnings": tally.warnings,
        "grade": grade,
        "karma": initiation_karma_total(grade, kept_choices),
        "choices": tally.choices,
        "metamagics": tally.metamagics,
        "arts": tally.arts,
        "art_names": tally.art_names,
        "metamagic_names": tally.metamagic_names,
        "bonus_sources": tally.bonus_sources,
        "mag_max_bonus": grade,
    }


@dataclass
class _Tally:
    """What the grades have taken so far, as they are read in order, and what
    a later grade is checked against."""

    state: CharacterState
    talent_name: str
    quality_names: set[str]
    critter_powers: set[str] | None
    limits: dict[int, list[str]]
    warnings: list[Notice] = field(default_factory=list)
    art_names: set[str] = field(default_factory=set)
    metamagic_names: set[str] = field(default_factory=set)
    choices: list[dict[str, Any]] = field(default_factory=list)
    metamagics: list[dict[str, Any]] = field(default_factory=list)
    arts: list[dict[str, Any]] = field(default_factory=list)
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = field(default_factory=list)
    seen_meta: set[str] = field(default_factory=set)
    seen_art: set[str] = field(default_factory=set)

    @property
    def can_adept(self) -> bool:
        return self.talent_name in {"Adept", "Mystic Adept"}

    @property
    def can_magician(self) -> bool:
        return self.talent_name in MAG_TALENTS and self.talent_name != "Adept"


def _kept_choices(state: CharacterState, grade: int) -> list[InitiationChoice]:
    """One choice per grade up to the character's, the saved one where there
    is one; written back to the state, so a grade dropped drops its choice."""
    by_grade: dict[int, InitiationChoice] = {}
    for inst in state.initiations or []:
        g = int(inst.grade or 0)
        if g >= 1:
            by_grade[g] = InitiationChoice(
                id=inst.id,
                grade=g,
                kind=inst.kind or "metamagic",
                art_ids=list(inst.art_ids),
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
    return kept_choices


def _keep_extra_arts(choice: InitiationChoice, tally: _Tally) -> None:
    """The arts a grade lists besides its option: unknown and repeated ones
    are dropped, the rest taken."""
    g = choice.grade
    kept_arts: list[str] = []
    for aid in choice.art_ids:
        art = _magic_art_by_id(aid)
        if not art:
            tally.warnings.append(notice("engine.initiation.artUnknownDropped", grade=g))
            continue
        if art["name"] in tally.seen_art:
            tally.warnings.append(notice("engine.initiation.duplicateDropped", name=term(str(art["name"]))))
            continue
        kept_arts.append(aid)
        tally.seen_art.add(art["name"])
        tally.art_names.add(art["name"])
        tally.arts.append(
            {
                "id": f"{choice.id}:art:{aid}",
                "art_id": aid,
                "name": art["name"],
                "grade": g,
                "source": art.get("source") or "",
                "page": art.get("page") or "",
            }
        )
        if art.get("bonus"):
            tally.bonus_sources.append((art["name"], list(art["bonus"])))
    choice.art_ids = kept_arts


def _choice_row(choice: InitiationChoice, limits: dict[int, list[str]]) -> dict[str, Any]:
    """The grade's public row, before its option is resolved into it."""
    g = choice.grade
    kind = "art" if choice.kind == "art" else "metamagic"
    choice.kind = kind
    return {
        "id": choice.id,
        "grade": g,
        "kind": kind,
        "option_id": (choice.option_id or "").strip(),
        "art_ids": list(choice.art_ids),
        "name": "",
        "karma": initiation_karma_for_grade(g, group=choice.group, ordeal=choice.ordeal, schooling=choice.schooling),
        "group": bool(choice.group),
        "ordeal": bool(choice.ordeal),
        "schooling": bool(choice.schooling),
        "source": "",
        "page": "",
        "allowed_metamagics": list(limits.get(g) or []),
    }


def _take_option(choice: InitiationChoice, row: dict[str, Any], tally: _Tally) -> None:
    """The grade's metamagic or art, taken into `row` — or refused, which
    clears it from both the row and the saved choice."""
    if not row["option_id"]:
        tally.warnings.append(notice("engine.initiation.pickOption", grade=choice.grade))
        return
    if row["kind"] == "art":
        _take_art(choice, row, tally)
    else:
        _take_metamagic(choice, row, tally)


def _refuse(choice: InitiationChoice, row: dict[str, Any], tally: _Tally, warning: Notice) -> None:
    tally.warnings.append(warning)
    choice.option_id = ""
    row["option_id"] = ""


def _named(row: dict[str, Any], spec: dict[str, Any]) -> None:
    row.update(
        {
            "option_id": spec["id"],
            "name": spec["name"],
            "source": spec.get("source") or "",
            "page": spec.get("page") or "",
        }
    )


def _take_art(choice: InitiationChoice, row: dict[str, Any], tally: _Tally) -> None:
    g = choice.grade
    spec = _magic_art_by_id(row["option_id"])
    if not spec:
        _refuse(choice, row, tally, notice("engine.initiation.artUnknownDropped", grade=g))
        return
    if spec["name"] in tally.seen_art:
        _refuse(choice, row, tally, notice("engine.initiation.duplicateDropped", name=term(str(spec["name"]))))
        return
    tally.seen_art.add(spec["name"])
    tally.art_names.add(spec["name"])
    tally.arts.append(
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
        tally.bonus_sources.append((spec["name"], list(spec.get("bonus") or [])))
    _named(row, spec)


def _take_metamagic(choice: InitiationChoice, row: dict[str, Any], tally: _Tally) -> None:
    g = choice.grade
    spec = _metamagic_by_id(row["option_id"])
    if not spec:
        _refuse(choice, row, tally, notice("engine.initiation.metamagicUnknownDropped", grade=g))
        return
    refusal = _metamagic_refusal(spec, g, tally)
    if refusal:
        _refuse(choice, row, tally, refusal)
        return
    _warn_unmet_requirements(spec, tally)
    tally.seen_meta.add(spec["name"])
    tally.metamagic_names.add(spec["name"])
    tally.metamagics.append(
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
        tally.bonus_sources.append((spec["name"], list(spec.get("bonus") or [])))
    _named(row, spec)


def _metamagic_refusal(spec: dict[str, Any], g: int, tally: _Tally) -> Notice | None:
    """Why this grade cannot take this metamagic: taken already, not for this
    kind of initiate, or not one the tradition allows at this grade."""
    name = term(str(spec["name"]))
    if not spec.get("repeatable") and spec["name"] in tally.seen_meta:
        return notice("engine.initiation.duplicateDropped", name=name)
    if tally.can_adept and not tally.can_magician and not spec.get("adept"):
        return notice("engine.initiation.notForAdepts", name=name)
    if tally.can_magician and not tally.can_adept and not spec.get("magician"):
        return notice("engine.initiation.notForMagicians", name=name)
    allowed = tally.limits.get(g) or []
    if allowed and spec["name"] not in allowed:
        return notice("engine.initiation.metamagicNotAllowed", grade=g, name=name, allowed=terms(allowed))
    return None


def _warn_unmet_requirements(spec: dict[str, Any], tally: _Tally) -> None:
    """A metamagic whose prerequisites are not met is kept, with a warning
    that names what is missing as precisely as the tree allows."""
    state = tally.state
    ctx = {
        "qualities": set(tally.quality_names) | {tally.talent_name},
        "arts": set(tally.art_names),
        "ignore_art": current_rules().ignore_art
        or (state.settings.ignore_art is None and bool(state.settings.books and "SG" not in state.settings.books)),
        "metamagics": set(tally.metamagic_names),
        "powers": set(),
        # Enhanced Mist Form needs the Mist Form power (an Infected's)
        "critter_powers": set(tally.critter_powers or ()),
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
    if not spec.get("required_tree") or requirement_tree_met(spec.get("required_tree"), ctx):
        return
    warnings = tally.warnings
    needed = [name for names in (spec.get("required") or {}).values() for name in names]
    tree = spec["required_tree"]
    children = (tree[0].get("children") or []) if len(tree) == 1 else []
    arts = [node["name"] for node in children if node.get("tag") == "art"]
    qualities = [node["name"] for node in children if node.get("tag") == "quality"]
    if arts and tree[0]["tag"] == "oneof" and len(arts) + len(qualities) == len(children):
        warnings.append(
            notice(
                "engine.initiation.requiresArtOrQuality",
                name=term(str(spec["name"])),
                arts=terms(arts),
                qualities=terms(qualities),
            )
        )
    elif arts and len(arts) == len(children):
        warnings.append(notice("engine.initiation.requiresArt", name=term(str(spec["name"])), arts=terms(arts)))
    elif needed:
        warnings.append(notice("engine.initiation.requires", name=term(str(spec["name"])), needed=terms(needed)))
    else:
        warnings.append(notice("engine.initiation.requiresUnmet", name=term(str(spec["name"]))))
