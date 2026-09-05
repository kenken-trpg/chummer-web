import { fireEvent, render, screen } from "@testing-library/react";
import type { ComponentType } from "react";
import { describe, expect, it, vi } from "vitest";
import type { Character } from "@/lib/types";
import type { TabPanelProps } from "@/components/character/types";
import { translate } from "@/lib/i18n";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import { ArmorGear } from "./ArmorGear";
import { CommlinkGear } from "./CommlinkGear";
import { CyberdeckGear } from "./CyberdeckGear";
import { MiscDrugsGear } from "./MiscDrugsGear";
import { RccGear } from "./RccGear";
import { VehicleDroneGear } from "./VehicleDroneGear";
import { WeaponGear } from "./WeaponGear";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * `gear-panels.test.tsx` covers the buying half — the `<CatalogPicker>` each
 * panel wraps. This covers the other half: the rows a character already owns,
 * where every control emits a patch built by mapping or filtering the whole
 * list on `row.id === item.id`.
 *
 * That predicate is the thing worth testing. Getting it wrong edits the wrong
 * item, and with one owned row of each kind on screen a test cannot tell the
 * difference — so every case here gives the character **two** rows and acts on
 * the second.
 */

// VehicleDroneGear takes an extra `mode`; renderPanel forwards it via `extra`.
type Panel = ComponentType<TabPanelProps & Record<string, never>> | ComponentType<any>;

function renderPanel(
  Panel: Panel,
  character: Character,
  patch: (b: Record<string, unknown>) => void,
  extra: Record<string, unknown> = {},
) {
  return render(
    <Panel
      catalog={makeCatalog()}
      character={character}
      d={character.derived}
      tr={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={patch}
      setCharacter={() => {}}
      {...(extra as any)}
    />,
  );
}

/** Two owned rows, mirrored into `character` and `derived` under their keys. */
function owning(chKey: string, dKey: string, rows: Record<string, unknown>[]): Character {
  return makeCharacter({ [chKey]: rows, derived: { [dKey]: rows } } as any);
}

const rated = (id: string, name: string, rating = 1) => ({
  id,
  name,
  rating,
  rating_max: 6,
  nuyen: 100,
  source: "SR5",
  device_rating: 1,
  dataprocessing: 1,
  firewall: 1,
  programs: 0,
  category: "",
});

const RATING_PANELS: [string, Panel, string, string][] = [
  ["CommlinkGear", CommlinkGear, "commlinks", "commlinks"],
  ["CyberdeckGear", CyberdeckGear, "cyberdecks", "cyberdecks"],
  ["RccGear", RccGear, "rccs", "rccs"],
];

describe.each(RATING_PANELS)("<%s> owned rows", (_name, Panel, chKey, dKey) => {
  const character = () => owning(chKey, dKey, [rated("x1", "First"), rated("x2", "Second")]);

  it("lists everything the character owns", () => {
    renderPanel(Panel, character(), vi.fn());

    expect(screen.getByText("First")).toBeDefined();
    expect(screen.getByText("Second")).toBeDefined();
  });

  it("rating on the second row leaves the first alone", () => {
    const patch = vi.fn();
    renderPanel(Panel, character(), patch);

    fireEvent.change(screen.getAllByRole("spinbutton")[1], { target: { value: "4" } });

    const rows = patch.mock.calls[0][0][chKey] as { id: string; rating: number }[];
    expect(rows).toHaveLength(2); // a map, not a replace
    expect(rows.find((r) => r.id === "x1")?.rating).toBe(1);
    expect(rows.find((r) => r.id === "x2")?.rating).toBe(4);
  });
});

describe("<ArmorGear> owned rows", () => {
  const armor = (id: string, name: string, equipped: boolean) => ({
    id,
    name,
    armor_id: `c-${id}`,
    armor_value: 9,
    contributes: 9,
    equipped,
    rating: 1,
    rating_max: 0,
    nuyen: 900,
    source: "SR5",
    mods: [],
  });
  const character = () =>
    owning("armor", "armor_items", [
      armor("a1", "Lined Coat", true),
      armor("a2", "Actioneer", false),
    ]);

  it("says which pieces are contributing and which are merely owned", () => {
    renderPanel(ArmorGear, character(), vi.fn());

    expect(screen.getByText("Lined Coat")).toBeDefined();
    expect(screen.getByText("Actioneer")).toBeDefined();
  });

  it("equipping the second piece does not unequip the first", () => {
    const patch = vi.fn();
    renderPanel(ArmorGear, character(), patch);

    fireEvent.click(screen.getAllByRole("checkbox")[1]);

    const rows = patch.mock.calls[0][0].armor as { id: string; equipped: boolean }[];
    expect(rows.find((r) => r.id === "a1")?.equipped).toBe(true);
    expect(rows.find((r) => r.id === "a2")?.equipped).toBe(true);
  });
});

describe("<WeaponGear> owned rows", () => {
  const weapon = (id: string, name: string) => ({
    id,
    name,
    weapon_id: `c-${id}`,
    category: "Heavy Pistols",
    type: "Ranged",
    damage: "8P",
    ap: "-1",
    accuracy: "5",
    mode: "SA",
    rc: "0",
    qty: 1,
    nuyen: 725,
    source: "SR5",
    accessories: [],
    ammo_options: [],
  });

  it("renders each owned weapon with its damage code", () => {
    renderPanel(
      WeaponGear,
      owning("weapons", "weapons", [weapon("w1", "Predator"), weapon("w2", "Warhawk")]),
      vi.fn(),
    );

    expect(screen.getByText("Predator")).toBeDefined();
    expect(screen.getByText("Warhawk")).toBeDefined();
    expect(screen.getAllByText(/8P/).length).toBeGreaterThan(0);
  });

  it("removing one weapon keeps the other", () => {
    const patch = vi.fn();
    renderPanel(
      WeaponGear,
      owning("weapons", "weapons", [weapon("w1", "Predator"), weapon("w2", "Warhawk")]),
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "削除" })[1]);

    const rows = patch.mock.calls[0][0].weapons as { id: string }[];
    expect(rows.map((r) => r.id)).toEqual(["w1"]);
  });
});

describe("<MiscDrugsGear> owned rows", () => {
  const gear = (id: string, name: string, parent_id: string | null = null) => ({
    id,
    name,
    gear_id: `c-${id}`,
    category: "Electronics",
    rating: 1,
    rating_max: 0,
    qty: 1,
    nuyen: 50,
    cost: "50",
    source: "SR5",
    parent_id,
  });

  it("nests a child under its parent rather than listing it twice", () => {
    const rows = [gear("g1", "Medkit"), gear("g1a", "Medkit Supplies", "g1"), gear("g2", "Rope")];
    const { container } = renderPanel(MiscDrugsGear, owning("gear", "gear", rows), vi.fn());

    const items = [...container.querySelectorAll(".cyber-item")];
    expect(items).toHaveLength(2); // the child is not a top-level row
    expect(items[0].textContent).toContain("Medkit Supplies");
    expect(items[1].textContent).toContain("Rope");
  });

  it("removing a parent takes its children with it", () => {
    // a child left behind would render as an orphan row referring to nothing
    const patch = vi.fn();
    const rows = [gear("g1", "Medkit"), gear("g1a", "Medkit Supplies", "g1"), gear("g2", "Rope")];
    renderPanel(MiscDrugsGear, owning("gear", "gear", rows), patch);

    // 削除 is the item itself; 外す on the line above is only its child
    fireEvent.click(screen.getAllByRole("button", { name: "削除" })[0]);

    const left = patch.mock.calls[0][0].gear as { id: string }[];
    expect(left.map((r) => r.id)).toEqual(["g2"]);
  });
});

describe("<VehicleDroneGear> owned rows", () => {
  const vehicle = (id: string, name: string) => ({
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
    slots: {},
    subsystems: {},
  });

  const mod = (id: string, name: string, over: Record<string, unknown> = {}) => ({
    id,
    name,
    mod_id: `c-${id}`,
    category: "Powertrain",
    rating: 1,
    rating_max: 6,
    nuyen: 1000,
    slots: 2,
    included: false,
    subsystems: [],
    ...over,
  });

  it("shows vehicles in vehicle mode and drones in drone mode, not both", () => {
    const ch = makeCharacter({
      vehicles: [vehicle("v1", "Americar")],
      drones: [vehicle("dr1", "Steel Lynx")],
      derived: { vehicles: [vehicle("v1", "Americar")], drones: [vehicle("dr1", "Steel Lynx")] },
    } as any);

    renderPanel(VehicleDroneGear, ch, vi.fn(), { mode: "vehicle" });
    expect(screen.getByText("Americar")).toBeDefined();
    expect(screen.queryByText("Steel Lynx")).toBeNull();

    screen.getByText("Americar"); // keep the first render mounted for contrast
    renderPanel(VehicleDroneGear, ch, vi.fn(), { mode: "drone" });
    expect(screen.getByText("Steel Lynx")).toBeDefined();
  });

  it("lists a vehicle's mods and mounts under it", () => {
    const v = {
      ...vehicle("v1", "Americar"),
      mods: [mod("m1", "Rigger Interface"), mod("m2", "Off-Road Suspension")],
      weapon_mounts: [
        { id: "wm1", name: "Standard Mount", nuyen: 2500, slots: 2, included: false },
      ],
    };
    const ch = makeCharacter({
      vehicles: [v],
      vehicle_mods: v.mods,
      weapon_mounts: v.weapon_mounts,
      derived: { vehicles: [v] },
    } as any);

    const { container } = renderPanel(VehicleDroneGear, ch, vi.fn(), { mode: "vehicle" });

    expect(container.textContent).toContain("Rigger Interface");
    expect(container.textContent).toContain("Off-Road Suspension");
    expect(container.textContent).toContain("Standard Mount");
    // an empty mount says so rather than showing a blank where a weapon goes
    expect(container.textContent).toContain(translate("ja", "veh.noWeapon"));
  });

  it("rating on the second mod leaves the first alone", () => {
    const v = {
      ...vehicle("v1", "Americar"),
      mods: [mod("m1", "First"), mod("m2", "Second")],
    };
    const patch = vi.fn();
    renderPanel(
      VehicleDroneGear,
      makeCharacter({ vehicles: [v], vehicle_mods: v.mods, derived: { vehicles: [v] } } as any),
      patch,
      { mode: "vehicle" },
    );

    fireEvent.change(screen.getAllByRole("spinbutton")[1], { target: { value: "5" } });

    const rows = patch.mock.calls[0][0].vehicle_mods as { id: string; rating: number }[];
    expect(rows.find((r) => r.id === "m1")?.rating).toBe(1);
    expect(rows.find((r) => r.id === "m2")?.rating).toBe(5);
  });

  it("an included mod has no remove button — it comes with the vehicle", () => {
    const v = {
      ...vehicle("v1", "Americar"),
      mods: [mod("m1", "Stock Rims", { included: true, rating_max: 0 })],
    };
    renderPanel(
      VehicleDroneGear,
      makeCharacter({ vehicles: [v], vehicle_mods: v.mods, derived: { vehicles: [v] } } as any),
      vi.fn(),
      { mode: "vehicle" },
    );

    expect(screen.queryByRole("button", { name: "外す" })).toBeNull();
  });

  it("mounting a weapon targets that mount only", () => {
    const weapon = { id: "w1", name: "MMG", weapon_id: "cw1", category: "Machine Guns" };
    const v = {
      ...vehicle("v1", "Americar"),
      weapon_mounts: [
        { id: "wm1", name: "Front Mount", nuyen: 2500, slots: 2, included: false },
        { id: "wm2", name: "Rear Mount", nuyen: 2500, slots: 2, included: false },
      ],
    };
    const patch = vi.fn();
    renderPanel(
      VehicleDroneGear,
      makeCharacter({
        vehicles: [v],
        weapons: [weapon],
        weapon_mounts: v.weapon_mounts,
        derived: { vehicles: [v], weapons: [weapon] },
      } as any),
      patch,
      { mode: "vehicle" },
    );

    fireEvent.change(screen.getByRole("combobox", { name: /Rear Mount/ }), {
      target: { value: "w1" },
    });

    const rows = patch.mock.calls[0][0].weapon_mounts as {
      id: string;
      weapon_install_id: string | null;
    }[];
    expect(rows.find((r) => r.id === "wm1")?.weapon_install_id).toBeUndefined();
    expect(rows.find((r) => r.id === "wm2")?.weapon_install_id).toBe("w1");
  });
});
