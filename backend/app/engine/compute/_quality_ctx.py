"""The requirement context a quality's `<required>` tree is read against.

Built twice: in ``economy`` (a `<costdiscount>` tree decides what a quality
costs before karma is summed) and in ``finalize`` (the quality rules). Both
need the same picture of the character, so it is built in one place.
"""

from __future__ import annotations

from typing import Any

from ..qualities import quality_requirement_context
from .context import Ctx


def quality_req_ctx(ctx: Ctx) -> dict[str, Any]:
    tradition = ctx.magic.get("tradition") if isinstance(ctx.magic.get("tradition"), dict) else {}
    return quality_requirement_context(
        ctx.state,
        ctx.talent,
        ctx.qualities,
        ctx.meta,
        ctx.ess,
        ctx.ess_lost,
        ctx.effective_skills,
        set(ctx.adept.get("power_names") or []),
        {str(item.get("name") or "") for item in (ctx.magic.get("public") or []) if item.get("name")},
        str((tradition or {}).get("name") or ""),
        {item["name"] for item in ctx.cyber_installed},
        {item["name"] for item in ctx.bio_installed},
        ctx.effective_knowledge,
    )
