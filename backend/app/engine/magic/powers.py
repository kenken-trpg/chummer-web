"""Adept power resolution.

``resolve_adept_powers`` prices the character's chosen powers (levels, Way
discounts, Mystic Adept power points) and emits the bonus nodes each power
grants. The ``power_*`` helpers (cost, max rating, select options, bonus
binding) are also used by the mentor and Qi-focus resolvers.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...data_loader import SPELL_CAST_CATEGORIES, catalog
from ...improvements import substitute_rating
from ...models import CharacterState
from ...notices import Notice, notice, term, terms, ui
from ...rules import current_rules
from ..bundle_types import AdeptBundle, EnhancementsBundle
from ..constants import ADEPT_TALENTS
from ..formulas import _ceil_div
from ..lookups import _enhancement_by_id, _power_by_id, _power_by_name
from ..selects import parse_selectskill_spec, selectskill_options
from ._common import spell_cast_info

#: What ``<selectlimit>`` offers, and the fixed-limit tag each pick becomes.
#: Chummer names the limits it wants to narrow to inside the bonus; with none
#: named, all three qualify.
LIMIT_CHOICES = ("Physical", "Mental", "Social")
LIMIT_BONUS_TAGS = {name: f"{name.lower()}limit" for name in LIMIT_CHOICES}


def power_point_cost(spec: dict[str, Any], rating: int, discounted: bool = False) -> float:
    points = float(spec.get("points") or 0)
    extra = float(spec.get("extrapointcost") or 0)
    rating = max(1, int(rating))
    if spec.get("levels"):
        cost = points * rating
        if extra:
            cost += extra
    else:
        cost = points
    if discounted:
        cost = max(0.0, cost - float(spec.get("adeptway") or 0))
    return round(cost, 4)


def way_discount_cap(mag: int) -> float:
    return float(_ceil_div(max(int(mag), 0) / 4))


def way_discount_eligible(spec: dict[str, Any], quality_names: set[str], magicians_way: bool) -> bool:
    if not float(spec.get("adeptway") or 0):
        return False
    if magicians_way and not spec.get("magicianswayforbids"):
        return True
    return any(name in quality_names for name in (spec.get("adeptwayrequires") or []))


def power_max_rating(spec: dict[str, Any], mag: int, learned: int | None = None) -> int:
    """How many levels a power may have (Chummer's `Power.TotalMaximumLevels`).

    Improved Ability is capped by the boosted skill's ``learned`` rating —
    half of it rounded up, or that plus the rating under
    `<increasedimprovedabilitymodifier>` — and, like every power, by MAG.
    With no skill picked yet only MAG caps it.
    """
    if not spec.get("levels"):
        return 1
    if spec.get("maxlevels"):
        return int(spec["maxlevels"])
    cap = max(1, int(mag))
    if str(spec.get("name") or "").startswith("Improved Ability") and learned is not None:
        half = _ceil_div(max(int(learned), 0) / 2)
        boost = int(learned) + half if current_rules().increased_improved_ability_modifier else half
        cap = min(cap, max(1, boost))
    return cap


def improved_ability_learned(
    state: CharacterState, spec: dict[str, Any], extra: str, skills_data: dict[str, Any]
) -> int | None:
    """The learned rating Improved Ability is capped by: the picked active
    skill's own rating or its group's, unaugmented (`Skill.LearnedRating`).
    `None` for any other power, or before a skill is picked."""
    if not extra or not str(spec.get("name") or "").startswith("Improved Ability"):
        return None
    group = next(
        (str(s.get("skillgroup") or "") for s in skills_data.get("skills") or [] if s.get("name") == extra),
        "",
    )
    return max(int((state.skills or {}).get(extra) or 0), int((state.skill_groups or {}).get(group) or 0))


def _field_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if value:
        return [str(value)]
    return []


def bind_power_bonus(nodes: list[dict[str, Any]], extra: str, rating: int) -> list[dict[str, Any]]:
    bound: list[dict[str, Any]] = []
    for node in substitute_rating(nodes, rating):
        tag = node.get("tag")
        fields = dict(node.get("fields") or {})
        if tag == "selectskill":
            if not extra:
                continue
            fields["name"] = extra
            bound.append({"tag": "specificskill", "fields": fields})
            continue
        if tag == "selectattribute":
            bonus = fields.get("val") or fields.get("bonus") or fields.get("value")
            if not extra or bonus in (None, ""):
                continue
            bound.append({"tag": "specificattribute", "fields": {"name": extra, "bonus": bonus}})
            continue
        if tag == "selectlimit":
            # The pick names the limit, the value is what it gains — so the
            # node becomes the fixed `<physicallimit>` the pick chose.
            bonus = fields.get("val") or fields.get("bonus") or fields.get("value")
            limit_tag = LIMIT_BONUS_TAGS.get(extra.strip().title())
            if not limit_tag or bonus in (None, ""):
                continue
            bound.append({"tag": limit_tag, "fields": {"val": bonus}})
            continue
        if tag == "selectspell":
            continue
        bound.append(node)
    return bound


def power_select_options(spec: dict[str, Any], skills_data: dict[str, Any]) -> list[str]:
    kind = spec.get("select")
    if kind == "skill":
        node = next((item for item in (spec.get("bonus") or []) if item.get("tag") == "selectskill"), None)
        if not node:
            return []
        parsed = parse_selectskill_spec(node)
        parsed["minimumrating"] = 0
        return selectskill_options(parsed, skills_data, {})
    if kind == "attribute":
        node = next((item for item in (spec.get("bonus") or []) if item.get("tag") == "selectattribute"), None)
        if not node:
            return []
        return _field_list((node.get("fields") or {}).get("attribute"))
    if kind == "spell":
        return [item["name"] for item in catalog().get("spells") or [] if item.get("category") in SPELL_CAST_CATEGORIES]
    if kind == "limit":
        node = next((item for item in (spec.get("bonus") or []) if item.get("tag") == "selectlimit"), None)
        if not node:
            return []
        named = {name.title() for name in _field_list((node.get("fields") or {}).get("limit"))}
        return [name for name in LIMIT_CHOICES if not named or name in named]
    return []


def resolve_adept_powers(
    state: CharacterState,
    talent_name: str,
    mag: int,
    skills_data: dict[str, Any],
    quality_names: set[str],
    magicians_way: bool,
    free_powers: list[dict[str, Any]] | None = None,
    wil: int = 1,
    intuition: int = 1,
) -> AdeptBundle:
    if talent_name not in ADEPT_TALENTS:
        return {
            "warnings": [],
            "errors": [],
            "public": [],
            "bonus_sources": [],
            "spent": 0.0,
            "discount_used": 0.0,
            "discount_max": 0.0,
            "mystic_pp": 0,
            "power_names": set(),
        }
    free_by_key, free_notes = _free_gifts(free_powers or [])
    installed_names = _installed_names(state, free_by_key)
    adept = _Adept(state, mag, skills_data, free_by_key, free_notes, installed_names, way_discount_cap(mag))
    for inst in state.adept_powers:
        spec = _power_by_id(inst.power_id)
        if spec:
            adept.price(inst, spec, quality_names, magicians_way, wil + intuition)
    # what is left was given and never bought: it shows, free, on its own row
    for key, free_levels in free_by_key.items():
        spec = _power_by_id(key[0])
        if spec:
            adept.add_free_only(spec, key, free_levels)
    if adept.discount_used > adept.cap_limit + 1e-9:
        adept.errors.append(
            notice("engine.adept.wayDiscountOver", used=f"{adept.discount_used:g}", max=f"{adept.cap_limit:g}")
        )
    return {
        "warnings": adept.warnings,
        "errors": adept.errors,
        "public": adept.public,
        "bonus_sources": adept.bonus_sources,
        "spent": round(adept.spent, 4),
        "discount_used": round(adept.discount_used, 4),
        "discount_max": adept.cap_limit,
        "mystic_pp": max(0, min(int(mag), int(state.mystic_pp or 0))) if talent_name == "Mystic Adept" else 0,
        "power_names": installed_names,
    }


def _free_gifts(
    free_powers: list[dict[str, Any]],
) -> tuple[dict[tuple[str, str], int], dict[tuple[str, str], list[Notice]]]:
    """Free levels per (power, pick), and a note naming where each came from."""
    free_by_key: dict[tuple[str, str], int] = {}
    free_notes: dict[tuple[str, str], list[Notice]] = {}
    for gift in free_powers:
        spec = _power_by_id(gift["power_id"]) or _power_by_name(gift.get("name") or "")
        if not spec:
            continue
        extra = (gift.get("extra") or "").strip()
        key = (spec["id"], extra)
        free_by_key[key] = free_by_key.get(key, 0) + max(1, int(gift.get("rating") or 1))
        source = gift.get("source") or ""
        free_notes.setdefault(key, []).append(
            notice("engine.adept.freeFrom", source=term(source)) if source else notice("engine.adept.free")
        )
    return free_by_key, free_notes


def _installed_names(state: CharacterState, free_by_key: dict[tuple[str, str], int]) -> set[str]:
    """Every power the character has, bought or given — what `required` is checked against."""
    names = set()
    for inst in state.adept_powers:
        spec = _power_by_id(inst.power_id)
        if spec:
            names.add(spec["name"])
    for key in free_by_key:
        spec = _power_by_id(key[0])
        if spec:
            names.add(spec["name"])
    return names


@dataclass
class _Adept:
    """The power rows, their power-point spend and the Way discount they use."""

    state: CharacterState
    mag: int
    skills_data: dict[str, Any]
    free_by_key: dict[tuple[str, str], int]
    free_notes: dict[tuple[str, str], list[Notice]]
    installed_names: set[str]
    cap_limit: float
    warnings: list[Notice] = field(default_factory=list)
    errors: list[Notice] = field(default_factory=list)
    public: list[dict[str, Any]] = field(default_factory=list)
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = field(default_factory=list)
    seen_keys: set[tuple[str, str]] = field(default_factory=set)
    spent: float = 0.0
    discount_used: float = 0.0

    def price(
        self, inst: Any, spec: dict[str, Any], quality_names: set[str], magicians_way: bool, drain_pool: int
    ) -> None:
        """One bought power: its rating, pick, Way discount and cost."""
        extra = (inst.extra or "").strip()
        cap = power_max_rating(spec, self.mag, improved_ability_learned(self.state, spec, extra, self.skills_data))
        free_levels = self.free_by_key.get((spec["id"], extra), 0)
        paid_max = max(1, cap - free_levels) if spec.get("levels") else 1
        rating = 1 if not spec.get("levels") else max(1, min(paid_max, int(inst.rating or 1)))
        inst.rating = rating
        options = power_select_options(spec, self.skills_data)
        extra = self._checked_pick(inst, spec, extra, options)
        key = (spec["id"], extra)
        free_levels = self.free_by_key.get(key, 0)
        kind = spec.get("select")
        spell = (
            spell_cast_info(extra, inst.force, self.mag, drain_pool, "WIL+INT") if kind == "spell" and extra else None
        )
        if spell:
            inst.force = int(spell["force"])
        if kind and extra and key in self.seen_keys:
            self.warnings.append(notice("engine.adept.duplicate", name=term(str(spec["name"])), extra=term(extra)))
        self.seen_keys.add(key)
        for needed in spec.get("required") or []:
            if needed not in self.installed_names:
                self.warnings.append(
                    notice("engine.adept.requires", name=term(str(spec["name"])), needed=terms([needed]))
                )
        eligible = way_discount_eligible(spec, quality_names, magicians_way)
        discounted = self._way_discount(inst, spec, eligible)
        full_cost = power_point_cost(spec, rating, False)
        cost = 0.0 if (not spec.get("levels") and free_levels) else power_point_cost(spec, rating, discounted)
        self.spent += cost
        total_rating = rating if not spec.get("levels") else min(cap, rating + free_levels)
        if not spec.get("levels") and free_levels:
            total_rating = 1
        self.bonus_sources.append((spec["name"], bind_power_bonus(spec.get("bonus") or [], extra, total_rating)))
        self.public.append(
            {
                "id": inst.id,
                "power_id": spec["id"],
                "name": spec["name"],
                "rating": rating,
                "total_rating": total_rating,
                "free_levels": free_levels,
                "rating_min": 1,
                "rating_max": paid_max,
                "extra": extra,
                "cost": cost,
                "full_cost": full_cost,
                "discounted": discounted,
                "can_discount": eligible,
                "select": kind,
                "options": options,
                "source": spec.get("source"),
                "page": spec.get("page"),
                "notes": list(self.free_notes.get(key) or []),
                "spell": spell,
            }
        )
        self.free_by_key.pop(key, None)

    def _checked_pick(self, inst: Any, spec: dict[str, Any], extra: str, options: list[str]) -> str:
        """The saved pick if it is one of the options, else "" — warned either way."""
        kind = spec.get("select")
        if kind and extra and extra not in options:
            self.warnings.append(notice("engine.adept.selectInvalid", name=term(str(spec["name"])), picked=term(extra)))
            extra = ""
            inst.extra = None
        if kind and not extra:
            select_key = kind if kind in {"skill", "attribute", "spell", "limit"} else "target"
            self.warnings.append(
                notice("engine.adept.pickSelect", name=term(str(spec["name"])), what=ui(f"engine.select.{select_key}"))
            )
        return extra

    def _way_discount(self, inst: Any, spec: dict[str, Any], eligible: bool) -> bool:
        """Whether the Way discount applies, within what MAG allows; it is
        dropped, with a warning, from the first power that would go over."""
        discounted = bool(inst.discounted) and eligible
        if discounted and self.discount_used + float(spec.get("adeptway") or 0) > self.cap_limit + 1e-9:
            discounted = False
            self.warnings.append(notice("engine.adept.wayDiscountCap", name=term(str(spec["name"]))))
        inst.discounted = discounted
        if discounted:
            self.discount_used += float(spec.get("adeptway") or 0)
        return discounted

    def add_free_only(self, spec: dict[str, Any], key: tuple[str, str], free_levels: int) -> None:
        """A power the character was given and never bought."""
        extra = key[1]
        cap = power_max_rating(spec, self.mag, improved_ability_learned(self.state, spec, extra, self.skills_data))
        total_rating = 1 if not spec.get("levels") else min(cap, free_levels)
        options = power_select_options(spec, self.skills_data)
        self.bonus_sources.append((spec["name"], bind_power_bonus(spec.get("bonus") or [], extra, total_rating)))
        self.public.append(
            {
                "id": f"free:{spec['id']}:{extra}",
                "power_id": spec["id"],
                "name": spec["name"],
                "rating": 0,
                "total_rating": total_rating,
                "free_levels": free_levels,
                "rating_min": 0,
                "rating_max": 0,
                "extra": extra,
                "cost": 0.0,
                "full_cost": 0.0,
                "discounted": False,
                "can_discount": False,
                "select": spec.get("select"),
                "options": options,
                "source": spec.get("source"),
                "page": spec.get("page"),
                "notes": list(self.free_notes.get(key) or []),
                "free_only": True,
            }
        )


def resolve_enhancements(
    state: CharacterState,
    talent_name: str,
    quality_names: set[str],
    power_names: set[str],
) -> EnhancementsBundle:
    warnings: list[Notice] = []
    public: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    kept: list[str] = []
    if talent_name not in ADEPT_TALENTS:
        state.adept_enhancements = []
        return {"warnings": warnings, "public": public, "bonus_sources": bonus_sources, "karma": 0}
    for eid in state.adept_enhancements:
        spec = _enhancement_by_id(eid)
        if not spec:
            continue
        req = spec.get("required") or {}
        missing_quality = [name for name in (req.get("quality") or []) if name not in quality_names]
        missing_power = [name for name in (req.get("power") or []) if name not in power_names]
        if spec.get("power") and spec["power"] not in power_names and spec["power"] not in missing_power:
            missing_power.append(spec["power"])
        if missing_quality:
            warnings.append(
                notice("engine.adept.droppedWithQuality", name=term(str(spec["name"])), needed=terms(missing_quality))
            )
            continue
        missing = missing_power
        if missing:
            warnings.append(notice("engine.adept.requires", name=term(str(spec["name"])), needed=terms(missing)))
        kept.append(spec["id"])
        bonus_sources.append((spec["name"], spec.get("bonus") or []))
        public.append(
            {
                "id": spec["id"],
                "name": spec["name"],
                "power": spec.get("power"),
                "karma": current_rules().karma_enhancement,
                "source": spec.get("source"),
                "page": spec.get("page"),
                "ok": not missing,
            }
        )
    state.adept_enhancements = kept
    return {
        "warnings": warnings,
        "public": public,
        "bonus_sources": bonus_sources,
        "karma": current_rules().karma_enhancement * len(kept),
    }
