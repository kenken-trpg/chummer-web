"""Commlink / cyberdeck / RCC / optics / gear / program / app / sensor loaders."""

from __future__ import annotations

from typing import Any

from .._xml import _int, _text, data_root
from ..bonus import _parse_weaponbonus, parse_bonus
from ..formulas import _is_variable_cost, parse_capacity, split_capacity, variable_cost_range


def _is_pi_tac_commlink(name: str, category: str) -> bool:
    return category == "PI-Tac" and name.startswith("PI-Tac")


def load_commlinks() -> list[dict[str, Any]]:
    root = data_root("gear.xml")
    if root is None:
        return []
    items: list[dict[str, Any]] = []
    for el in root.findall("./gears/gear"):
        category = _text(el.find("category"))
        name = _text(el.find("name"))
        if category != "Commlinks" and not _is_pi_tac_commlink(name, category):
            continue
        if el.find("hide") is not None:
            continue
        gear_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not gear_id or _is_variable_cost(cost):
            continue
        rating_max = _int(el.find("rating"), 0)
        device = _text(el.find("devicerating"), "0")
        processing = _text(el.find("dataprocessing"))
        firewall = _text(el.find("firewall"))
        if _is_pi_tac_commlink(name, category):
            processing = processing or device
            firewall = firewall or device
        items.append(
            {
                "id": gear_id,
                "name": name,
                "category": category or "Commlinks",
                "cost": cost,
                "avail": _text(el.find("avail")),
                "minrating": _int(el.find("minrating"), 1) if rating_max > 0 else 0,
                "maxrating": rating_max,
                "devicerating": device,
                "dataprocessing": processing or "0",
                "firewall": firewall or "0",
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def _load_gear_categories(
    categories: set[str], *, allow_brackets: bool = False, allow_variable: bool = False
) -> list[dict[str, Any]]:
    """`allow_variable`: keep a `Variable(lo-hi)` price as `cost_range` (the
    cost itself 0) — only for buckets whose engine prices from the range."""
    root = data_root("gear.xml")
    if root is None:
        return []
    items: list[dict[str, Any]] = []
    for el in root.findall("./gears/gear"):
        if el.find("hide") is not None:
            continue
        category = _text(el.find("category"))
        if category not in categories:
            continue
        name = _text(el.find("name"))
        gear_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        cost_range = variable_cost_range(cost) if allow_variable else None
        if cost_range:
            cost = "0"
        if not name or not gear_id or name.startswith("ID ERROR") or _is_variable_cost(cost):
            continue
        if name.startswith("[") and not allow_brackets:
            continue
        rating_max = _int(el.find("rating"), 0)
        cap_raw = _text(el.find("capacity"))
        plugin, cap_expr = parse_capacity(cap_raw)
        _plugin_only, host_expr, plugin_expr = split_capacity(cap_raw)
        included: list[dict[str, Any]] = []
        ammo_types = [part.strip() for part in _text(el.find("ammoforweapontype")).split(",") if part.strip()]
        weapon_details = ""
        bonus_el = el.find("bonus")
        if bonus_el is not None:
            select = bonus_el.find("selectweapon")
            if select is not None:
                weapon_details = (select.attrib.get("weapondetails") or _text(select)).strip()
        for gift in el.findall("./gears/usegear"):
            gift_name = _text(gift.find("name"))
            if not gift_name:
                continue
            included.append(
                {
                    "name": gift_name,
                    "category": _text(gift.find("category")),
                    "rating": max(1, _int(gift.find("rating"), 1)),
                    "capacity": _text(gift.find("capacity")),
                }
            )
        items.append(
            {
                "id": gear_id,
                "name": name,
                "category": category,
                "cost": cost,
                "avail": _text(el.find("avail")),
                "minrating": 1 if rating_max > 0 else 0,
                "maxrating": rating_max,
                "capacity": cap_expr,
                "plugin": plugin,
                "host_capacity": host_expr,
                "plugin_capacity": plugin_expr,
                "requireparent": el.find("requireparent") is not None,
                "addoncategories": [_text(c) for c in el.findall("addoncategory") if _text(c)],
                "required_names": [
                    _text(n)
                    for n in (
                        el.findall("./required/geardetails//name")
                        if el.find("./required/geardetails") is not None
                        else []
                    )
                    if _text(n)
                ],
                "required_categories": [
                    _text(n)
                    for n in (
                        el.findall("./required/geardetails//category")
                        if el.find("./required/geardetails") is not None
                        else []
                    )
                    if _text(n)
                ],
                "included": included,
                "ammo_weapon_types": ammo_types,
                "costfor": max(0, _int(el.find("costfor"), 0)),
                "cost_range": list(cost_range) if cost_range else None,
                # what it takes of an armor's capacity when carried in one
                "armor_capacity": _text(el.find("armorcapacity")),
                "weapon_details": weapon_details,
                "add_weapon": _text(el.find("addweapon")),
                "weaponbonus": _parse_weaponbonus(el.find("weaponbonus")),
                "bonus": parse_bonus(el.find("bonus")),
                "devicerating": _text(el.find("devicerating"), "0"),
                "attack": _text(el.find("attack"), "0"),
                "sleaze": _text(el.find("sleaze"), "0"),
                "dataprocessing": _text(el.find("dataprocessing"), "0"),
                "firewall": _text(el.find("firewall"), "0"),
                "attributearray": _text(el.find("attributearray")),
                # what an accessory adds to its host's ASDF (Attack Dongle, DT p.61)
                "modattack": _text(el.find("modattack")),
                "modsleaze": _text(el.find("modsleaze")),
                "moddataprocessing": _text(el.find("moddataprocessing")),
                "modfirewall": _text(el.find("modfirewall")),
                # a positional delta on a cyberdeck's ASDF array, slot by slot
                # ("1,-1,0,0"): the Data Trails modifications trade one point
                # of one attribute for another
                "modattributearray": _text(el.find("modattributearray")),
                "programs": _text(el.find("programs"), "0"),
                "matrixcmbonus": _text(el.find("matrixcmbonus"), "0"),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_cyberdecks() -> list[dict[str, Any]]:
    return _load_gear_categories({"Cyberdecks"})


def load_rccs() -> list[dict[str, Any]]:
    return _load_gear_categories({"Rigger Command Consoles"})


def load_optics() -> list[dict[str, Any]]:
    return _load_gear_categories({"Vision Devices", "Audio Devices", "Vision Enhancements", "Audio Enhancements"})


PROGRAM_HOSTS = {
    "Common Programs": "cyberdecks",
    "Hacking Programs": "cyberdecks",
    "Autosofts": "rccs",
}


def _extra_kind(bonus: list[dict[str, Any]] | None, name: str = "") -> str:
    if str(name or "").startswith("Group Autosoft"):
        return "group"
    tags = {node.get("tag") for node in (bonus or [])}
    if (
        "selectskill" in tags
        or "activesoft" in tags
        or "skillsoft" in tags
        or "knowsoft" in tags
        or "linguasoft" in tags
    ):
        return "skill"
    if "selecttext" in tags or "selectrestricted" in tags or "selecttradition" in tags:
        return "text"
    return ""


GEAR_SPECIALIZED_CATEGORIES = {
    "Commlinks",
    "Cyberdecks",
    "Rigger Command Consoles",
    "Vision Devices",
    "Audio Devices",
    "Vision Enhancements",
    "Audio Enhancements",
    "Common Programs",
    "Hacking Programs",
    "Autosofts",
    "Software",
    "Sensors",
    "Sensor Housings",
    "Sensor Functions",
}

# Stable rules from the pinned DT catalog. Custom/hidden Decrease entries are
# deliberately unsupported; a label is never used to infer a materials rule.
ELECTRONIC_RULES = {
    "f860ec1a-b688-4975-95f4-4c11648b04f0": ("add", "attack"),
    "6638ae8f-d6e4-4d0b-ba3f-0fe05ef64ce0": ("add", "sleaze"),
    "d6802ad9-5dca-434a-bc92-bf8a17a8c5dc": ("module", ""),
    "48f8cb8e-dc9f-405e-b49a-fce3d61a1bda": ("persona", ""),
    "e833a66b-f8b6-4720-b702-ee8efb8522c7": ("increase", "sleaze"),
    "e2c6eded-5897-4ae6-9911-230292d3f858": ("increase", "attack"),
    "0b2cb1ca-d97a-4aee-bf63-5c516b4d0e3e": ("increase", "dataprocessing"),
    "fe32ba65-0c81-48df-98cb-d80f740d54a5": ("increase", "firewall"),
    "02100ba4-7b39-4cdc-9e7a-6c6454d34dae": ("modify", ""),
    "4aea9305-cc4d-4541-95b6-47c820883bba": ("modify", ""),
    "94abb740-bd23-4ba7-be99-ffb916b83376": ("modify", ""),
    "4f502946-c52d-423b-9c3e-be417fe1d5f7": ("modify", ""),
    "9a97cc83-3169-46c1-9826-32ff19be3c5a": ("modify", ""),
    "0647880e-0b6b-4728-a58e-2ccf83feb899": ("modify", ""),
    "16c14307-ffec-49e4-8e25-bf5f50a9c4a0": ("modify", ""),
    "c2b6244b-983b-40ab-b64a-5770bb305ec7": ("modify", ""),
    "fd0d1b50-ed44-482e-838c-474415d93f57": ("modify", ""),
    "50df5261-5193-4066-9a77-6f0412bd5bc9": ("modify", ""),
    "5b2676eb-6111-43a4-bd8d-98754d43d02c": ("modify", ""),
    "683f2644-5cba-4943-ab38-ccc95c2f12c8": ("modify", ""),
    "821d8a12-b883-49de-9ccf-f39c42fba860": ("modify", ""),
    "6c0cb237-1f39-4b6c-ad77-39fc18101d28": ("modify", ""),
    "38ed8ebf-9909-4935-bb08-bb0daea127c9": ("modify", ""),
    "2419a0e9-630c-4d08-9edd-fc97f50e2921": ("modify", ""),
    "0f8c6d4d-b1bf-459e-aa24-556991c9de58": ("modify", ""),
    "652131d8-793d-453b-b0e1-bde8e38ad665": ("modify", ""),
    "a7bc2f96-44ea-4f7f-85b3-d16a626505ee": ("modify", ""),
    "39611c65-89aa-4194-95e2-4a7a17dfc43d": ("modify", ""),
    "38107ab3-4ccf-45d6-9ffb-7ade22f29d4c": ("modify", ""),
    "ce52acd5-afb6-477c-86b9-df5824bfe4dd": ("modify", ""),
    "6b6eb8a4-fc1c-4972-a4da-ffcb5a9fd785": ("modify", ""),
    "7ec549ec-c2ac-4541-9c30-e2d10f9c13e1": ("modify", ""),
}

GEAR_SKIP_CATEGORIES = GEAR_SPECIALIZED_CATEGORIES | {
    "Foci",
    "Formulae",
    "Custom Cyberdeck Attributes",
    "Custom Drugs",
    "Paydata",
    "Commlink Apps",
    "Drug Grades",
    "Currency",
}

GEAR_RATING_CAP = 24


def load_gear() -> list[dict[str, Any]]:
    root = data_root("gear.xml")
    if root is None:
        return []
    cats: set[str] = set()
    for el in root.findall("./gears/gear"):
        cat = _text(el.find("category"))
        if cat:
            cats.add(cat)
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories(cats - GEAR_SKIP_CATEGORIES, allow_variable=True):
        cost = str(item.get("cost") or "").strip()
        if "Parent Cost" in cost:
            continue
        if cost.lstrip().startswith("+"):
            item["requireparent"] = True
        if item.get("category") == "Electronic Modification":
            item["electronic_rule"], item["electronic_attribute"] = ELECTRONIC_RULES.get(str(item["id"]), ("", ""))
            # DT p.66: no fee beyond materials/tools; only applies on the device
            # it is soldered into. `<required><geardetails>` here is a test on
            # the host's matrix attributes ("has an Attack of its own", "already
            # carries Add Attack") rather than a whitelist of parent names, so
            # the two name/category lists would only mis-file it.
            item["requireparent"] = True
            item["required_names"] = []
            item["required_categories"] = []
            # its `<armorcapacity>` is the module space it takes in the device,
            # not something a jacket could carry: without this every one of
            # them would offer itself as armor-borne gear
            item["armor_capacity"] = ""
        if item.get("category") == "Cyberdeck Modules":
            item["armor_capacity"] = ""
        if item.get("required_names") or item.get("required_categories"):
            item["requireparent"] = True
        if _is_pi_tac_commlink(str(item.get("name") or ""), str(item.get("category") or "")):
            continue
        if item.get("category") == "PI-Tac Programs":
            item["requireparent"] = True
        if cost in {"0", ""} and not item.get("requireparent") and not item.get("cost_range"):
            continue
        rating_max = int(item.get("maxrating") or 0)
        if rating_max > GEAR_RATING_CAP:
            item["maxrating"] = 12
            item["minrating"] = 1
        name = item.get("name") or ""
        item["extra_kind"] = _extra_kind(item.get("bonus"), name)
        item["needs_extra"] = bool(item["extra_kind"])
        items.append(item)
    return items


def load_programs() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories(
        {"Common Programs", "Hacking Programs", "Autosofts"},
        allow_brackets=True,
    ):
        name = item.get("name") or ""
        if name.startswith("[") and item.get("category") != "Autosofts":
            continue
        if "Parent Cost" in (item.get("cost") or ""):
            continue
        item["requireparent"] = True
        item["program_host"] = PROGRAM_HOSTS.get(item.get("category") or "", "cyberdecks")
        item["extra_kind"] = _extra_kind(item.get("bonus"), name)
        item["needs_extra"] = bool(item["extra_kind"])
        items.append(item)
    return items


def load_apps() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories({"Software", "Commlink Apps"}, allow_variable=True):
        if "Parent Cost" in (item.get("cost") or ""):
            continue
        if (item.get("cost") or "").strip() in {"0", ""} and not item.get("cost_range"):
            continue
        item["requireparent"] = True
        item["extra_kind"] = _extra_kind(item.get("bonus"), item.get("name") or "")
        item["needs_extra"] = bool(item["extra_kind"])
        items.append(item)
    return items


def load_sensors() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories({"Sensors", "Sensor Housings", "Sensor Functions"}):
        if "Parent Cost" in (item.get("cost") or ""):
            continue
        item["requireparent"] = item.get("category") == "Sensor Functions"
        items.append(item)
    return items
