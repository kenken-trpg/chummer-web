"""Chummer's ``precedence`` rule: which of several bonuses to one value count.

The tagged bonuses are parked in ``effects["precedence_bonus"]`` by
``nodes/stats.py`` rather than added, and folded into the plain buckets here.
Bonuses keep arriving after the first pass (adept powers, drugs), so this runs
more than once per character and each call applies only the change since the
last — hence ``precedence_applied``."""

from __future__ import annotations

from .effects import EffectsDict


def precedence_value(groups: dict[str, list[int]]) -> int:
    """Chummer's rule for bonuses tagged ``precedence`` (ImprovementManager
    ``ValueOf``): with any precedence 0 present only the *best* of them counts,
    plus every precedence −1 — reflex augmentations do not stack (SR5 p.459).
    Without one, the precedence 1 bonuses stack (the wireless Wired Reflexes +
    Reaction Enhancers pair); a lone −1 group gives its best."""
    zero, minus, one = groups.get("0") or [], groups.get("-1") or [], groups.get("1") or []
    if zero:
        return max(zero) + sum(minus)
    if one:
        return sum(one)
    return max(minus) if minus else 0


def resolve_precedence(effects: EffectsDict) -> None:
    """Fold the precedence groups into the plain buckets. Bonuses keep coming
    after the first pass (adept powers, drugs), and Wired Reflexes against
    Improved Reflexes is one group across all of them — so the groups stay,
    and each call applies only the change since the last one. Untagged
    bonuses (a drug's REA, say) were added directly and keep stacking."""
    applied = effects.setdefault("precedence_applied", {})
    for key, groups in (effects.get("precedence_bonus") or {}).items():
        delta = precedence_value(groups) - int(applied.get(key) or 0)
        if not delta:
            continue
        applied[key] = int(applied.get(key) or 0) + delta
        if key.startswith("attr:"):
            name = key[len("attr:") :]
            effects["attribute_bonus"][name] = int(effects["attribute_bonus"].get(name) or 0) + delta
        elif key in ("initiative_dice", "initiative"):
            effects[key] += delta  # type: ignore[literal-required]
