import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { makeCatalog, makeCharacter } from "@/tests/fixtures";
import { vehicle, renderVehicle, installNextTo, owning } from "./vehicle-drone-gear.helpers";

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
