import { fireEvent, render, screen } from "@testing-library/react";
import type { Derived, InstalledWare, WareCatalogItem } from "@/lib/types";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import { modularMountCandidates, modularVehicleHosts } from "@/lib/character/ware";
import { CyberTab } from "./CyberTab";
import { VehicleModRows } from "./gear/vehicle/VehicleModRows";

const spec = (id: string, extra: Partial<WareCatalogItem> = {}): WareCatalogItem => ({
  id,
  name: id,
  category: "Cyberlimb",
  ess: "0",
  cost: "0",
  minrating: 1,
  maxrating: 1,
  plugin: false,
  has_wireless: false,
  source: "CF",
  page: "0",
  ...extra,
});
const specs = [
  spec("wrist", { modular_mount: "wrist" }),
  spec("hand", { mounts_to: "wrist", allow_subsystems: ["Enhancement"] }),
  spec("blade"),
  spec("enhancement", { category: "Enhancement", plugin: true }),
];
const row = (id: string, ware_id: string, extra: Partial<InstalledWare> = {}): InstalledWare => ({
  id,
  ware_id,
  name: ware_id,
  category: "Cyberlimb",
  grade: "Standard",
  rating: 1,
  wireless: true,
  essence: 0,
  nuyen: 100,
  side: "Left",
  ...extra,
});
const catalog = makeCatalog({
  cyberware: { items: specs, grades: [{ name: "Standard", ess: 1, ess_adapsin: 0.9, cost: 1 }] },
});
const vehicle = {
  id: "drone",
  name: "Doberman",
  category: "Drones: Medium",
  nuyen: 5000,
  mods: [
    {
      id: "mod",
      mod_id: "arm-spec",
      name: "Drone Arm",
      rating: 1,
      rating_max: 0,
      nuyen: 500,
      subsystems: ["Cyberlimb"],
      capacity_max: 15,
      capacity_used: 1,
    },
  ],
};
function fixture(onVehicle: boolean) {
  const rows = [
    row("body", "wrist"),
    row("vehicle", "wrist", { parent_id: "mod" }),
    row("hand", "hand", { parent_id: onVehicle ? "vehicle" : "body", modular_equipped: true }),
    row("blade", "blade", { parent_id: "hand" }),
  ];
  const ch = makeCharacter({
    cyberware: rows,
    derived: { cyberware: rows, drones: [vehicle] },
  } as never);
  return { ch, rows };
}

beforeEach(() => localStorage.setItem("wareCompact", "0"));

it("offers a labeled vehicle connector from the body and changes only the purchased parent", () => {
  const { ch } = fixture(false);
  const patch = vi.fn();
  render(<CyberTab {...panelProps(ch, { catalog, patch })} />);
  const select = screen.getByRole("combobox", {
    name: "hand: モジュラー接続先",
  }) as HTMLSelectElement;
  expect([...select.options].map((option) => option.value)).toEqual(["", "body", "vehicle"]);
  expect(select.options[2].text).toContain("Doberman / Drone Arm");
  fireEvent.change(select, { target: { value: "vehicle" } });
  expect(patch).toHaveBeenCalledWith({
    cyberware: ch.cyberware!.map((ware) =>
      ware.id === "hand" ? { ...ware, parent_id: "vehicle" } : ware,
    ),
  });
});

it("renders descendants in the vehicle and lets the same hand detach or return to the body", () => {
  const { ch } = fixture(true);
  const patch = vi.fn();
  render(
    <VehicleModRows
      {...panelProps(ch, { catalog, patch })}
      item={vehicle as never}
      slotPick={{}}
      setSlotPick={vi.fn()}
    />,
  );
  expect(screen.getByText(/blade/, { selector: "b" })).toBeDefined();
  const select = screen.getByRole("combobox", {
    name: "hand: モジュラー接続先",
  }) as HTMLSelectElement;
  expect(select.value).toBe("vehicle");
  expect(select.selectedOptions[0].disabled).toBe(false);
  fireEvent.change(select, { target: { value: "" } });
  expect(patch).toHaveBeenLastCalledWith({
    cyberware: ch.cyberware!.map((ware) =>
      ware.id === "hand" ? { ...ware, parent_id: null } : ware,
    ),
  });
  fireEvent.change(select, { target: { value: "body" } });
  expect(patch).toHaveBeenLastCalledWith({
    cyberware: ch.cyberware!.map((ware) =>
      ware.id === "hand" ? { ...ware, parent_id: "body" } : ware,
    ),
  });
});

it("adds an enhancement to the nested vehicle hand rather than its connector", () => {
  const { ch } = fixture(true);
  const patch = vi.fn();
  render(
    <VehicleModRows
      {...panelProps(ch, { catalog, patch })}
      item={vehicle as never}
      slotPick={{}}
      setSlotPick={vi.fn()}
    />,
  );
  const mount = screen.getByRole("combobox", { name: "hand: モジュラー接続先" });
  const picker = mount.closest(".cyber-item")!.querySelector(".slot-picker")!;
  fireEvent.click(picker.querySelector("button")!);
  expect(patch).toHaveBeenCalledWith({
    cyberware: [
      ...ch.cyberware!,
      { ware_id: "enhancement", rating: 1, grade: "Standard", wireless: true, parent_id: "hand" },
    ],
  });
});

it("requires exact sides for vehicle hosts and rejects unknown roots and cycles", () => {
  const { ch, rows } = fixture(false);
  const hosts = modularVehicleHosts(ch.derived, (name) => name);
  const plug = { ...rows[2], side: null };
  const invalid = [
    row("orphan", "wrist", { parent_id: "unknown" }),
    row("cycle", "wrist", { parent_id: "cycle" }),
  ];
  expect(
    modularMountCandidates(plug, [...rows, ...invalid], specs, hosts).map(
      (candidate) => candidate.id,
    ),
  ).toEqual(["body"]);
  expect(
    modularMountCandidates(rows[2], [...rows, ...invalid], specs, hosts).map(
      (candidate) => candidate.id,
    ),
  ).toEqual(["body", "vehicle"]);
  expect(
    modularVehicleHosts(
      {
        drones: [{ ...vehicle, mods: [{ ...vehicle.mods[0], subsystems: [] }] }],
      } as unknown as Derived,
      (name) => name,
    ),
  ).toEqual({});
});
