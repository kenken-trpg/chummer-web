"""Mentor spirit resolution.

``resolve_mentor`` picks the character's mentor choices (respecting adept /
magician audience gates), collects the bonus nodes and free powers they grant,
and shapes the public payload the UI renders.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import parse_select_power_slot
from ...models import CharacterState
from ...notices import Notice, notice, term
from ..constants import ADEPT_TALENTS, MAG_TALENTS
from ..lookups import _mentor_by_id, _paragon_by_id, _power_by_name
from .powers import power_select_options


def _choice_allowed(audience: str, talent_name: str) -> bool:
    if audience == "all":
        return True
    if audience == "adept":
        return talent_name in ADEPT_TALENTS
    if audience == "magician":
        return talent_name in MAG_TALENTS and talent_name != "Adept"
    return False


def _power_target_key(choice_name: str, power_name: str) -> str:
    """Where a granted power's own pick lives in ``mentor_extras``.

    A choice that also carries ``<selectpowers>`` already spends its plain
    ``mentor_extras[choice]`` on *which* power it grants (Chaos, SG p.200), so a
    power that then asks for a target of its own — the ``<selectlimit>`` on
    Improved Potential (Chaos Mentor) — needs a key beside it.
    """
    return f"{choice_name} / {power_name}"


def resolve_mentor(
    state: CharacterState,
    talent_name: str,
    needs_mentor: bool,
    skills_data: dict[str, Any],
    *,
    paragon: bool = False,
) -> dict[str, Any]:
    """``paragon`` reads the pick out of ``paragons.xml`` instead.

    A paragon (KC p.102) is the technomancer's mentor spirit, and Chummer
    models it with the same class in the same ``<mentorspirit>`` element, so it
    lives in the same ``state.mentor_id`` here. The two qualities cannot meet:
    Mentor Spirit wants an awakened quality, Paragon wants Technomancer, and no
    character is both.
    """
    warnings: list[Notice] = []
    errors: list[Notice] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    free_powers: list[dict[str, Any]] = []
    if not needs_mentor:
        state.mentor_id = None
        state.mentor_choices = []
        state.mentor_extras = {}
        return {
            "warnings": warnings,
            "errors": errors,
            "bonus_sources": bonus_sources,
            "free_powers": free_powers,
            "public": None,
        }
    spec = _paragon_by_id(state.mentor_id or "") if paragon else _mentor_by_id(state.mentor_id or "")
    if not spec:
        warnings.append(notice("engine.qualities.paragonMissing" if paragon else "engine.qualities.mentorMissing"))
        return {
            "warnings": warnings,
            "errors": errors,
            "bonus_sources": bonus_sources,
            "free_powers": free_powers,
            "public": None,
        }
    bonus_sources.append((spec["name"], spec.get("bonus") or []))
    allowed = [
        choice for choice in spec.get("choices") or [] if _choice_allowed(choice.get("audience") or "all", talent_name)
    ]
    selected: list[str] = []
    wanted = {name for name in (state.mentor_choices or []) if name}
    for choices in _choice_groups(allowed).values():
        names = [choice["name"] for choice in choices]
        picked = next((name for name in names if name in wanted), "") or names[0]
        selected.append(picked)
        choice = next(item for item in choices if item["name"] == picked)
        choice_nodes = [node for node in (choice.get("bonus") or []) if node.get("tag") != "specificpower"]
        bonus_sources.append((f"{spec['name']}: {picked}", choice_nodes))
        free_powers.extend(_granted_powers(state, spec, choice, skills_data, warnings))
    state.mentor_choices = selected
    public = {
        "id": spec["id"],
        "name": spec["name"],
        "advantage": spec.get("advantage") or "",
        "disadvantage": spec.get("disadvantage") or "",
        "source": spec.get("source"),
        "choices": [_public_choice(state, choice, selected, skills_data) for choice in allowed],
    }
    return {
        "warnings": warnings,
        "errors": errors,
        "bonus_sources": bonus_sources,
        "free_powers": free_powers,
        "public": public,
    }


def _choice_groups(allowed: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """The choices one pick is made from, as Chummer's `SelectMentorSpirit`
    lists them: those of `set="2"` in the second box, every other one the
    character may take in the first — an "Adept:" or "Magician:" choice is
    one more option there, not a pick of its own (Berserker's adept takes
    one of its three)."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for choice in allowed:
        groups.setdefault(f"set:{choice.get('set') or '1'}", []).append(choice)
    return groups


def _granted_powers(
    state: CharacterState,
    spec: dict[str, Any],
    choice: dict[str, Any],
    skills_data: dict[str, Any],
    warnings: list[Notice],
) -> list[dict[str, Any]]:
    """The free powers a picked choice grants, each bound to its own pick or the choice's."""
    picked = choice["name"]
    extra = (state.mentor_extras or {}).get(picked, "")
    granted: list[dict[str, Any]] = []
    for power in choice.get("powers") or []:
        power_spec = _power_by_name(power["name"])
        if not power_spec:
            continue
        options = power_select_options(power_spec, skills_data)
        own = (state.mentor_extras or {}).get(_power_target_key(picked, power_spec["name"]), "")
        bound_extra = next((value for value in (own, extra) if value in options), "")
        if power_spec.get("select") and not bound_extra:
            warnings.append(
                notice(
                    "engine.qualities.mentorPowerTarget",
                    mentor=term(str(spec["name"])),
                    power=term(str(power_spec["name"])),
                )
            )
        granted.append(
            {
                "power_id": power_spec["id"],
                "name": power_spec["name"],
                "rating": int(power.get("rating") or 1),
                "extra": bound_extra,
                "source": spec["name"],
            }
        )
    return granted


def _public_choice(
    state: CharacterState, choice: dict[str, Any], selected: list[str], skills_data: dict[str, Any]
) -> dict[str, Any]:
    power_options: list[str] = next(
        (
            list(parse_select_power_slot(node).get("options") or [])
            for node in choice.get("bonus") or []
            if node.get("tag") == "selectpowers"
        ),
        [],
    )
    extras = power_options
    if not extras:
        # the last granted power that exists names the options
        for power in choice.get("powers") or []:
            power_spec = _power_by_name(power["name"])
            if power_spec:
                extras = power_select_options(power_spec, skills_data)
    power_targets: list[dict[str, Any]] = []
    if power_options:
        for power in choice.get("powers") or []:
            power_spec = _power_by_name(power["name"])
            if not power_spec or not power_spec.get("select"):
                continue
            key = _power_target_key(choice["name"], power_spec["name"])
            power_targets.append(
                {
                    "power": power_spec["name"],
                    "key": key,
                    "kind": str(power_spec.get("select") or ""),
                    "extra": (state.mentor_extras or {}).get(key, ""),
                    "options": power_select_options(power_spec, skills_data),
                }
            )
    return {
        "name": choice["name"],
        "set": choice.get("set") or "",
        "audience": choice.get("audience") or "all",
        "selected": choice["name"] in selected,
        "extra": (state.mentor_extras or {}).get(choice["name"], ""),
        "extra_options": extras,
        "power_targets": power_targets,
    }
