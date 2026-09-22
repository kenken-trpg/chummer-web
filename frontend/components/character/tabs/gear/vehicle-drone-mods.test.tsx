import { fireEvent, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { makeCatalog, makeCharacter } from "@/tests/fixtures";
import {
  GRADES,
  vehicle,
  mod,
  ware,
  renderVehicle,
  installNextTo,
  owning,
} from "./vehicle-drone-gear.helpers";

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
