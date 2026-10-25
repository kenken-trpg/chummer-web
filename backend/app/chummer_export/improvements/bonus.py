"""The walk over a `<bonus>`'s tags that turns it into improvements."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ._imp import _Imp, _is_int, _text
from .rating import _rated
from .readers import _READERS, _addcontact, _attribute, _cost, _selectattributes, _selectskill, _spirit_pick
from .tables import _COSTS, _NUMBERS, _PICKS, _SEEKER, _SPELL_DRAIN


def _bonus_improvements(
    bonus: ET.Element,
    rating: int,
    pick: str | None,
    mentor: str = "",
    contact: str = "",
    attributes: list[str] | None = None,
    skills: dict[str, str] | None = None,
    spell_category: str = "",
) -> list[_Imp]:
    """The improvements the tags of `bonus` make whose improvement needs
    nothing but the bonus, its rating and its pick — as
    `AddImprovementCollection` makes them. `pick` None: nothing was picked,
    so `<selecttext>` makes nothing. `mentor`: the mentor spirit or paragon
    picked, whose `<mentorspirit>` row `_export_mentor_block` writes with the
    id as its guid. `contact`: the id of the contact the quality added.
    `attributes`: the attribute picked for each `<selectattribute>`, in order.
    `skills`: the skill picks, keyed as `resolve_skill_picks` numbers them —
    `0`, `1`… for each `<selectskill>` / `<hardwires>`, `acc0`… for each
    `<weaponskillaccuracy>` that asks for one. `spell_category`: the category
    an empty `<limitspellcategory />` picked, which Chummer keeps on that
    improvement rather than in the extra; a `<spellcategorydrain>` with no
    category of its own is that one's (Hedge Witch/Wizard)."""
    rows: list[_Imp] = []
    picked = accuracy = 0
    # the spirits `AddSpiritOrSprite` asked for, in the order the tags ask:
    # Chain Breaker's two `<addspirit />` are the first and second of its pick
    # (an Apprentice's extra leads with its spell category, which is not one)
    spirits = [part.strip() for part in (pick or "").split(",") if part.strip() and part.strip() != spell_category]
    for node in _rated(bonus, rating) if rating else bonus:
        if node.tag in ("selectskill", "hardwires"):
            # the first pick is also the owner's own pick (`SelectedValue`,
            # which Chummer saves as the extra), when no slot holds it
            name = (skills or {}).get(str(picked), "") or (pick or "" if not picked else "")
            picked += 1
            rows += _selectskill(node, name) if node.tag == "selectskill" and name else []
            continue
        if node.tag == "weaponskillaccuracy":
            if node.find("selectskill") is not None:
                name = (skills or {}).get(f"acc{accuracy}", "") or (pick or "" if not accuracy else "")
                accuracy += 1
            else:
                name = _text(node, "name")
            value = _text(node, "value")
            rows += [_Imp("WeaponSkillAccuracy", name, val=int(value))] if name and _is_int(value) else []
            continue
        if node.tag in ("selecttext", "selectweapon"):
            rows += [_Imp("Text", pick)] if pick is not None else []
        elif node.tag == "weaponspecificdice":
            # the weapon picked, by its guid
            value = _text(node)
            rows += [_Imp("WeaponSpecificDice", pick, val=int(value))] if pick and _is_int(value) else []
        elif node.tag in _PICKS:
            rows += [_Imp(_PICKS[node.tag], pick)] if pick else []
        elif node.tag in ("selectmentorspirit", "selectparagon"):
            kind = "MentorSpirit" if node.tag == "selectmentorspirit" else "Paragon"
            rows += [_Imp(kind, mentor, unique=mentor)] if mentor else []
        elif node.tag == "selectattribute":
            options = {_text(option) for option in node.findall("attribute")} or _SEEKER - {
                "BOX",
                "ESS",
                *(_text(option) for option in node.findall("excludeattribute")),
            }
            rows += _attribute(node, pick) if pick and pick in options else []
        elif node.tag == "selectattributes":
            rows += _selectattributes(node, attributes or [])
        elif node.tag in ("limitspiritcategory", "addspirit"):
            rows += _spirit_pick(node, spirits)
        elif node.tag in _SPELL_DRAIN:
            kind, field = _SPELL_DRAIN[node.tag]
            named = _text(node, field) or (spell_category if node.tag == "spellcategorydrain" else "")
            value = _text(node, "val")
            rows += [_Imp(kind, named, val=int(value))] if named and _is_int(value) else []
        elif node.tag == "addcontact":
            rows += _addcontact(node, contact) if contact else []
        elif node.tag in _COSTS:
            rows += _cost(node)
        elif node.tag in _NUMBERS:
            text = (node.text or "").strip()
            rows += [_Imp(_NUMBERS[node.tag], val=int(text))] if _is_int(text) else []
        elif node.tag in _READERS:
            rows += _READERS[node.tag](node, rating)
    # `<bonus unique="…">` is the unique name of every improvement the tags
    # make that does not name its own: Chemical Protection twice counts once
    unique = bonus.get("unique") or ""
    return [row._replace(unique=row.unique or unique) for row in rows]
