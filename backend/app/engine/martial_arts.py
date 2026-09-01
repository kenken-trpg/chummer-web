"""Martial arts resolution.

``sync_quality_martial_arts`` reconciles the character's styles/techniques with
what qualities grant or forbid; ``resolve_martial_arts`` validates each pick
(required trees, chargen caps), prices the karma, and emits the public rows plus
the bonus nodes techniques contribute.

Imports only ``catalog`` / already-extracted engine modules / models — never
back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog
from ..models import CharacterState, MartialArtInstall
from .constants import (
    MARTIAL_ART_CHARGEN_STYLE_MAX,
    MARTIAL_ART_CHARGEN_TECHNIQUE_MAX,
    MARTIAL_ART_STYLE_KARMA,
    MARTIAL_ART_TECHNIQUE_KARMA,
)
from .requirements import requirement_tree_met


def _martial_art_by_id(art_id: str) -> dict[str, Any] | None:
    for item in catalog().get("martial_arts") or []:
        if item["id"] == art_id:
            return item
    return None


def _martial_art_by_name(name: str) -> dict[str, Any] | None:
    needle = str(name or "").strip()
    if not needle:
        return None
    for item in catalog().get("martial_arts") or []:
        if item["name"] == needle:
            return item
    return None


def _martial_technique_by_name(name: str) -> dict[str, Any] | None:
    for item in catalog().get("martial_art_techniques") or []:
        if item["name"] == name:
            return item
    return None


def _martial_art_spec_options(bonus_nodes: list[dict[str, Any]] | None) -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = []
    for node in bonus_nodes or []:
        if node.get("tag") != "addskillspecializationoption":
            continue
        fields = node.get("fields") or {}
        skill = str(fields.get("skill") or "").strip()
        spec = str(fields.get("spec") or "").strip()
        if skill and spec:
            options.append((skill, spec))
    return options


def sync_quality_martial_arts(
    state: CharacterState,
    effects: dict[str, Any],
    qualities: list[dict[str, Any]],
) -> list[str]:
    """Ensure free martial arts granted by martialart qualities exist; drop orphans."""
    warnings: list[str] = []
    by_qname = {q["name"]: q for q in qualities}
    specs: list[dict[str, Any]] = []
    for entry in effects.get("free_martial_arts") or []:
        art_name = str(entry.get("name") or "").strip()
        q = by_qname.get(str(entry.get("source") or "").strip())
        art = _martial_art_by_name(art_name)
        if not q or not art:
            continue
        specs.append({"art": art, "quality_id": q["id"], "quality_name": q["name"]})
    wanted_qids = {str(s["quality_id"]) for s in specs}

    remaining: list[MartialArtInstall] = []
    for inst in state.martial_arts or []:
        sq = str(inst.source_quality_id or "").strip()
        if sq and sq not in wanted_qids:
            continue
        remaining.append(inst)

    existing_by_qid = {
        str(inst.source_quality_id): inst for inst in remaining if str(inst.source_quality_id or "").strip()
    }
    existing_art_ids = {str(inst.art_id) for inst in remaining}
    for spec in specs:
        art = spec["art"]
        qid = str(spec["quality_id"])
        if qid in existing_by_qid:
            inst = existing_by_qid[qid]
            inst.art_id = art["id"]
            inst.free = True
            continue
        if art["id"] in existing_art_ids:
            for inst in remaining:
                if str(inst.art_id) == art["id"]:
                    inst.free = True
                    inst.source_quality_id = qid
                    break
            continue
        remaining.append(
            MartialArtInstall(
                art_id=art["id"],
                techniques=[],
                free=True,
                source_quality_id=qid,
            )
        )
    state.martial_arts = remaining
    return warnings


def resolve_martial_arts(
    state: CharacterState,
    ctx: dict[str, Any],
    errors: list[str],
    *,
    career: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    kept: list[MartialArtInstall] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    spec_extras: dict[str, list[str]] = {}
    karma = 0
    technique_total = 0
    paid_style_count = 0

    for inst in state.martial_arts or []:
        spec = _martial_art_by_id(inst.art_id)
        if not spec:
            warnings.append("未知の武道を外しました")
            continue
        is_free = bool(inst.free or inst.source_quality_id)
        if spec.get("is_quality") and not is_free:
            warnings.append(f"{spec['name']} は資質経由のみです")
            continue
        if spec.get("required_tree") and not requirement_tree_met(spec.get("required_tree"), ctx):
            errors.append(f"{spec['name']} の前提を満たしていません")
            continue

        allowed = set(spec.get("techniques") or [])
        if spec.get("all_techniques"):
            allowed = {item["name"] for item in catalog().get("martial_art_techniques") or []}
        picked: list[str] = []
        seen: set[str] = set()
        for raw in inst.techniques or []:
            name = str(raw or "").strip()
            if not name or name in seen:
                continue
            if name not in allowed:
                warnings.append(f"{spec['name']} に {name} は選べません")
                continue
            seen.add(name)
            picked.append(name)
        # Quality arts (One Trick Pony) grant a single free technique.
        if is_free and spec.get("is_quality") and len(picked) > 1:
            warnings.append(f"{spec['name']} は技を1つまでです（余分を外しました）")
            picked = picked[:1]
        if not picked:
            warnings.append(f"{spec['name']} の技を1つ選んでください")
            if not is_free:
                continue

        style_cost = 0 if is_free else int(spec.get("cost") or MARTIAL_ART_STYLE_KARMA)
        paid_techniques = 0 if is_free else max(0, len(picked) - 1)
        art_karma = style_cost + paid_techniques * MARTIAL_ART_TECHNIQUE_KARMA
        karma += art_karma
        technique_total += len(picked)
        if not is_free:
            paid_style_count += 1

        tech_public: list[dict[str, Any]] = []
        for idx, name in enumerate(picked):
            tech = _martial_technique_by_name(name) or {"id": "", "name": name, "bonus": [], "source": "", "page": ""}
            free_tech = is_free or idx == 0
            tech_public.append(
                {
                    "id": tech.get("id") or "",
                    "name": name,
                    "free": free_tech,
                    "karma": 0 if free_tech else MARTIAL_ART_TECHNIQUE_KARMA,
                    "source": tech.get("source") or "",
                    "page": tech.get("page") or "",
                }
            )
            for node in tech.get("bonus") or []:
                bonus_sources.append((f"{spec['name']}:{name}", [node]))

        for skill_name, spec_name in _martial_art_spec_options(spec.get("bonus") or []):
            bucket = spec_extras.setdefault(skill_name, [])
            if spec_name not in bucket:
                bucket.append(spec_name)
        other_nodes = [node for node in (spec.get("bonus") or []) if node.get("tag") != "addskillspecializationoption"]
        if other_nodes:
            bonus_sources.append((spec["name"], other_nodes))

        inst.techniques = picked
        inst.free = is_free
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "art_id": spec["id"],
                "name": spec["name"],
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
                "style_karma": style_cost,
                "karma": art_karma,
                "free": is_free,
                "locked": bool(inst.source_quality_id),
                "source_quality_id": inst.source_quality_id,
                "techniques": tech_public,
                "technique_options": sorted(allowed),
                "technique_max": 1 if (is_free and spec.get("is_quality")) else None,
            }
        )

    state.martial_arts = kept
    style_max = 99 if career else MARTIAL_ART_CHARGEN_STYLE_MAX
    tech_max = 99 if career else MARTIAL_ART_CHARGEN_TECHNIQUE_MAX
    if not career and paid_style_count > MARTIAL_ART_CHARGEN_STYLE_MAX:
        errors.append(f"作成時の武道流派は{MARTIAL_ART_CHARGEN_STYLE_MAX}つまでです（現在 {paid_style_count}）")
    if not career and technique_total > MARTIAL_ART_CHARGEN_TECHNIQUE_MAX:
        errors.append(f"作成時の武道技は合計{MARTIAL_ART_CHARGEN_TECHNIQUE_MAX}つまでです（現在 {technique_total}）")

    return {
        "warnings": warnings,
        "public": public,
        "karma": karma,
        "style_count": paid_style_count,
        "technique_count": technique_total,
        "style_max": style_max,
        "technique_max": tech_max,
        "spec_extras": spec_extras,
        "bonus_sources": bonus_sources,
    }
