"""Spell resolution.

``resolve_spells`` walks the character's spell list against the tradition,
free-spell allowances (priority + freespells improvements + touch-only pools),
descriptor/category limits and per-kind karma, emitting the public rows plus
the drain-resistance summary. The ``bind_*`` helpers resolve empty
quality-driven spell/spirit-category slots from ``quality_extras``, and
``apply_granted_spells`` keeps addspell grants in sync.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import SPELL_CATEGORIES
from ...improvements import apply_bonus_nodes
from ...models import CharacterState, SpellInstall
from ..constants import MAG_TALENTS, SPELL_KARMA, SPELL_TALENTS, quality_spirit_category_extra_key
from ..lookups import _spell_by_id, _spell_by_name, _tradition_by_id
from ._common import _active_skill_rating_from_state, spell_cast_info, tradition_resist


def _tradition_public(tradition: dict[str, Any] | None) -> dict[str, Any] | None:
    if not tradition:
        return None
    return {
        "id": tradition["id"],
        "name": tradition["name"],
        "drain": tradition.get("drain") or "",
        "drain_attrs": list(tradition.get("drain_attrs") or []),
        "spirits": dict(tradition.get("spirits") or {}),
        "source": tradition.get("source"),
        "page": tradition.get("page"),
    }


def apply_tradition_bonuses(effects: dict[str, Any], tradition: dict[str, Any] | None) -> None:
    if not tradition:
        return
    nodes = list(tradition.get("bonus") or [])
    if not nodes:
        return
    apply_bonus_nodes(nodes, effects, str(tradition.get("name") or "Tradition"))


def spell_defense_pools(effects: dict[str, Any] | None) -> dict[str, Any]:
    general = int((effects or {}).get("spell_resistance") or 0)
    specific = (effects or {}).get("spell_defense_resist") or {}
    decrease_attrs = ("BOD", "AGI", "REA", "STR", "CHA", "LOG", "INT", "WIL")
    return {
        "general": general,
        "direct_mana": general + int(specific.get("direct_mana") or 0),
        "detection": general + int(specific.get("detection") or 0),
        "mental_manipulation": general + int(specific.get("mental_manipulation") or 0),
        "mana_illusion": general + int(specific.get("mana_illusion") or 0),
        "physical_illusion": general + int(specific.get("physical_illusion") or 0),
        "decrease": {attr: general + int(specific.get(f"decrease_{attr.lower()}") or 0) for attr in decrease_attrs},
    }


def bind_spell_spirit_limits(
    effects: dict[str, Any],
    qualities: list[dict[str, Any]],
    state: CharacterState,
    errors: list[str],
) -> None:
    """Resolve empty limitspell/spiritcategory slots from quality_extras."""
    by_name = {q["name"]: q for q in qualities}
    extras = state.quality_extras or {}
    spell_limits: list[str] = []
    for slot in effects.get("limit_spell_category_slots") or []:
        value = str(slot.get("value") or "").strip()
        source = str(slot.get("source") or "")
        spec = by_name.get(source)
        if not value and spec:
            value = str(extras.get(spec["id"]) or "").strip()
            if not value:
                errors.append(f"{spec['name']} の呪文カテゴリを選んでください")
                continue
            options = list(spec.get("select_options") or [])
            if options and value not in options:
                errors.append(f"{spec['name']} の呪文カテゴリが不正です")
                continue
        if value and value not in spell_limits:
            spell_limits.append(value)
    spirit_limits: list[str] = []
    for slot in effects.get("limit_spirit_category_slots") or []:
        spirits = [str(name).strip() for name in (slot.get("spirits") or []) if str(name).strip()]
        source = str(slot.get("source") or "")
        spec = by_name.get(source)
        if not spirits and spec:
            picked = str(extras.get(quality_spirit_category_extra_key(spec["id"])) or "").strip()
            if not picked and not _limit_spell_needs_from_spec(spec):
                picked = str(extras.get(spec["id"]) or "").strip()
            if not picked:
                errors.append(f"{spec['name']} の精霊を選んでください")
                continue
            options = list(spec.get("spirit_options") or [])
            if options and picked not in options:
                errors.append(f"{spec['name']} の精霊が不正です")
                continue
            spirits = [picked]
        for name in spirits:
            if name and name not in spirit_limits:
                spirit_limits.append(name)
    effects["limit_spell_categories"] = spell_limits
    effects["limit_spirit_categories"] = spirit_limits


def bind_spell_category_drain_damage(
    effects: dict[str, Any],
    qualities: list[dict[str, Any]],
    state: CharacterState,
) -> None:
    """Fill empty spellcategorydrain/damage categories from the quality's selected spell category."""
    by_name = {q["name"]: q for q in qualities}
    extras = state.quality_extras or {}
    for key in ("spell_category_drain", "spell_category_damage"):
        for row in effects.get(key) or []:
            if str(row.get("category") or "").strip():
                continue
            source = str(row.get("source") or "")
            spec = by_name.get(source)
            if not spec:
                continue
            picked = str(extras.get(spec["id"]) or "").strip()
            if picked:
                row["category"] = picked


def apply_granted_spells(
    state: CharacterState,
    effects: dict[str, Any],
    qualities: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    """Ensure addspell quality bonuses exist on the character; drop orphans."""
    by_name = {q["name"]: q for q in qualities}
    grants: list[dict[str, Any]] = []
    for row in effects.get("grant_spells") or []:
        source = str(row.get("source") or "")
        q = by_name.get(source)
        if not q:
            continue
        spell_name = str(row.get("name") or "").strip()
        spec = _spell_by_name(spell_name)
        if not spec:
            warnings.append(f"{source} の呪文 {spell_name} が見つかりません")
            continue
        grants.append(
            {
                "quality_id": q["id"],
                "spell_id": spec["id"],
                "alchemical": bool(row.get("alchemical")),
            }
        )
    wanted_qids = {str(g["quality_id"]) for g in grants}

    remaining: list[SpellInstall] = []
    for inst in state.spells or []:
        sq = str(inst.source_quality_id or "").strip()
        if sq and sq not in wanted_qids:
            continue
        remaining.append(inst)

    existing_by_qid = {
        str(inst.source_quality_id): inst for inst in remaining if str(inst.source_quality_id or "").strip()
    }
    existing_spell_ids = {str(inst.spell_id) for inst in remaining}
    for grant in grants:
        qid = str(grant["quality_id"])
        if qid in existing_by_qid:
            inst = existing_by_qid[qid]
            inst.spell_id = str(grant["spell_id"])
            inst.alchemical = bool(grant["alchemical"])
            continue
        if str(grant["spell_id"]) in existing_spell_ids:
            continue
        remaining.append(
            SpellInstall(
                spell_id=str(grant["spell_id"]),
                source_quality_id=qid,
                alchemical=bool(grant["alchemical"]),
            )
        )
    state.spells = remaining


def _limit_spell_needs_from_spec(spec: dict[str, Any]) -> bool:
    return any(
        node.get("tag") == "limitspellcategory" and not str(node.get("value") or "").strip()
        for node in (spec.get("bonus") or [])
    )


def _spell_allowed_by_limits(
    spec: dict[str, Any],
    effects: dict[str, Any],
    *,
    range_gated: bool = False,
) -> bool:
    range_ = str(spec.get("range") or "").strip()
    allowed_ranges = [str(r).strip() for r in (effects.get("allow_spell_ranges") or []) if str(r).strip()]
    # Chummer SelectSpell: AllowSpellRange bypasses descriptor/category limits
    if allowed_ranges and range_ in allowed_ranges:
        return True
    for blocked in effects.get("block_spell_descriptors") or []:
        text = str(blocked or "").strip()
        if not text:
            continue
        if text.lower() == "spell" and (spec.get("kind") or "spell") == "spell":
            return False
        descriptor = str(spec.get("descriptor") or "")
        if text and text in descriptor:
            return False
    # Pure Adept (etc.): only ranges granted by allowspellrange
    if range_gated:
        return False
    category = str(spec.get("category") or "")
    limits = list(effects.get("limit_spell_categories") or [])
    allows = list(effects.get("allow_spell_categories") or [])
    if limits or allows:
        allowed = set(limits) | set(allows)
        if category not in allowed:
            return False
    return True


def _spell_kind_karma_type(kind: str) -> str:
    if kind == "ritual":
        return "Rituals"
    if kind == "enchantment":
        return "Preparations"
    return "Spells"


def spell_karma_cost(kind: str | None, effects: dict[str, Any] | None = None) -> int:
    """Base spell karma (default 5) plus newspellkarmacost improvements for the spell type."""
    cost = SPELL_KARMA
    category = _spell_kind_karma_type(kind or "spell")
    for row in (effects or {}).get("new_spell_karma_cost") or []:
        row_type = str(row.get("type") or "").strip()
        if row_type and row_type != category:
            continue
        cost += int(row.get("value") or 0)
    return max(0, cost)


def _apply_free_spell_limit(value: int, limit: str) -> tuple[int, bool]:
    """Return (points, touch_only) from freespells limit attrs like half,touchonly."""
    parts = {part.strip().lower() for part in str(limit or "").split(",") if part.strip()}
    points = int(value)
    if "half" in parts:
        points = (points + 1) // 2  # DivAwayFromZero for positive ints
    return max(0, points), "touchonly" in parts


def free_spell_bonus_points(
    effects: dict[str, Any] | None,
    state: CharacterState,
    attrs: dict[str, int] | None = None,
    skills_data: dict[str, Any] | None = None,
) -> tuple[int, int]:
    """Return (generic_free, touch_only_free) from freespells improvements."""
    effects = effects or {}
    generic = int(effects.get("free_spells_flat") or 0)
    touch_only = 0
    for row in effects.get("free_spells_skill") or []:
        skill = str(row.get("skill") or "").strip()
        if not skill:
            continue
        rating = _active_skill_rating_from_state(state, skill, skills_data)
        points, is_touch = _apply_free_spell_limit(rating, str(row.get("limit") or ""))
        if is_touch:
            touch_only += points
        else:
            generic += points
    attr_totals = attrs or {}
    for row in effects.get("free_spells_attribute") or []:
        attr = str(row.get("attribute") or "").strip().upper()
        if not attr:
            continue
        value = int(attr_totals.get(attr) or 0)
        points, is_touch = _apply_free_spell_limit(value, str(row.get("limit") or ""))
        if is_touch:
            touch_only += points
        else:
            generic += points
    return max(0, generic), max(0, touch_only)


def _spell_is_touch_range(spec: dict[str, Any]) -> bool:
    raw = str(spec.get("range") or "").strip()
    return raw in {"T", "T (A)"}


def resolve_spells(
    state: CharacterState,
    talent: dict[str, Any],
    mag: int,
    attrs: dict[str, int],
    owned_magic_names: set[str] | None = None,
    effects: dict[str, Any] | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    owned = set(owned_magic_names or [])
    effects = effects or {}
    tradition = _tradition_by_id(state.tradition_id)
    if state.tradition_id and not tradition:
        warnings.append("選んだ伝統が見つからないため外しました")
        state.tradition_id = None
    resist, resist_attrs = tradition_resist(tradition, attrs)
    resist += int(effects.get("drain_resist") or 0)
    allow_ranges = [str(r).strip() for r in (effects.get("allow_spell_ranges") or []) if str(r).strip()]
    range_gated = talent["name"] not in SPELL_TALENTS and bool(allow_ranges)
    can_spells = talent["name"] in SPELL_TALENTS or bool(allow_ranges)
    if not can_spells:
        state.spells = []
        if talent["name"] not in MAG_TALENTS:
            state.tradition_id = None
        return {
            "warnings": warnings,
            "public": public,
            "free_max": 0,
            "used": 0,
            "paid": 0,
            "karma": 0,
            "tradition": None,
            "resist": resist,
            "resist_attrs": resist_attrs,
            "range_gated": False,
        }

    if not tradition:
        warnings.append("伝統を選んでください")
    priority_free = int(talent.get("spells") or 0) if talent["name"] in SPELL_TALENTS else 0
    bonus_free, touch_free = free_spell_bonus_points(effects, state, attrs)
    free_max = priority_free + bonus_free + touch_free
    free_generic_left = priority_free + bonus_free
    free_touch_left = touch_free
    seen: set[str] = set()
    kept: list[SpellInstall] = []
    karma_total = 0
    paid = 0
    for inst in state.spells:
        spec = _spell_by_id(inst.spell_id)
        if not spec:
            continue
        if spec.get("category") not in SPELL_CATEGORIES:
            warnings.append(f"{spec['name']} はこの段階では扱えません")
            continue
        if not _spell_allowed_by_limits(spec, effects, range_gated=range_gated):
            warnings.append(f"{spec['name']} はこの制限では習得できません（{spec.get('category') or '—'}）")
            continue
        if spec["id"] in seen:
            warnings.append(f"{spec['name']} は重複しているため外しました")
            continue
        seen.add(spec["id"])
        kind = spec.get("kind") or "spell"
        has_force = kind != "enchantment"
        granted = bool(inst.source_quality_id)
        is_touch = _spell_is_touch_range(spec)
        free = False
        if granted:
            free = True
        elif is_touch and free_touch_left > 0:
            free = True
            free_touch_left -= 1
        elif free_generic_left > 0:
            free = True
            free_generic_left -= 1
        # Pure Adept free touch spells use Barehanded Adept casting rules (Chummer)
        barehanded = talent["name"] == "Adept" and free and is_touch and not granted
        info = spell_cast_info(
            spec["name"],
            inst.force if has_force else None,
            mag,
            resist,
            resist_attrs,
            effects=effects,
            barehanded=barehanded,
        )
        if info and has_force:
            inst.force = int(info["force"])
        missing = [
            name for names in (spec.get("required") or {}).values() for name in names if name and name not in owned
        ]
        if missing:
            warnings.append(f"{spec['name']} には {' / '.join(missing)} が必要です")
        cost = 0 if free else spell_karma_cost(kind, effects)
        if not free:
            paid += 1
            karma_total += cost
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "spell_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category"),
                "kind": kind,
                "useskill": "Unarmed Combat" if barehanded else (spec.get("useskill") or "Spellcasting"),
                "has_force": has_force,
                "type": spec.get("type"),
                "range": spec.get("range"),
                "duration": spec.get("duration"),
                "descriptor": spec.get("descriptor"),
                "dv": spec.get("dv") or "",
                "damage": spec.get("damage") or "",
                "damage_mod": int((info or {}).get("damage_mod") or 0) if has_force else 0,
                "required": missing,
                "source": spec.get("source"),
                "page": spec.get("page"),
                "free": free,
                "karma": cost,
                "barehanded_adept": barehanded,
                "alchemical": bool(inst.alchemical),
                "granted": granted,
                "spell": info if has_force else None,
            }
        )
    state.spells = kept
    return {
        "warnings": warnings,
        "public": public,
        "free_max": free_max,
        "used": len(public),
        "paid": paid,
        "karma": karma_total,
        "tradition": _tradition_public(tradition),
        "resist": resist,
        "resist_attrs": resist_attrs,
        "range_gated": range_gated,
    }
