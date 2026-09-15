"""Quality resolution, split by what each step is responsible for.

``_gather``    which qualities a character has, chains included
``_picks``     what a quality still needs the player to pick
``_binders``   attaching those picks onto the bonus rows ``compute`` collected
``_context``   the snapshot every requirement tree is evaluated against
``_sides``     quality-level ``<selectside>`` and the limb it claims
``_limits``    cost discounts, and which cap a quality counts against
``_validate``  every error a quality list can raise

Imports only ``re`` / already-extracted engine modules / models — never back
into ``app.engine`` — so the import graph stays a DAG. ``app.engine``
re-exports the names ``characters.py`` / ``catalog_view.py`` need
(``is_way_quality`` / ``sanitize_quality_ids``) plus everything ``compute``
calls, and every one of those names is re-exported here, so the split is
invisible to the fourteen modules that import from it.
"""

from __future__ import annotations

from ._binders import bind_action_dice_pools, bind_select_powers, free_powers_from_grants
from ._context import quality_requirement_context
from ._gather import (
    _at_quality_limit,
    gather_qualities,
    is_way_quality,
    sanitize_quality_ids,
    tradition_quality_grants,
)
from ._limits import apply_cost_discounts, counts_toward_quality_limit, surge_metagenic_limit
from ._picks import (
    _quality_extra_key_owned,
    _quality_has_actiondicepool,
    _quality_has_selectside,
    _quality_limb_slot,
    _quality_needs_spell_category,
    _quality_needs_spirit_category,
    quality_needs_extra,
)
from ._sides import resolve_quality_sides
from ._validate import apply_quality_rules

__all__ = [
    "_at_quality_limit",
    "_quality_extra_key_owned",
    "_quality_has_actiondicepool",
    "_quality_has_selectside",
    "_quality_limb_slot",
    "_quality_needs_spell_category",
    "_quality_needs_spirit_category",
    "apply_cost_discounts",
    "apply_quality_rules",
    "bind_action_dice_pools",
    "bind_select_powers",
    "counts_toward_quality_limit",
    "free_powers_from_grants",
    "gather_qualities",
    "is_way_quality",
    "quality_needs_extra",
    "quality_requirement_context",
    "resolve_quality_sides",
    "sanitize_quality_ids",
    "surge_metagenic_limit",
    "tradition_quality_grants",
]
