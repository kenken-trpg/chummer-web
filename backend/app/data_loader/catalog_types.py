"""``CatalogDict`` — the shape of ``data_loader.catalog()``.

``catalog()`` assembles ~46 keys from the per-domain ``load_*`` loaders (all
already annotated), so the return literal type-checks against this
``TypedDict`` as-is. Typing it removes the single ``Any`` fountain for the
engine: ``catalog()["weapons"]`` is now ``list[dict[str, Any]]``, and a
mistyped key is a ``mypy`` error.

Row shapes stay ``dict[str, Any]`` — typing those is a separate job (the
row lists here are the same "public DTO" territory as the ``Ctx`` bundles).
Imports only ``typing``. See ``docs/refactor-catalog-typeddict-plan.md``.
"""

from __future__ import annotations

from typing import Any, TypedDict

Row = dict[str, Any]


class CatalogDict(TypedDict):
    metatypes: list[Row]
    all_metatypes: dict[str, Row]
    skills: Row
    qualities: list[Row]
    cyberware: Row
    bioware: Row
    powers: list[Row]
    enhancements: list[Row]
    mentors: list[Row]
    spells: list[Row]
    traditions: list[Row]
    spirits: list[Row]
    complex_forms: list[Row]
    streams: list[Row]
    sprites: list[Row]
    foci: list[Row]
    qi_focus: Row | None
    armor: list[Row]
    armor_mods: list[Row]
    weapons: list[Row]
    weapon_ranges: dict[str, dict[str, str]]
    weapon_accessories: list[Row]
    commlinks: list[Row]
    cyberdecks: list[Row]
    rccs: list[Row]
    optics: list[Row]
    programs: list[Row]
    apps: list[Row]
    sensors: list[Row]
    gear: list[Row]
    drugs: list[Row]
    drug_grades: list[Row]
    drones: list[Row]
    vehicles: list[Row]
    vehicle_mods: list[Row]
    weapon_mounts: list[Row]
    vehicle_names: list[str]
    lifestyles: list[Row]
    lifestyle_qualities: list[Row]
    martial_arts: list[Row]
    martial_art_techniques: list[Row]
    metamagics: list[Row]
    magic_arts: list[Row]
    echoes: list[Row]
    priorities: list[Row]
    translations: dict[str, str]
    ui_strings: dict[str, str]
