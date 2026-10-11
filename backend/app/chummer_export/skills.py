"""Skills, the way Chummer stores them: ``<newskills>``, an active skill named
by its ``skills.xml`` id, a knowledge skill by name and type.

The mirror of :mod:`app.chummer_import.skills`.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET

from ..data_loader import catalog
from ..models import CharacterState
from ._common import _Ctx, _Names, _sub, improvements_of

#: Chummer's id for a knowledge skill it has no data for (a custom one).
_NO_SKILL_ID = "00000000-0000-0000-0000-000000000000"


def _export_skills(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write skills the way Chummer does: `<newskills>`, an active skill named
    only by its skills.xml id (`<suid>`), a knowledge skill by name and type.

    Chummer drops a skill that has no `<suid>` (`Skill.Load`), and without
    `<newskills>` falls back to a pre-5 layout this app never wrote — so the
    old `<skills><skills>` export opened in Chummer with no skills at all.
    """
    data = catalog()["skills"]
    active_ids = {str(row["name"]): str(row["id"]) for row in data.get("skills") or []}
    active_cats = {str(row["name"]): str(row.get("category") or "") for row in data.get("skills") or []}
    knowledge_ids = {str(row["name"]): str(row["id"]) for row in data.get("knowledge") or [] if row.get("id")}
    # The engine keeps a listed skill's type only when it was changed, so the
    # list is where an unchanged one's type comes from.
    # Street is what the engine takes a typeless unlisted one for.
    knowledge_cats = {str(row["name"]): str(row.get("category") or "") for row in data.get("knowledge") or []}
    ns = _sub(root, "newskills")
    talent = ctx["derived"].get("talent_skills") or {}
    free_rating = int(talent.get("rating") or 0)
    free = dict.fromkeys(talent.get("picked") or [], free_rating)
    free_skills = {} if talent.get("group") else free
    free_groups = free if talent.get("group") else {}

    def karma_of(levels: dict[str, int], name: str, rating: int) -> int:
        # the top levels bought with karma at creation are Chummer's <karma>
        return 0 if state.career else max(0, min(int(levels.get(name, 0)), int(rating)))

    def specs(el: ET.Element, name: str) -> None:
        spn = state.skill_specializations.get(name)
        if spn:
            spec = _sub(_sub(el, "specs"), "spec")
            _sub(spec, "guid", str(uuid.uuid5(uuid.NAMESPACE_URL, f"{state.id}:spec:{name}")))
            _sub(spec, "name", spn)
            _sub(spec, "free", "False")
        _sub(el, "buywithkarma", "True" if spn and name in state.skill_specs_karma else "False")

    active = _sub(ns, "skills")
    for name, rating in sorted(state.skills.items()):
        if name not in active_ids:
            continue
        s = _sub(active, "skill")
        _sub(s, "suid", active_ids[name])
        _sub(s, "isknowledge", "False")
        _sub(s, "skillcategory", active_cats.get(name, ""))
        karma = karma_of(state.skill_karma, name, rating)
        _sub(s, "karma", karma)
        _sub(s, "base", max(0, rating - karma - free_skills.get(name, 0)))
        specs(s, name)
    for exotic in state.exotic_skills:
        # One skill per weapon, which Chummer writes as the exotic skill's id
        # plus the weapon in `<specific>`.
        if exotic.skill_name not in active_ids:
            continue
        s = _sub(active, "skill")
        _sub(s, "suid", active_ids[exotic.skill_name])
        _sub(s, "isknowledge", "False")
        _sub(s, "skillcategory", active_cats.get(exotic.skill_name, ""))
        _sub(s, "karma", 0)
        _sub(s, "base", exotic.rating)
        _sub(s, "specific", exotic.extra)

    kno = _sub(ns, "knoskills")

    def knowledge(name: str, typ: str, base: int, karma: int, native: bool) -> None:
        s = _sub(kno, "skill")
        _sub(s, "suid", knowledge_ids.get(name, _NO_SKILL_ID))
        _sub(s, "isknowledge", "True")
        _sub(s, "skillcategory", typ)
        _sub(s, "karma", karma)
        _sub(s, "base", base)
        _sub(s, "name", name)
        _sub(s, "type", typ)
        _sub(s, "isnativelanguage", "True" if native else "False")
        specs(s, name)

    for name in state.native_languages:
        knowledge(name, "Language", 0, 0, True)
    for name, rating in sorted(state.knowledge_skills.items()):
        karma = karma_of(state.knowledge_karma, name, rating)
        category = state.knowledge_categories.get(name) or knowledge_cats.get(name) or "Street"
        knowledge(name, category, rating - karma, karma, False)

    grps = _sub(ns, "groups")
    for name, rating in sorted(state.skill_groups.items()):
        grp_el = _sub(grps, "group")
        karma = karma_of(state.skill_group_karma, name, rating)
        _sub(grp_el, "karma", karma)
        _sub(grp_el, "base", max(0, rating - karma - free_groups.get(name, 0)))
        _sub(grp_el, "name", name)

    # Chummer gives the free levels back only through these (`FreeBase`)
    for kind, picks in (("SkillBase", free_skills), ("SkillGroupBase", free_groups)):
        for name, val in picks.items():
            imp = _sub(improvements_of(root), "improvement")
            _sub(imp, "improvedname", name)
            _sub(imp, "val", val)
            _sub(imp, "rating", 1)
            _sub(imp, "improvementttype", kind)
            _sub(imp, "improvementsource", "Heritage")
            _sub(imp, "enabled", "True")
