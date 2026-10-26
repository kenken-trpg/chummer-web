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
from ...notices import Notice, notice, term, terms, ui
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
        "source": spec.get("source"),
        "page": spec.get("page"),
        "effects": mentor_effects(spec.get("bonus") or []),
        "choices": [_public_choice(state, choice, selected, skills_data) for choice in allowed],
    }
    return {
        "warnings": warnings,
        "errors": errors,
        "bonus_sources": bonus_sources,
        "free_powers": free_powers,
        "public": public,
    }


#: Tags whose nodes differ only by the name they apply to: one line per
#: value, naming them all (Shooter's +1 accuracy for twelve weapon skills).
_LISTED = {
    "specificskill": "engine.mentorEffect.skill",
    "skillcategory": "engine.mentorEffect.skillCategory",
    "skillgroup": "engine.mentorEffect.skillGroup",
    "weaponskillaccuracy": "engine.mentorEffect.accuracy",
}
#: Tags that carry nothing but a value.
_PLAIN = {
    "damageresistance": "engine.mentorEffect.damageResistance",
    "composure": "engine.mentorEffect.composure",
    "judgeintentions": "engine.mentorEffect.judgeIntentions",
    "memory": "engine.mentorEffect.memory",
    "initiative": "engine.mentorEffect.initiative",
    "matrixinitiative": "engine.mentorEffect.matrixInitiative",
}
#: Resistance tags folded into one line per family; Chummer gives each vector.
_FAMILIES = {"toxin": "engine.mentorEffect.toxinResist", "pathogen": "engine.mentorEffect.pathogenResist"}
_MATRIX_ATTRS = {"attack": "Attack", "sleaze": "Sleaze", "dataprocessing": "Data Processing", "firewall": "Firewall"}


def _value(node: dict[str, Any]) -> str:
    fields = node.get("fields") or {}
    raw = str(fields.get("bonus") or fields.get("val") or fields.get("value") or node.get("value") or "").strip()
    return raw if raw.startswith(("-", "+")) or not raw else f"+{raw}"


def mentor_effects(nodes: list[dict[str, Any]]) -> list[Notice]:
    """A mentor's fixed ``<bonus>`` as short lines the client renders — what
    the engine applies, in place of the rulebook's advantage text the app does
    not reproduce. Choices are not here: their checkboxes name them."""
    out: list[Notice] = []
    listed: dict[tuple[str, str], tuple[int, list[str]]] = {}
    families: dict[str, str] = {}
    for node in nodes:
        tag = str(node.get("tag") or "")
        fields = node.get("fields") or {}
        attrs = node.get("attrs") or {}
        value = _value(node)
        family = next((name for name in _FAMILIES if tag.startswith(name) and tag.endswith("resist")), "")
        if tag in _LISTED:
            if (tag, value) not in listed:
                listed[(tag, value)] = (len(out), [])
                out.append(notice(_LISTED[tag], value=value))
            names = listed[(tag, value)][1]
            if str(fields.get("name") or "") not in names:
                names.append(str(fields.get("name") or ""))
        elif family:
            if family not in families:
                families[family] = value
                out.append(notice(_FAMILIES[family], value=value))
        elif tag in _PLAIN:
            out.append(notice(_PLAIN[tag], value=value))
        elif tag == "selectskill":
            out.append(_select_skill(attrs, fields, value))
        elif tag == "addqualities":
            for grant in node.get("quality_grants") or []:
                pick = str(grant.get("select") or "")
                out.append(
                    notice("engine.mentorEffect.qualityPick", name=term(grant["name"]), pick=term(pick))
                    if pick
                    else notice("engine.mentorEffect.quality", name=term(grant["name"]))
                )
        elif tag == "skillgrouplevel":
            out.append(
                notice("engine.mentorEffect.skillGroupLevel", name=term(str(fields.get("name") or "")), value=value)
            )
        elif tag == "actiondicepool":
            out.append(notice("engine.mentorEffect.action", name=term(str(fields.get("name") or "")), value=value))
        elif tag == "skillcategorykarmacost":
            out.append(
                notice(
                    "engine.mentorEffect.karmaCost",
                    name=term(str(fields.get("name") or "")),
                    value=value,
                    min=str(fields.get("min") or ""),
                )
            )
        elif tag == "livingpersona":
            for key, amount in fields.items():
                if key in _MATRIX_ATTRS:
                    out.append(
                        notice(
                            "engine.mentorEffect.persona",
                            name=term(_MATRIX_ATTRS[key]),
                            value=_value({"value": amount}),
                        )
                    )
        else:
            out.append(notice("engine.mentorEffect.other"))
    for at, names in listed.values():
        out[at]["params"]["names"] = terms(names)
    return out


def _select_skill(attrs: dict[str, Any], fields: dict[str, Any], value: str) -> Notice:
    """``<selectskill>``: a skill the player picks, from a list, a category or
    the knowledge skills."""
    key = (
        "engine.mentorEffect.pickSkillRating"
        if str(fields.get("applytorating") or "").lower() == "true"
        else "engine.mentorEffect.pickSkill"
    )
    if attrs.get("limittoskill"):
        options = [name.strip() for name in str(attrs["limittoskill"]).split(",") if name.strip()]
        return notice(key, options=terms(options), value=value)
    if attrs.get("skillcategory"):
        return notice(key, options=terms([str(attrs["skillcategory"])]), value=value)
    if str(attrs.get("knowledgeskills") or "").lower() == "true":
        return notice(key, options=ui("engine.mentorEffect.knowledge"), value=value)
    return notice(key, options=ui("engine.mentorEffect.anySkill"), value=value)


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
