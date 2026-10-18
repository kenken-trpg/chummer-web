"""The dict every `<required>` / `<forbidden>` tree is evaluated against.

Assembled once per compute and passed to `requirement_tree_met` wherever a
requirement is checked — qualities, ware, gear, powers — so they all answer to
the same snapshot of the character.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ...data_loader import catalog
from ...models import CharacterState
from ..constants import quality_optional_power_extra_key
from ..lookups import critter_power_label
from ..special_attributes import special_attribute_floors

#: Where a `critter_power_sources` power came from when no quality gave it.
METATYPE_SOURCE = "metatype"


def bought_source(install_id: str) -> str:
    """The `critter_power_sources` source of a power bought on the tab."""
    return f"bought:{install_id}"


def bought_critter_powers(state: CharacterState) -> list[tuple[str, str]]:
    """(install id, power name) for each power bought on the Critter Powers tab."""
    names = {str(row["id"]): str(row["name"]) for row in catalog().get("buyable_critter_powers") or []}
    return [(inst.id, names[inst.power_id]) for inst in state.critter_powers if inst.power_id in names]


def critter_power_sources(
    meta: dict[str, Any],
    qualities: list[dict[str, Any]],
    extras: dict[str, str],
    bought: Iterable[tuple[str, str]] = (),
) -> dict[str, set[str]]:
    """Critter power name -> what gives it: the metatype, a quality's id, or
    a purchase on the Critter Powers tab (`bought_source`).

    `<critterpower>` in a requirement tree names the power alone (Chummer
    matches `CritterPower.Name`), so a pick like `Immunity (Toxins)` counts
    as `Immunity`. The sources are kept so a quality can be checked without
    the powers it grants itself: Infected Optional Power: Compulsion forbids
    Compulsion, and is what gives it — Chummer checks that only when the
    quality is added, where this engine re-checks on every compute.
    """
    out: dict[str, set[str]] = {}
    for grant in meta.get("power_grants") or []:
        if not grant.get("unresolved"):
            out.setdefault(str(grant["name"]), set()).add(METATYPE_SOURCE)
    for q in qualities:
        picked = extras.get(quality_optional_power_extra_key(q["id"])) or ""
        refs = list(q.get("critter_powers") or [])
        refs += [ref for ref in q.get("optional_powers") or [] if critter_power_label(ref) == picked]
        for ref in refs:
            out.setdefault(str(ref["name"]), set()).add(str(q["id"]))
    for install_id, name in bought:
        out.setdefault(name, set()).add(bought_source(install_id))
    return out


def without_source(ctx: dict[str, Any], source: str) -> dict[str, Any]:
    """`ctx` without the critter powers only `source` gives — a bought power
    checked as before it was bought, the way `as_before_taking` does a quality."""
    sources: dict[str, set[str]] = ctx.get("critter_power_sources") or {}
    return {**ctx, "critter_powers": {name for name, ids in sources.items() if ids - {source}}}


def as_before_taking(ctx: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
    """`ctx` as it was before `quality` was taken: without the quality itself
    and the critter powers only it gives.

    Chummer evaluates a quality's `<required>` / `<forbidden>` when it is
    added (`RequirementsMetAsync`), so the quality and what it grants are not
    there yet. Re-checking against the finished character instead made
    Infected: Mutaqua — whose forbidden list names Mutaqua — forbid itself,
    and an Infected Optional Power forbid the power it gives.
    """
    sources: dict[str, set[str]] = ctx.get("critter_power_sources") or {}
    qid = str(quality["id"])
    return {
        **ctx,
        "qualities": set(ctx.get("qualities") or ()) - {quality["name"]},
        "critter_powers": {name for name, ids in sources.items() if ids - {qid}},
    }


def quality_requirement_context(
    state: CharacterState,
    talent: dict[str, Any],
    qualities: list[dict[str, Any]],
    meta: dict[str, Any],
    ess: float,
    ess_lost: float,
    skill_totals: dict[str, int],
    power_names: set[str],
    spell_names: set[str],
    tradition_name: str,
    cyber_names: set[str],
    bio_names: set[str],
    knowledge_ratings: dict[str, int] | None = None,
) -> dict[str, Any]:
    specials = special_attribute_floors(meta, talent)
    metatypes = {state.metatype}
    if state.metavariant:
        metatypes.add(state.metavariant)
    parent = meta.get("parent")
    if parent:
        metatypes.add(str(parent))
    categories = {str(meta.get("category") or "")}
    power_sources = critter_power_sources(meta, qualities, state.quality_extras, bought_critter_powers(state))
    return {
        "qualities": {item["name"] for item in qualities},
        "metatypes": metatypes,
        "metatype_categories": {name for name in categories if name},
        "magenabled": "MAG" in specials,
        "resenabled": "RES" in specials,
        "powers": power_names,
        "critter_powers": set(power_sources),
        "critter_power_sources": power_sources,
        "cyberware": cyber_names,
        "bioware": bio_names,
        "spells": spell_names,
        "tradition": tradition_name,
        "skills": skill_totals,
        "knowledge": dict(knowledge_ratings if knowledge_ratings is not None else state.knowledge_skills or {}),
        "essence": ess,
        "ess_lost": ess_lost,
    }
