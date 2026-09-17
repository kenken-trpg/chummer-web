"""Rows bought as gear: ware, armor, weapons, vehicles, commlinks, gear, drugs, lifestyles."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CyberwareInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ware_id: str
    rating: int = 1
    grade: str = "Standard"
    wireless: bool = True
    parent_id: str | None = None
    included: bool = False
    side: str | None = None
    # `<selectcyberware>`: the implant this one is keyed to (Implant Medic,
    # Nanohive Soft). A label, like Chummer's `<extra>` — it grants nothing.
    extra: str | None = None
    #: bought through the Black Market Pipeline: 10% off (Chummer's
    #: `<discountedcost>`, which the quality's categories allow)
    discounted: bool = False


class ArmorInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    armor_id: str
    rating: int = 1
    #: the price picked for a `Variable(lo-hi)` piece (Clothing)
    cost: int | None = None
    equipped: bool = True
    wireless: bool = True
    #: bought through the Black Market Pipeline: 10% off (Chummer's
    #: `<discountedcost>`, which the quality's categories allow)
    discounted: bool = False


class ArmorModInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mod_id: str
    parent_id: str | None = None
    included: bool = False
    rating: int = 1
    wireless: bool = True
    # Custom Fit (Stack) `<selectarmor>`: the catalog name of the armor this
    # piece was tailored to stack with (Chummer's `<extra>`)
    stack_with: str = ""


class WeaponInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    weapon_id: str
    qty: int = 1
    loaded_ammo_id: str | None = None
    #: bought through the Black Market Pipeline: 10% off (Chummer's
    #: `<discountedcost>`, which the quality's categories allow)
    discounted: bool = False


class VehicleModInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mod_id: str
    parent_id: str | None = None
    included: bool = False
    rating: int = 1


class WeaponMountInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str | None = None
    size_id: str = ""
    visibility_id: str = ""
    flexibility_id: str = ""
    control_id: str = ""
    included: bool = False
    weapon_install_id: str | None = None
    allowedweapons: str = ""


class WeaponAccessoryInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    accessory_id: str
    parent_id: str | None = None
    included: bool = False
    rating: int = 1
    mount: str = ""
    #: bought through the Black Market Pipeline: 10% off (Chummer's
    #: `<discountedcost>`, which the quality's categories allow)
    discounted: bool = False


class CommlinkInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gear_id: str
    rating: int = 1
    #: how many alike — a stack of burner Meta Links
    qty: int = Field(default=1, ge=1, le=999)
    #: bought through the Black Market Pipeline: 10% off (Chummer's
    #: `<discountedcost>`, which the quality's categories allow)
    discounted: bool = False


class GearInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gear_id: str
    rating: int = 1
    qty: int = 1
    parent_id: str | None = None
    included: bool = False
    capacity_override: str | None = None
    array_order: list[str] = Field(default_factory=list)
    extra: str | None = None
    active: bool = False  # drugs/toxins: effect currently applied
    #: the price picked for a `Variable(lo-hi)` item (a Custom Item, a
    #: Commlink App), and a Custom Item's own name
    cost: int | None = None
    name: str | None = Field(default=None, max_length=200)
    #: bought through the Black Market Pipeline: 10% off (Chummer's
    #: `<discountedcost>`, which the quality's categories allow)
    discounted: bool = False


class CustomDrugPart(BaseModel):
    """One component in a mixed drug, at the level it was added at."""

    component_id: str
    level: int = 0


class CustomDrugInstall(BaseModel):
    """A drug the character cooked rather than bought (CF p.190).

    It has no catalog entry — the parts are the drug — so unlike every other
    piece of gear it carries its own name.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    grade: str = "Standard"
    qty: int = 1
    active: bool = False  # effect currently applied, like GearInstall.active
    parts: list[CustomDrugPart] = Field(default_factory=list)


class LifestyleInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lifestyle_id: str
    months: int = 1
    #: Points bought above the lifestyle's own Comforts / Neighborhood /
    #: Security (RF p.219, Chummer's `<comforts>` / `<area>` / `<security>`).
    comforts: int = 0
    area: int = 0
    security: int = 0
    quality_ids: list[str] = Field(default_factory=list)
    quality_extras: dict[str, str] = Field(default_factory=dict)
