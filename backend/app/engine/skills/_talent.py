"""The skills a priority talent hands out at a fixed rating (SR5 p.65 and the
talents Chummer adds: Adept's one active skill, Aspected Magician's group)."""

from __future__ import annotations

from typing import Any

from ..bundle_types import TalentSkills

#: Chummer's `GetMatrixSkillList`: the Cracking and Electronics skills.
_MATRIX_GROUPS = {"Cracking", "Electronics"}

#: The one `<skilltype xpath>` the vendored priorities.xml uses (Adept): any
#: active skill but a Resonance / Depth one and a grouped magical one.
_ADEPT_XPATH = (
    "not(attribute = 'RES' or attribute = 'DEP') and "
    "(not(category = 'Magical Active') or skillgroup = '' or not(skillgroup))"
)


def _qualifies(spec: dict[str, Any], row: dict[str, Any]) -> bool:
    typ = str(spec.get("type") or "")
    category = str(row.get("category") or "")
    group = str(row.get("skillgroup") or "")
    if typ == "magic":
        return category in {"Magical Active", "Pseudo-Magical Active"}
    if typ == "resonance":
        return category == "Resonance Active" or group in _MATRIX_GROUPS
    if typ == "matrix":
        return group in _MATRIX_GROUPS
    if typ == "specific":
        return str(row.get("name") or "") in (spec.get("choices") or [])
    if typ == "xpath" and " ".join(str(spec.get("xpath") or "").split()) == _ADEPT_XPATH:
        return str(row.get("attribute") or "") not in {"RES", "DEP"} and (category != "Magical Active" or not group)
    # an xpath this does not know (custom data) or no type: any active skill,
    # which is what Chummer offers when it has no filter
    return True


def talent_skill_options(spec: dict[str, Any] | None, skills_data: dict[str, Any]) -> list[str]:
    """What the talent's pickers offer, sorted — skill names, or group names
    for a ``group`` talent."""
    if not spec:
        return []
    if spec.get("group"):
        return sorted(str(g) for g in spec.get("choices") or [])
    return sorted(
        str(row["name"]) for row in skills_data.get("skills") or [] if not row.get("exotic") and _qualifies(spec, row)
    )


def resolve_talent_skills(picked: list[str], spec: dict[str, Any] | None, skills_data: dict[str, Any]) -> TalentSkills:
    """The talent's free skills as the character has picked them.

    Picks that the talent does not offer, repeats, and any past its count are
    dropped, so a changed talent or priority cannot leave a free rating behind.
    """
    options = talent_skill_options(spec, skills_data)
    qty = int((spec or {}).get("qty") or 0)
    kept: list[str] = []
    for name in picked:
        if name in options and name not in kept and len(kept) < qty:
            kept.append(name)
    return {
        "qty": qty,
        "rating": int((spec or {}).get("val") or 0) if spec else 0,
        "group": bool((spec or {}).get("group")),
        "options": options,
        "picked": kept,
    }
