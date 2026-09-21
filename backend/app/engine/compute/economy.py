"""Phases 12 + 13 + 14 + 15 — priority points / nuyen, skills, karma
totals and the social pass (contacts, martial arts, spend breakdowns,
notoriety / public awareness)."""

from ._econ_karma import _karma_totals
from ._econ_priority import _priority_points
from ._econ_skills import _skill_spend
from ._econ_social import _social_pass
from .context import Ctx


def economy(ctx: Ctx) -> None:
    """Phases 12 + 13 + 14 + 15.

    Four passes that used to be one 480-line function. They talk to each other
    only through `ctx`, which is what made the split mechanical: the two locals
    that crossed a boundary (`current_rules()` and the skill-category map) are
    both pure projections, recomputed where they are needed rather than
    threaded through.
    """
    _priority_points(ctx)
    _skill_spend(ctx)
    _karma_totals(ctx)
    _social_pass(ctx)
