"""Phase 15 — the social pass: contacts, martial arts, spend breakdowns,
notoriety / public awareness."""

from __future__ import annotations

from ...improvements import apply_bonus_nodes
from ...notices import notice
from ...rules import current_rules
from ..contacts import resolve_contacts, sync_quality_contacts
from ..gear import apply_unarmed_bonuses
from ..martial_arts import resolve_martial_arts, sync_quality_martial_arts
from ._career import (
    nuyen_spend_breakdown,
)
from ._career_qualities import career_quality_karma
from ._quality_ctx import quality_req_ctx
from .context import Ctx


def _social_pass(ctx: Ctx) -> None:
    """Phase 15 — contacts and martial arts (both karma, so after the ledger
    opens), the spend breakdowns, and notoriety / street cred / public
    awareness."""
    # Chummer's `{CHAUnaug}`: free contact points come off natural Charisma,
    # so a tailored-pheromones bonus does not buy a bigger network.
    cha = ctx.ratings["CHA"]
    ctx.warnings.extend(sync_quality_contacts(ctx.state, ctx.effects, ctx.qualities))
    ctx.contacts = resolve_contacts(
        ctx.state,
        int(cha or 0),
        career=ctx.career,
        friends_in_high_places=bool(ctx.effects.get("friends_in_high_places")),
        black_market_contact_id=ctx.bmp_contact_id if ctx.bmp_active else "",
        contact_karma_adj=int(ctx.effects.get("contact_karma_adj") or 0),
        contact_karma_min=int(ctx.effects.get("contact_karma_min") or 0),
        excon=bool(ctx.effects.get("excon")),
    )
    ctx.warnings.extend(ctx.contacts["warnings"])
    ctx.karma_spent += int(ctx.contacts.get("karma") or 0)

    martial_ctx = quality_req_ctx(ctx)
    martial_ctx = {
        **martial_ctx,
        "qualities": set(martial_ctx.get("qualities") or []) | {ctx.talent["name"]},
    }
    ctx.warnings.extend(sync_quality_martial_arts(ctx.state, ctx.effects, ctx.qualities))
    ctx.martial = resolve_martial_arts(ctx.state, martial_ctx, ctx.errors, career=ctx.career)
    ctx.warnings.extend(ctx.martial["warnings"])
    for source, nodes in ctx.martial.get("bonus_sources") or []:
        apply_bonus_nodes(nodes, ctx.effects, source)
    apply_unarmed_bonuses(
        ctx.gear.get("weapons"),
        int(ctx.effects.get("unarmed_reach") or 0),
        int(ctx.effects.get("unarmed_ap") or 0),
    )
    ctx.karma_spent += int(ctx.martial.get("karma") or 0)
    ctx.karma_spent += int(ctx.initiation.get("karma") or 0)
    ctx.karma_spent += int(ctx.submersion.get("karma") or 0)
    baseline_qualities = ctx.state.career_baseline.quality_ids if ctx.state.career_baseline else None
    if ctx.career and baseline_qualities is not None:
        ctx.quality_career_pricing = True
        ctx.quality_career_karma, ctx.quality_career_costs, ctx.qualities_removed = career_quality_karma(
            ctx.qualities, ctx.free_quality_ids, baseline_qualities
        )
        ctx.karma_spent += ctx.quality_career_karma
    if ctx.career:
        ctx.karma_pool += int(ctx.state.karma_adjust or 0)
    ctx.karma_left = ctx.karma_pool - ctx.karma_spent

    ctx.karma_spend_lines = list(ctx.career_adv_lines)
    for key, amount in (
        ("engine.spend.qualities", ctx.karma_from_q),
        ("engine.spend.qualitiesCareer", ctx.quality_career_karma),
        ("engine.spend.metatype", ctx.metatype_karma_cost if ctx.is_karma else ctx.heritage_karma_cost),
        ("engine.spend.attributesKarma", ctx.attr_karma),
        ("engine.spend.skillsKarma", ctx.skill_buy_karma),
        ("engine.spend.knowledgeKarma", ctx.knowledge_karma),
        ("engine.spend.specializations", ctx.spec_karma),
        ("engine.spend.nuyenExchange", int(ctx.state.karma_nuyen or 0)),
        ("engine.spend.mysticPP", ctx.mystic_karma),
        ("engine.spend.adeptPower", ctx.extra_adept_karma),
        ("engine.spend.spells", ctx.spell_karma),
        ("engine.spend.spiritServices", ctx.spirit_karma),
        ("engine.spend.contactsOver", int(ctx.contacts.get("karma") or 0)),
        ("engine.spend.martialArts", int(ctx.martial.get("karma") or 0)),
        ("engine.spend.initiation", int(ctx.initiation.get("karma") or 0)),
        ("engine.spend.submersion", int(ctx.submersion.get("karma") or 0)),
    ):
        if amount:
            ctx.karma_spend_lines.append({"kind": "other", "notice": notice(key), "amount": int(amount)})
    ctx.nuyen_spend_lines = nuyen_spend_breakdown(
        ctx.cyber_installed,
        ctx.bio_installed,
        ctx.gear,
        qi_nuyen=int(ctx.qi.get("nuyen") or 0),
        foci_nuyen=int(ctx.foci.get("nuyen") or 0),
        spirits_nuyen=int(ctx.spirits.get("nuyen") or 0),
        markup_nuyen=ctx.nuyen_markup,
    )

    ctx.quality_notoriety = int(ctx.effects.get("notoriety") or 0)
    # Chummer `CalculatedNotoriety`: burned Street Cred, two for one
    ctx.notoriety_total = (
        ctx.quality_notoriety + int(ctx.state.notoriety_bonus or 0) - int(ctx.state.burnt_street_cred or 0) // 2
    )
    # SR5 p.372: a point of Street Cred per 10 karma earned in play, on top of
    # what the table hands out (`street_cred`, Chummer's own manual field).
    # Consummate Professional (AP p.17) raises the 10.
    ctx.street_cred_divisor = max(1, 10 + int(ctx.effects.get("street_cred_divisor") or 0))
    ctx.street_cred_earned = int(ctx.state.karma_earned or 0) // ctx.street_cred_divisor if ctx.career else 0
    ctx.street_cred_total = max(
        0, ctx.street_cred_earned + int(ctx.state.street_cred or 0) - int(ctx.state.burnt_street_cred or 0)
    )
    # Chummer `TotalPublicAwareness`: what the GM awarded, what qualities
    # give, and — only under `<usecalculatedpublicawareness>`, off in every
    # preset it ships — a point per three of Street Cred and Notoriety.
    quality_pa = int(ctx.effects.get("public_awareness") or 0)
    earned_pa = (
        (ctx.street_cred_total + max(0, ctx.notoriety_total)) // 3
        if current_rules().use_calculated_public_awareness
        else 0
    )
    ctx.public_awareness_total = max(0, int(ctx.state.public_awareness or 0) + quality_pa + earned_pa)
    if ctx.effects.get("erased") and ctx.public_awareness_total >= 1:
        ctx.public_awareness_total = 1
