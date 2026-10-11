"""``Rules`` — the settings a character is built under, resolved to numbers.

``core.py`` holds the printed SR5 values, the :class:`Rules` dataclass they
seed, and the ``ContextVar`` the engine reads them through; ``settings.py``
folds a Chummer settings file's overrides into one; ``foci.py`` prices a focus
bonding against whichever rules are in force. This module is the barrel, so
``from app.rules import …`` is unchanged.
"""

from __future__ import annotations

from .core import (
    CHARGEN_KARMA,
    CHARGEN_KNOWLEDGE_SKILL_MAX,
    CHARGEN_SKILL_MAX,
    DEFAULT_PRIORITY_TABLE,
    DEFAULT_RULES,
    Rules,
    current_rules,
    using_rules,
)
from .foci import focus_karma_multiplier
from .settings import _DIRECT, RULE_FIELDS, rules_for

__all__ = [
    "CHARGEN_KARMA",
    "CHARGEN_KNOWLEDGE_SKILL_MAX",
    "CHARGEN_SKILL_MAX",
    "DEFAULT_PRIORITY_TABLE",
    "DEFAULT_RULES",
    "RULE_FIELDS",
    "Rules",
    "_DIRECT",
    "current_rules",
    "focus_karma_multiplier",
    "rules_for",
    "using_rules",
]
