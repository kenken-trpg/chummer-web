"""Skill resolution: knowledge skills, specializations / expertise, exotic
skills, `<skillsoft>` autosofts, activesoft-driven skill picks, and the
`<skillcategory>` / dice-pool skill-bonus modifiers compute() applies.

``_knowledge``   the knowledge pool, native languages and each skill's type
``_specs``       specializations and granted expertise
``_exotic``      exotic skills, one per weapon
``_mods``        dice modifiers by category, group and skill
``_skillsofts``  activesofts / knowsofts and the jack or wires they need
``_picks``       `<selectskill>` / `<hardwires>` picks and ware accuracy
``_talent``      the priority talent's free skills

Imports only ``catalog`` / already-extracted engine modules / models — never
back into ``app.engine``. Every name the old module held is re-exported here,
so the split is invisible to the modules that import from it.
"""

from __future__ import annotations

from ._exotic import (
    _copy_exotic_skill_bonuses,
    exotic_skill_label,
    resolve_exotic_skills,
)
from ._knowledge import (
    KNOWLEDGE_CATEGORIES,
    KNOWLEDGE_DEFAULT_ATTR,
    knowledge_pool,
    resolve_knowledge,
)
from ._mods import (
    resolve_skill_mods,
)
from ._picks import (
    REFLEX_RECORDER,
    SKILL_PICK_TAGS,
    _accuracy_select_node,
    _default_free_skills,
    _extra_kind,
    _needs_accuracy_pick,
    _ware_bonus_nodes,
    bind_ware_skill_accuracy,
    resolve_skill_picks,
    ware_accuracy_picks,
)
from ._skillsofts import (
    _attach_skillsoft_knowledge,
    _merge_skill_ratings,
    _skillsoft_value,
    resolve_skillsofts,
)
from ._specs import (
    _attach_specializations,
    apply_select_expertise,
    resolve_specializations,
)
from ._talent import resolve_talent_skills, talent_skill_options

__all__ = [
    "KNOWLEDGE_CATEGORIES",
    "KNOWLEDGE_DEFAULT_ATTR",
    "REFLEX_RECORDER",
    "SKILL_PICK_TAGS",
    "_accuracy_select_node",
    "_attach_skillsoft_knowledge",
    "_attach_specializations",
    "_copy_exotic_skill_bonuses",
    "_default_free_skills",
    "_extra_kind",
    "_merge_skill_ratings",
    "_needs_accuracy_pick",
    "_skillsoft_value",
    "_ware_bonus_nodes",
    "apply_select_expertise",
    "bind_ware_skill_accuracy",
    "exotic_skill_label",
    "knowledge_pool",
    "resolve_exotic_skills",
    "resolve_knowledge",
    "resolve_skill_mods",
    "resolve_skill_picks",
    "resolve_skillsofts",
    "resolve_specializations",
    "resolve_talent_skills",
    "talent_skill_options",
    "ware_accuracy_picks",
]
