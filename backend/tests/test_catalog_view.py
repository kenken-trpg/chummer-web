"""The shape of `GET /api/catalog`.

`public_catalog()` merges one `section(raw)` per domain into a single dict. The
merge is the risk: a key defined in two sections is silently won by whichever
runs last, and nothing else in the suite would notice — the frontend would just
start reading a list built by the wrong projection.
"""

from __future__ import annotations

from app.catalog_view import _SECTIONS, public_catalog
from app.data_loader import catalog

# Every key the frontend reads. Adding one is fine — this list is a reminder to
# add the TypeScript type in `frontend/lib/types/catalog.ts` alongside it, not
# a freeze. Removing one is a breaking change to the UI.
EXPECTED_KEYS = {
    # chargen
    "metatypes",
    "skills",
    "qualities",
    "martial_arts",
    "martial_art_techniques",
    "priority_table",
    "karma_talents",
    # ware
    "cyberware",
    "bioware",
    # magic
    "powers",
    "enhancements",
    "mentors",
    "spells",
    "traditions",
    "spirits",
    "complex_forms",
    "streams",
    "sprites",
    "foci",
    "qi_focus",
    "metamagics",
    "magic_arts",
    "echoes",
    # gear
    "armor",
    "armor_mods",
    "weapons",
    "weapon_accessories",
    "gear",
    "lifestyles",
    "lifestyle_qualities",
    "drugs",
    "drug_grades",
    # matrix
    "commlinks",
    "cyberdecks",
    "rccs",
    "optics",
    "programs",
    "apps",
    "sensors",
    # vehicles
    "drones",
    "vehicles",
    "vehicle_mods",
    "weapon_mounts",
    # passthroughs
    "weapon_ranges",
    "translations",
    "ui_strings",
}


def test_the_sections_do_not_overlap() -> None:
    raw = catalog()
    seen: dict[str, str] = {}
    for module in _SECTIONS:
        for key in module.section(raw):
            assert key not in seen, f"{key} is defined by both {seen[key]} and {module.__name__}"
            seen[key] = module.__name__


def test_the_catalog_has_exactly_the_keys_the_ui_reads() -> None:
    keys = set(public_catalog())
    assert keys == EXPECTED_KEYS, f"added: {keys - EXPECTED_KEYS}, removed: {EXPECTED_KEYS - keys}"


def test_every_section_is_a_pure_function_of_raw() -> None:
    """No section may mutate the loader's cached dict — `catalog()` is
    `lru_cache`d, so a section that edited `raw` would corrupt every later
    request in the process."""
    raw = catalog()
    before = {key: len(value) for key, value in raw.items() if isinstance(value, list | dict)}
    public_catalog()
    after = {key: len(value) for key, value in raw.items() if isinstance(value, list | dict)}
    assert before == after


def test_the_projection_drops_the_fields_the_ui_never_reads() -> None:
    """The point of the projection: a raw weapon carries loader bookkeeping the
    client has no use for, and it is ~2.9 MB before that is dropped."""
    raw_weapon = next(w for w in catalog()["weapons"] if not w.get("hidden"))
    public_weapon = next(w for w in public_catalog()["weapons"] if w["id"] == raw_weapon["id"])
    assert set(public_weapon) < set(raw_weapon)
    assert "bonus" not in public_weapon
