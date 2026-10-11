"""What bonding a focus costs in karma per point of Force.

Chummer prices a focus by its *kind* rather than its full name, and every kind
is its own settings field — so the lookup is a table from the one to the other
plus a read off the rules in force (``Focus.BindingKarmaCost``).
"""

from __future__ import annotations

from .core import current_rules

#: A focus's name, as `foci.xml` spells it, cut down to the kind Chummer
#: prices: everything from the first `(` or `,` is dropped, so
#: `Counterspelling Focus, Combat` and `Weapon Focus (2050)` both land on
#: their kind. A name that matches nothing (Spell Lock) binds at Force flat,
#: which is Chummer's multiplier of 1.
_FOCUS_KARMA_FIELDS: dict[str, str] = {
    "Alchemical Focus": "karma_alchemical_focus",
    "Banishing Focus": "karma_banishing_focus",
    "Binding Focus": "karma_binding_focus",
    "Centering Focus": "karma_centering_focus",
    "Counterspelling Focus": "karma_counterspelling_focus",
    "Disenchanting Focus": "karma_disenchanting_focus",
    "Flexible Signature Focus": "karma_flexible_signature_focus",
    "Masking Focus": "karma_masking_focus",
    "Power Focus": "karma_power_focus",
    "Qi Focus": "karma_qi_focus",
    "Ritual Spellcasting Focus": "karma_ritual_spellcasting_focus",
    "Spell Shaping Focus": "karma_spell_shaping_focus",
    "Spellcasting Focus": "karma_spellcasting_focus",
    "Summoning Focus": "karma_summoning_focus",
    "Sustaining Focus": "karma_sustaining_focus",
    "Weapon Focus": "karma_weapon_focus",
}


def focus_karma_multiplier(name: str) -> int:
    """Karma per point of Force for bonding this focus (`Focus.BindingKarmaCost`)."""
    kind = str(name or "").split("(")[0].split(",")[0].strip()
    field = _FOCUS_KARMA_FIELDS.get(kind)
    return int(getattr(current_rules(), field)) if field else 1
