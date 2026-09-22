import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Character } from "@/lib/types";
import { BooksProvider } from "@/lib/character/books";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import { VehicleDroneGear } from "./VehicleDroneGear";

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
  books?: string[],
) {
  return render(
    <BooksProvider books={books}>
      <VehicleDroneGear {...panelProps(ch, { catalog, patch })} mode={mode} />
    </BooksProvider>,
  );
}

describe("<VehicleDroneGear> the mod picker and the books", () => {
  // The list was `SR5 || R5`: a book list written in code. It bit hardest
  // here — of the 151 vehicle mods in the real catalog only 2 are SR5, so
  // every one of the other books' mods depended on that `|| R5`, and the
  // nineteen outside both were unreachable however the GM set up the table.
  const modCatalog = () =>
    makeCatalog({
      vehicle_mods: [
        { id: "vm-r5", name: "Rigger Cocoon", category: "Cosmetic", slots: 1, source: "R5" },
        {
          id: "vm-ht",
          name: "Smuggling Compartment",
          category: "Cosmetic",
          slots: 1,
          source: "HT",
        },
      ],
    } as never);
  const modOptions = () =>
    [
      ...screen.getByRole("combobox", { name: "Americar: 改造を追加" }).querySelectorAll("option"),
    ].map((o) => o.textContent);

  it("offers the mods of every enabled book, not just R5", () => {
    renderVehicle(owning(vehicle("v1", "Americar")), vi.fn(), modCatalog());
    expect(modOptions().join(" ")).toContain("Smuggling Compartment");
  });

  it("drops the ones whose book the settings turned off", () => {
    renderVehicle(owning(vehicle("v1", "Americar")), vi.fn(), modCatalog(), "vehicle", ["R5"]);
    const shown = modOptions().join(" ");
    expect(shown).toContain("Rigger Cocoon");
    expect(shown).not.toContain("Smuggling Compartment");
  });
});

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
  } as never);
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
    } as never);

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
    } as never);

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

describe("<VehicleDroneGear> Rigger 5.0's optional drone mods", () => {
  // Chummer's `BookXPath` hides every `<optionaldrone>` mod and mount size
  // unless `<dronemods>` is on; under it the free ones (downgrades) are
  // fitted by hand, so cost "0" does not hide them there.
  const catalog = () =>
    makeCatalog({
      vehicle_mods: [
        { id: "vm1", name: "Speed (Drone)", category: "Speed", cost: "400", optionaldrone: true },
        {
          id: "vm2",
          name: "Speed Downgrade (Drone)",
          category: "Speed",
          cost: "0",
          purchasable: false,
          optionaldrone: true,
        },
        { id: "vm3", name: "Rigger Interface", category: "Cosmetic", cost: "1000" },
      ],
      weapon_mounts: [
        { id: "wm1", name: "Small (Drone)", category: "Size", cost: "1600", optionaldrone: true },
        { id: "wm2", name: "Standard", category: "Size", cost: "2500" },
      ],
    } as never);
  const drone = vehicle("v1", "Doberman", { category: "Drones: Medium" });
  const options = (name: string) =>
    [...screen.getByRole("combobox", { name }).querySelectorAll("option")].map(
      (o) => o.textContent,
    );

  it("hides them while the rules are off", () => {
    renderVehicle(owning(drone), vi.fn(), catalog());
    expect(options("Doberman: 改造を追加").join(" ")).not.toContain("(Drone)");
    expect(options("Doberman: 武器マウントを追加").join(" ")).not.toContain("(Drone)");
  });

  it("offers them, free downgrades included, once the rules are on", () => {
    renderVehicle(owning(drone, { derived: { drone_mods: true } }), vi.fn(), catalog());
    const mods = options("Doberman: 改造を追加").join(" ");
    expect(mods).toContain("Speed (Drone)");
    expect(mods).toContain("Speed Downgrade (Drone)");
    expect(options("Doberman: 武器マウントを追加").join(" ")).toContain("Small (Drone)");
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
    } as never);
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
    } as never);

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
    } as never);

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
      } as never),
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
      } as never),
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
        { category: "Powertrain", used: 1, max: 4 },
        { category: "Body", used: 2, max: 6 },
      ],
    });
    const { container } = renderVehicle(owning(v), vi.fn());

    expect(container.textContent).toContain("パワートレイン 1/4 · ボディ 2/6");
    expect(container.textContent).not.toContain("3/20");
  });

  it("falls back to the flat slot count, and names the seats when there are any", () => {
    const v = vehicle("v1", "Americar", { slots_used: 3, slots_max: 20, seats: 4 });
    const { container } = renderVehicle(owning(v), vi.fn());

    expect(container.textContent).toContain("SEAT 4");
    expect(container.textContent).toContain("3/20");
  });
});

describe("<VehicleDroneGear> compact view", () => {
  beforeEach(() => localStorage.clear());

  it("folds a vehicle to its name and what is fitted, and remembers it", () => {
    const v = vehicle("v1", "Americar", {
      mods: [mod("m1", "Improved Economy")],
      weapon_mounts: [{ id: "wm1", name: "Front", nuyen: 2500, slots: 2, included: false }],
    });
    const patch = vi.fn();
    const first = renderVehicle(owning(v), patch);
    expect(document.querySelectorAll(".cyber-item .cyber-controls").length).toBeGreaterThan(0);

    fireEvent.click(screen.getByLabelText("簡易表示（名称のみ）"));
    const card = document.querySelector(".cyber-item.compact")!;
    expect(card.querySelector(".cyber-controls")).toBeNull();
    expect(card.textContent).not.toContain("HND");
    expect(card.textContent).toContain("Improved Economy、Front");
    expect(localStorage.getItem("vehicleCompact")).toBe("1");
    // a garage folds apart from the body
    expect(localStorage.getItem("wareCompact")).toBeNull();

    fireEvent.click(within(card as HTMLElement).getByRole("button", { name: "削除" }));
    expect(patch).toHaveBeenCalledWith(expect.objectContaining({ vehicles: [] }));

    first.unmount();
    renderVehicle(owning(v), vi.fn());
    expect(document.querySelector(".cyber-item.compact")).not.toBeNull();
  });

  it("has no switch until there is a vehicle to fold", () => {
    renderVehicle(makeCharacter({} as never), vi.fn());
    expect(screen.queryByLabelText("簡易表示（名称のみ）")).toBeNull();
  });
});

describe("<VehicleDroneGear> autosofts a drone runs itself", () => {
  const autosoft = {
    id: "as1",
    name: "Clearsight Autosoft",
    category: "Autosofts",
    cost: "Rating * 500",
    avail: "4",
    source: "SR5",
    minrating: 1,
    maxrating: 6,
    program_host: "rccs",
    needs_extra: false,
  };

  it("lists the drone's own autosofts and loads a new one onto the drone", () => {
    const dr = vehicle("d1", "Fly-Spy", { category: "Drones: Micro" });
    const loaded = {
      id: "p1",
      gear_id: "as0",
      name: "[Model] Stealth Autosoft",
      label: "[Model] Stealth Autosoft (Fly-Spy)",
      rating: 3,
      rating_max: 6,
      parent_id: "d1",
      nuyen: 1500,
    };
    const ch = makeCharacter({
      drones: [dr],
      programs: [{ id: "p1", gear_id: "as0", rating: 3, parent_id: "d1" }],
      derived: { drones: [dr], programs: [loaded] },
    } as never);
    const patch = vi.fn();
    renderVehicle(ch, patch, makeCatalog({ programs: [autosoft] as never }), "drone");

    expect(screen.getByText(/\[Model\] Stealth Autosoft \(Fly-Spy\)/)).toBeTruthy();
    const select = screen.getByRole("combobox", { name: "Fly-Spy: オートソフトを追加" });
    fireEvent.change(select, { target: { value: "as1" } });
    fireEvent.click(screen.getByRole("button", { name: "Fly-Spy: 装着" }));

    const out = patch.mock.calls[0][0].programs as { gear_id: string; parent_id: string }[];
    expect(out.map((r) => [r.gear_id, r.parent_id])).toEqual([
      ["as0", "d1"],
      ["as1", "d1"],
    ]);
  });
});

describe("<VehicleDroneGear> the mod-slot help", () => {
  /** The text of the tooltip a "?" button points at. */
  const tipFor = (name: string) => {
    const button = screen.getByRole("button", { name });
    return document.getElementById(button.getAttribute("aria-describedby")!)?.textContent || "";
  };

  it("explains what a mod takes from the chassis", () => {
    renderVehicle(
      owning(vehicle("v1", "Americar", { mods: [mod("m1", "Rigger Interface")] }), {
        vehicle_mods: [mod("m1", "Rigger Interface")],
      }),
      vi.fn(),
    );
    const tip = tipFor("Rigger Interface の説明");
    expect(tip).toContain("この改造が車体から食う枠");
    expect(tip).toContain("標準装備");
  });

  it("names the six R5 categories on a vehicle", () => {
    const tracks = [{ category: "Powertrain", used: 2, max: 11 }];
    renderVehicle(
      owning(vehicle("v1", "Americar", { slot_tracks: tracks, slots_used: 2, slots_max: 11 })),
      vi.fn(),
    );
    expect(tipFor("Americar の説明")).toContain("駆動系");
  });

  it("describes the single pool instead, on a drone", () => {
    // a drone reports no per-category tracks: the engine keeps one pool for it
    const drone = vehicle("d1", "Steel Lynx", {
      category: "Drones",
      slots_used: 1,
      slots_max: 4,
    });
    renderVehicle(
      makeCharacter({ drones: [drone], derived: { drones: [drone] } } as never),
      vi.fn(),
      makeCatalog(),
      "drone",
    );
    expect(tipFor("Steel Lynx の説明")).toContain("1 つのプール");
  });
});
