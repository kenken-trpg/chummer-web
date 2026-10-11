"""Row shapes for what a bonus *grants* outright — a spell, a power, a piece of
gear, a free martial art (group G3 of
``docs/plans/refactor-effect-rows-plan.md``)."""

from __future__ import annotations

from typing import TypedDict


class GrantEchoRow(TypedDict):
    """``grant_echoes`` — an ``<addecho>`` grant."""

    source: str
    name: str


class GrantSpellRow(TypedDict):
    """``grant_spells`` — an ``<addspell>`` grant with its variant flags."""

    source: str
    name: str
    alchemical: bool
    extended: bool
    limited: bool


class GrantWeaponRow(TypedDict):
    """``grant_weapons`` — an ``<addweapon>`` bonus node: the attack a power
    grows (Elemental Body, SG p.170)."""

    source: str
    name: str


class GrantGearRow(TypedDict):
    """``grant_gear`` — an ``<addgear>`` grant: the item a quality hands over,
    with the children that come clipped to it (Dead SIN's fake licenses)."""

    source: str
    name: str
    category: str
    rating: int
    children: list[dict[str, str]]


class GrantWareRow(TypedDict):
    """``grant_ware`` — an ``<addware>`` grant: the implant a quality comes
    with, at the grade it forces (Busted Cyberware, TSG p.30)."""

    source: str
    name: str
    kind: str
    grade: str


class GrantPowerRow(TypedDict):
    """``grant_powers`` — a ``<specificpower>`` / resolved ``<selectpowers>``
    grant."""

    source: str
    name: str
    rating: int
    extra: str


class FreeMartialArtRow(TypedDict):
    """``free_martial_arts`` — a ``<martialart>`` quality grant."""

    name: str
    source: str


class FreeMetamagicRow(TypedDict):
    """``free_metamagics`` — an ``<addmetamagic>`` grant (``forced`` skips the
    normal grade gate)."""

    name: str
    source: str
    forced: bool


class MetamagicLimitRow(TypedDict):
    """``metamagic_limits`` — one ``<metamagiclimit><metamagic grade="N">`` row:
    the only metamagic that grade may take."""

    grade: int
    name: str
    source: str
