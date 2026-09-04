import { testUi } from "@/tests/fixtures";
import {
  accessoryFits,
  ammoFits,
  armorModFits,
  dropDrone,
  dropTree,
  miscFits,
  swapMatrixOrder,
  vehicleFits,
  vehicleForbidden,
  vehicleInteriorFits,
  wareFitsVehicleMod,
  weaponDetailsMatch,
  weaponLine,
} from "@/lib/character/gear";

/* eslint-disable @typescript-eslint/no-explicit-any */

describe("swapMatrixOrder", () => {
  it("swaps the element at fromKey with the one at toPos", () => {
    expect(
      swapMatrixOrder(["attack", "sleaze", "dataprocessing", "firewall"], "attack", 2),
    ).toEqual(["dataprocessing", "sleaze", "attack", "firewall"]);
  });
  it("falls back to the default order when the input is malformed", () => {
    expect(swapMatrixOrder(undefined, "sleaze", 0)).toEqual([
      "sleaze",
      "attack",
      "dataprocessing",
      "firewall",
    ]);
  });
  it("no-ops on an unknown key / out-of-range / same position", () => {
    const o = ["attack", "sleaze", "dataprocessing", "firewall"];
    expect(swapMatrixOrder(o, "nope", 1)).toEqual(o);
    expect(swapMatrixOrder(o, "attack", 9)).toEqual(o);
    expect(swapMatrixOrder(o, "attack", 0)).toEqual(o);
  });
});

describe("vehicleFits / vehicleForbidden", () => {
  const bike = { name: "Dirt Bike", category: "Bikes", body: "5/3" };
  it("passes an unconstrained mod", () => {
    expect(vehicleFits({}, bike)).toBe(true);
    expect(vehicleFits(undefined, bike)).toBe(true);
  });
  it("checks name / category_contains / equals", () => {
    expect(vehicleFits({ names: ["Dirt Bike"] }, bike)).toBe(true);
    expect(vehicleFits({ names: ["Van"] }, bike)).toBe(false);
    expect(vehicleFits({ category_contains: ["ike"] }, bike)).toBe(true);
    expect(vehicleFits({ category_equals: ["Cars"] }, bike)).toBe(false);
  });
  it("checks body bounds against the leading number", () => {
    expect(vehicleFits({ body_lte: 4 }, bike)).toBe(false);
    expect(vehicleFits({ body_gte: 5 }, bike)).toBe(true);
  });
  it("vehicleForbidden is only true for a real, matching constraint", () => {
    expect(vehicleForbidden(undefined, bike)).toBe(false);
    expect(vehicleForbidden({}, bike)).toBe(false);
    expect(vehicleForbidden({ names: ["Dirt Bike"] }, bike)).toBe(true);
  });
});

describe("dropTree", () => {
  it("removes a node and its transitive descendants", () => {
    const rows = [
      { id: "a" },
      { id: "b", parent_id: "a" },
      { id: "c", parent_id: "b" },
      { id: "d" },
    ];
    expect(dropTree(rows, "a").map((r) => r.id)).toEqual(["d"]);
    expect(dropTree(rows, "b").map((r) => r.id)).toEqual(["a", "d"]);
  });
});

describe("dropDrone", () => {
  it("drops the drone + its mods, mounts, child sensors and gear", () => {
    const ch: any = {
      drones: [{ id: "dr1" }, { id: "dr2" }],
      vehicle_mods: [
        { id: "m1", parent_id: "dr1" },
        { id: "m2", parent_id: "dr2" },
      ],
      weapon_mounts: [{ parent_id: "dr1" }],
      sensors: [
        { id: "s1", parent_id: "dr1" },
        { id: "s2", parent_id: "s1" },
      ],
      gear: [{ id: "g1", parent_id: "dr1" }],
      cyberware: [],
    };
    const out = dropDrone(ch, "dr1");
    expect((out.drones ?? []).map((d: any) => d.id)).toEqual(["dr2"]);
    expect(out.vehicle_mods).toEqual([{ id: "m2", parent_id: "dr2" }]);
    expect(out.weapon_mounts).toEqual([]);
    expect(out.sensors).toEqual([]);
    expect(out.gear).toEqual([]);
  });
});

describe("miscFits", () => {
  const link = {
    name: "Erika MCD-1",
    category: "Commlinks",
    addoncategories: ["Software", "Custom"],
  };
  it("uses required_names / required_categories when present", () => {
    expect(miscFits(link, { category: "X", required_names: ["Erika MCD-1"] })).toBe(true);
    expect(miscFits(link, { category: "X", required_categories: ["Vehicles"] })).toBe(false);
  });
  it("falls back to the parent's addoncategories, then requireparent", () => {
    expect(miscFits(link, { category: "Software" })).toBe(true);
    expect(miscFits(link, { category: "Ammunition" })).toBe(false);
    expect(
      miscFits({ name: "x", category: "Sensors" }, { category: "Sensors", requireparent: true }),
    ).toBe(true);
  });
});

describe("wareFitsVehicleMod", () => {
  const mod = { name: "Weapon Mount, Standard", subsystems: ["Cyberware"] };
  it("requires the category slot + plugin/requireparent", () => {
    expect(wareFitsVehicleMod({ category: "Cyberware", plugin: true } as any, mod)).toBe(true);
    expect(wareFitsVehicleMod({ category: "Bioware", plugin: true } as any, mod)).toBe(false);
    expect(wareFitsVehicleMod({ category: "Cyberware" } as any, mod)).toBe(false);
  });
  it("honours required_parent_names", () => {
    expect(
      wareFitsVehicleMod(
        { category: "Cyberware", plugin: true, required_parent_names: ["Standard"] } as any,
        mod,
      ),
    ).toBe(true);
  });
});

describe("weaponDetailsMatch / ammoFits", () => {
  it("evaluates the contains(ammo, …) / name = … DSL", () => {
    const w = { name: "Ares Predator V", ammo: "15 (c)" };
    expect(weaponDetailsMatch(w, "contains(ammo, '(c)')")).toBe(true);
    expect(weaponDetailsMatch(w, "contains(ammo, '(b)')")).toBe(false);
    expect(weaponDetailsMatch(w, "name = 'Ares Predator V'")).toBe(true);
    expect(weaponDetailsMatch(w, "name != 'Ares Predator V'")).toBe(false);
  });
  it("rejects anything that isn't the whitelisted grammar", () => {
    expect(weaponDetailsMatch({ name: "x" }, "process.exit(1)")).toBe(false);
  });
  it("ammoFits: category gate, then weapon_details or ammo_weapon_types", () => {
    expect(ammoFits({ category: "Gear" }, { name: "x" })).toBe(false);
    expect(
      ammoFits(
        { category: "Ammunition", ammo_weapon_types: ["Heavy Pistol"] },
        {
          name: "x",
          weapon_type: "Heavy Pistol",
        },
      ),
    ).toBe(true);
  });
});

describe("weaponLine", () => {
  it("joins the non-empty stat bits", () => {
    expect(
      weaponLine(
        {
          type: "Ranged",
          accuracy: "5",
          damage: "8P",
          ap: "-1",
          mode: "SA",
          ammo: "15(c)",
          reach: "0",
        },
        testUi,
      ),
    ).toBe("遠隔 / Acc 5 / 8P / AP -1 / SA / 15(c)");
    expect(weaponLine({ type: "Melee", accuracy: "0", ap: "-", reach: "1" }, testUi)).toBe(
      "近接 / Reach 1",
    );
  });
});

describe("accessoryFits / armorModFits", () => {
  it("accessoryFits: mount + required 'or' + forbidden", () => {
    const acc = { mounts: ["Top"], required: { categories: ["Assault Rifles"] } };
    const rifle = { name: "AK-97", category: "Assault Rifles", mounts: ["Top", "Barrel"] };
    expect(accessoryFits(acc as any, rifle, [])).toBe(true);
    expect(accessoryFits(acc as any, { ...rifle, mounts: ["Barrel"] }, [])).toBe(false);
    expect(
      accessoryFits({ ...acc, forbidden: { accessories: ["Smartgun"] } } as any, rifle, [
        "Smartgun",
      ]),
    ).toBe(false);
  });
  it("armorModFits: purchasable + required + category allow-list", () => {
    const armor = {
      name: "Armor Jacket",
      category: "Armor",
      addmodcategories: ["Chemical Protection"],
    };
    expect(armorModFits({ category: "General" }, armor, [])).toBe(true);
    expect(armorModFits({ category: "Chemical Protection" }, armor, [])).toBe(true);
    expect(armorModFits({ category: "Fire Resistance" }, armor, [])).toBe(false);
    expect(armorModFits({ purchasable: false, category: "General" }, armor, [])).toBe(false);
    expect(
      armorModFits({ category: "General", required_names: ["Full Body Armor"] }, armor, []),
    ).toBe(false);
  });
});

describe("vehicleInteriorFits", () => {
  it("true for interior categories or a Commlinks requirement", () => {
    expect(vehicleInteriorFits({ category: "Commlink Accessories" })).toBe(true);
    expect(vehicleInteriorFits({ category: "X", required_categories: ["Commlinks"] })).toBe(true);
    expect(vehicleInteriorFits({ category: "X" })).toBe(false);
  });
});
