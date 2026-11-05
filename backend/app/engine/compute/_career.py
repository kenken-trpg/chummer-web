"""Career-advancement helpers used by the economy phase (and re-exported
via ``app.engine`` for ``characters.py`` / tests): chargen baseline snapshot,
Priority/SumToTen raise-cost diff and the nuyen spend breakdown.
"""

from __future__ import annotations

import math
from typing import Any

from ...improvements import EffectsDict, empty_effects
from ...models import CareerBaseline, CharacterState
from ...notices import notice, term
from ...rules import current_rules
from ..bundle_types import GearBundle
from ..karma import (
    _active_karma_mults,
    _filter_karma_rules,
    _group_floor_map,
    _karma_cost_with_category_mods,
    _matching_karma_rules,
    _skill_category_map,
    _skill_group_category_map,
    alternate_attribute_shift,
    group_first_level,
)
from ..lookups import find_metatype
from ..skills import exotic_skill_label


def snapshot_career_baseline(state: CharacterState) -> CareerBaseline:
    # A legacy/manual purchase record overlapping the species' free grant is
    # retained in state, but was not paid at chargen. It must not become a
    # historical charge when career starts. Read the resolved species rather
    # than a potentially stale `derived` payload during the phase loop.
    meta = find_metatype(state.metatype, state.metavariant)
    innate = {q["id"] for q in meta.get("quality_grants") or [] if q.get("id")}
    return CareerBaseline(
        attributes={str(k): int(v) for k, v in (state.attributes or {}).items()},
        skills={str(k): int(v) for k, v in (state.skills or {}).items()},
        skill_groups={str(k): int(v) for k, v in (state.skill_groups or {}).items()},
        knowledge_skills={str(k): int(v) for k, v in (state.knowledge_skills or {}).items()},
        skill_specializations=sorted(
            str(name) for name, spec in (state.skill_specializations or {}).items() if str(spec or "").strip()
        ),
        exotic_skills={
            str(row.id): int(row.rating or 0) for row in (state.exotic_skills or []) if getattr(row, "id", None)
        },
        quality_ids=[str(qid) for qid in state.quality_ids or [] if qid not in innate],
        item_ids=sorted({str(row.id) for field in _ITEM_FIELDS for row in getattr(state, field) or []}),
        mystic_pp=int(state.mystic_pp or 0),
    )


#: The `CharacterState` lists whose rows a career purchase is told apart by:
#: things bought with nuyen, for the Restricted / Forbidden markup (lifestyles
#: are rent, not a buy), and the spirits / sprites chargen paid karma for.
_ITEM_FIELDS = (
    "spirits",
    "sprites",
    "cyberware",
    "bioware",
    "qi_foci",
    "foci",
    "armor",
    "armor_mods",
    "weapons",
    "weapon_accessories",
    "commlinks",
    "cyberdecks",
    "rccs",
    "optics",
    "programs",
    "apps",
    "sensors",
    "drones",
    "vehicles",
    "gear",
    "custom_drugs",
    "vehicle_mods",
    "weapon_mounts",
)

#: The published rows `restricted_markup` looks at, by `GearBundle` key.
_GEAR_ROW_KEYS = (
    "armor_items",
    "armor_mods",
    "weapons",
    "weapon_accessories",
    "commlinks",
    "cyberdecks",
    "rccs",
    "optics",
    "programs",
    "apps",
    "sensors",
    "drones",
    "vehicles",
    "vehicle_mods",
    "weapon_mounts",
    "gear",
    "custom_drugs",
)


def restricted_markup(baseline: CareerBaseline | None, rows: list[dict[str, Any]]) -> int:
    """Extra nuyen for Restricted / Forbidden things bought after chargen.

    Chummer multiplies the price of an R / F item as it is bought in career
    (`<multiplyrestrictedcost>` and the forbidden twin); what came through
    chargen is never marked up. So a row counts when its id is not in the
    baseline. A row bolted onto another new row is skipped: Chummer charges
    the whole assembly once, at the parent's availability."""
    rules = current_rules()
    factors = {"R": rules.career_restricted_cost_multiplier, "F": rules.career_forbidden_cost_multiplier}
    if baseline is None or baseline.item_ids is None or factors == {"R": 1, "F": 1}:
        return 0
    old = set(baseline.item_ids)
    new_ids = {str(row.get("id")) for row in rows if row.get("id") and str(row.get("id")) not in old}
    extra = 0
    for row in rows:
        row_id = str(row.get("id") or "")
        if not row_id or row_id in old or str(row.get("parent_id") or "") in new_ids:
            continue
        factor = factors.get(str(row.get("avail_suffix") or ""), 1)
        extra += int(row.get("nuyen") or 0) * (factor - 1)
    return extra


def career_raise_karma(
    state: CharacterState,
    baseline: CareerBaseline,
    skill_totals: dict[str, int],
    skills_data: dict[str, Any],
    *,
    effects: EffectsDict | None = None,
    ratings: dict[str, int] | None = None,
    minimums: dict[str, int] | None = None,
    level_drops: dict[str, list[int]] | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    """Karma to raise Priority/SumToTen characters from chargen snapshot to current ratings.

    ``ratings`` are the attribute ratings compute settled on (``state.attributes``
    otherwise), the same ones the baseline is taken from. ``level_drops`` is,
    for each MAG / RES / DEP level raised, how far essence loss held it below
    its rating when it was bought: Chummer's `UpgradeKarmaCost` prices a
    raise from the value after the loss.

    One spend line per thing raised, in this order: attributes, skill groups,
    active skills, knowledge skills, new specializations, exotic skills."""
    eff = effects or empty_effects()
    skill_cats = _skill_category_map(skills_data)
    skill_mults = _active_karma_mults(eff.get("skill_category_karma_cost_mult"), career=True)
    active_flat = _filter_karma_rules(eff.get("active_skill_karma_cost"), career=True)
    know_cats = _knowledge_categories(state, skills_data)
    lines = [
        *_attribute_raises(state, baseline, eff, ratings, minimums, level_drops),
        *_skill_group_raises(state, baseline, eff, skills_data),
        *_active_skill_raises(state, baseline, skill_totals, skills_data, skill_cats, skill_mults, active_flat),
        *_knowledge_raises(state, baseline, eff, know_cats, skill_mults),
        *_specialization_buys(state, baseline, eff, skill_cats, know_cats),
        *_exotic_raises(state, baseline, active_flat),
    ]
    return sum(line["amount"] for line in lines), lines


def _spend_line(kind: str, line_notice: Any, amount: int) -> dict[str, Any]:
    return {"kind": kind, "notice": line_notice, "amount": amount}


def _knowledge_categories(state: CharacterState, skills_data: dict[str, Any]) -> dict[str, str]:
    """Each knowledge skill's category: the one the character picked, else the
    catalog's. A name in neither is left out (the caller picks its default)."""
    catalog = {str(s.get("name") or ""): str(s.get("category") or "") for s in (skills_data.get("knowledge") or [])}
    picked = {name: str(cat) for name, cat in (state.knowledge_categories or {}).items() if cat}
    return {name: cat for name, cat in {**catalog, **picked}.items() if cat}


def _attribute_raises(
    state: CharacterState,
    baseline: CareerBaseline,
    eff: EffectsDict,
    ratings: dict[str, int] | None,
    minimums: dict[str, int] | None,
    level_drops: dict[str, list[int]] | None,
) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    base_attrs = baseline.attributes or {}
    attr_flat = _filter_karma_rules(eff.get("attribute_karma_cost"), career=True)
    for key, rating in (state.attributes if ratings is None else ratings).items():
        if key == "ESS":
            continue
        from_r = int(base_attrs.get(key, rating))
        to_r = int(rating or 0)
        shift = alternate_attribute_shift(key, int((minimums or {}).get(key) or 1))
        flat_rules = _matching_karma_rules(attr_flat, key)
        drops = (level_drops or {}).get(key)
        if drops:
            # one level at a time, each from the value of its own day
            cost = sum(
                _karma_cost_with_category_mods(
                    from_r + i - shift - drop,
                    from_r + i + 1 - shift - drop,
                    current_rules().karma_attribute,
                    flat_rules=flat_rules,
                )
                for i, drop in enumerate(drops)
            )
        else:
            cost = _karma_cost_with_category_mods(
                from_r - shift,
                to_r - shift,
                current_rules().karma_attribute,
                flat_rules=flat_rules,
            )
        if cost:
            lines.append(
                _spend_line("attribute", notice("engine.spend.attribute", name=key, before=from_r, after=to_r), cost)
            )
    return lines


def _skill_group_raises(
    state: CharacterState, baseline: CareerBaseline, eff: EffectsDict, skills_data: dict[str, Any]
) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    group_cat_map = _skill_group_category_map(skills_data)
    group_mults = _active_karma_mults(eff.get("skill_group_category_karma_cost_mult"), career=True)
    base_groups = baseline.skill_groups or {}
    for group, rating in (state.skill_groups or {}).items():
        from_r = int(base_groups.get(group, 0))
        to_r = int(rating or 0)
        mult = int(group_mults.get(group_cat_map.get(group, ""), 100))
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            current_rules().karma_skill_group,
            mult_pct=mult,
            first_level=group_first_level(from_r, to_r),
        )
        if cost:
            lines.append(
                _spend_line(
                    "skill_group",
                    notice("engine.spend.skillGroup", name=term(group), before=from_r, after=to_r),
                    cost,
                )
            )
    return lines


def _active_skill_raises(
    state: CharacterState,
    baseline: CareerBaseline,
    skill_totals: dict[str, int],
    skills_data: dict[str, Any],
    skill_cats: dict[str, str],
    skill_mults: dict[str, Any],
    active_flat: list[Any],
) -> list[dict[str, Any]]:
    """A skill raised past both its baseline rating and the floor its group
    sets, then or now."""
    lines: list[dict[str, Any]] = []
    base_floors = _group_floor_map(baseline.skill_groups or {}, skills_data)
    now_floors = _group_floor_map(dict(state.skill_groups or {}), skills_data)
    base_skills = baseline.skills or {}
    # `skill_totals` carries the exotic skills too, under the composed
    # `Name (extra)` label the skills phase puts them there with. The baseline's
    # `skills` has no such key, so pricing them here reads `from_r` as 0 and
    # charges the whole rating — on top of what `_exotic_raises` charges for
    # the raise. They are that one's, keyed by row id against a baseline that
    # does hold them.
    exotic_labels = {
        exotic_skill_label(str(row.skill_name), str(row.extra or "")) for row in (state.exotic_skills or [])
    }
    for name, rating in (skill_totals or {}).items():
        if name in exotic_labels:
            continue
        from_r = max(int(base_skills.get(name, 0)), int(base_floors.get(name, 0)), int(now_floors.get(name, 0)))
        to_r = int(rating or 0)
        cat = skill_cats.get(name, "")
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            current_rules().karma_active_skill,
            mult_pct=int(skill_mults.get(cat, 100)),
            flat_rules=_matching_karma_rules(active_flat, cat),
            first_level=current_rules().karma_new_active_skill,
        )
        if cost:
            lines.append(
                _spend_line("skill", notice("engine.spend.skill", name=term(name), before=from_r, after=to_r), cost)
            )
    return lines


def _knowledge_raises(
    state: CharacterState,
    baseline: CareerBaseline,
    eff: EffectsDict,
    know_cats: dict[str, str],
    skill_mults: dict[str, Any],
) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    base_know = baseline.knowledge_skills or {}
    natives = set(state.native_languages or [])
    know_flat = _filter_karma_rules(
        list(eff.get("skill_category_karma_cost") or []) + list(eff.get("knowledge_skill_karma_cost") or []),
        career=True,
    )
    know_min = _filter_karma_rules(eff.get("knowledge_skill_karma_cost_min"), career=True)
    for name, rating in (state.knowledge_skills or {}).items():
        # Belt and braces: `skills/_knowledge.py` already pops every native out
        # of `knowledge_skills` while normalising them, so nothing here reaches
        # the `continue`. Kept because this loop prices whatever the dict holds
        # and a native carried in it would be charged for a rating it does not
        # have — see `test_a_native_language_is_free_however_far_it_is_raised`.
        if name in natives:
            continue
        cat = know_cats.get(name, "Street")
        from_r = int(base_know.get(name, 0))
        to_r = int(rating or 0)
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            current_rules().karma_knowledge,
            mult_pct=int(skill_mults.get(cat, 100)),
            flat_rules=_matching_karma_rules(know_flat, cat),
            min_rules=_matching_karma_rules(know_min, cat),
            first_level=current_rules().karma_new_knowledge_skill,
        )
        if cost:
            lines.append(
                _spend_line(
                    "knowledge", notice("engine.spend.knowledge", name=term(name), before=from_r, after=to_r), cost
                )
            )
    return lines


def _specialization_buys(
    state: CharacterState,
    baseline: CareerBaseline,
    eff: EffectsDict,
    skill_cats: dict[str, str],
    know_cats: dict[str, str],
) -> list[dict[str, Any]]:
    """A specialization the baseline did not have, at the active or the
    knowledge price."""
    lines: list[dict[str, Any]] = []
    spec_mults = _active_karma_mults(eff.get("skill_category_spec_karma_cost_mult"), career=True)
    base_specs = set(baseline.skill_specializations or [])
    for name, spec in (state.skill_specializations or {}).items():
        if not str(spec or "").strip() or name in base_specs:
            continue
        cat = skill_cats.get(name) or know_cats.get(name, "")
        price = (
            current_rules().karma_specialization
            if name in skill_cats
            else current_rules().karma_knowledge_specialization
        )
        amount = max(1, int(math.ceil(price * int(spec_mults.get(cat, 100)) / 100.0)))
        lines.append(
            _spend_line(
                "specialization",
                notice("engine.spend.specialization", name=term(name), spec=term(str(spec))),
                amount,
            )
        )
    return lines


def _exotic_raises(state: CharacterState, baseline: CareerBaseline, active_flat: list[Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    base_exotic = baseline.exotic_skills or {}
    for row in state.exotic_skills or []:
        rid = str(getattr(row, "id", "") or "")
        if not rid:
            continue
        from_r = int(base_exotic.get(rid, 0))
        to_r = int(row.rating or 0)
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            current_rules().karma_active_skill,
            mult_pct=100,
            flat_rules=_matching_karma_rules(active_flat, ""),
            first_level=current_rules().karma_new_active_skill,
        )
        if cost:
            label = exotic_skill_label(str(row.skill_name), str(row.extra or ""))
            lines.append(
                _spend_line("exotic", notice("engine.spend.exotic", name=term(label), before=from_r, after=to_r), cost)
            )
    return lines


#: (`nuyen_by_bucket` key, message key), in the order the sidebar lists them.
#: Every bucket the gear engine records must appear here, or the money would
#: vanish from the breakdown while still counting against the total —
#: `test_nuyen_breakdown` holds the two together. The message keys are spelled
#: out rather than built from the bucket name so `test_notice_keys` can still
#: see them.
_GEAR_SPEND_ORDER = (
    ("armor", "engine.spend.armor"),
    ("armorMods", "engine.spend.armorMods"),
    ("weapons", "engine.spend.weapons"),
    ("weaponAccessories", "engine.spend.weaponAccessories"),
    ("commlinks", "engine.spend.commlinks"),
    ("cyberdecks", "engine.spend.cyberdecks"),
    ("rccs", "engine.spend.rccs"),
    ("optics", "engine.spend.optics"),
    ("sensors", "engine.spend.sensors"),
    ("programs", "engine.spend.programs"),
    ("drones", "engine.spend.drones"),
    ("vehicles", "engine.spend.vehicles"),
    ("vehicleMods", "engine.spend.vehicleMods"),
    ("otherGear", "engine.spend.otherGear"),
    ("customDrugs", "engine.spend.customDrugs"),
    ("lifestyles", "engine.spend.lifestyles"),
)


def nuyen_spend_breakdown(
    cyber: list[dict[str, Any]],
    bio: list[dict[str, Any]],
    gear: GearBundle,
    *,
    qi_nuyen: int = 0,
    foci_nuyen: int = 0,
    spirits_nuyen: int = 0,
    markup_nuyen: int = 0,
) -> list[dict[str, Any]]:
    """The sidebar's "where the nuyen went", as lines that add up to what was
    spent.

    The gear half comes from the tally `resolve_gear` kept while it was
    counting, not from re-adding the rows it published: a thing bolted onto
    something else has its price folded into the row it is bolted to, so the
    rows do not partition the money and adding them up counts some of it twice.
    """
    by_bucket = gear.get("nuyen_by_bucket") or {}
    buckets: list[tuple[str, int]] = [
        ("engine.spend.cyberware", sum(int(item.get("nuyen") or 0) for item in cyber)),
        ("engine.spend.bioware", sum(int(item.get("nuyen") or 0) for item in bio)),
        *((message, int(by_bucket.get(bucket) or 0)) for bucket, message in _GEAR_SPEND_ORDER),
        ("engine.spend.qiFoci", int(qi_nuyen or 0)),
        ("engine.spend.foci", int(foci_nuyen or 0)),
        ("engine.spend.spirits", int(spirits_nuyen or 0)),
        ("engine.spend.restrictedMarkup", int(markup_nuyen or 0)),
    ]
    return [{"kind": "nuyen", "notice": notice(key), "amount": amount} for key, amount in buckets if amount]
