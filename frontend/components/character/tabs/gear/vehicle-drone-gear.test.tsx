import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Character } from "@/lib/types";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import { VehicleDroneGear } from "./VehicleDroneGear";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * `gear-owned.test.tsx` pins this panel's backbone — mods, weapon mounts, and
 * the vehicle/drone split. This file covers the four trees hanging off it,
 * each with its own picker and its own idea of what "the parent" means:
 * cyberware hosted inside a mod, subsystem slots, sensor functions, and
 * interior gear.
 *
 * What makes them worth their own file is that **they all patch top-level
 * character lists** — `ch.cyberware`, `ch.sensors`, `ch.gear` — while what is
 * on screen is a nested row. The only thing tying a row to its place in the
 * tree is `parent_id`, so an install that parents to the vehicle instead of
 * the mod, or a removal that filters one row out of a subtree, still renders
 * plausibly and is wrong. Every test here therefore asserts the `parent_id`
 * that came back, not just that something was added.
 */

const GRADES = [{ name: "Standard", ess: 1, cost: 1 }];

const vehicle = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  vehicle_id: `c-${id}`,
  category: "Cars",
  handling: "4",
  speed: "3",
  accel: "2",
  body: "11",
  armor: "6",
  pilot: "1",
  sensor: "2",
  nuyen: 16000,
  source: "SR5",
  mods: [],
  weapon_mounts: [],
  sensors: [],
  gear: [],
  ...over,
});

const mod = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  mod_id: `c-${id}`,
  category: "Powertrain",
  rating: 1,
  rating_max: 0,
  nuyen: 1000,
  slots: 2,
  included: false,
  subsystems: [],
  ...over,
});

/** An installed cyberware row, shaped far enough for `<WareRow>` to render. */
const ware = (id: string, name: string, parent_id: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  ware_id: `cat-${name}`,
  category: "Cyberlimb Enhancement",
  essence: 0,
  nuyen: 5000,
  source: "SR5",
  avail: "6R",
  rating: 1,
  grade: "Standard",
  wireless: true,
  parent_id,
  ...over,
});

function renderVehicle(
  ch: Character,
  patch: (b: Record<string, unknown>) => void,
  catalog = makeCatalog(),
  mode: "vehicle" | "drone" = "vehicle",
) {
  return render(
    <VehicleDroneGear
      catalog={catalog}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={((k: string) => k) as any}
      ui={testUi}
      patch={patch as any}
      setCharacter={() => {}}
      mode={mode}
    />,
  );
}

/**
 * The 装着 button belonging to one picker. A vehicle has four of them on
 * screen at once (mods, mounts, sensor functions, interior gear), so every
 * install has to be aimed at the select it sits next to.
 */
function installNextTo(select: HTMLElement) {
  return within(select.parentElement as HTMLElement).getByRole("button", { name: "装着" });
}

/** A character owning one vehicle, mirrored into `derived` with its subtrees. */
function owning(v: Record<string, unknown>, rest: Record<string, unknown> = {}): Character {
  const { derived = {}, ...top } = rest;
  return makeCharacter({
    vehicles: [v],
    ...top,
    derived: { vehicles: [v], ...(derived as object) },
  } as any);
}

describe("<VehicleDroneGear> cyberware hosted in a mod", () => {
  const ARM = mod("m1", "Drone Arm", { subsystems: ["Cyberlimb Enhancement"] });
  const catalog = () =>
    makeCatalog({
      cyberware: {
        grades: GRADES,
        items: [
          {
            id: "cat-Enhanced Agility",
            name: "Enhanced Agility",
            category: "Cyberlimb Enhancement",
            plugin: true,
            minrating: 1,
            maxrating: 3,
            capacity: "1",
          },
          // wrong category for this mod's only subsystem slot
          {
            id: "cat-Smartlink",
            name: "Smartlink",
            category: "Eyeware",
            plugin: true,
            minrating: 1,
            maxrating: 1,
          },
        ],
      },
    } as any);

  it("offers only the ware the mod has a slot for", () => {
    renderVehicle(
      owning(vehicle("v1", "Americar", { mods: [ARM] }), { vehicle_mods: [ARM] }),
      vi.fn(),
      catalog(),
    );

    const select = screen.getByRole("combobox", { name: "Drone Arm: 強化を追加" });
    const options = [...select.querySelectorAll("option")].map((o) => o.textContent);
    expect(options).toHaveLength(1);
    expect(options[0]).toContain("Enhanced Agility");
  });

  it("installs it parented to the mod, at the ware's own minimum rating", () => {
    const patch = vi.fn();
    renderVehicle(
      owning(vehicle("v1", "Americar", { mods: [ARM] }), { vehicle_mods: [ARM] }),
      patch,
      catalog(),
    );

    fireEvent.click(screen.getByRole("button", { name: "スロットに追加" }));

    const rows = patch.mock.calls[0][0].cyberware as Record<string, unknown>[];
    expect(rows).toHaveLength(1);
    // parented to the mod, not the vehicle: the engine bills its capacity
    // against the mod, and dropping the mod has to take it along
    expect(rows[0]).toMatchObject({ ware_id: "cat-Enhanced Agility", parent_id: "m1", rating: 1 });
  });

  it("renders the hosted ware nested, and removes its subtree", () => {
    // the parent's own remove has to take the plugin with it, or the plugin
    // outlives the limb it was plugged into
    const boost = ware("cw1", "Enhanced Agility", "m1");
    const plug = ware("cw2", "Sub Plugin", "cw1");
    const patch = vi.fn();
    const { container } = renderVehicle(
      owning(vehicle("v1", "Americar", { mods: [ARM] }), {
        vehicle_mods: [ARM],
        cyberware: [boost, plug],
        derived: { cyberware: [boost, plug] },
      }),
      patch,
      catalog(),
    );

    const nested = container.querySelector(".cyber-item.nested") as HTMLElement;
    expect(within(nested).getByText("Enhanced Agility")).toBeDefined();

    // last, not first: `<WareRow>` renders its children above its own button,
    // so index 0 belongs to the plugin rather than the row under test
    fireEvent.click(within(nested).getAllByRole("button", { name: "削除" }).at(-1)!);

    const left = patch.mock.calls[0][0].cyberware as { id: string }[];
    expect(left).toEqual([]);
  });

  it("removing the mod takes the ware inside it, and leaves the other mod", () => {
    const other = mod("m2", "Rigger Interface");
    const boost = ware("cw1", "Enhanced Agility", "m1");
    const patch = vi.fn();
    renderVehicle(
      owning(vehicle("v1", "Americar", { mods: [ARM, other] }), {
        vehicle_mods: [ARM, other],
        cyberware: [boost],
        derived: { cyberware: [boost] },
      }),
      patch,
      catalog(),
    );

    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[0]);

    const body = patch.mock.calls[0][0];
    expect((body.vehicle_mods as { id: string }[]).map((r) => r.id)).toEqual(["m2"]);
    expect(body.cyberware).toEqual([]);
  });
});

describe("<VehicleDroneGear> the inline mod picker", () => {
  const catalog = () =>
    makeCatalog({
      vehicle_mods: [
        {
          id: "vm1",
          name: "Rigger Interface",
          category: "Powertrain",
          cost: "1000",
          source: "SR5",
        },
        {
          id: "vm2",
          name: "Handling Boost",
          category: "Powertrain",
          cost: "500",
          minrating: 2,
          source: "R5",
        },
        // free, so nothing to buy — the panel drops cost "0" rows
        { id: "vm3", name: "Standard Fitting", category: "Body", cost: "0", source: "SR5" },
        // fits bikes only; this vehicle is a car
        {
          id: "vm4",
          name: "Sidecar",
          category: "Body",
          cost: "800",
          source: "SR5",
          required: { category_equals: ["Bike"] },
        },
      ],
    } as any);

  it("leaves out free mods, mods the vehicle cannot take, and ones already on it", () => {
    const fitted = mod("m1", "Rigger Interface", { mod_id: "vm1" });
    renderVehicle(
      owning(vehicle("v1", "Americar", { mods: [fitted] }), { vehicle_mods: [fitted] }),
      vi.fn(),
      catalog(),
    );

    const select = screen.getByRole("combobox", { name: "Americar: 改造を追加" });
    const options = [...select.querySelectorAll("option")].map((o) => o.textContent);
    expect(options).toEqual(["改造を追加", "Handling Boost (500¥)"]);
  });

  it("installs at the catalog minimum rating, parented to the vehicle", () => {
    const patch = vi.fn();
    renderVehicle(owning(vehicle("v1", "Americar")), patch, catalog());

    const select = screen.getByRole("combobox", { name: "Americar: 改造を追加" });
    fireEvent.change(select, { target: { value: "vm2" } });
    fireEvent.click(installNextTo(select));

    expect(patch.mock.calls[0][0].vehicle_mods).toEqual([
      { mod_id: "vm2", parent_id: "v1", rating: 2 },
    ]);
  });
});

describe("<VehicleDroneGear> weapon mounts", () => {
  const mount = (id: string, name: string, over: Record<string, unknown> = {}) => ({
    id,
    name,
    size_id: `c-${id}`,
    nuyen: 2500,
    slots: 2,
    included: false,
    ...over,
  });

  it("offers only weapons that are not already mounted somewhere", () => {
    const weapons = [
      { id: "w1", name: "MMG", category: "Machine Guns" },
      { id: "w2", name: "Ares Alpha", category: "Assault Rifles" },
      // carried by the runner, not free to bolt onto a vehicle
      { id: "w3", name: "Predator", category: "Heavy Pistols", mounted_on: "wm9" },
    ];
    const v = vehicle("v1", "Americar", {
      weapon_mounts: [mount("wm1", "Front", { weapon_install_id: "w1", weapon_name: "MMG" })],
    });
    renderVehicle(
      owning(v, { weapon_mounts: v.weapon_mounts, weapons, derived: { weapons } }),
      vi.fn(),
    );

    const select = screen.getByRole("combobox", { name: "Front: 武器を搭載" });
    const options = [...select.querySelectorAll("option")].map((o) => o.textContent);
    // the blank row, the weapon already in this mount, then what is left
    expect(options).toEqual(["武器を搭載", "MMG", "Ares Alpha"]);
  });

  it("removing one mount keeps the other", () => {
    const v = vehicle("v1", "Americar", {
      weapon_mounts: [mount("wm1", "Front"), mount("wm2", "Rear")],
    });
    const patch = vi.fn();
    renderVehicle(owning(v, { weapon_mounts: v.weapon_mounts }), patch);

    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[1]);

    const rows = patch.mock.calls[0][0].weapon_mounts as { id: string }[];
    expect(rows.map((r) => r.id)).toEqual(["wm1"]);
  });

  it("adds a mount of the chosen size, parented to the vehicle", () => {
    const catalog = makeCatalog({
      weapon_mounts: [
        { id: "sz1", name: "Standard", category: "Size", cost: "2500", source: "SR5" },
        // not a size — control, flexibility and visibility live in the same list
        { id: "sz2", name: "Remote", category: "Control", cost: "2000", source: "SR5" },
      ],
    } as any);
    const patch = vi.fn();
    renderVehicle(owning(vehicle("v1", "Americar")), patch, catalog);

    const select = screen.getByRole("combobox", { name: "Americar: 武器マウントを追加" });
    expect([...select.querySelectorAll("option")]).toHaveLength(2); // blank + Standard

    fireEvent.change(select, { target: { value: "sz1" } });
    fireEvent.click(installNextTo(select));

    expect(patch.mock.calls[0][0].weapon_mounts).toEqual([{ size_id: "sz1", parent_id: "v1" }]);
  });
});

describe("<VehicleDroneGear> sensor functions", () => {
  const sensor = (id: string, name: string, over: Record<string, unknown> = {}) => ({
    id,
    name,
    gear_id: `c-${id}`,
    rating: 2,
    rating_max: 0,
    nuyen: 0,
    included: true,
    addoncategories: ["Sensor Functions"],
    ...over,
  });
  const fn = (id: string, name: string, gear_id: string, parent_id: string) => ({
    id,
    name,
    gear_id,
    parent_id,
    capacity_cost: 1,
    rating: 1,
    rating_max: 0,
    nuyen: 100,
  });
  const catalog = () =>
    makeCatalog({
      sensors: [
        { id: "sf1", name: "Camera", category: "Sensor Functions", cost: "100", source: "SR5" },
        { id: "sf2", name: "Radar", category: "Sensor Functions", cost: "800", source: "SR5" },
        // "Custom" is the build-your-own placeholder, never an option
        { id: "sf3", name: "Custom", category: "Custom", cost: "0", source: "SR5" },
      ],
    } as any);

  it("lists a sensor's functions under it, and does not offer one twice", () => {
    const camera = fn("s1a", "Camera", "sf1", "s1");
    const { container } = renderVehicle(
      owning(vehicle("v1", "Americar", { sensors: [sensor("s1", "Sensor Array")] }), {
        sensors: [camera],
        derived: { sensors: [camera] },
      }),
      vi.fn(),
      catalog(),
    );

    expect(container.textContent).toContain("Camera");
    const select = screen.getByRole("combobox", { name: "Sensor Array: 機能を追加" });
    const options = [...select.querySelectorAll("option")].map((o) => o.textContent);
    expect(options).toEqual(["機能を追加", "Radar (800¥)"]);
  });

  it("removing a function leaves the other functions of the same sensor", () => {
    const camera = fn("s1a", "Camera", "sf1", "s1");
    const radar = fn("s1b", "Radar", "sf2", "s1");
    const patch = vi.fn();
    renderVehicle(
      owning(vehicle("v1", "Americar", { sensors: [sensor("s1", "Sensor Array")] }), {
        sensors: [camera, radar],
        derived: { sensors: [camera, radar] },
      }),
      patch,
      catalog(),
    );

    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[1]);

    const rows = patch.mock.calls[0][0].sensors as { id: string }[];
    expect(rows.map((r) => r.id)).toEqual(["s1a"]);
  });

  it("adds a function parented to the sensor, not to the vehicle", () => {
    const patch = vi.fn();
    renderVehicle(
      owning(vehicle("v1", "Americar", { sensors: [sensor("s1", "Sensor Array")] })),
      patch,
      catalog(),
    );

    const select = screen.getByRole("combobox", { name: "Sensor Array: 機能を追加" });
    fireEvent.change(select, { target: { value: "sf2" } });
    fireEvent.click(installNextTo(select));

    expect(patch.mock.calls[0][0].sensors).toEqual([
      { gear_id: "sf2", rating: 1, parent_id: "s1" },
    ]);
  });
});

describe("<VehicleDroneGear> interior gear", () => {
  const acc = (id: string, name: string, over: Record<string, unknown> = {}) => ({
    id,
    name,
    gear_id: `c-${id}`,
    rating: 1,
    rating_max: 6,
    nuyen: 250,
    included: false,
    ...over,
  });
  const catalog = () =>
    makeCatalog({
      gear: [
        {
          id: "g-jammer",
          name: "Area Jammer",
          category: "Communications and Countermeasures",
          cost: "600",
          minrating: 3,
          source: "SR5",
        },
        // a category no vehicle interior takes
        { id: "g-ammo", name: "Ammo: Regular", category: "Ammunition", cost: "20", source: "SR5" },
      ],
    } as any);

  it("offers only interior-fitting gear the vehicle does not already carry", () => {
    renderVehicle(owning(vehicle("v1", "Americar")), vi.fn(), catalog());

    const select = screen.getByRole("combobox", { name: "Americar: 内装ギアを追加" });
    const options = [...select.querySelectorAll("option")].map((o) => o.textContent);
    expect(options).toEqual(["内装ギアを追加", "Area Jammer (600¥)"]);
  });

  it("adds it at the catalog minimum rating, parented to the vehicle", () => {
    const patch = vi.fn();
    renderVehicle(owning(vehicle("v1", "Americar")), patch, catalog());

    const select = screen.getByRole("combobox", { name: "Americar: 内装ギアを追加" });
    fireEvent.change(select, { target: { value: "g-jammer" } });
    fireEvent.click(installNextTo(select));

    expect(patch.mock.calls[0][0].gear).toEqual([
      { gear_id: "g-jammer", rating: 3, parent_id: "v1" },
    ]);
  });

  it("rating on the second piece leaves the first alone", () => {
    const rows = [acc("ig1", "Jammer"), acc("ig2", "Rigger Cocoon")];
    const patch = vi.fn();
    renderVehicle(
      owning(vehicle("v1", "Americar", { gear: rows }), { gear: rows, derived: { gear: rows } }),
      patch,
      catalog(),
    );

    fireEvent.change(screen.getAllByRole("spinbutton")[1], { target: { value: "4" } });

    const left = patch.mock.calls[0][0].gear as { id: string; rating: number }[];
    expect(left.find((r) => r.id === "ig1")?.rating).toBe(1);
    expect(left.find((r) => r.id === "ig2")?.rating).toBe(4);
  });

  it("removing a piece takes whatever is plugged into it", () => {
    const rows = [acc("ig1", "Jammer"), acc("ig1a", "Jammer Battery", { parent_id: "ig1" })];
    const patch = vi.fn();
    renderVehicle(
      owning(vehicle("v1", "Americar", { gear: [rows[0]] }), {
        gear: rows,
        derived: { gear: rows },
      }),
      patch,
      catalog(),
    );

    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[0]);

    expect(patch.mock.calls[0][0].gear).toEqual([]);
  });
});

describe("<VehicleDroneGear> deleting the vehicle", () => {
  it("takes every subtree hanging off it with it", () => {
    const m = mod("m1", "Drone Arm", { parent_id: "v1" });
    const w = ware("cw1", "Enhanced Agility", "m1");
    const s = { id: "s1", name: "Camera", gear_id: "sf1", parent_id: "v1" };
    const g = { id: "ig1", name: "Jammer", gear_id: "g-jammer", parent_id: "v1" };
    const wm = { id: "wm1", name: "Front", size_id: "sz1", parent_id: "v1" };
    const patch = vi.fn();
    const v = vehicle("v1", "Americar", { mods: [m] });
    const { container } = renderVehicle(
      makeCharacter({
        vehicles: [v],
        vehicle_mods: [{ ...m, parent_id: "v1" }],
        weapon_mounts: [wm],
        sensors: [s],
        gear: [g],
        cyberware: [w],
        derived: { vehicles: [v], cyberware: [w] },
      } as any),
      patch,
    );

    // the vehicle's own delete, not the hosted ware's: it is the one button
    // that is a direct child of the top-level row
    fireEvent.click(container.querySelector(":scope > .cyber-item > button.danger")!);

    const body = patch.mock.calls[0][0];
    expect(body.vehicles).toEqual([]);
    expect(body.vehicle_mods).toEqual([]);
    expect(body.weapon_mounts).toEqual([]);
    expect(body.sensors).toEqual([]);
    expect(body.gear).toEqual([]);
    // the mod is gone, so the ware that lived inside it has nowhere to be
    expect(body.cyberware).toEqual([]);
  });

  it("deletes out of `drones` in drone mode, leaving `vehicles` untouched", () => {
    const drone = vehicle("dr1", "Steel Lynx", { category: "Drones" });
    const car = vehicle("v1", "Americar");
    const patch = vi.fn();
    renderVehicle(
      makeCharacter({
        vehicles: [car],
        drones: [drone],
        derived: { vehicles: [car], drones: [drone] },
      } as any),
      patch,
      makeCatalog(),
      "drone",
    );

    fireEvent.click(screen.getByRole("button", { name: "削除" }));

    const body = patch.mock.calls[0][0];
    expect(body.drones).toEqual([]);
    expect((body.vehicles as { id: string }[]).map((r) => r.id)).toEqual(["v1"]);
  });
});

describe("<VehicleDroneGear> the summary line", () => {
  it("prefers per-category slot tracks over the single used/max count", () => {
    // R5 splits a vehicle's capacity into named tracks; a vehicle with tracks
    // must not also print the flat SR5 total, or the two disagree on screen
    const v = vehicle("v1", "Americar", {
      slots_used: 3,
      slots_max: 20,
      slot_tracks: [
        { label: "Power", used: 1, max: 4 },
        { label: "Body", used: 2, max: 6 },
      ],
    });
    const { container } = renderVehicle(owning(v), vi.fn());

    expect(container.textContent).toContain("Power 1/4 · Body 2/6");
    expect(container.textContent).not.toContain("3/20");
  });

  it("falls back to the flat slot count, and names the seats when there are any", () => {
    const v = vehicle("v1", "Americar", { slots_used: 3, slots_max: 20, seats: 4 });
    const { container } = renderVehicle(owning(v), vi.fn());

    expect(container.textContent).toContain("SEAT 4");
    expect(container.textContent).toContain("3/20");
  });
});
