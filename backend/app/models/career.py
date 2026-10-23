"""Career mode: the chargen baseline and the reward ledger."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CareerBaseline(BaseModel):
    """Snapshot of chargen ratings when entering career mode (Priority/SumToTen raises bill from here)."""

    attributes: dict[str, int] = Field(default_factory=dict)
    skills: dict[str, int] = Field(default_factory=dict)
    skill_groups: dict[str, int] = Field(default_factory=dict)
    knowledge_skills: dict[str, int] = Field(default_factory=dict)
    skill_specializations: list[str] = Field(default_factory=list)
    exotic_skills: dict[str, int] = Field(default_factory=dict)
    # None for a baseline saved before qualities were recorded: those
    # characters keep the chargen price for every quality they hold.
    quality_ids: list[str] | None = None
    # Every gear / ware instance id owned on entering career, so what was
    # bought after is known (Restricted / Forbidden markup). None for an
    # older baseline: nothing is marked up.
    item_ids: list[str] | None = None
    # A mystic adept's power points bought at chargen, so a career purchase
    # can be told apart (`<mysaddppcareer>`). None for an older baseline.
    mystic_pp: int | None = None
    # How far MAG / RES / DEP stood below their bought rating from essence
    # loss on entering career. Chummer prices a career raise from the value
    # after the loss; this keeps loss taken later from refunding raises
    # already paid. None until the first career compute records it.
    special_drop: dict[str, int] | None = None
    # The same drop for each level of MAG / RES / DEP raised in career, as it
    # stood when that level was bought: a raise is priced from the value of
    # its day, so ware installed between two raises makes only the later one
    # cheaper. None for a baseline from before it was kept, whose existing
    # levels take `special_drop` (capped by today's).
    raise_drops: dict[str, list[int]] | None = None


class RewardEntry(BaseModel):
    """Career reward ledger row (run payout, bonus, etc.)."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str = ""
    karma: int = 0
    nuyen: int = 0
