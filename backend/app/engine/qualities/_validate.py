"""Every error a quality list can raise.

The picks that are still missing or no longer valid, the requirement and
forbidden trees, the two 25-karma caps, and the SURGE metagenic rules
(RF p.106). Returns the negative karma gained, which `compute` spends.
"""

from __future__ import annotations

from typing import Any

from ...models import CharacterState
from ...notices import Notice, notice, term
from ...rules import current_rules
from ..constants import (
    _normalize_side,
    quality_addspirit_extra_key,
    quality_optional_power_extra_key,
    quality_spirit_category_extra_key,
)
from ..lookups import critter_power_label
from ..requirements import requirement_tree_met
from ._limits import counts_toward_quality_limit, surge_metagenic_limit
from ._picks import (
    _quality_extra_key_owned,
    _quality_has_actiondicepool,
    _quality_has_selectside,
    _quality_needs_spell_category,
    _quality_needs_spirit_category,
    quality_needs_extra,
)


def _is_flavour_text_only(spec: dict[str, Any]) -> bool:
    """A quality whose only unfilled pick is a line of prose.

    `<selecttext>` on its own sets the quality's Extra and nothing else — what
    you regret (Big Regret), who wants you (Wanted). No rule reads it, so an
    empty one cannot make a build illegal, and Chummer saves it empty without
    complaint on three of its own test characters. A pick that carries a
    mechanical choice — a skill, an attribute, an expertise — is a different
    thing and stays an error: the bonus cannot be applied without it.
    """
    if spec.get("select_options") or spec.get("optional_powers"):
        return False
    tags = [node.get("tag") for node in (spec.get("bonus") or [])]
    return tags == ["selecttext"]


def apply_quality_rules(
    state: CharacterState,
    qualities: list[dict[str, Any]],
    free_quality_ids: list[str],
    ctx: dict[str, Any],
    errors: list[Notice],
    *,
    career: bool = False,
    report: dict[str, Any] | None = None,
    warnings: list[Notice] | None = None,
) -> int:
    owned = {item["id"] for item in qualities}
    extras = {
        key: str(value).strip()
        for key, value in (state.quality_extras or {}).items()
        if _quality_extra_key_owned(key, owned) and str(value).strip()
    }
    state.quality_extras = extras
    free_ids = set(free_quality_ids)
    surge = surge_metagenic_limit(qualities) > 0
    negative_gain = 0
    positive_spend = 0
    for spec in qualities:
        is_free = bool(spec.get("onlyprioritygiven") or spec["id"] in free_ids)
        # Chummer's `PositiveQualityLimitKarma` / `NegativeQualityLimitKarma`
        counted = not is_free and counts_toward_quality_limit(spec, surge)
        if counted and spec["karma"] < 0:
            negative_gain += -int(spec["karma"])
        if counted and spec["karma"] > 0:
            positive_spend += int(spec["karma"])
        if str(spec.get("extra_kind") or "") == "add_spirit":
            count = max(1, int(spec.get("add_spirit_count") or 1))
            if any(quality_addspirit_extra_key(spec["id"], idx) not in extras for idx in range(count)):
                errors.append(notice("engine.qualities.pickAddSpirit", name=term(str(spec["name"]))))
        elif quality_needs_extra(spec) and spec["id"] not in extras:
            if _quality_has_selectside(spec):
                errors.append(notice("engine.qualities.pickSide", name=term(str(spec["name"]))))
            elif _quality_has_actiondicepool(spec):
                errors.append(notice("engine.qualities.pickMatrixAction", name=term(str(spec["name"]))))
            elif _quality_needs_spell_category(spec):
                errors.append(notice("engine.qualities.pickSpellCategory", name=term(str(spec["name"]))))
            elif _quality_needs_spirit_category(spec):
                errors.append(notice("engine.qualities.pickSpirit", name=term(str(spec["name"]))))
            elif str(spec.get("extra_kind") or "") == "weapon_skill":
                errors.append(notice("engine.qualities.pickWeaponSkill", name=term(str(spec["name"]))))
            elif _is_flavour_text_only(spec):
                if warnings is not None:
                    warnings.append(notice("engine.qualities.pickText", name=term(str(spec["name"]))))
            else:
                errors.append(notice("engine.qualities.pickExtra", name=term(str(spec["name"]))))
        optional = [critter_power_label(row) for row in spec.get("optional_powers") or []]
        if optional:
            picked = extras.get(quality_optional_power_extra_key(spec["id"]))
            if not picked:
                errors.append(notice("engine.qualities.pickOptionalPower", name=term(str(spec["name"]))))
            elif picked not in optional:
                errors.append(notice("engine.qualities.extraInvalid", name=term(str(spec["name"]))))
        if _quality_needs_spirit_category(spec) and _quality_needs_spell_category(spec):
            spirit_key = quality_spirit_category_extra_key(spec["id"])
            if spirit_key not in extras:
                errors.append(notice("engine.qualities.pickSpirit", name=term(str(spec["name"]))))
        elif _quality_has_selectside(spec) and spec["id"] in extras and not _normalize_side(extras[spec["id"]]):
            errors.append(notice("engine.qualities.sideInvalid", name=term(str(spec["name"]))))
        options = list(spec.get("select_options") or [])
        if not options:
            for node in spec.get("bonus") or []:
                if node.get("tag") != "selectquality":
                    continue
                raw = (node.get("fields") or {}).get("quality") or node.get("value") or []
                options = [str(item).strip() for item in (raw if isinstance(raw, list) else [raw]) if str(item).strip()]
        if options and spec["id"] in extras and extras[spec["id"]] not in options:
            if not _quality_has_actiondicepool(spec):
                errors.append(notice("engine.qualities.extraInvalid", name=term(str(spec["name"]))))
        if is_free or career:
            # `<required>` / `<forbidden>` are a purchase-time gate, not a
            # standing invariant: Chummer evaluates `RequirementsMetAsync` when
            # a quality is *added* and never again. So a career character who
            # legally bought Apt Pupil at Arcana 6 keeps it after moving those
            # points elsewhere, and re-deciding it every compute would call two
            # of Chummer's own career saves illegal. In creation the engine is
            # the only gate there is, so the check stays.
            continue
        if spec.get("required_tree") and not requirement_tree_met(spec.get("required_tree"), ctx):
            errors.append(notice("engine.qualities.prereq", name=term(str(spec["name"]))))
        forbidden = spec.get("forbidden_tree") or []
        if forbidden and requirement_tree_met(forbidden, ctx):
            errors.append(notice("engine.qualities.forbidden", name=term(str(spec["name"]))))
    rules = current_rules()
    if negative_gain > rules.quality_karma_cap_negative and not career and not rules.quality_exceed_negative:
        errors.append(
            notice(
                "engine.qualities.negativeCap", karma=negative_gain, limit=current_rules().quality_karma_cap_negative
            )
        )
    if positive_spend > current_rules().quality_karma_cap_positive and not career:
        errors.append(
            notice(
                "engine.qualities.positiveCap", karma=positive_spend, limit=current_rules().quality_karma_cap_positive
            )
        )

    # --- Metagenic / SURGE (Run Faster p.106) ------------------------------
    metagenic_limit = surge_metagenic_limit(qualities)
    mg_specs = [spec for spec in qualities if spec.get("metagenic") and spec.get("contributes_to_limit")]
    mg_pos = sum(int(spec["karma"]) for spec in mg_specs if int(spec["karma"]) > 0)
    mg_neg = sum(-int(spec["karma"]) for spec in mg_specs if int(spec["karma"]) < 0)
    mg_balanced = (not mg_pos) or mg_neg in (mg_pos, mg_pos - 1)
    if not career:
        if (mg_pos or mg_neg) and metagenic_limit <= 0:
            # RF p.106 sells metagenic qualities to Changelings alone, but the
            # data does not say so — Chummer keeps non-Changelings away from
            # them by filtering its purchase list, and its validity sweep runs
            # the whole metagenic block only `if (intMetagenicLimit > 0)`. So a
            # save that holds one without SURGE is legal as far as Chummer is
            # concerned, and calling it invalid would reject a character it
            # wrote. Said, not enforced.
            if warnings is not None:
                warnings.append(notice("engine.qualities.metagenicNeedsChangeling"))
        elif metagenic_limit > 0:
            if mg_neg > metagenic_limit:
                errors.append(notice("engine.qualities.metagenicNegativeCap", karma=mg_neg, limit=metagenic_limit))
            if mg_pos > metagenic_limit:
                errors.append(notice("engine.qualities.metagenicPositiveCap", karma=mg_pos, limit=metagenic_limit))
            if mg_pos and not mg_balanced:
                errors.append(
                    notice(
                        "engine.qualities.metagenicUnbalanced",
                        negative=mg_neg,
                        min=max(0, mg_pos - 1),
                        max=mg_pos,
                    )
                )
    if report is not None:
        report["metagenic"] = {
            "limit": metagenic_limit,
            "positive": mg_pos,
            "negative": mg_neg,
            "balanced": bool(mg_balanced),
            "count": len(mg_specs),
        }
    return negative_gain
