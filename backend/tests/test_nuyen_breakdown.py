"""The sidebar's spending breakdown has to add up to what was spent.

`nuyen_spend_breakdown` used to re-add the rows the engine had published,
bucket by bucket. That does not work, because a thing bolted onto something
else has its price folded into the row it is bolted to so the tab can show what
the whole assembly cost: a cyberspur's row carries the implant's price, a
weapon's row carries its accessories' and its ammunition's, a jacket's carries
its plates'. Adding the rows up counted that money twice, and the breakdown
came out over the total it was breaking down on 29 of Chummer's 34 test saves —
by 61,910¥ on the worst of them.

It is built from the tally `resolve_gear` keeps while it is counting instead,
so the parts add back up to the whole by construction. These pin that, one
absorbing relationship at a time.
"""

from __future__ import annotations

import pytest

from app.engine import compute
from app.models import (
    ArmorInstall,
    ArmorModInstall,
    CommlinkInstall,
    CyberwareInstall,
    GearInstall,
    LifestyleInstall,
    VehicleModInstall,
    WeaponAccessoryInstall,
    WeaponInstall,
)
from tests.engine_support import (
    FORD_AMERICAR,
    MECHANICAL_ARM,
    _armor_mod_named,
    _mundane,
    _ware_named,
)


def _spent_and_lines(state) -> tuple[int, int]:
    out = compute(state).derived
    lines = sum(int(row.get("amount") or 0) for row in out["nuyen_spend_breakdown"])
    return int(out["nuyen_spent"]), lines


def _cat(bucket: str, name: str) -> str:
    from app.data_loader import catalog

    return next(item["id"] for item in catalog()[bucket] if item["name"] == name)


def _armored() -> object:
    armor = ArmorInstall(id="a", armor_id=_cat("armor", "Armor Jacket"))
    return _mundane(
        "armored",
        armor=[armor],
        armor_mods=[ArmorModInstall(id="m", mod_id=_armor_mod_named("Chemical Protection"), parent_id="a")],
    )


def _gunned() -> object:
    weapon = WeaponInstall(id="w", weapon_id=_cat("weapons", "Ares Predator V"))
    return _mundane(
        "gunned",
        weapons=[weapon],
        weapon_accessories=[
            WeaponAccessoryInstall(
                id="acc", accessory_id=_cat("weapon_accessories", "Silencer/Suppressor"), parent_id="w"
            )
        ],
        gear=[GearInstall(id="ammo", gear_id=_cat("gear", "Ammo: APDS"), qty=2, parent_id="w")],
    )


def _driven() -> object:
    car = GearInstall(id="v", gear_id=FORD_AMERICAR)
    return _mundane(
        "driven",
        vehicles=[car],
        vehicle_mods=[VehicleModInstall(id="vm", mod_id=MECHANICAL_ARM, parent_id="v")],
        gear=[GearInstall(id="kit", gear_id=_cat("gear", "Medkit"), rating=3, parent_id="v")],
    )


def _spurred() -> object:
    """A cyberspur is a weapon you own and did not buy: it was paid for as
    cyberware, and its weapon row carries the implant's price so the weapons
    tab can show it."""
    return _mundane(
        "spurred",
        cyberware=[CyberwareInstall(id="c", ware_id=_ware_named("Spurs"))],
    )


def _housed() -> object:
    """A lifestyle whose cost a quality moves after the fact (`apply_lifestyle_cost_mod`
    reaches back into the finished tally)."""
    return _mundane(
        "housed",
        lifestyles=[LifestyleInstall(id="l", lifestyle_id=_cat("lifestyles", "Medium"), months=2)],
        commlinks=[CommlinkInstall(id="cl", gear_id=_cat("commlinks", "Meta Link"))],
    )


@pytest.mark.parametrize(
    "build",
    [_armored, _gunned, _driven, _spurred, _housed],
    ids=["armor+mod", "weapon+accessory+ammo", "vehicle+mod+cargo", "ware-granted weapon", "lifestyle"],
)
def test_the_breakdown_adds_up_to_what_was_spent(build) -> None:
    spent, lines = _spent_and_lines(build())
    assert lines == spent


def test_a_cyberspur_is_not_paid_for_twice() -> None:
    """The regression itself: the implant's price belongs to the cyberware
    line, and the weapon row it grants must not add a second copy."""
    out = compute(_spurred()).derived
    lines = {row["notice"]["key"]: row["amount"] for row in out["nuyen_spend_breakdown"]}
    assert "engine.spend.weapons" not in lines
    assert lines["engine.spend.cyberware"] == out["nuyen_spent"]
