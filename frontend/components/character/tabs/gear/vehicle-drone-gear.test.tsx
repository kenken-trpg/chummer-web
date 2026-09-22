import { fireEvent, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { makeCatalog, makeCharacter } from "@/tests/fixtures";
import { vehicle, mod, ware, renderVehicle, owning } from "./vehicle-drone-gear.helpers";

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
