"""The one thing the Awakened and Emerged loaders genuinely share.

A sprite's attribute block is shaped exactly like a spirit's — same keys, same
`F`-relative defaults — so both loaders read it with the same tuple rather than
each keeping its own copy to drift.
"""

from __future__ import annotations

SPIRIT_ATTR_KEYS = ("bod", "agi", "rea", "str", "cha", "int", "log", "wil", "ini")
