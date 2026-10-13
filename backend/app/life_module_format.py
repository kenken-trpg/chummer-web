"""Shared v2 chum5 extension fields and standard-projection consistency."""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from copy import deepcopy

V2_INPUT_FIELDS = (
    "settings",
    "career",
    "career_baseline",
    "karma_adjust",
    "nuyen_adjust",
    "karma_earned",
    "nuyen_earned",
    "reward_log",
    "expense_log",
    "life_module_rules_version",
    "life_modules",
    "life_module_entry_ids",
    "life_module_choices",
    "life_module_skill_snapshot",
    "life_module_skill_advancements",
    "life_module_skill_advancement_history",
    "life_module_transfers",
    "skills",
    "skill_groups",
    "exotic_skills",
    "knowledge_skills",
    "knowledge_categories",
    "native_languages",
    "skill_specializations",
)


def standard_digest(root: ET.Element) -> str:
    projection = ET.Element("standard")
    for tag in (
        "newskills",
        "attributes",
        "qualities",
        "contacts",
        "karma",
        "nuyen",
        "expenses",
        "created",
        "buildmethod",
        "metatype",
        "metavariant",
    ):
        element = root.find(tag)
        if element is not None:
            projection.append(deepcopy(element))
    canonical = ET.canonicalize(ET.tostring(projection, encoding="unicode"), strip_text=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
